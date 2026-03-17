import argparse
import copy
import hashlib
import json
import logging
import math
import os
import re
import signal
import socket
import subprocess
import sys
import threading
import time
import uuid
from urllib.parse import urlparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict

from src.config.manager import ConfigManager
from src.data.credentials import CredentialManager
from src.data.vault import VaultManager
from src.data.usage_db import UsageDatabase
from src.mcp_server.agent_server import MCPAgentServer
from src.mcp_server.pipeline_v1 import (
    ExecutionRequestV1,
    PreflightGuardV1,
    RouterV1,
    ProviderAdapterV1,
    ObserverV1,
)
from src.providers.factory import ProviderFactory
from src.mcp_server.pipeline_v1 import ExecutionContextV1
from src.mcp_server.interceptor_p3_p1 import repair_json_syntax


logger = logging.getLogger(__name__)


class ServerManager:
    _REQUEST_DEDUP_TTL_SECONDS = 20.0
    _VERTEX_PROBE_CLIENT_TTL_SECONDS = 300.0
    _VERTEX_PROBE_TIMEOUT_SECONDS = 4.0

    def __init__(
        self,
        config: ConfigManager | None = None,
        creds: CredentialManager | None = None,
        usage_db: UsageDatabase | None = None,
        vault: VaultManager | None = None,
    ) -> None:
        self._config = config or ConfigManager()
        self._creds = creds or CredentialManager()
        self._usage_db = usage_db or UsageDatabase()
        self._vault = vault or VaultManager()
        self.active_agents: Dict[str, MCPAgentServer] = {}
        self._request_dedup_cache: dict[str, dict[str, object]] = {}
        self._vertex_probe_client_cache: dict[tuple[str, str, str, str], dict[str, object]] = {}
        self._vertex_probe_cache_lock = threading.Lock()
        self._vertex_probe_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="vertex-probe")

    @staticmethod
    def _connection_port(connection: dict) -> int | None:
        if "port" in connection:
            try:
                return int(connection.get("port"))
            except Exception:
                return None
        endpoint = str(connection.get("endpoint") or "").strip()
        m = re.match(r"^https?://(?:127\.0\.0\.1|localhost):(\d+)/sse$", endpoint)
        if not m:
            return None
        try:
            return int(m.group(1))
        except Exception:
            return None

    @staticmethod
    def _probe_sse_endpoint(port: int, timeout_seconds: float = 0.5) -> tuple[bool, str, str]:
        host = "127.0.0.1"
        try:
            with socket.create_connection((host, int(port)), timeout_seconds) as sock:
                sock.settimeout(timeout_seconds)
                # TCP-level reachability is sufficient and avoids mutating/interrupting SSE flow.
                _ = sock.getpeername()
            return True, "TCP_CONNECT_OK", ""
        except Exception as exc:
            return False, "", str(exc)

    @staticmethod
    def _endpoint_reachable(port: int, timeout_seconds: float = 0.5) -> bool:
        reachable, _, _ = ServerManager._probe_sse_endpoint(port, timeout_seconds=timeout_seconds)
        return reachable

    @staticmethod
    def _tail_text(value: str | None, limit: int = 240) -> str:
        s = str(value or "").replace("\r", " ").replace("\n", " ").strip()
        if len(s) <= limit:
            return s
        return s[-limit:]

    @staticmethod
    def _canonical_provider(provider_id: str) -> str:
        raw = str(provider_id or "").strip().lower()
        if raw == "vertex":
            return "vertex_ai"
        return raw or "unknown"

    @staticmethod
    def _sanitize_error_raw(value: object) -> str:
        text = str(value or "").replace("\r", " ").replace("\n", " ").strip()
        text = re.sub(r"(?i)bearer\s+[a-z0-9._\-+/=]+", "Bearer [REDACTED]", text)
        text = re.sub(r"(?i)(api[_\- ]?key|token|secret|authorization)\s*[:=]\s*[^;\s]+", r"\1=[REDACTED]", text)
        path_patterns = [
            r'(^|[\s\'"=(\[])([a-zA-Z]:\\(?:[^\\\r\n]+))',
            r'(^|[\s\'"=(\[])(\\\\[^\s\'":;<>()\[\]]+)',
            r'(^|[\s\'"=(\[])(/(?:[^/\s]+/)+[^/\s\'":;<>()\[\]]+)',
        ]
        for pattern in path_patterns:
            text = re.sub(pattern, lambda m: f"{m.group(1)}[REDACTED_PATH]", text)
        if len(text) > 700:
            text = text[:700]
        return text

    @staticmethod
    def _classify_canonical_error_code(reason: str, provider_id: str, phase: str) -> str:
        msg = str(reason or "").lower()
        provider = str(provider_id or "").lower()
        if "hf_enable_network must be true" in msg or "network gate is disabled" in msg:
            return "NETWORK_GATE_BLOCKED"
        if "model not found" in msg or "not found" in msg or "404" in msg:
            return "MODEL_NOT_FOUND"
        if provider in {"vertex", "vertex_ai"} and ("permission" in msg or "access denied" in msg):
            return "MODEL_NOT_FOUND"
        if phase == "preflight":
            return "PREFLIGHT_FAILED"
        return "EXECUTION_FAILED"

    @classmethod
    def _build_canonical_error(
        cls,
        *,
        phase: str,
        provider_id: str,
        model_id: str,
        request_id: str | None,
        reason: str,
        raw: object = "",
        code: str | None = None,
    ) -> dict[str, object]:
        final_reason = str(reason or "").strip() or "request failed"
        error_code = str(code or "").strip() or cls._classify_canonical_error_code(final_reason, provider_id, phase)
        envelope: dict[str, object] = {
            "code": error_code,
            "provider": cls._canonical_provider(provider_id),
            "model_id": str(model_id or "").strip() or None,
            "request_id": str(request_id or "").strip() or None,
            "reason": final_reason,
        }
        sanitized = cls._sanitize_error_raw(raw)
        if sanitized:
            envelope["raw"] = sanitized
        return envelope

    @staticmethod
    def _validate_http_endpoint(value: str, field_name: str) -> list[str]:
        errors: list[str] = []
        endpoint = str(value or "").strip()
        if not endpoint:
            return errors
        if any(ch.isspace() for ch in endpoint):
            errors.append(f"{field_name} must not contain whitespace")
            return errors
        parsed = urlparse(endpoint)
        if parsed.scheme not in ("http", "https"):
            errors.append(f"{field_name} must start with http:// or https://")
            return errors
        if not parsed.netloc:
            errors.append(f"{field_name} must be a valid URL with host")
            return errors
        return errors

    @staticmethod
    def _runtime_proc_alive(pid: int) -> bool:
        if pid <= 0:
            return False
        try:
            os.kill(int(pid), 0)
            return True
        except OSError as exc:
            # Windows may return access denied for existing processes we do not own.
            if os.name == "nt" and getattr(exc, "winerror", None) == 5:
                return True
            return False
        except Exception:
            return False

    @staticmethod
    def _listener_pid_for_port(port: int) -> int | None:
        if int(port) <= 0:
            return None
        if os.name != "nt":
            return None
        try:
            proc = subprocess.run(
                ["netstat", "-ano", "-p", "tcp"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            if proc.returncode != 0:
                return None
            pattern = re.compile(rf"^\s*TCP\s+\S+:{int(port)}\s+\S+\s+LISTENING\s+(\d+)\s*$", re.IGNORECASE)
            for line in str(proc.stdout or "").splitlines():
                m = pattern.match(line)
                if not m:
                    continue
                try:
                    pid = int(m.group(1))
                    if pid > 0:
                        return pid
                except Exception:
                    continue
            return None
        except Exception:
            return None

    @staticmethod
    def _terminate_runtime_process(pid: int) -> tuple[bool, str]:
        if pid <= 0:
            return True, ""
        if os.name != "nt":
            try:
                os.kill(pid, signal.SIGTERM)
                return True, ""
            except Exception as exc:
                return False, str(exc)

        # Windows: SIGTERM may fail with WinError 87 for some detached/runtime processes.
        try:
            os.kill(pid, signal.SIGTERM)
            return True, ""
        except Exception as primary_exc:
            try:
                tk = subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    capture_output=True,
                    text=True,
                    timeout=8,
                    check=False,
                )
            except Exception as taskkill_exc:
                return False, f"{primary_exc}; taskkill_failed={taskkill_exc}"

            if tk.returncode == 0:
                return True, ""
            stdout_tail = ServerManager._tail_text(tk.stdout)
            stderr_tail = ServerManager._tail_text(tk.stderr)
            taskkill_text = f"{stdout_tail} {stderr_tail}".lower()
            # Treat "process not found" as already-stopped to keep stop idempotent.
            if "not found" in taskkill_text or "cannot find the process" in taskkill_text:
                return True, ""
            if not ServerManager._runtime_proc_alive(pid):
                return True, ""
            return (
                False,
                f"{primary_exc}; taskkill_rc={tk.returncode}, stdout={stdout_tail or 'none'}, stderr={stderr_tail or 'none'}",
            )

    @staticmethod
    def _runtime_command(connection_id: str, name: str, port: int) -> list[str]:
        runtime_python = sys.executable
        if os.name == "nt":
            pythonw = Path(sys.executable).with_name("pythonw.exe")
            if pythonw.exists():
                runtime_python = str(pythonw)
        return [
            runtime_python,
            "-m",
            "src.mcp_server.manager",
            "--connection-runtime",
            "--connection-id",
            str(connection_id),
            "--name",
            str(name),
            "--port",
            str(int(port)),
        ]

    def create_agent(
        self,
        name: str,
        model_id: str,
        credentials_path: str,
        project_id: str,
    ) -> dict:
        logger.info("Creating agent name=%s project_id=%s", name, project_id)
        agent = self._config.add_agent(
            name=name,
            project_id=project_id,
            location="us-central1",
            model_id=model_id,
            price_per_1m_input=0.0,
            price_per_1m_output=0.0,
            port=None,
        )
        self._creds.save_credential(agent["id"], credentials_path)

        server = MCPAgentServer(
            name=agent["name"],
            port=int(agent["port"]),
            project_id=agent["project_id"],
            location=agent["location"],
            agent_id=agent["id"],
            execute_request_v1=self.execute_request_v1,
        )
        self.active_agents[agent["id"]] = server

        logger.info(
            "Agent created id=%s name=%s port=%s",
            agent["id"],
            agent["name"],
            agent["port"],
        )
        return agent

    def start_agent(self, agent_id: str) -> dict:
        logger.info("Starting agent id=%s", agent_id)
        agent = self._config.get_agent(agent_id)
        if not agent:
            raise ValueError("Agent not found")

        server = self.active_agents.get(agent_id)
        if server is None:
            server = MCPAgentServer(
                name=agent["name"],
                port=int(agent["port"]),
                project_id=agent["project_id"],
                location=agent["location"],
                agent_id=agent_id,
                execute_request_v1=self.execute_request_v1,
            )
            self.active_agents[agent_id] = server

        started = server.start()
        if not started:
            logger.error(
                "Failed to start agent id=%s on port=%s",
                agent_id,
                agent["port"],
            )
            raise RuntimeError(f"Failed to start agent on port {agent['port']}")

        self._config.update_agent_status(agent_id, "running")
        config = server.get_mcp_config()
        logger.info("Agent id=%s started successfully", agent_id)
        return config

    def stop_agent(self, agent_id: str) -> None:
        logger.info("Stopping agent id=%s", agent_id)
        server = self.active_agents.get(agent_id)
        if server:
            server.stop()
            self._config.update_agent_status(agent_id, "stopped")
            del self.active_agents[agent_id]
            logger.info("Agent id=%s stopped", agent_id)

    def stop_all(self) -> None:
        logger.info("Stopping all agents")
        for agent_id, server in list(self.active_agents.items()):
            server.stop()
            self._config.update_agent_status(agent_id, "stopped")
            del self.active_agents[agent_id]
        logger.info("All agents stopped")

    def list_connections(self) -> dict[str, object]:
        connections = self._config.list_connections()
        for connection in connections:
            if not isinstance(connection, dict):
                continue
            connection_id = str(connection.get("id") or "").strip()
            if not connection_id:
                continue
            status = str(connection.get("status") or "stopped").strip().lower()
            pid_value = connection.get("runtime_pid")
            pid = int(pid_value) if isinstance(pid_value, int) or str(pid_value).isdigit() else 0
            port = self._connection_port(connection)
            if status == "running":
                connection["status"] = "running"
                if port is not None:
                    connection["endpoint"] = f"http://127.0.0.1:{int(port)}/sse"
                if pid > 0:
                    connection["runtime_pid"] = int(pid)
        return {"ok": True, "errors": [], "warnings": [], "connections": connections}

    def vault_list(self) -> dict[str, object]:
        try:
            entries = self._vault.list_entries()
            return {"ok": True, "errors": [], "warnings": [], "data": {"entries": entries}}
        except Exception as exc:
            return {"ok": False, "errors": [f"Vault storage unavailable: {exc}"], "warnings": [], "data": {}}

    def vault_create(self, params: dict) -> dict[str, object]:
        entry = params.get("entry") if isinstance(params.get("entry"), dict) else {}
        name = entry.get("name") if isinstance(entry, dict) else None
        entry_type = entry.get("type") if isinstance(entry, dict) else None
        secret = entry.get("secret") if isinstance(entry, dict) else None
        import_mode = entry.get("import_mode") if isinstance(entry, dict) else None
        try:
            created = self._vault.create_entry(
                str(name or ""),
                str(entry_type or ""),
                str(secret or ""),
                str(import_mode or "").strip() or None,
            )
            return {"ok": True, "errors": [], "warnings": [], "data": {"entry": created}}
        except ValueError as exc:
            return {"ok": False, "errors": [str(exc)], "warnings": [], "data": {}}
        except Exception as exc:
            return {"ok": False, "errors": [f"Vault storage unavailable: {exc}"], "warnings": [], "data": {}}

    def vault_read(self, params: dict) -> dict[str, object]:
        entry_id = str(params.get("entry_id") or "").strip()
        try:
            metadata = self._vault.get_entry_metadata(entry_id)
            return {"ok": True, "errors": [], "warnings": [], "data": metadata}
        except ValueError as exc:
            return {"ok": False, "errors": [str(exc)], "warnings": [], "data": {}}
        except Exception:
            return {"ok": False, "errors": ["Vault storage unavailable"], "warnings": [], "data": {}}

    def vault_delete(self, params: dict) -> dict[str, object]:
        entry_id = str(params.get("entry_id") or "").strip()
        try:
            self._vault.delete_entry(entry_id)
            return {"ok": True, "errors": [], "warnings": [], "data": {"id": entry_id}}
        except ValueError as exc:
            return {"ok": False, "errors": [str(exc)], "warnings": [], "data": {}}
        except Exception as exc:
            return {"ok": False, "errors": [f"Vault storage unavailable: {exc}"], "warnings": [], "data": {}}

    def vault_pick_credentials_path(self) -> dict[str, object]:
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            try:
                root.attributes("-topmost", True)
            except Exception:
                pass
            picked = filedialog.askopenfilename(
                title="Select credentials file",
                filetypes=[("All files", "*.*"), ("JSON files", "*.json"), ("Text files", "*.txt")],
            )
            root.destroy()
            return {"ok": True, "errors": [], "warnings": [], "data": {"path": str(picked or "")}}
        except Exception:
            return {"ok": False, "errors": ["File picker unavailable"], "warnings": [], "data": {}}

    @staticmethod
    def _persona_now_utc() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _canonicalize_persona_state(self, payload: dict | None) -> dict:
        source = payload if isinstance(payload, dict) else {}
        base = self._config.default_persona_state()

        selected_persona_id = str(source.get("selected_persona_id") or base.get("selected_persona_id") or "default").strip() or "default"
        selected_target_id = str(source.get("selected_target_id") or base.get("selected_target_id") or "bridge_alpha").strip() or "bridge_alpha"
        legacy_target_ids = {"bridge_alpha", "bridge_beta", "conn_local_a", "conn_remote_staging"}
        connection_ids = [
            str(connection.get("id") or "").strip()
            for connection in self._config.list_connections()
            if isinstance(connection, dict) and str(connection.get("id") or "").strip()
        ]
        if connection_ids and selected_target_id in legacy_target_ids:
            selected_target_id = connection_ids[0]

        presets_src = source.get("presets")
        presets: list[dict[str, str]] = []
        if isinstance(presets_src, list):
            for item in presets_src:
                if not isinstance(item, dict):
                    continue
                pid = str(item.get("id") or "").strip() or f"preset_{uuid.uuid4().hex[:12]}"
                name = str(item.get("name") or "").strip()
                text = str(item.get("text") or "")
                if not name:
                    continue
                presets.append({"id": pid, "name": name, "text": text})
        if not presets:
            defaults = base.get("presets")
            if isinstance(defaults, list):
                for item in defaults:
                    if isinstance(item, dict):
                        presets.append(
                            {
                                "id": str(item.get("id") or f"preset_{uuid.uuid4().hex[:12]}"),
                                "name": str(item.get("name") or "Preset"),
                                "text": str(item.get("text") or ""),
                            }
                        )

        selected_preset_id = str(source.get("selected_preset_id") or "").strip()
        if not selected_preset_id or not any(p.get("id") == selected_preset_id for p in presets):
            selected_preset_id = str(presets[0].get("id"))

        applied_src = source.get("applied_rows")
        applied_rows: list[dict[str, str]] = []
        if isinstance(applied_src, list):
            for item in applied_src:
                if not isinstance(item, dict):
                    continue
                persona_id = str(item.get("persona_id") or "").strip()
                target_id = str(item.get("target_id") or "").strip()
                if not persona_id or not target_id:
                    continue
                row_id = str(item.get("id") or "").strip() or f"applied_{uuid.uuid4().hex}"
                applied_at = str(item.get("applied_at") or "").strip() or self._persona_now_utc()
                applied_rows.append(
                    {
                        "id": row_id,
                        "persona_id": persona_id,
                        "target_id": target_id,
                        "applied_at": applied_at,
                    }
                )

        return {
            "selected_persona_id": selected_persona_id,
            "selected_target_id": selected_target_id,
            "applied_rows": applied_rows,
            "presets": presets,
            "selected_preset_id": selected_preset_id,
        }

    def get_policies_persona_state(self, payload: dict | None = None) -> dict[str, object]:
        state = self._canonicalize_persona_state(self._config.get_policies_persona_state())
        return {"ok": True, "errors": [], "warnings": [], "state": state}

    def set_policies_persona_state(self, payload: dict | None = None) -> dict[str, object]:
        data = payload if isinstance(payload, dict) else {}
        state_payload = data.get("state")
        if not isinstance(state_payload, dict):
            return {
                "ok": False,
                "errors": ["state is required"],
                "warnings": [],
                "error_code": "invalid_persona_state",
            }
        if not isinstance(state_payload.get("selected_persona_id"), str) or not str(state_payload.get("selected_persona_id") or "").strip():
            return {
                "ok": False,
                "errors": ["selected_persona_id is required"],
                "warnings": [],
                "error_code": "invalid_persona_state",
            }
        if not isinstance(state_payload.get("selected_target_id"), str) or not str(state_payload.get("selected_target_id") or "").strip():
            return {
                "ok": False,
                "errors": ["selected_target_id is required"],
                "warnings": [],
                "error_code": "invalid_persona_state",
            }
        if "applied_rows" in state_payload and not isinstance(state_payload.get("applied_rows"), list):
            return {
                "ok": False,
                "errors": ["applied_rows must be a list"],
                "warnings": [],
                "error_code": "invalid_persona_state",
            }
        if "presets" in state_payload and not isinstance(state_payload.get("presets"), list):
            return {
                "ok": False,
                "errors": ["presets must be a list"],
                "warnings": [],
                "error_code": "invalid_persona_state",
            }
        canonical = self._canonicalize_persona_state(state_payload)
        persisted = self._config.set_policies_persona_state(canonical)
        return {"ok": True, "errors": [], "warnings": [], "state": persisted}

    @staticmethod
    def _resolve_persona_preset_id(candidate: str, preset_ids: set[str], preset_id_by_name: dict[str, str]) -> str:
        raw = str(candidate or "").strip()
        if not raw:
            return ""
        if raw in preset_ids:
            return raw
        aliases = {
            "default": "preset_default",
            "analyst": "preset_analyst",
            "concise": "preset_concise",
        }
        alias_id = aliases.get(raw.lower())
        if alias_id and alias_id in preset_ids:
            return alias_id
        return preset_id_by_name.get(raw.lower(), "")

    def _resolve_persona_text_for_connection(self, connection_id: str) -> str:
        cid = str(connection_id or "").strip()
        if not cid:
            return ""
        state = self._canonicalize_persona_state(self._config.get_policies_persona_state())
        presets_src = state.get("presets")
        if not isinstance(presets_src, list):
            return ""

        preset_text_by_id: dict[str, str] = {}
        preset_id_by_name: dict[str, str] = {}
        for item in presets_src:
            if not isinstance(item, dict):
                continue
            pid = str(item.get("id") or "").strip()
            if not pid:
                continue
            preset_text_by_id[pid] = str(item.get("text") or "")
            name = str(item.get("name") or "").strip().lower()
            if name and name not in preset_id_by_name:
                preset_id_by_name[name] = pid
        if not preset_text_by_id:
            return ""

        preset_ids = set(preset_text_by_id.keys())
        applied_rows = state.get("applied_rows")
        resolved_preset_id = ""
        if isinstance(applied_rows, list):
            # Most-recent matching row wins.
            for row in reversed(applied_rows):
                if not isinstance(row, dict):
                    continue
                if str(row.get("target_id") or "").strip() != cid:
                    continue
                resolved_preset_id = self._resolve_persona_preset_id(
                    str(row.get("persona_id") or ""),
                    preset_ids,
                    preset_id_by_name,
                )
                if resolved_preset_id:
                    break

        if not resolved_preset_id:
            selected_target_id = str(state.get("selected_target_id") or "").strip()
            if selected_target_id == cid:
                resolved_preset_id = self._resolve_persona_preset_id(
                    str(state.get("selected_persona_id") or ""),
                    preset_ids,
                    preset_id_by_name,
                )

        if not resolved_preset_id:
            return ""
        return str(preset_text_by_id.get(resolved_preset_id) or "").strip()

    def _canonicalize_optimizations_state(self, payload: dict | None) -> dict:
        source = payload if isinstance(payload, dict) else {}
        base = self._config.default_optimizations_state()
        return {
            "context_caching_enabled": bool(
                source.get("context_caching_enabled", base.get("context_caching_enabled", False))
            ),
            "request_dedup_enabled": bool(
                source.get("request_dedup_enabled", base.get("request_dedup_enabled", False))
            ),
        }

    def get_policies_optimizations_state(self, payload: dict | None = None) -> dict[str, object]:
        state = self._canonicalize_optimizations_state(self._config.get_policies_optimizations_state())
        return {"ok": True, "errors": [], "warnings": [], "state": state}

    def set_policies_optimizations_state(self, payload: dict | None = None) -> dict[str, object]:
        data = payload if isinstance(payload, dict) else {}
        state_payload = data.get("state")
        if not isinstance(state_payload, dict):
            return {
                "ok": False,
                "errors": ["state is required"],
                "warnings": [],
                "error_code": "invalid_optimizations_state",
            }
        if not isinstance(state_payload.get("context_caching_enabled"), bool):
            return {
                "ok": False,
                "errors": ["context_caching_enabled must be boolean"],
                "warnings": [],
                "error_code": "invalid_optimizations_state",
            }
        if not isinstance(state_payload.get("request_dedup_enabled"), bool):
            return {
                "ok": False,
                "errors": ["request_dedup_enabled must be boolean"],
                "warnings": [],
                "error_code": "invalid_optimizations_state",
            }
        canonical = self._canonicalize_optimizations_state(state_payload)
        persisted = self._config.set_policies_optimizations_state(canonical)
        return {"ok": True, "errors": [], "warnings": [], "state": persisted}

    @staticmethod
    def _is_budget_unit(value: str) -> bool:
        return value in ("usd_per_day", "tokens_per_day")

    def _canonicalize_resilience_budget_state(self, payload: dict | None) -> dict:
        source = payload if isinstance(payload, dict) else {}
        base = self._config.default_resilience_budget_state()
        selected_scope_id = str(
            source.get("selected_scope_id") or base.get("selected_scope_id") or "all"
        ).strip() or "all"
        limit_value = str(source.get("limit_value") if source.get("limit_value") is not None else base.get("limit_value") or "").strip()
        unit_raw = str(source.get("unit") or base.get("unit") or "usd_per_day").strip()
        unit = unit_raw if self._is_budget_unit(unit_raw) else "usd_per_day"

        applied_src = source.get("applied_guards")
        applied_guards: list[dict[str, str]] = []
        if isinstance(applied_src, list):
            for item in applied_src:
                if not isinstance(item, dict):
                    continue
                scope_id = str(item.get("scope_id") or "").strip()
                row_limit = str(item.get("limit_value") if item.get("limit_value") is not None else "").strip()
                row_unit_raw = str(item.get("unit") or "").strip()
                if not scope_id or not row_limit or not self._is_budget_unit(row_unit_raw):
                    continue
                row_id = str(item.get("id") or "").strip() or f"guard_{uuid.uuid4().hex}"
                applied_at = str(item.get("applied_at") or "").strip() or self._persona_now_utc()
                applied_guards.append(
                    {
                        "id": row_id,
                        "scope_id": scope_id,
                        "limit_value": row_limit,
                        "unit": row_unit_raw,
                        "applied_at": applied_at,
                    }
                )

        return {
            "selected_scope_id": selected_scope_id,
            "limit_value": limit_value,
            "unit": unit,
            "applied_guards": applied_guards,
        }

    def get_resilience_budget_state(self, payload: dict | None = None) -> dict[str, object]:
        state = self._canonicalize_resilience_budget_state(self._config.get_resilience_budget_state())
        return {"ok": True, "errors": [], "warnings": [], "state": state}

    def set_resilience_budget_state(self, payload: dict | None = None) -> dict[str, object]:
        data = payload if isinstance(payload, dict) else {}
        state_payload = data.get("state")
        if not isinstance(state_payload, dict):
            return {
                "ok": False,
                "errors": ["state is required"],
                "warnings": [],
                "error_code": "invalid_resilience_budget_state",
            }
        if not isinstance(state_payload.get("selected_scope_id"), str) or not str(state_payload.get("selected_scope_id") or "").strip():
            return {
                "ok": False,
                "errors": ["selected_scope_id is required"],
                "warnings": [],
                "error_code": "invalid_resilience_budget_state",
            }
        if not isinstance(state_payload.get("limit_value"), str):
            return {
                "ok": False,
                "errors": ["limit_value must be string"],
                "warnings": [],
                "error_code": "invalid_resilience_budget_state",
            }
        unit_value = str(state_payload.get("unit") or "").strip()
        if not self._is_budget_unit(unit_value):
            return {
                "ok": False,
                "errors": ["unit must be one of: usd_per_day, tokens_per_day"],
                "warnings": [],
                "error_code": "invalid_resilience_budget_state",
            }
        guards_payload = state_payload.get("applied_guards")
        if guards_payload is not None and not isinstance(guards_payload, list):
            return {
                "ok": False,
                "errors": ["applied_guards must be a list"],
                "warnings": [],
                "error_code": "invalid_resilience_budget_state",
            }
        if isinstance(guards_payload, list):
            seen_guard_keys: set[str] = set()
            for item in guards_payload:
                if not isinstance(item, dict):
                    return {
                        "ok": False,
                        "errors": ["applied_guards items must be objects"],
                        "warnings": [],
                        "error_code": "invalid_resilience_budget_state",
                    }
                guard_scope = str(item.get("scope_id") or "").strip()
                guard_limit = item.get("limit_value")
                guard_unit = str(item.get("unit") or "").strip()
                if not guard_scope:
                    return {
                        "ok": False,
                        "errors": ["applied_guards.scope_id is required"],
                        "warnings": [],
                        "error_code": "invalid_resilience_budget_state",
                    }
                if not isinstance(guard_limit, str):
                    return {
                        "ok": False,
                        "errors": ["applied_guards.limit_value must be string"],
                        "warnings": [],
                        "error_code": "invalid_resilience_budget_state",
                    }
                if not self._is_budget_unit(guard_unit):
                    return {
                        "ok": False,
                        "errors": ["applied_guards.unit must be one of: usd_per_day, tokens_per_day"],
                        "warnings": [],
                        "error_code": "invalid_resilience_budget_state",
                    }
                guard_key = f"{guard_scope}::{guard_unit}"
                if guard_key in seen_guard_keys:
                    return {
                        "ok": False,
                        "errors": ["duplicate guard for same scope/unit is not allowed"],
                        "warnings": [],
                        "error_code": "invalid_resilience_budget_state",
                    }
                seen_guard_keys.add(guard_key)
        canonical = self._canonicalize_resilience_budget_state(state_payload)
        persisted = self._config.set_resilience_budget_state(canonical)
        return {"ok": True, "errors": [], "warnings": [], "state": persisted}

    @staticmethod
    def _is_interceptor_mode(value: str) -> bool:
        return value in ("off", "safe", "aggressive")

    def _canonicalize_resilience_interceptors_state(self, payload: dict | None) -> dict:
        source = payload if isinstance(payload, dict) else {}
        base = self._config.default_resilience_interceptors_state()
        enabled_in = source.get("enabled_by_id") if isinstance(source.get("enabled_by_id"), dict) else {}
        settings_in = source.get("settings_by_id") if isinstance(source.get("settings_by_id"), dict) else {}

        default_enabled = base.get("enabled_by_id") if isinstance(base.get("enabled_by_id"), dict) else {}
        default_settings = base.get("settings_by_id") if isinstance(base.get("settings_by_id"), dict) else {}

        enabled = dict(default_enabled)
        for key, value in enabled_in.items():
            normalized_key = str(key or "").strip()
            if not normalized_key:
                continue
            enabled[normalized_key] = bool(value)

        settings = dict(default_settings)
        for key, value in settings_in.items():
            normalized_key = str(key or "").strip()
            if not normalized_key or not isinstance(value, dict):
                continue
            default_row = settings.get(normalized_key) if isinstance(settings.get(normalized_key), dict) else {}
            mode_raw = str(value.get("mode") or default_row.get("mode") or "safe").strip()
            mode = mode_raw if self._is_interceptor_mode(mode_raw) else "safe"
            raw_attempts = value.get("max_attempts", default_row.get("max_attempts", 0))
            try:
                max_attempts = int(raw_attempts)
            except Exception:
                max_attempts = 0
            if max_attempts < 0:
                max_attempts = 0
            strict_json = bool(value.get("strict_json", default_row.get("strict_json", True)))
            note = str(value.get("note") if value.get("note") is not None else default_row.get("note") or "")
            settings[normalized_key] = {
                "mode": mode,
                "max_attempts": max_attempts,
                "strict_json": strict_json,
                "note": note,
            }

        return {
            "enabled_by_id": enabled,
            "settings_by_id": settings,
        }

    def get_resilience_interceptors_state(self, payload: dict | None = None) -> dict[str, object]:
        state = self._canonicalize_resilience_interceptors_state(self._config.get_resilience_interceptors_state())
        return {"ok": True, "errors": [], "warnings": [], "result": state}

    def set_resilience_interceptors_state(self, payload: dict | None = None) -> dict[str, object]:
        data = payload if isinstance(payload, dict) else {}
        state_payload = data.get("state")
        if not isinstance(state_payload, dict):
            return {
                "ok": False,
                "errors": ["state is required"],
                "warnings": [],
                "error_code": "invalid_resilience_interceptors_state",
            }
        enabled_by_id = state_payload.get("enabled_by_id")
        settings_by_id = state_payload.get("settings_by_id")
        if not isinstance(enabled_by_id, dict):
            return {
                "ok": False,
                "errors": ["enabled_by_id must be an object"],
                "warnings": [],
                "error_code": "invalid_resilience_interceptors_state",
            }
        if not isinstance(settings_by_id, dict):
            return {
                "ok": False,
                "errors": ["settings_by_id must be an object"],
                "warnings": [],
                "error_code": "invalid_resilience_interceptors_state",
            }
        for key, value in enabled_by_id.items():
            if not str(key or "").strip():
                return {
                    "ok": False,
                    "errors": ["enabled_by_id key is required"],
                    "warnings": [],
                    "error_code": "invalid_resilience_interceptors_state",
                }
            if not isinstance(value, bool):
                return {
                    "ok": False,
                    "errors": ["enabled_by_id values must be boolean"],
                    "warnings": [],
                    "error_code": "invalid_resilience_interceptors_state",
                }
        for key, row in settings_by_id.items():
            if not str(key or "").strip():
                return {
                    "ok": False,
                    "errors": ["settings_by_id key is required"],
                    "warnings": [],
                    "error_code": "invalid_resilience_interceptors_state",
                }
            if not isinstance(row, dict):
                return {
                    "ok": False,
                    "errors": ["settings_by_id values must be objects"],
                    "warnings": [],
                    "error_code": "invalid_resilience_interceptors_state",
                }
            mode = str(row.get("mode") or "").strip()
            if not self._is_interceptor_mode(mode):
                return {
                    "ok": False,
                    "errors": ["settings_by_id.mode must be one of: off, safe, aggressive"],
                    "warnings": [],
                    "error_code": "invalid_resilience_interceptors_state",
                }
            max_attempts = row.get("max_attempts")
            if not isinstance(max_attempts, int):
                return {
                    "ok": False,
                    "errors": ["settings_by_id.max_attempts must be integer"],
                    "warnings": [],
                    "error_code": "invalid_resilience_interceptors_state",
                }
            if max_attempts < 0:
                return {
                    "ok": False,
                    "errors": ["settings_by_id.max_attempts must be >= 0"],
                    "warnings": [],
                    "error_code": "invalid_resilience_interceptors_state",
                }
            if not isinstance(row.get("strict_json"), bool):
                return {
                    "ok": False,
                    "errors": ["settings_by_id.strict_json must be boolean"],
                    "warnings": [],
                    "error_code": "invalid_resilience_interceptors_state",
                }
            if "note" in row and not isinstance(row.get("note"), str):
                return {
                    "ok": False,
                    "errors": ["settings_by_id.note must be string"],
                    "warnings": [],
                    "error_code": "invalid_resilience_interceptors_state",
                }
        canonical = self._canonicalize_resilience_interceptors_state(state_payload)
        persisted = self._config.set_resilience_interceptors_state(canonical)
        return {"ok": True, "errors": [], "warnings": [], "result": persisted}

    def _canonicalize_dashboard_state(self, payload: dict | None) -> dict:
        source = payload if isinstance(payload, dict) else {}
        base = self._config.default_dashboard_state()

        def list_of_dicts(value: object, default_key: str) -> list[dict]:
            if not isinstance(value, list):
                value = base.get(default_key)
            out: list[dict] = []
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        out.append(dict(item))
            return out

        def parse_int_cfg(
            value: object,
            fallback: int,
            *,
            minimum: int | None = None,
            maximum: int | None = None,
        ) -> int:
            try:
                parsed = int(value)
            except Exception:
                parsed = int(fallback)
            if minimum is not None and parsed < minimum:
                parsed = minimum
            if maximum is not None and parsed > maximum:
                parsed = maximum
            return parsed

        def parse_float_cfg(
            value: object,
            fallback: float,
            *,
            minimum: float | None = None,
            maximum: float | None = None,
        ) -> float:
            try:
                parsed = float(value)
            except Exception:
                parsed = float(fallback)
            if not math.isfinite(parsed):
                parsed = float(fallback)
            if minimum is not None and parsed < minimum:
                parsed = minimum
            if maximum is not None and parsed > maximum:
                parsed = maximum
            return parsed

        default_health_cfg = base.get("health_alerts_config")
        base_health_cfg = default_health_cfg if isinstance(default_health_cfg, dict) else {}
        source_health_cfg = source.get("health_alerts_config")
        health_cfg_src = source_health_cfg if isinstance(source_health_cfg, dict) else {}
        health_alerts_config = {
            "window_rows": parse_int_cfg(health_cfg_src.get("window_rows"), int(base_health_cfg.get("window_rows", 500)), minimum=50, maximum=5000),
            "min_samples_total": parse_int_cfg(health_cfg_src.get("min_samples_total"), int(base_health_cfg.get("min_samples_total", 20)), minimum=1, maximum=5000),
            "min_samples_success": parse_int_cfg(health_cfg_src.get("min_samples_success"), int(base_health_cfg.get("min_samples_success", 10)), minimum=1, maximum=5000),
            "success_rate_warning_pct": parse_float_cfg(health_cfg_src.get("success_rate_warning_pct"), float(base_health_cfg.get("success_rate_warning_pct", 95.0)), minimum=1.0, maximum=100.0),
            "success_rate_critical_pct": parse_float_cfg(health_cfg_src.get("success_rate_critical_pct"), float(base_health_cfg.get("success_rate_critical_pct", 85.0)), minimum=0.0, maximum=100.0),
            "latency_warning_ms": parse_int_cfg(health_cfg_src.get("latency_warning_ms"), int(base_health_cfg.get("latency_warning_ms", 8000)), minimum=1, maximum=120000),
            "latency_critical_ms": parse_int_cfg(health_cfg_src.get("latency_critical_ms"), int(base_health_cfg.get("latency_critical_ms", 15000)), minimum=1, maximum=240000),
            "budget_warning_pct": parse_float_cfg(health_cfg_src.get("budget_warning_pct"), float(base_health_cfg.get("budget_warning_pct", 75.0)), minimum=1.0, maximum=1000.0),
            "budget_critical_pct": parse_float_cfg(health_cfg_src.get("budget_critical_pct"), float(base_health_cfg.get("budget_critical_pct", 90.0)), minimum=1.0, maximum=1000.0),
            "monitor_only": bool(health_cfg_src.get("monitor_only", base_health_cfg.get("monitor_only", True))),
        }

        return {
            "kpis": list_of_dicts(source.get("kpis"), "kpis"),
            "recent_requests": list_of_dicts(source.get("recent_requests"), "recent_requests"),
            "top_expensive": list_of_dicts(source.get("top_expensive"), "top_expensive"),
            "breakdown_legend": list_of_dicts(source.get("breakdown_legend"), "breakdown_legend"),
            "trend_data": list_of_dicts(source.get("trend_data"), "trend_data"),
            "quick_alerts": list_of_dicts(source.get("quick_alerts"), "quick_alerts"),
            "health_alerts_config": health_alerts_config,
        }

    @staticmethod
    def _format_usd(value: float) -> str:
        normalized = float(value or 0.0)
        if normalized > 0 and normalized < 0.0001:
            return "<$0.0001"
        return f"${normalized:,.4f}"

    @staticmethod
    def _matches_utc_day(timestamp_value: object, day_key: str) -> bool:
        raw = str(timestamp_value or "").strip()
        if not raw:
            return False
        if len(raw) >= 10 and raw[4] == "-" and raw[7] == "-":
            return raw[:10] == day_key
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except Exception:
            return False
        return parsed.astimezone(timezone.utc).date().isoformat() == day_key

    @staticmethod
    def _parse_positive_limit(value: object) -> float | None:
        raw = str(value if value is not None else "").strip()
        if not raw:
            return None
        try:
            parsed = float(raw)
        except Exception:
            return None
        if not math.isfinite(parsed) or parsed <= 0:
            return None
        return parsed

    def _build_dashboard_live_state(self) -> dict[str, object]:
        dashboard_state_cfg = self._config.get_dashboard_state()
        dashboard_state_cfg = dashboard_state_cfg if isinstance(dashboard_state_cfg, dict) else {}
        raw_health_cfg = dashboard_state_cfg.get("health_alerts_config")
        health_cfg = raw_health_cfg if isinstance(raw_health_cfg, dict) else {}

        def int_cfg(name: str, default: int, *, minimum: int | None = None, maximum: int | None = None) -> int:
            try:
                parsed = int(health_cfg.get(name, default))
            except Exception:
                parsed = int(default)
            if minimum is not None and parsed < minimum:
                parsed = minimum
            if maximum is not None and parsed > maximum:
                parsed = maximum
            return parsed

        def float_cfg(name: str, default: float, *, minimum: float | None = None, maximum: float | None = None) -> float:
            try:
                parsed = float(health_cfg.get(name, default))
            except Exception:
                parsed = float(default)
            if not math.isfinite(parsed):
                parsed = float(default)
            if minimum is not None and parsed < minimum:
                parsed = minimum
            if maximum is not None and parsed > maximum:
                parsed = maximum
            return parsed

        window_rows = int_cfg("window_rows", 500, minimum=50, maximum=5000)
        min_samples_total = int_cfg("min_samples_total", 20, minimum=1, maximum=5000)
        min_samples_success = int_cfg("min_samples_success", 10, minimum=1, maximum=5000)
        success_warn_pct = float_cfg("success_rate_warning_pct", 95.0, minimum=1.0, maximum=100.0)
        success_critical_pct = float_cfg("success_rate_critical_pct", 85.0, minimum=0.0, maximum=100.0)
        if success_critical_pct > success_warn_pct:
            success_critical_pct = success_warn_pct
        latency_warn_ms = int_cfg("latency_warning_ms", 8000, minimum=1, maximum=120000)
        latency_critical_ms = int_cfg("latency_critical_ms", 15000, minimum=1, maximum=240000)
        if latency_critical_ms < latency_warn_ms:
            latency_critical_ms = latency_warn_ms
        budget_warn_pct = float_cfg("budget_warning_pct", 75.0, minimum=1.0, maximum=1000.0)
        budget_critical_pct = float_cfg("budget_critical_pct", 90.0, minimum=1.0, maximum=1000.0)
        if budget_critical_pct < budget_warn_pct:
            budget_critical_pct = budget_warn_pct
        monitor_only = bool(health_cfg.get("monitor_only", True))

        rows = self._usage_db.get_recent_usage(limit=window_rows)
        total_requests = int(len(rows))
        total_cost = float(sum(float(r.get("cost_usd") or 0.0) for r in rows))
        total_tokens = int(
            sum(int(r.get("tokens_input") or 0) + int(r.get("tokens_output") or 0) for r in rows)
        )
        success_count = int(sum(1 for r in rows if str(r.get("status") or "") == "success"))
        success_rate = (float(success_count) / float(total_requests) * 100.0) if total_requests > 0 else 0.0

        success_rows = [r for r in rows if str(r.get("status") or "") == "success"]
        success_latency_values: list[int] = []
        for r in success_rows:
            value = r.get("latency_ms")
            if value is None:
                continue
            try:
                success_latency_values.append(int(value))
            except Exception:
                continue
        avg_success_latency = int(round(sum(success_latency_values) / len(success_latency_values))) if success_latency_values else 0

        connections = self._config.list_connections()
        active_bridges = int(
            sum(1 for c in connections if str(c.get("status") or "").strip().lower() == "running")
        )

        kpis = [
            {"label": "Total Cost USD", "value": self._format_usd(total_cost), "icon": "$"},
            {"label": "Total Requests", "value": str(total_requests), "icon": "R"},
            {"label": "Total Tokens", "value": str(total_tokens), "icon": "T"},
            {"label": "Success Rate %", "value": f"{success_rate:.1f}%", "icon": "S"},
            {"label": "Avg Latency ms", "value": f"{avg_success_latency}ms", "icon": "L"},
            {"label": "Active Bridges count", "value": str(active_bridges), "icon": "B"},
        ]

        known_provider_ids = (
            "vertex",
            "azure_openai",
            "openai",
            "bedrock",
            "anthropic",
            "groq",
            "lmstudio",
            "ollama",
            "huggingface",
        )

        def provider_label_from_row(row: dict[str, object]) -> str:
            raw = str(row.get("provider") or "").strip().lower()
            canonical = re.sub(r"[^a-z0-9]+", "_", raw).strip("_")
            aliases = {
                "azure": "azure_openai",
                "azure_openai": "azure_openai",
                "bedrock": "bedrock",
            }
            if raw:
                if canonical in aliases:
                    return aliases[canonical]
                for provider_id in known_provider_ids:
                    if raw == provider_id or raw.startswith(provider_id) or canonical == provider_id:
                        return provider_id
                return raw
            return "unknown"

        recent_requests: list[dict[str, object]] = []
        for r in rows[:30]:
            status = "Success" if str(r.get("status") or "") == "success" else "Error"
            tokens_in = int(r.get("tokens_input") or 0)
            tokens_out = int(r.get("tokens_output") or 0)
            recent_requests.append(
                {
                    "time": str(r.get("timestamp") or ""),
                    "request_id": str(r.get("request_id") or ""),
                    "status": status,
                    "connection": str(r.get("agent_name") or "").strip(),
                    "provider": provider_label_from_row(r),
                    "latency": f"{int(r.get('latency_ms') or 0)}ms",
                    "tokens": f"{tokens_in} / {tokens_out}",
                    "cost": self._format_usd(float(r.get("cost_usd") or 0.0)),
                }
            )

        connection_name_by_id: dict[str, str] = {}
        for connection in connections:
            if not isinstance(connection, dict):
                continue
            cid = str(connection.get("id") or "").strip()
            if not cid:
                continue
            name = str(connection.get("connection_name") or "").strip()
            connection_name_by_id[cid] = name or cid

        top_expensive: list[dict[str, object]] = []
        sorted_by_cost = sorted(rows, key=lambda r: float(r.get("cost_usd") or 0.0), reverse=True)
        for r in sorted_by_cost[:5]:
            req_id = str(r.get("request_id") or r.get("id") or "n/a")
            scope_id = str(r.get("agent_id") or "").strip()
            connection_name = connection_name_by_id.get(scope_id, str(r.get("agent_name") or "").strip())
            provider_name = provider_label_from_row(r)
            top_expensive.append(
                {
                    "id": req_id,
                    "time": str(r.get("timestamp") or ""),
                    "connection": connection_name,
                    "provider": provider_name,
                    "cost": self._format_usd(float(r.get("cost_usd") or 0.0)),
                }
            )

        provider_costs: dict[str, float] = defaultdict(float)
        for r in rows:
            provider = provider_label_from_row(r)
            provider_costs[provider] += float(r.get("cost_usd") or 0.0)
        sorted_provider_costs = sorted(provider_costs.items(), key=lambda kv: kv[1], reverse=True)
        palette = ["var(--accent-base)", "#3b82f6", "#6366f1", "#64748b", "#14b8a6"]
        breakdown_legend: list[dict[str, object]] = []
        for idx, (name, value) in enumerate(sorted_provider_costs[:5]):
            breakdown_legend.append(
                {
                    "name": name,
                    "color": palette[idx % len(palette)],
                    "cost": self._format_usd(value),
                }
            )

        daily_costs: dict[str, float] = defaultdict(float)
        for r in rows:
            ts = str(r.get("timestamp") or "")
            day = ts[:10] if len(ts) >= 10 else "unknown"
            daily_costs[day] += float(r.get("cost_usd") or 0.0)
        trend_data: list[dict[str, object]] = []
        # Always emit a contiguous 30-day series so the dashboard trend genuinely
        # represents "Last 30 Days" instead of a sparse subset of active days.
        today_date = datetime.now(timezone.utc).date()
        day_keys = [(today_date - timedelta(days=offset)).isoformat() for offset in range(29, -1, -1)]
        for day in day_keys:
            trend_data.append({"label": day, "valueFormatted": self._format_usd(float(daily_costs.get(day, 0.0)))})

        quick_alerts: list[dict[str, object]] = []
        budget_alerts: list[dict[str, object]] = []

        today_key = datetime.now(timezone.utc).date().isoformat()
        daily_cost_by_scope: dict[str, float] = defaultdict(float)
        daily_tokens_by_scope: dict[str, int] = defaultdict(int)
        for r in rows:
            if not self._matches_utc_day(r.get("timestamp"), today_key):
                continue
            scope_id = str(r.get("agent_id") or "").strip()
            cost_value = float(r.get("cost_usd") or 0.0)
            token_value = int(r.get("tokens_input") or 0) + int(r.get("tokens_output") or 0)
            daily_cost_by_scope["all"] += cost_value
            daily_tokens_by_scope["all"] += token_value
            if scope_id:
                daily_cost_by_scope[scope_id] += cost_value
                daily_tokens_by_scope[scope_id] += token_value

        budget_state = self._canonicalize_resilience_budget_state(self._config.get_resilience_budget_state())
        guards_src = budget_state.get("applied_guards")
        guards = guards_src if isinstance(guards_src, list) else []
        for guard in guards:
            if not isinstance(guard, dict):
                continue
            scope_id = str(guard.get("scope_id") or "").strip()
            if not scope_id:
                continue
            unit = str(guard.get("unit") or "").strip()
            limit = self._parse_positive_limit(guard.get("limit_value"))
            if limit is None:
                continue
            if unit == "usd_per_day":
                consumed = float(daily_cost_by_scope.get(scope_id, 0.0))
                unit_label = "USD/day"
            elif unit == "tokens_per_day":
                consumed = float(daily_tokens_by_scope.get(scope_id, 0))
                unit_label = "tokens/day"
            else:
                continue
            utilization = (consumed / limit) * 100.0
            if utilization < budget_warn_pct:
                continue
            level = "critical" if utilization >= budget_critical_pct else "warning"
            scope_label = "All Bridges" if scope_id == "all" else connection_name_by_id.get(scope_id, scope_id)
            text = (
                f"Budget threshold {'critical' if level == 'critical' else 'warning'}: {scope_label}"
            )
            detail = f"Current usage: {utilization:.1f}% of {unit_label}"
            budget_alerts.append(
                {
                    "level": level,
                    "text": text,
                    "detail": detail,
                    "monitor_only": monitor_only,
                    "_utilization": utilization,
                }
            )
        budget_alerts.sort(
            key=lambda row: (
                0 if str(row.get("level") or "") == "critical" else 1,
                -float(row.get("_utilization") or 0.0),
                str(row.get("text") or ""),
            )
        )
        for row in budget_alerts:
            row.pop("_utilization", None)

        has_total_sample = total_requests >= min_samples_total
        has_success_sample = len(success_rows) >= min_samples_success
        success_alert_level: str | None = None
        if has_total_sample and success_rate < success_warn_pct:
            success_level = "critical" if success_rate < success_critical_pct else "warning"
            success_target = f"{success_critical_pct:.0f}%" if success_level == "critical" else f"{success_warn_pct:.0f}%"
            success_alert_level = success_level
            success_detail = f"Current: {success_rate:.1f}%"
            if success_level == "critical" and has_success_sample and avg_success_latency >= latency_warn_ms:
                success_detail = f"{success_detail}; Incident context: avg_success_latency={avg_success_latency}ms"
            quick_alerts.append(
                {
                    "level": success_level,
                    "text": f"Success rate {'critical' if success_level == 'critical' else 'warning'} (<{success_target})",
                    "detail": success_detail,
                    "monitor_only": monitor_only,
                }
            )
        if has_total_sample and has_success_sample and avg_success_latency >= latency_warn_ms and success_alert_level != "critical":
            latency_level = "critical" if avg_success_latency >= latency_critical_ms else "warning"
            quick_alerts.append(
                {
                    "level": latency_level,
                    "text": f"High average latency (success E2E): {avg_success_latency}ms",
                    "detail": f"Window={window_rows} rows; samples={len(success_rows)} success",
                    "monitor_only": monitor_only,
                }
            )
        if not has_total_sample:
            quick_alerts.append(
                {
                    "level": "info",
                    "text": "Insufficient data for success/latency alerts.",
                    "detail": f"Need >= {min_samples_total} requests in last {window_rows} rows.",
                    "monitor_only": monitor_only,
                }
            )
        elif not has_success_sample:
            quick_alerts.append(
                {
                    "level": "info",
                    "text": "Insufficient successful samples for latency alerts.",
                    "detail": f"Need >= {min_samples_success} successful requests in last {window_rows} rows.",
                    "monitor_only": monitor_only,
                }
            )
        quick_alerts.extend(budget_alerts)
        if not quick_alerts:
            quick_alerts.append(
                {
                    "level": "info",
                    "text": "No active health alerts.",
                    "monitor_only": monitor_only,
                }
            )

        return {
            "kpis": kpis,
            "recent_requests": recent_requests,
            "top_expensive": top_expensive,
            "breakdown_legend": breakdown_legend,
            "trend_data": trend_data,
            "quick_alerts": quick_alerts,
        }

    def get_dashboard_state(self, payload: dict | None = None) -> dict[str, object]:
        state = self._build_dashboard_live_state()
        return {"ok": True, "errors": [], "warnings": [], "result": state}

    def set_dashboard_state(self, payload: dict | None = None) -> dict[str, object]:
        data = payload if isinstance(payload, dict) else {}
        state_payload = data.get("state")
        if not isinstance(state_payload, dict):
            return {
                "ok": False,
                "errors": ["state is required"],
                "warnings": [],
                "error_code": "invalid_dashboard_state",
            }
        expected_list_keys = [
            "kpis",
            "recent_requests",
            "top_expensive",
            "breakdown_legend",
            "trend_data",
            "quick_alerts",
        ]
        if "health_alerts_config" in state_payload and not isinstance(state_payload.get("health_alerts_config"), dict):
            return {
                "ok": False,
                "errors": ["health_alerts_config must be an object"],
                "warnings": [],
                "error_code": "invalid_dashboard_state",
            }
        for key in expected_list_keys:
            if key in state_payload and not isinstance(state_payload.get(key), list):
                return {
                    "ok": False,
                    "errors": [f"{key} must be a list"],
                    "warnings": [],
                    "error_code": "invalid_dashboard_state",
                }
            values = state_payload.get(key)
            if isinstance(values, list):
                for item in values:
                    if not isinstance(item, dict):
                        return {
                            "ok": False,
                            "errors": [f"{key} items must be objects"],
                            "warnings": [],
                            "error_code": "invalid_dashboard_state",
                        }
        canonical = self._canonicalize_dashboard_state(state_payload)
        persisted = self._config.set_dashboard_state(canonical)
        return {"ok": True, "errors": [], "warnings": [], "result": persisted}

    def _canonicalize_settings_state(self, payload: dict | None) -> dict:
        source = payload if isinstance(payload, dict) else {}
        base = self._config.default_settings_state()
        data_retention = str(source.get("data_retention") or base.get("data_retention") or "3m").strip()
        if data_retention not in ("1m", "3m", "6m", "unlimited"):
            data_retention = "3m"
        port_mode = str(source.get("port_mode") or base.get("port_mode") or "auto").strip()
        if port_mode not in ("auto", "manual"):
            port_mode = "auto"
        port_min = str(source.get("port_min") if source.get("port_min") is not None else base.get("port_min") or "").strip()
        port_max = str(source.get("port_max") if source.get("port_max") is not None else base.get("port_max") or "").strip()
        return {
            "data_retention": data_retention,
            "port_mode": port_mode,
            "port_min": port_min,
            "port_max": port_max,
        }

    def get_settings_state(self, payload: dict | None = None) -> dict[str, object]:
        state = self._canonicalize_settings_state(self._config.get_settings_state())
        return {"ok": True, "errors": [], "warnings": [], "result": state}

    def set_settings_state(self, payload: dict | None = None) -> dict[str, object]:
        data = payload if isinstance(payload, dict) else {}
        state_payload = data.get("state")
        if not isinstance(state_payload, dict):
            return {
                "ok": False,
                "errors": ["state is required"],
                "warnings": [],
                "error_code": "invalid_settings_state",
            }
        data_retention = str(state_payload.get("data_retention") or "").strip()
        if data_retention not in ("1m", "3m", "6m", "unlimited"):
            return {
                "ok": False,
                "errors": ["data_retention must be one of: 1m, 3m, 6m, unlimited"],
                "warnings": [],
                "error_code": "invalid_settings_state",
            }
        port_mode = str(state_payload.get("port_mode") or "").strip()
        if port_mode not in ("auto", "manual"):
            return {
                "ok": False,
                "errors": ["port_mode must be one of: auto, manual"],
                "warnings": [],
                "error_code": "invalid_settings_state",
            }
        if not isinstance(state_payload.get("port_min"), str):
            return {
                "ok": False,
                "errors": ["port_min must be string"],
                "warnings": [],
                "error_code": "invalid_settings_state",
            }
        if not isinstance(state_payload.get("port_max"), str):
            return {
                "ok": False,
                "errors": ["port_max must be string"],
                "warnings": [],
                "error_code": "invalid_settings_state",
            }
        if port_mode == "manual":
            port_min_raw = str(state_payload.get("port_min") or "").strip()
            port_max_raw = str(state_payload.get("port_max") or "").strip()
            try:
                port_min_int = int(port_min_raw)
            except Exception:
                return {
                    "ok": False,
                    "errors": ["port_min must be integer when port_mode=manual"],
                    "warnings": [],
                    "error_code": "invalid_settings_state",
                }
            try:
                port_max_int = int(port_max_raw)
            except Exception:
                return {
                    "ok": False,
                    "errors": ["port_max must be integer when port_mode=manual"],
                    "warnings": [],
                    "error_code": "invalid_settings_state",
                }
            if port_min_int < 1 or port_min_int > 65535:
                return {
                    "ok": False,
                    "errors": ["port_min must be between 1 and 65535"],
                    "warnings": [],
                    "error_code": "invalid_settings_state",
                }
            if port_max_int < 1 or port_max_int > 65535:
                return {
                    "ok": False,
                    "errors": ["port_max must be between 1 and 65535"],
                    "warnings": [],
                    "error_code": "invalid_settings_state",
                }
            if port_min_int > port_max_int:
                return {
                    "ok": False,
                    "errors": ["port_min must be <= port_max"],
                    "warnings": [],
                    "error_code": "invalid_settings_state",
                }
        canonical = self._canonicalize_settings_state(state_payload)
        persisted = self._config.set_settings_state(canonical)
        return {"ok": True, "errors": [], "warnings": [], "result": persisted}

    def _find_available_connection_port(self, start: int, end: int) -> int:
        if int(start) > int(end):
            raise RuntimeError("invalid port range")
        config_data = self._config._read_config()
        used_ports: set[int] = set()
        for agent in config_data.get("agents", []) or []:
            if not isinstance(agent, dict):
                continue
            try:
                used_ports.add(int(agent.get("port")))
            except Exception:
                continue
        for connection in config_data.get("connections", []) or []:
            if not isinstance(connection, dict):
                continue
            try:
                used_ports.add(int(connection.get("port")))
            except Exception:
                continue
        for port in range(int(start), int(end) + 1):
            if port in used_ports:
                continue
            endpoint_in_use, _, _ = self._probe_sse_endpoint(port)
            if endpoint_in_use:
                continue
            return port
        raise RuntimeError("no available ports in requested range")

    def _resolve_connection_port_from_settings(self) -> tuple[int | None, list[str]]:
        state = self._canonicalize_settings_state(self._config.get_settings_state())
        port_mode = str(state.get("port_mode") or "auto").strip()
        defaults = self._config.default_settings_state()
        if port_mode != "manual":
            try:
                default_min = int(str(defaults.get("port_min") or "5000").strip())
                default_max = int(str(defaults.get("port_max") or "6000").strip())
                return self._find_available_connection_port(default_min, default_max), []
            except Exception:
                return None, ["no available ports in default range (5000-6000)"]

        port_min_raw = str(state.get("port_min") or "").strip()
        port_max_raw = str(state.get("port_max") or "").strip()
        try:
            port_min = int(port_min_raw)
            port_max = int(port_max_raw)
        except Exception:
            return None, ["settings manual port range is invalid"]
        if port_min < 1 or port_min > 65535 or port_max < 1 or port_max > 65535:
            return None, ["settings manual port range must be between 1 and 65535"]
        if port_min > port_max:
            return None, ["settings manual port range requires port_min <= port_max"]
        try:
            return self._find_available_connection_port(start=port_min, end=port_max), []
        except RuntimeError:
            return None, [f"no available ports in configured manual range ({port_min}-{port_max})"]

    def _resolve_credentials_path(self, raw_value: str) -> tuple[str, list[str]]:
        value = str(raw_value or "").strip()
        if not value:
            return "", []
        if not value.lower().startswith("vault://"):
            return value, []
        try:
            resolved = self._vault.resolve_credentials_reference(value)
            return str(resolved or "").strip(), []
        except ValueError as exc:
            return "", [str(exc)]
        except Exception:
            return "", ["vault credentials resolution failed"]

    @staticmethod
    def _classify_vertex_probe_error(message: str) -> str:
        text = str(message or "").lower()
        if "404" in text or "not found" in text or "does not have access" in text:
            return "NOT_FOUND_OR_NO_ACCESS (404)"
        if "403" in text or "permission" in text or "forbidden" in text or "unauthorized" in text:
            return "PERMISSION (403)"
        if "quota" in text or "rate limit" in text or "resource exhausted" in text:
            return "QUOTA"
        return "PROBE_FAILED"

    def _get_cached_vertex_probe_client(
        self,
        *,
        project_id: str,
        location: str,
        model_id: str,
        credentials_path: str,
    ):
        key = (
            str(project_id).strip(),
            str(location).strip(),
            str(model_id).strip(),
            str(credentials_path).strip(),
        )
        now = time.monotonic()
        with self._vertex_probe_cache_lock:
            cached = self._vertex_probe_client_cache.get(key)
            if cached:
                age = now - float(cached.get("ts") or 0.0)
                if age <= self._VERTEX_PROBE_CLIENT_TTL_SECONDS:
                    return cached.get("client")
        probe_agent = {
            "id": "preflight-probe",
            "name": "PreflightProbe",
            "provider_id": "vertex",
            "project_id": str(project_id),
            "location": str(location),
            "model_id": str(model_id),
            "price_per_1m_input": 0.0,
            "price_per_1m_output": 0.0,
        }
        context = ExecutionContextV1(
            agent=probe_agent,
            project_id=str(project_id),
            location=str(location),
            provider_id="vertex",
            model_id=str(model_id),
            credentials_path=str(credentials_path),
            price_per_1m_input=0.0,
            price_per_1m_output=0.0,
            streaming=False,
        )
        client = ProviderFactory.create("vertex", context)
        with self._vertex_probe_cache_lock:
            self._vertex_probe_client_cache[key] = {"ts": now, "client": client}
        return client

    def _run_vertex_preflight_probe_sync(
        self,
        *,
        project_id: str,
        location: str,
        model_id: str,
        credentials_path: str,
    ) -> tuple[bool, str]:
        try:
            client = self._get_cached_vertex_probe_client(
                project_id=project_id,
                location=location,
                model_id=model_id,
                credentials_path=credentials_path,
            )
            # Minimal targeted probe (short prompt + low output budget).
            client.generate_content("hi", stream=False, max_output_tokens=8)
            return True, ""
        except Exception as exc:
            raw = self._tail_text(str(exc), limit=700)
            label = self._classify_vertex_probe_error(raw)
            return False, f"{label}: {raw}"

    def _run_vertex_preflight_probe(
        self,
        *,
        project_id: str,
        location: str,
        model_id: str,
        credentials_path: str,
    ) -> tuple[bool, str]:
        future = self._vertex_probe_executor.submit(
            self._run_vertex_preflight_probe_sync,
            project_id=project_id,
            location=location,
            model_id=model_id,
            credentials_path=credentials_path,
        )
        try:
            return future.result(timeout=self._VERTEX_PROBE_TIMEOUT_SECONDS)
        except FutureTimeoutError:
            future.cancel()
            return False, "PROBE_FAILED: probe timeout while checking model access"
        except Exception as exc:
            raw = self._tail_text(str(exc), limit=700)
            return False, f"PROBE_FAILED: {raw}"

    def _build_connection_schema_hint(self, provider_id: str) -> dict[str, object]:
        provider = str(provider_id or "").strip()
        fields: list[dict[str, object]] = [
            {
                "id": "connection_name",
                "label": "Connection name",
                "required": True,
                "kind": "text",
                "placeholder": "Example: Synapse Agent",
                "help": "Used as the server name in copied MCP config.",
                "section": "common",
            },
            {
                "id": "model_id",
                "label": "Model ID",
                "required": True,
                "kind": "text",
                "placeholder": "Example: gpt-4o-mini",
                "help": "Model identifier for the selected provider.",
                "section": "common",
            },
            {
                "id": "endpoint",
                "label": "Endpoint / Base URL",
                "required": False,
                "kind": "text",
                "placeholder": "Optional override",
                "help": "Optional provider endpoint override. Leave blank to use core defaults.",
                "section": "advanced",
            },
            {
                "id": "credentials_path",
                "label": "Credentials path",
                "required": False,
                "kind": "text",
                "placeholder": r"C:\path\to\credentials.json",
                "help": "Optional path to a local credentials file used by the core runtime.",
                "section": "advanced",
            },
        ]

        suggested_defaults: dict[str, str] = {}
        notes: list[str] = []

        if provider == "vertex":
            fields.insert(
                2,
                {
                    "id": "project_id",
                    "label": "Project ID",
                    "required": True,
                    "kind": "text",
                    "placeholder": "Example: my-gcp-project",
                    "help": "GCP project used for Vertex requests.",
                    "section": "common",
                },
            )
            fields.insert(
                3,
                {
                    "id": "location",
                    "label": "Location",
                    "required": False,
                    "kind": "text",
                    "placeholder": "Example: us-central1",
                    "help": "Vertex location override. Leave blank to use core defaults.",
                    "section": "advanced",
                },
            )
            suggested_defaults["location"] = "us-central1"

        if provider == "ollama":
            for f in fields:
                if not isinstance(f, dict):
                    continue
                field_id = str(f.get("id") or "").strip()
                if field_id == "model_id":
                    f["placeholder"] = "Example: gemma3:1b"
                    f["help"] = "Ollama local model tag (required)."
                elif field_id == "endpoint":
                    f["required"] = True
                    f["placeholder"] = "http://127.0.0.1:11434"
                    f["help"] = "Ollama base URL for local runtime."
                elif field_id == "credentials_path":
                    f["help"] = "Not required for local Ollama runtime."
            suggested_defaults["endpoint"] = "http://127.0.0.1:11434"
            notes.append("Ollama local default endpoint is http://127.0.0.1:11434.")

        if provider == "bedrock":
            for f in fields:
                if isinstance(f, dict) and str(f.get("id") or "").strip() == "credentials_path":
                    f["required"] = False
                    f["help"] = "AWS credentials file path (used when Credential source = File)."
                    break
            fields.insert(
                2,
                {
                    "id": "aws_region",
                    "label": "AWS region",
                    "required": True,
                    "kind": "text",
                    "placeholder": "Example: us-east-1",
                    "help": "AWS region for Bedrock runtime requests.",
                    "section": "common",
                },
            )
            fields.insert(
                3,
                {
                    "id": "credential_source",
                    "label": "Credential source",
                    "required": True,
                    "kind": "select",
                    "options": [
                        {"value": "file", "label": "File"},
                        {"value": "manual", "label": "Manual"},
                        {"value": "api_key", "label": "API Key"},
                    ],
                    "placeholder": "file",
                    "help": "File uses credentials_path. Manual uses access key + secret key. API Key uses Bedrock bearer token.",
                    "section": "advanced",
                },
            )
            fields.append(
                {
                    "id": "aws_access_key_id",
                    "label": "AWS Access Key ID",
                    "required": False,
                    "kind": "text",
                    "placeholder": "Example: AKIA...",
                    "help": "Required when Credential source is Manual.",
                    "section": "advanced",
                },
            )
            fields.append(
                {
                    "id": "aws_secret_access_key",
                    "label": "AWS Secret Access Key",
                    "required": False,
                    "kind": "password",
                    "placeholder": "Enter AWS secret access key",
                    "help": "Required when Credential source is Manual.",
                    "section": "advanced",
                },
            )
            fields.append(
                {
                    "id": "aws_session_token",
                    "label": "AWS Session Token",
                    "required": False,
                    "kind": "text",
                    "placeholder": "Optional (temporary credentials)",
                    "help": "Optional; required only for temporary session credentials.",
                    "section": "advanced",
                },
            )
            fields.append(
                {
                    "id": "bedrock_api_key",
                    "label": "Bedrock API Key",
                    "required": False,
                    "kind": "password",
                    "placeholder": "ABSK...",
                    "help": "Required when Credential source is API Key.",
                    "section": "advanced",
                },
            )
            suggested_defaults["aws_region"] = "us-east-1"
            suggested_defaults["credential_source"] = "file"

        if provider == "azure_openai":
            fields = [
                f
                for f in fields
                if not (
                    isinstance(f, dict)
                    and str(f.get("id") or "").strip() == "endpoint"
                )
            ]
            for f in fields:
                if not isinstance(f, dict):
                    continue
                field_id = str(f.get("id") or "").strip()
                if field_id == "model_id":
                    f["label"] = "Deployment name"
                    f["placeholder"] = "Example: gpt-4o-mini-deploy"
                    f["help"] = "Azure uses deployment name instead of raw model ID."
                elif field_id == "credentials_path":
                    f["required"] = True
                    f["placeholder"] = r"C:\path\to\azure_api_key.txt"
                    f["help"] = "Path to a local file that contains your Azure OpenAI API key."
            fields.insert(
                2,
                {
                    "id": "azure_endpoint",
                    "label": "Endpoint / Base URL",
                    "required": True,
                    "kind": "text",
                    "placeholder": "https://<resource>.openai.azure.com",
                    "help": "Azure OpenAI resource endpoint (required).",
                    "section": "common",
                },
            )
            fields.insert(
                3,
                {
                    "id": "azure_api_version",
                    "label": "API version",
                    "required": True,
                    "kind": "text",
                    "placeholder": "Example: 2024-10-21",
                    "help": "Required Azure OpenAI API version.",
                    "section": "common",
                },
            )
            suggested_defaults["azure_api_version"] = "2024-10-21"
            notes.append("Azure OpenAI uses deployment name (not raw model name).")

        if provider == "huggingface":
            for f in fields:
                if not isinstance(f, dict):
                    continue
                field_id = str(f.get("id") or "").strip()
                if field_id == "endpoint":
                    f["required"] = False
                    f["placeholder"] = "https://router.huggingface.co/v1"
                    f["help"] = "HF OpenAI-compatible base URL. Leave blank to use default."
                elif field_id == "credentials_path":
                    f["required"] = True
                    f["placeholder"] = r"C:\path\to\hf_token.txt"
                    f["help"] = "Path to a local file (or vault:// reference) that contains your HF access token."
            fields.insert(
                3,
                {
                    "id": "hf_enable_network",
                    "label": "Enable HF network calls",
                    "required": True,
                    "kind": "select",
                    "options": [
                        {"value": "false", "label": "Disabled (default)"},
                        {"value": "true", "label": "Enabled"},
                    ],
                    "placeholder": "false",
                    "help": "Safety rail: set Enabled to allow live Hugging Face outbound calls.",
                    "section": "advanced",
                },
            )
            suggested_defaults["endpoint"] = "https://router.huggingface.co/v1"
            suggested_defaults["hf_enable_network"] = "false"
            notes.append("Current HF scope is OpenAI-compatible chat only (non-streaming).")

        if not provider:
            notes.append("Select a provider to see core-driven field requirements.")

        hint: dict[str, object] = {"fields": fields}
        if suggested_defaults:
            hint["suggested_defaults"] = suggested_defaults
        if notes:
            hint["notes"] = notes
        return hint

    def connections_schema_hint(self, payload: dict) -> dict[str, object]:
        provider_id = str(payload.get("provider_id") or "").strip()
        hint = self._build_connection_schema_hint(provider_id)
        return {"ok": True, "errors": [], "warnings": [], "schema_hint": hint}

    def preflight_connection(self, payload: dict) -> dict[str, object]:
        errors: list[str] = []
        warnings: list[str] = []
        probe: dict[str, object] | None = None
        connection_name = str(payload.get("connection_name") or "").strip()
        provider_id = str(payload.get("provider_id") or "").strip()
        model_id = str(payload.get("model_id") or payload.get("deployment_name") or "").strip()
        credentials_provided = "credentials_path" in payload
        endpoint = str(payload.get("endpoint") or "").strip()
        credentials_path = str(payload.get("credentials_path") or "").strip()
        resolved_credentials_path = ""

        if not connection_name:
            errors.append("connection_name is required")
        if not provider_id:
            errors.append("provider_id is required")
        if not model_id:
            errors.append("model_id is required")

        schema_hint = self._build_connection_schema_hint(provider_id)
        schema_fields = schema_hint.get("fields") if isinstance(schema_hint, dict) else None
        if isinstance(schema_fields, list):
            for f in schema_fields:
                if not isinstance(f, dict):
                    continue
                field_id = str(f.get("id") or "").strip()
                required = bool(f.get("required"))
                if not required:
                    continue
                if field_id in ("connection_name", "model_id"):
                    continue
                if provider_id == "ollama" and field_id == "endpoint":
                    value = str(payload.get("endpoint") or payload.get("ollama_base_url") or "").strip()
                else:
                    value = str(payload.get(field_id) or "").strip()
                if not value:
                    errors.append(f"{field_id} is required")

        if provider_id == "vertex":
            project_id = str(payload.get("project_id") or "").strip()
            if project_id:
                # GCP project IDs are 6-30 chars, lowercase letters/digits/hyphen,
                # start with a letter, and end with letter/digit.
                if not re.match(r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$", project_id):
                    errors.append("project_id format is invalid for Vertex")
        elif provider_id == "bedrock":
            aws_region = str(payload.get("aws_region") or "").strip()
            if not aws_region:
                errors.append("aws_region is required")
            elif not re.match(r"^[a-z]{2}-[a-z]+-\d+$", aws_region):
                errors.append("aws_region format is invalid for Bedrock")
            credential_source = str(payload.get("credential_source") or "file").strip().lower()
            if credential_source not in ("file", "manual", "api_key"):
                errors.append("credential_source must be one of: file, manual, api_key")
            if credential_source == "file":
                if not credentials_path:
                    errors.append("credentials_path is required when credential_source=file")
            elif credential_source == "manual":
                access_key = str(payload.get("aws_access_key_id") or "").strip()
                secret_key = str(payload.get("aws_secret_access_key") or "").strip()
                if not access_key:
                    errors.append("aws_access_key_id is required when credential_source=manual")
                if not secret_key:
                    errors.append("aws_secret_access_key is required when credential_source=manual")
            else:
                bedrock_api_key = str(payload.get("bedrock_api_key") or "").strip()
                if not bedrock_api_key:
                    errors.append("bedrock_api_key is required when credential_source=api_key")
        elif provider_id == "azure_openai":
            azure_endpoint = str(payload.get("azure_endpoint") or endpoint).strip()
            azure_api_version = str(payload.get("azure_api_version") or "").strip()
            deployment_name = str(payload.get("deployment_name") or model_id).strip()
            if not azure_endpoint:
                errors.append("azure_endpoint is required")
            else:
                errors.extend(self._validate_http_endpoint(azure_endpoint, "azure_endpoint"))
            if not azure_api_version:
                errors.append("azure_api_version is required")
            if not deployment_name:
                errors.append("deployment_name is required")
            if not credentials_path:
                errors.append("credentials_path is required for azure_openai")
        elif provider_id == "ollama":
            ollama_base_url = str(payload.get("ollama_base_url") or endpoint).strip()
            if not ollama_base_url:
                errors.append("endpoint is required for ollama")
            elif re.match(r"^https?://(?:127\.0\.0\.1|localhost):\d+/sse$", ollama_base_url):
                errors.append("endpoint must be Ollama base URL, not local bridge /sse endpoint")
            else:
                errors.extend(self._validate_http_endpoint(ollama_base_url, "endpoint"))
        elif provider_id == "huggingface":
            hf_endpoint = str(payload.get("hf_endpoint") or endpoint).strip()
            if hf_endpoint:
                errors.extend(self._validate_http_endpoint(hf_endpoint, "hf_endpoint"))
            hf_enable_raw = payload.get("hf_enable_network")
            if isinstance(hf_enable_raw, bool):
                hf_enable_text = "true" if hf_enable_raw else "false"
            else:
                hf_enable_text = str(hf_enable_raw or "").strip().lower()
            allowed_values = {"true", "false", "1", "0", "yes", "no", "on", "off"}
            if hf_enable_text and hf_enable_text not in allowed_values:
                errors.append("hf_enable_network must be one of: true, false")
            hf_enabled = hf_enable_text in {"true", "1", "yes", "on"}
            if not hf_enabled:
                errors.append("hf_enable_network must be true for live calls")

        if endpoint:
            errors.extend(self._validate_http_endpoint(endpoint, "endpoint"))
            placeholder_tokens = ("example", "placeholder", "your_", "your-", "changeme", "todo")
            lower = endpoint.lower()
            if any(token in lower for token in placeholder_tokens):
                warnings.append("endpoint appears to be a placeholder")

        if credentials_provided and not credentials_path and not (
            provider_id == "bedrock"
            and str(payload.get("credential_source") or "file").strip().lower() in ("manual", "api_key")
        ):
            errors.append("credentials_path must be non-empty if provided")
        if credentials_path and not (
            provider_id == "bedrock"
            and str(payload.get("credential_source") or "file").strip().lower() in ("manual", "api_key")
        ):
            resolved_candidate, resolve_errors = self._resolve_credentials_path(credentials_path)
            if resolve_errors:
                errors.extend(resolve_errors)
            elif not resolved_candidate or not Path(resolved_candidate).exists():
                errors.append("credentials_path does not exist")
            else:
                resolved_credentials_path = resolved_candidate

        normalized_payload: dict[str, str] = {
            "connection_name": connection_name,
            "provider_id": provider_id,
            "model_id": model_id,
        }
        if endpoint:
            normalized_payload["endpoint"] = endpoint
        if credentials_path:
            normalized_payload["credentials_path"] = credentials_path
        if isinstance(schema_fields, list):
            for f in schema_fields:
                if not isinstance(f, dict):
                    continue
                field_id = str(f.get("id") or "").strip()
                if not field_id:
                    continue
                if field_id in ("connection_name", "provider_id", "model_id", "endpoint", "credentials_path"):
                    continue
                value = str(payload.get(field_id) or "").strip()
                if value:
                    normalized_payload[field_id] = value
        if provider_id == "bedrock":
            credential_source = str(payload.get("credential_source") or "file").strip().lower()
            if credential_source not in ("file", "manual", "api_key"):
                credential_source = "file"
            normalized_payload["credential_source"] = credential_source
            if credential_source == "manual":
                normalized_payload.pop("credentials_path", None)
                access_key = str(payload.get("aws_access_key_id") or "").strip()
                secret_key = str(payload.get("aws_secret_access_key") or "").strip()
                session_token = str(payload.get("aws_session_token") or "").strip()
                if access_key:
                    normalized_payload["aws_access_key_id"] = access_key
                if secret_key:
                    normalized_payload["aws_secret_access_key"] = secret_key
                if session_token:
                    normalized_payload["aws_session_token"] = session_token
                normalized_payload.pop("bedrock_api_key", None)
            elif credential_source == "api_key":
                normalized_payload.pop("credentials_path", None)
                normalized_payload.pop("aws_access_key_id", None)
                normalized_payload.pop("aws_secret_access_key", None)
                normalized_payload.pop("aws_session_token", None)
                bedrock_api_key = str(payload.get("bedrock_api_key") or "").strip()
                if bedrock_api_key:
                    normalized_payload["bedrock_api_key"] = bedrock_api_key
            else:
                normalized_payload.pop("aws_access_key_id", None)
                normalized_payload.pop("aws_secret_access_key", None)
                normalized_payload.pop("aws_session_token", None)
                normalized_payload.pop("bedrock_api_key", None)
        elif provider_id == "azure_openai":
            azure_endpoint = str(payload.get("azure_endpoint") or endpoint).strip()
            azure_api_version = str(payload.get("azure_api_version") or "").strip()
            deployment_name = str(payload.get("deployment_name") or model_id).strip()
            normalized_payload.pop("endpoint", None)
            if azure_endpoint:
                normalized_payload["azure_endpoint"] = azure_endpoint
            if azure_api_version:
                normalized_payload["azure_api_version"] = azure_api_version
            if deployment_name:
                normalized_payload["deployment_name"] = deployment_name
        elif provider_id == "ollama":
            ollama_base_url = str(payload.get("ollama_base_url") or endpoint).strip()
            normalized_payload.pop("endpoint", None)
            if ollama_base_url:
                normalized_payload["ollama_base_url"] = ollama_base_url
        elif provider_id == "huggingface":
            hf_endpoint = str(payload.get("hf_endpoint") or endpoint).strip()
            normalized_payload.pop("endpoint", None)
            if hf_endpoint:
                normalized_payload["hf_endpoint"] = hf_endpoint

        if provider_id == "vertex" and not errors:
            project_id = str(payload.get("project_id") or "").strip()
            location = str(payload.get("location") or "us-central1").strip() or "us-central1"
            probe_path = resolved_credentials_path or credentials_path
            probe_ok, probe_error = self._run_vertex_preflight_probe(
                project_id=project_id,
                location=location,
                model_id=model_id,
                credentials_path=probe_path,
            )
            probe = {
                "provider_id": "vertex",
                "status": "ok" if probe_ok else "error",
            }
            if probe_error:
                probe["message"] = probe_error
            if not probe_ok:
                errors.append(probe_error)

        canonical_error = None
        if errors:
            joined_errors = "; ".join([str(e) for e in errors])
            reason = str(errors[0])
            if "hf_enable_network must be true for live calls" in joined_errors:
                reason = "hf_enable_network must be true for live calls"
            canonical_error = self._build_canonical_error(
                phase="preflight",
                provider_id=provider_id,
                model_id=model_id,
                request_id=None,
                reason=reason,
                raw=joined_errors,
            )
        result: dict[str, object] = {
            "ok": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "normalized_payload": normalized_payload,
            "canonical_error": canonical_error,
        }
        if probe is not None:
            result["probe"] = probe
        return result

    def create_connection(self, payload: dict) -> dict[str, object]:
        preflight = self.preflight_connection(payload)
        if not preflight.get("ok"):
            return {
                "ok": False,
                "errors": preflight.get("errors", []),
                "warnings": preflight.get("warnings", []),
                "normalized_payload": preflight.get("normalized_payload"),
                "canonical_error": preflight.get("canonical_error"),
                "connections": self._config.list_connections(),
            }

        normalized = preflight.get("normalized_payload") or {}
        resolved_port, port_errors = self._resolve_connection_port_from_settings()
        if port_errors:
            return {
                "ok": False,
                "errors": port_errors,
                "warnings": preflight.get("warnings", []),
                "normalized_payload": normalized,
                "connections": self._config.list_connections(),
            }
        known_keys = {"connection_name", "provider_id", "model_id", "endpoint", "credentials_path"}
        options: dict[str, object] = {}
        if isinstance(normalized, dict):
            for k, v in normalized.items():
                if k in known_keys:
                    continue
                options[str(k)] = v
        self._config.add_connection(
            connection_name=str(normalized.get("connection_name") or ""),
            provider_id=str(normalized.get("provider_id") or ""),
            model_id=str(normalized.get("model_id") or ""),
            endpoint=str(normalized.get("endpoint") or "") or None,
            credentials_path=str(normalized.get("credentials_path") or "") or None,
            port=resolved_port,
            options=options or None,
        )

        return {
            "ok": True,
            "errors": [],
            "warnings": preflight.get("warnings", []),
            "normalized_payload": normalized,
            "connections": self._config.list_connections(),
        }

    def update_connection(self, payload: dict) -> dict[str, object]:
        connection_id = str(payload.get("connection_id") or "").strip()
        if not connection_id:
            return {
                "ok": False,
                "errors": ["connection_id is required"],
                "warnings": [],
                "connections": self._config.list_connections(),
            }

        current = self._config.get_connection(connection_id)
        if not current:
            return {
                "ok": False,
                "errors": ["connection not found"],
                "warnings": [],
                "connections": self._config.list_connections(),
            }

        incoming = payload.get("connection")
        if not isinstance(incoming, dict):
            incoming = {}

        existing_options = dict(current.get("options") or {}) if isinstance(current.get("options"), dict) else {}
        merged_payload: dict[str, object] = {
            "connection_name": str(current.get("connection_name") or ""),
            "provider_id": str(current.get("provider_id") or ""),
            "model_id": str(current.get("model_id") or ""),
        }
        if "endpoint" in current:
            merged_payload["endpoint"] = str(current.get("endpoint") or "")
        if "credentials_path" in current:
            merged_payload["credentials_path"] = str(current.get("credentials_path") or "")
        for key, value in existing_options.items():
            merged_payload[str(key)] = value

        for key, value in incoming.items():
            merged_payload[str(key)] = value

        preflight = self.preflight_connection(merged_payload)
        if not preflight.get("ok"):
            return {
                "ok": False,
                "errors": preflight.get("errors", []),
                "warnings": preflight.get("warnings", []),
                "normalized_payload": preflight.get("normalized_payload"),
                "canonical_error": preflight.get("canonical_error"),
                "connections": self._config.list_connections(),
            }

        normalized = preflight.get("normalized_payload") or {}
        known_keys = {"connection_name", "provider_id", "model_id", "endpoint", "credentials_path"}
        options: dict[str, object] = {}
        if isinstance(normalized, dict):
            for k, v in normalized.items():
                if k in known_keys:
                    continue
                options[str(k)] = v

        updated = self._config.update_connection(
            connection_id=connection_id,
            connection_name=str(normalized.get("connection_name") or ""),
            provider_id=str(normalized.get("provider_id") or ""),
            model_id=str(normalized.get("model_id") or ""),
            endpoint=str(normalized.get("endpoint") or "") or None,
            credentials_path=str(normalized.get("credentials_path") or "") or None,
            options=options or None,
        )
        if not updated:
            return {
                "ok": False,
                "errors": ["connection not found"],
                "warnings": [],
                "connections": self._config.list_connections(),
            }

        return {
            "ok": True,
            "errors": [],
            "warnings": preflight.get("warnings", []),
            "normalized_payload": normalized,
            "connections": self._config.list_connections(),
        }

    def start_connection(self, payload: dict) -> dict[str, object]:
        connection_id = str(payload.get("connection_id") or "").strip()
        if not connection_id:
            return {
                "ok": False,
                "errors": ["connection_id is required"],
                "warnings": [],
                "connections": self._config.list_connections(),
            }

        connection = self._config.get_connection(connection_id)
        if not connection:
            return {
                "ok": False,
                "errors": ["connection not found"],
                "warnings": [],
                "connections": self._config.list_connections(),
            }

        port = self._connection_port(connection)
        if port is None:
            return {
                "ok": False,
                "errors": ["start failed: connection port is missing"],
                "warnings": [],
                "connections": self._config.list_connections(),
            }

        endpoint = f"http://127.0.0.1:{int(port)}/sse"
        current_pid_raw = connection.get("runtime_pid")
        current_pid = int(current_pid_raw) if isinstance(current_pid_raw, int) or str(current_pid_raw).isdigit() else 0
        if current_pid > 0 and self._runtime_proc_alive(current_pid) and self._endpoint_reachable(port):
            self._config.update_connection_runtime(connection_id, "running", endpoint=endpoint, runtime_pid=current_pid)
            return {
                "ok": True,
                "errors": [],
                "warnings": [],
                "connections": self._config.list_connections(),
            }

        endpoint_in_use, status_line, probe_error = self._probe_sse_endpoint(port)
        if endpoint_in_use:
            owner_pid = self._listener_pid_for_port(port)
            if owner_pid is not None and owner_pid > 0 and current_pid > 0 and int(owner_pid) == int(current_pid):
                self._config.update_connection_runtime(connection_id, "running", endpoint=endpoint, runtime_pid=int(owner_pid))
                return {
                    "ok": True,
                    "errors": [],
                    "warnings": [f"start warning: adopted existing listener on port {port} (pid={int(owner_pid)})"],
                    "connections": self._config.list_connections(),
                }
            return {
                "ok": False,
                "errors": [
                    f"start failed: endpoint already in use (endpoint={endpoint}, status_line={status_line or 'none'}, probe_error={probe_error or 'none'})"
                ],
                "warnings": [],
                "connections": self._config.list_connections(),
            }

        runtime_name = str(connection.get("connection_name") or connection_id)
        proc = None
        try:
            repo_root = str(Path(__file__).resolve().parents[2])
            env = dict(os.environ)
            python_path = str(env.get("PYTHONPATH") or "")
            if repo_root not in python_path.split(os.pathsep):
                env["PYTHONPATH"] = repo_root if not python_path else f"{repo_root}{os.pathsep}{python_path}"
            base_kwargs: dict[str, object] = {
                "stdout": subprocess.DEVNULL,
                # Keep runtime process independent from the short-lived dispatcher process.
                "stderr": subprocess.DEVNULL,
                "text": True,
                "cwd": repo_root,
                "env": env,
            }
            cmd = self._runtime_command(connection_id, runtime_name, port)
            last_spawn_error: Exception | None = None
            creationflags_candidates: list[int | None] = [None]
            if os.name == "nt":
                detached_flag = int(getattr(subprocess, "DETACHED_PROCESS", 0))
                if detached_flag:
                    creationflags_candidates = [detached_flag, None]

            for creationflags in creationflags_candidates:
                popen_kwargs = dict(base_kwargs)
                if creationflags:
                    popen_kwargs["creationflags"] = creationflags
                try:
                    proc = subprocess.Popen(cmd, **popen_kwargs)
                    break
                except PermissionError as exc:
                    last_spawn_error = exc
                    continue
                except OSError as exc:
                    # Windows access-denied failures may surface as generic OSError.
                    if os.name == "nt" and getattr(exc, "winerror", None) == 5:
                        last_spawn_error = exc
                        continue
                    raise

            if proc is None:
                raise RuntimeError(f"spawn_failed: {last_spawn_error}")
        except Exception as exc:
            return {
                "ok": False,
                "errors": [f"start failed: {exc}"],
                "warnings": [],
                "connections": self._config.list_connections(),
            }

        started = False
        startup_timeout_seconds = 15.0
        deadline = time.time() + startup_timeout_seconds
        while time.time() < deadline:
            if proc.poll() is not None:
                break
            if self._endpoint_reachable(port):
                started = True
                break
            time.sleep(0.1)

        if not started:
            return_code = proc.poll()
            alive_before_terminate = return_code is None
            if alive_before_terminate:
                try:
                    proc.terminate()
                except Exception:
                    pass
            stderr_text = ""
            try:
                _, stderr_text = proc.communicate(timeout=1.0)
            except Exception:
                pass
            _, fail_status_line, fail_probe_error = self._probe_sse_endpoint(port)
            stderr_tail = self._tail_text(stderr_text)
            if return_code is not None:
                failure = (
                    f"start failed: runtime exited early (code={return_code}, endpoint={endpoint}, "
                    f"port={int(port)}, status_line={fail_status_line or 'none'}, "
                    f"probe_error={fail_probe_error or 'none'}, stderr={stderr_tail or 'none'})"
                )
            else:
                failure = (
                    f"start failed: runtime not reachable (endpoint={endpoint}, port={int(port)}, "
                    f"timeout_s={startup_timeout_seconds}, pid={proc.pid}, "
                    f"alive_before_terminate={alive_before_terminate}, "
                    f"status_line={fail_status_line or 'none'}, probe_error={fail_probe_error or 'none'}, "
                    f"stderr={stderr_tail or 'none'})"
                )
            return {
                "ok": False,
                "errors": [failure],
                "warnings": [],
                "connections": self._config.list_connections(),
            }

        # Prevent false-positive "started" when runtime exits immediately after first successful probe.
        stable = True
        stable_deadline = time.time() + 1.5
        while time.time() < stable_deadline:
            if proc.poll() is not None:
                stable = False
                break
            if not self._endpoint_reachable(port):
                stable = False
                break
            time.sleep(0.1)
        if not stable:
            return_code = proc.poll()
            alive_before_terminate = return_code is None
            if alive_before_terminate:
                try:
                    proc.terminate()
                except Exception:
                    pass
            stderr_text = ""
            try:
                _, stderr_text = proc.communicate(timeout=1.0)
            except Exception:
                pass
            _, fail_status_line, fail_probe_error = self._probe_sse_endpoint(port)
            stderr_tail = self._tail_text(stderr_text)
            failure = (
                f"start failed: runtime became unstable after initial start "
                f"(endpoint={endpoint}, port={int(port)}, pid={proc.pid}, "
                f"returncode={return_code if return_code is not None else 'none'}, "
                f"status_line={fail_status_line or 'none'}, probe_error={fail_probe_error or 'none'}, "
                f"stderr={stderr_tail or 'none'})"
            )
            return {
                "ok": False,
                "errors": [failure],
                "warnings": [],
                "connections": self._config.list_connections(),
            }

        runtime_pid = int(proc.pid)
        owner_pid = self._listener_pid_for_port(port)
        if owner_pid is not None and owner_pid > 0:
            runtime_pid = int(owner_pid)
        self._config.update_connection_runtime(connection_id, "running", endpoint=endpoint, runtime_pid=runtime_pid)
        return {
            "ok": True,
            "errors": [],
            "warnings": [],
            "connections": self._config.list_connections(),
        }

    def stop_connection(self, payload: dict) -> dict[str, object]:
        connection_id = str(payload.get("connection_id") or "").strip()
        if not connection_id:
            return {
                "ok": False,
                "errors": ["connection_id is required"],
                "warnings": [],
                "connections": self._config.list_connections(),
            }

        connection = self._config.get_connection(connection_id)
        if not connection:
            return {
                "ok": False,
                "errors": ["connection not found"],
                "warnings": [],
                "connections": self._config.list_connections(),
            }

        port = self._connection_port(connection)
        pid_raw = connection.get("runtime_pid")
        pid = int(pid_raw) if isinstance(pid_raw, int) or str(pid_raw).isdigit() else 0
        if pid > 0 and not self._runtime_proc_alive(pid):
            if port is not None and self._endpoint_reachable(port):
                owner_pid = self._listener_pid_for_port(port)
                if owner_pid is not None and owner_pid > 0:
                    pid = int(owner_pid)
                else:
                    self._config.update_connection_runtime(connection_id, "stopped", endpoint=None, runtime_pid=None)
                    return {
                        "ok": True,
                        "errors": [],
                        "warnings": [],
                        "connections": self._config.list_connections(),
                    }
            else:
                self._config.update_connection_runtime(connection_id, "stopped", endpoint=None, runtime_pid=None)
                return {
                    "ok": True,
                    "errors": [],
                    "warnings": [],
                    "connections": self._config.list_connections(),
                }
        if pid <= 0 and port is not None and self._endpoint_reachable(port):
            owner_pid = self._listener_pid_for_port(port)
            if owner_pid is not None and owner_pid > 0:
                pid = int(owner_pid)
        if pid <= 0:
            self._config.update_connection_runtime(connection_id, "stopped", endpoint=None, runtime_pid=None)
            return {
                "ok": True,
                "errors": [],
                "warnings": [],
                "connections": self._config.list_connections(),
            }

        terminated, terminate_err = self._terminate_runtime_process(pid)
        if not terminated:
            return {
                "ok": False,
                "errors": [f"stop failed: {terminate_err}"],
                "warnings": [],
                "connections": self._config.list_connections(),
            }

        deadline = time.time() + 5.0
        while time.time() < deadline:
            if not self._runtime_proc_alive(pid):
                break
            time.sleep(0.1)

        still_alive = self._runtime_proc_alive(pid)
        # On Windows, PID checks may report a live unrelated process after PID reuse.
        # If the target endpoint is no longer reachable, treat runtime as stopped.
        if still_alive and port is not None and not self._endpoint_reachable(port):
            still_alive = False
        if still_alive:
            return {
                "ok": False,
                "errors": ["stop failed: runtime process still alive"],
                "warnings": [],
                "connections": self._config.list_connections(),
            }

        if port is not None:
            deadline_port = time.time() + 2.0
            while time.time() < deadline_port and self._endpoint_reachable(port):
                time.sleep(0.05)

        if port is not None and self._endpoint_reachable(port):
            owner_pid = self._listener_pid_for_port(port)
            if owner_pid is not None and owner_pid > 0:
                owner_pid_int = int(owner_pid)
                # If the live listener does not match the managed runtime PID, treat it as external.
                if owner_pid_int != pid:
                    self._config.update_connection_runtime(
                        connection_id, "stopped", endpoint=None, runtime_pid=owner_pid_int
                    )
                    return {
                        "ok": True,
                        "errors": [],
                        "warnings": [f"stop warning: unmanaged listener remains on port {port} (pid={owner_pid_int})"],
                        "connections": self._config.list_connections(),
                    }
                # On Windows, PID ownership checks can fail for foreign/elevated processes.
                if not self._runtime_proc_alive(owner_pid_int):
                    self._config.update_connection_runtime(
                        connection_id, "stopped", endpoint=None, runtime_pid=owner_pid_int
                    )
                    return {
                        "ok": True,
                        "errors": [],
                        "warnings": [f"stop warning: unmanaged listener remains on port {port} (pid={owner_pid_int})"],
                        "connections": self._config.list_connections(),
                    }
            return {
                "ok": False,
                "errors": ["stop failed: endpoint still reachable"],
                "warnings": [],
                "connections": self._config.list_connections(),
            }

        self._config.update_connection_runtime(connection_id, "stopped", endpoint=None, runtime_pid=None)
        return {
            "ok": True,
            "errors": [],
            "warnings": [],
            "connections": self._config.list_connections(),
        }

    def stop_all_connections(self) -> dict[str, object]:
        errors: list[str] = []
        warnings: list[str] = []
        for connection in self._config.list_connections():
            if not isinstance(connection, dict):
                continue
            connection_id = str(connection.get("id") or "").strip()
            if not connection_id:
                continue
            port = self._connection_port(connection)
            status = str(connection.get("status") or "").strip().lower()
            runtime_pid_raw = connection.get("runtime_pid")
            runtime_pid = int(runtime_pid_raw) if isinstance(runtime_pid_raw, int) or str(runtime_pid_raw).isdigit() else 0
            should_stop = (
                status == "running"
                or (runtime_pid > 0 and self._runtime_proc_alive(runtime_pid))
                or (port is not None and self._endpoint_reachable(port))
            )
            if not should_stop:
                continue
            result = self.stop_connection({"connection_id": connection_id})
            if result.get("ok"):
                for warning in result.get("warnings", []) or []:
                    warnings.append(f"{connection_id}: {warning}")
                continue
            message = "; ".join([str(e) for e in result.get("errors", []) or []]) or "stop failed"
            errors.append(f"{connection_id}: {message}")
        return {
            "ok": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "connections": self._config.list_connections(),
        }

    def delete_connection(self, payload: dict) -> dict[str, object]:
        connection_id = str(payload.get("connection_id") or "").strip()
        if not connection_id:
            return {
                "ok": False,
                "errors": ["connection_id is required"],
                "warnings": [],
                "connections": self._config.list_connections(),
            }

        stop_result = self.stop_connection({"connection_id": connection_id})
        if not stop_result.get("ok"):
            stop_errors = stop_result.get("errors", []) or []
            message = "; ".join([str(e) for e in stop_errors]) if stop_errors else "runtime stop failed before delete"
            return {
                "ok": False,
                "errors": [f"delete failed: {message}"],
                "warnings": stop_result.get("warnings", []) or [],
                "connections": self._config.list_connections(),
            }

        removed = self._config.remove_connection(connection_id)
        if not removed:
            return {
                "ok": False,
                "errors": ["connection not found"],
                "warnings": [],
                "connections": self._config.list_connections(),
            }

        return {
            "ok": True,
            "errors": [],
            "warnings": stop_result.get("warnings", []) or [],
            "connections": self._config.list_connections(),
        }

    def copy_connection_config(self, payload: dict) -> dict[str, object]:
        connection_id = str(payload.get("connection_id") or "").strip()
        connection_name = str(payload.get("connection_name") or "").strip()
        verbose = bool(payload.get("verbose"))
        connections = self._config.list_connections()
        errors: list[str] = []

        def _extract_port(connection: dict) -> int | None:
            if "port" in connection:
                try:
                    return int(connection.get("port"))
                except Exception:
                    return None
            endpoint = str(connection.get("endpoint") or "").strip()
            m = re.match(r"^https?://localhost:(\d+)/sse$", endpoint)
            if m:
                try:
                    return int(m.group(1))
                except Exception:
                    return None
            return None

        def build_url_entry(connection: dict) -> dict[str, object]:
            port = _extract_port(connection)
            if port is None:
                return {}
            return {"url": f"http://localhost:{port}/sse"}

        def build_debug_entry(connection: dict) -> dict[str, object]:
            entry: dict[str, object] = dict(build_url_entry(connection))
            provider_id = str(connection.get("provider_id") or "").strip()
            model_id = str(connection.get("model_id") or "").strip()
            endpoint = str(connection.get("endpoint") or "").strip()
            credentials_path = str(connection.get("credentials_path") or "").strip()
            if provider_id:
                entry["provider_id"] = provider_id
            if model_id:
                entry["model_id"] = model_id
            if endpoint:
                entry["endpoint"] = endpoint
            if credentials_path:
                entry["credentials_path"] = credentials_path
            if isinstance(connection.get("options"), dict) and connection.get("options"):
                entry["options"] = dict(connection.get("options") or {})
            return entry

        def build_entry(connection: dict) -> dict[str, object]:
            return build_debug_entry(connection) if verbose else build_url_entry(connection)

        def canonical_key(connection: dict, used: set[str]) -> str:
            base = str(connection.get("connection_name") or "").strip()
            if not base:
                base = str(connection.get("id") or "").strip()
            key = base or "connection"
            if key in used:
                suffix = str(connection.get("id") or "").strip()
                key = f"{key}-{suffix}" if suffix else f"{key}-dup"
            used.add(key)
            return key

        if connection_id or connection_name:
            target = None
            for connection in connections:
                if connection_id and connection.get("id") == connection_id:
                    target = connection
                    break
                if not connection_id and connection_name and connection.get("connection_name") == connection_name:
                    target = connection
                    break
            if not target:
                errors.append("connection not found")
                return {"ok": False, "errors": errors, "config_text": ""}

            key = str(target.get("connection_name") or "").strip() or str(target.get("id") or "").strip()
            entry = build_entry(target)
            if not entry:
                errors.append("connection missing port")
                return {"ok": False, "errors": errors, "config_text": ""}
            cfg = {"mcpServers": {key: entry}}
            config_text = json.dumps(cfg, indent=2, sort_keys=True)
            return {"ok": True, "errors": [], "config_text": config_text}

        used: set[str] = set()
        servers: dict[str, dict[str, object]] = {}
        for connection in connections:
            entry = build_entry(connection)
            if not entry:
                continue
            servers[canonical_key(connection, used)] = entry
        if not servers and connections:
            errors.append("no connections have a usable port")
            return {"ok": False, "errors": errors, "config_text": ""}
        cfg = {"mcpServers": servers}
        config_text = json.dumps(cfg, indent=2, sort_keys=True)
        return {"ok": True, "errors": [], "config_text": config_text}

    def dry_run_connection(self, payload: dict) -> dict[str, object]:
        connection_id = str(payload.get("connection_id") or "").strip()
        if not connection_id:
            return {"ok": False, "errors": ["connection_id is required"]}

        connections = self._config.list_connections()
        target = None
        for connection in connections:
            if connection.get("id") == connection_id:
                target = connection
                break

        if not target:
            return {"ok": False, "errors": ["connection not found"]}

        preflight_payload = {
            "connection_name": target.get("connection_name"),
            "provider_id": target.get("provider_id"),
            "model_id": target.get("model_id"),
        }
        if "endpoint" in target:
            preflight_payload["endpoint"] = target.get("endpoint")
        if "credentials_path" in target:
            preflight_payload["credentials_path"] = target.get("credentials_path")
        options_payload = target.get("options")
        if isinstance(options_payload, dict):
            for k, v in options_payload.items():
                key = str(k or "").strip()
                if not key or key in preflight_payload:
                    continue
                if v is None:
                    continue
                preflight_payload[key] = v

        preflight = self.preflight_connection(preflight_payload)
        preflight_ok = bool(preflight.get("ok"))
        preflight_errors = list(preflight.get("errors") or [])
        preflight_warnings = list(preflight.get("warnings") or [])
        canonical_error = preflight.get("canonical_error")

        copy_result = self.copy_connection_config({"connection_id": connection_id})
        if not copy_result.get("ok"):
            errors = list(copy_result.get("errors") or [])
            return {"ok": False, "errors": errors}

        config_text = str(copy_result.get("config_text") or "")
        config_hash = hashlib.sha256(config_text.encode("utf-8")).hexdigest()

        trace = {
            "request_id": f"dry-run-{connection_id}",
            "connection_id": connection_id,
            "connection_name": str(target.get("connection_name") or ""),
            "provider_id": str(target.get("provider_id") or ""),
            "model_id": str(target.get("model_id") or ""),
            "preflight_result": {
                "ok": preflight_ok,
                "errors_count": len(preflight_errors),
                "warnings_count": len(preflight_warnings),
            },
            "canonical_config_hash": config_hash,
            "simulated_steps": [
                "load_connection",
                "preflight",
                "build_request_envelope",
                "copy_config",
                "dry_run_complete",
            ],
            "dry_run_result": "DRY_RUN_OK",
        }

        return {
            "ok": preflight_ok,
            "errors": preflight_errors,
            "warnings": preflight_warnings,
            "dry_run_trace": trace,
            "canonical_error": canonical_error,
        }

    def test_agent_connection(self, agent_id: str) -> str:
        agent = self._config.get_agent(agent_id)
        if not agent:
            raise ValueError("Agent not found")

        cred_path = self._creds.get_credential(agent_id)
        if not cred_path:
            raise ValueError("No credentials configured for agent")

        provider_id = agent.get("provider_id") or agent.get("provider") or "vertex"
        logger.info(
            "Testing provider connection for agent id=%s project_id=%s provider_id=%s",
            agent_id,
            agent["project_id"],
            provider_id,
        )

        context = ExecutionContextV1(
            agent=agent,
            project_id=agent["project_id"],
            location=agent["location"],
            provider_id=str(provider_id),
            model_id=agent["model_id"],
            credentials_path=cred_path,
            price_per_1m_input=float(agent["price_per_1m_input"]),
            price_per_1m_output=float(agent["price_per_1m_output"]),
            streaming=False,
        )
        client = ProviderFactory.create(context.provider_id, context)
        result = client.generate_content(
            "Reply with exactly three words: 'Connection is Successful'. Do not add any other text."
        )
        text = str(result.get("text", ""))
        try:
            tokens_in = int(result.get("tokens_input", 0) or 0)
            tokens_out = int(result.get("tokens_output", 0) or 0)
            cost = float(result.get("cost_usd", 0.0) or 0.0)
            cost_source = result.get("cost_source")
            try:
                self._usage_db.log_usage(
                    agent_id=agent_id,
                    agent_name=f"_test_{agent['name']}",
                    tokens_input=tokens_in,
                    tokens_output=tokens_out,
                    cost_usd=cost,
                    cost_source=str(cost_source) if cost_source is not None else None,
                    status="success",
                )
            except Exception as db_exc:
                logger.warning(
                    "Failed to log usage for agent id=%s: %s",
                    agent_id,
                    db_exc,
                )
        except Exception as exc:
            logger.warning(
                "Failed to extract usage metrics for agent id=%s: %s",
                agent_id,
                exc,
            )
        logger.info("Provider connection test succeeded for agent id=%s", agent_id)
        return text

    def execute_request_v1(self, agent_id: str, prompt: str, dry_run: bool = False) -> dict[str, object]:
        request = ExecutionRequestV1(agent_id=agent_id, prompt=prompt)
        preflight = PreflightGuardV1()
        context = preflight.run(self._config, self._creds, request)

        if dry_run:
            return {
                "text": "DRY_RUN_OK",
                "tokens_input": 0,
                "tokens_output": 0,
                "cost_usd": 0.0,
                "latency_ms": 0,
                "status": "success",
                "error_type": None,
                "request_id": "dry-run-id",
                "provider": context.provider_id,
                "model_id": context.model_id,
                "dry_run": True,
                "payload_summary": {
                    "provider_id": context.provider_id,
                    "model_id": context.model_id,
                    "agent_id": agent_id,
                }
            }

        router = RouterV1()
        routed_context = router.route(context)
        provider = ProviderAdapterV1()
        observer = ObserverV1()
        try:
            result = provider.execute(routed_context, prompt)
        except Exception as exc:
            canonical_error = getattr(exc, "canonical_error", None)
            if not isinstance(canonical_error, dict):
                canonical_error = self._build_canonical_error(
                    phase="runtime",
                    provider_id=str(getattr(exc, "provider", routed_context.provider_id) or ""),
                    model_id=str(getattr(exc, "model_id", routed_context.model_id) or ""),
                    request_id=str(getattr(exc, "request_id", "") or "") or None,
                    reason=str(exc),
                    raw=exc,
                )
                try:
                    setattr(exc, "canonical_error", canonical_error)
                except Exception:
                    pass
            error_result: dict[str, object] = {
                "text": "",
                "tokens_input": 0,
                "tokens_output": 0,
                "cost_usd": 0.0,
                "latency_ms": getattr(exc, "latency_ms", None),
                "status": "error",
                "error_type": getattr(exc, "error_type", exc.__class__.__name__),
                "request_id": getattr(exc, "request_id", None),
                "provider": getattr(exc, "provider", None),
                "model_id": getattr(exc, "model_id", routed_context.model_id),
                "error": canonical_error,
            }
            observer.observe(self._usage_db, routed_context, error_result)
            raise
        observer.observe(self._usage_db, routed_context, result)
        return result

    def _request_dedup_key(
        self,
        connection_id: str,
        provider_id: str,
        model_id: str,
        prompt: str,
        persona_text: str,
    ) -> str:
        payload = {
            "connection_id": str(connection_id or "").strip(),
            "provider_id": str(provider_id or "").strip(),
            "model_id": str(model_id or "").strip(),
            "prompt": str(prompt or ""),
            "persona": str(persona_text or ""),
        }
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _request_dedup_get(self, key: str) -> dict[str, object] | None:
        row = self._request_dedup_cache.get(str(key or ""))
        if not isinstance(row, dict):
            return None
        created_at = row.get("created_at")
        try:
            created = float(created_at)
        except Exception:
            created = 0.0
        if created <= 0 or (time.time() - created) > float(self._REQUEST_DEDUP_TTL_SECONDS):
            self._request_dedup_cache.pop(str(key or ""), None)
            return None
        return copy.deepcopy(row)

    def _request_dedup_put(self, key: str, text: str, provider_id: str, model_id: str, request_id: str) -> None:
        dedup_key = str(key or "").strip()
        if not dedup_key:
            return
        self._request_dedup_cache[dedup_key] = {
            "created_at": float(time.time()),
            "text": str(text or ""),
            "provider": str(provider_id or ""),
            "model_id": str(model_id or ""),
            "source_request_id": str(request_id or ""),
        }

    def _apply_json_syntax_repair_interceptor(
        self,
        result: dict[str, object],
    ) -> dict[str, object]:
        interceptors_state = self._canonicalize_resilience_interceptors_state(
            self._config.get_resilience_interceptors_state()
        )
        enabled_by_id = interceptors_state.get("enabled_by_id")
        settings_by_id = interceptors_state.get("settings_by_id")
        enabled = bool(enabled_by_id.get("json_syntax_repair")) if isinstance(enabled_by_id, dict) else False
        settings_row = settings_by_id.get("json_syntax_repair") if isinstance(settings_by_id, dict) else {}
        settings = settings_row if isinstance(settings_row, dict) else {}
        mode = str(settings.get("mode") or "safe").strip() or "safe"
        strict_json = bool(settings.get("strict_json", True))
        max_attempts_raw = settings.get("max_attempts", 0)
        try:
            max_attempts = int(max_attempts_raw)
        except Exception:
            max_attempts = 0
        if max_attempts < 0:
            max_attempts = 0

        trace: dict[str, object] = {
            "enabled": enabled,
            "mode": mode,
            "strict_json": strict_json,
            "max_attempts": max_attempts,
            "applied": False,
            "changes": [],
            "error": None,
        }
        if not enabled or mode == "off":
            result["interceptor_json_syntax_repair"] = trace
            return result

        raw_text = str(result.get("text") or "")
        repair = repair_json_syntax(raw_text)
        trace["changes"] = list(repair.changes)

        if repair.ok:
            if isinstance(repair.repaired, str):
                result["text"] = repair.repaired
                trace["applied"] = True
            result["interceptor_json_syntax_repair"] = trace
            return result

        if strict_json and mode == "aggressive":
            trace["error"] = "interceptor_json_syntax_repair_failed"
            result["interceptor_json_syntax_repair"] = trace
            raise ValueError("interceptor_json_syntax_repair_failed")

        trace["error"] = "interceptor_json_syntax_repair_not_applied"
        result["interceptor_json_syntax_repair"] = trace
        return result

    def execute_connection_request_v1(self, connection_id: str, prompt: str) -> dict[str, object]:
        target = self._config.get_connection(str(connection_id or "").strip())
        if not target:
            raise ValueError("Connection not found")

        connection_name = str(target.get("connection_name") or connection_id or "connection-runtime")
        provider_id = str(target.get("provider_id") or "vertex").strip() or "vertex"
        model_id = str(target.get("model_id") or "").strip()
        if not model_id:
            raise ValueError("model_id is required")

        options = target.get("options")
        options_map = dict(options) if isinstance(options, dict) else {}

        # Flatten options into an agent-like payload so provider adapters can read provider-specific keys.
        agent_payload: dict[str, object] = dict(target)
        for key, value in options_map.items():
            normalized_key = str(key or "").strip()
            if not normalized_key:
                continue
            if normalized_key not in agent_payload:
                agent_payload[normalized_key] = value
        agent_payload["id"] = str(target.get("id") or connection_id)
        agent_payload["name"] = connection_name
        persona_text = self._resolve_persona_text_for_connection(str(target.get("id") or connection_id))
        if persona_text:
            agent_payload["persona"] = persona_text
        optimizations_state = self._canonicalize_optimizations_state(
            self._config.get_policies_optimizations_state()
        )
        context_caching_enabled = bool(optimizations_state.get("context_caching_enabled", False))
        request_dedup_enabled = bool(optimizations_state.get("request_dedup_enabled", False))
        agent_payload["context_caching_enabled"] = context_caching_enabled
        agent_payload["request_dedup_enabled"] = request_dedup_enabled

        project_id = str(
            target.get("project_id")
            or agent_payload.get("project_id")
            or options_map.get("project_id")
            or ""
        ).strip()
        location = str(
            target.get("location")
            or agent_payload.get("location")
            or options_map.get("location")
            or "us-central1"
        ).strip() or "us-central1"
        credentials_path = str(
            target.get("credentials_path")
            or agent_payload.get("credentials_path")
            or options_map.get("credentials_path")
            or ""
        ).strip()
        resolved_credentials_path, resolve_errors = self._resolve_credentials_path(credentials_path)
        if resolve_errors:
            raise ValueError("; ".join(resolve_errors))

        if provider_id == "vertex" and not project_id:
            raise ValueError("project_id is required")

        context = ExecutionContextV1(
            agent=agent_payload,
            project_id=project_id or "runtime-project",
            location=location,
            provider_id=provider_id,
            model_id=model_id,
            credentials_path=resolved_credentials_path,
            price_per_1m_input=0.0,
            price_per_1m_output=0.0,
            streaming=False,
        )

        router = RouterV1()
        routed_context = router.route(context)
        provider = ProviderAdapterV1()
        observer = ObserverV1()

        dedup_key = self._request_dedup_key(
            connection_id=str(target.get("id") or connection_id),
            provider_id=provider_id,
            model_id=model_id,
            prompt=prompt,
            persona_text=persona_text,
        )
        if request_dedup_enabled:
            dedup_hit = self._request_dedup_get(dedup_key)
            if isinstance(dedup_hit, dict):
                dedup_result: dict[str, object] = {
                    "text": str(dedup_hit.get("text") or ""),
                    "tokens_input": 0,
                    "tokens_output": 0,
                    "cost_usd": 0.0,
                    "latency_ms": 0,
                    "status": "success",
                    "error_type": None,
                    "request_id": f"dedup-{uuid.uuid4().hex[:12]}",
                    "provider": str(dedup_hit.get("provider") or provider_id),
                    "model_id": str(dedup_hit.get("model_id") or model_id),
                    "request_dedup_enabled": True,
                    "request_dedup_hit": True,
                    "request_dedup_source_request_id": str(dedup_hit.get("source_request_id") or ""),
                }
                observer.observe(self._usage_db, routed_context, dedup_result)
                return dedup_result

        try:
            result = provider.execute(routed_context, prompt)
            result = self._apply_json_syntax_repair_interceptor(result)
            result["request_dedup_enabled"] = request_dedup_enabled
            result["request_dedup_hit"] = False
            if request_dedup_enabled:
                self._request_dedup_put(
                    key=dedup_key,
                    text=str(result.get("text") or ""),
                    provider_id=str(result.get("provider") or provider_id),
                    model_id=str(result.get("model_id") or model_id),
                    request_id=str(result.get("request_id") or ""),
                )
        except Exception as exc:
            canonical_error = getattr(exc, "canonical_error", None)
            if not isinstance(canonical_error, dict):
                canonical_error = self._build_canonical_error(
                    phase="runtime",
                    provider_id=str(getattr(exc, "provider", provider_id) or ""),
                    model_id=str(getattr(exc, "model_id", model_id) or ""),
                    request_id=str(getattr(exc, "request_id", "") or "") or None,
                    reason=str(exc),
                    raw=exc,
                )
                try:
                    setattr(exc, "canonical_error", canonical_error)
                except Exception:
                    pass
            error_result: dict[str, object] = {
                "text": "",
                "tokens_input": 0,
                "tokens_output": 0,
                "cost_usd": 0.0,
                "latency_ms": getattr(exc, "latency_ms", None),
                "status": "error",
                "error_type": getattr(exc, "error_type", exc.__class__.__name__),
                "request_id": getattr(exc, "request_id", None),
                "provider": getattr(exc, "provider", provider_id),
                "model_id": getattr(exc, "model_id", model_id),
                "request_dedup_enabled": request_dedup_enabled,
                "request_dedup_hit": False,
                "error": canonical_error,
            }
            observer.observe(self._usage_db, routed_context, error_result)
            raise
        observer.observe(self._usage_db, routed_context, result)
        return result


def _parse_runtime_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--connection-runtime", action="store_true")
    parser.add_argument("--connection-id", default="")
    parser.add_argument("--name", default="ConnectionRuntime")
    parser.add_argument("--port", type=int, default=0)
    return parser.parse_known_args(argv)[0]


def _run_connection_runtime(args: argparse.Namespace) -> int:
    if not args.connection_runtime:
        return 0
    if int(args.port or 0) <= 0:
        return 2
    runtime_connection_id = str(args.connection_id or "").strip()
    if not runtime_connection_id:
        return 2

    runtime_manager = ServerManager()
    runtime_connection = runtime_manager._config.get_connection(runtime_connection_id)
    if not runtime_connection:
        return 3
    runtime_options = runtime_connection.get("options")
    runtime_options_map = dict(runtime_options) if isinstance(runtime_options, dict) else {}
    runtime_project_id = str(
        runtime_connection.get("project_id")
        or runtime_options_map.get("project_id")
        or "runtime-project"
    ).strip() or "runtime-project"
    runtime_location = str(
        runtime_connection.get("location")
        or runtime_options_map.get("location")
        or "us-central1"
    ).strip() or "us-central1"

    def _runtime_execute_request(agent_id: str, prompt: str) -> dict[str, object]:
        effective_connection_id = str(agent_id or runtime_connection_id).strip() or runtime_connection_id
        return runtime_manager.execute_connection_request_v1(effective_connection_id, prompt)

    server = MCPAgentServer(
        name=str(args.name),
        port=int(args.port),
        project_id=runtime_project_id,
        location=runtime_location,
        agent_id=runtime_connection_id,
        execute_request_v1=_runtime_execute_request,
    )
    started = server.start()
    if not started:
        return 1
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
    return 0


if __name__ == "__main__":
    runtime_args = _parse_runtime_args()
    if runtime_args.connection_runtime:
        raise SystemExit(_run_connection_runtime(runtime_args))
