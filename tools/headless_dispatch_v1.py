import argparse
import json
import os
import sys
from pathlib import Path


def _repo_root_from_tools_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _ok(text: str | None) -> dict:
    return {"ok": True, "status": "success", "text": text, "error": None}


def _fail(code: str, message: str) -> dict:
    return {"ok": False, "status": "error", "text": None, "error": {"code": code, "message": message}}


def _connections_response(result: dict) -> dict:
    ok = bool(result.get("ok"))
    errors = list(result.get("errors") or [])
    warnings = list(result.get("warnings") or [])
    connections = list(result.get("connections") or [])
    normalized_payload = result.get("normalized_payload")
    config_text = result.get("config_text")
    dry_run_trace = result.get("dry_run_trace")
    schema_hint = result.get("schema_hint")
    error_payload = None
    status = "success" if ok else "error"
    if not ok:
        message = "; ".join([str(e) for e in errors]) if errors else "invalid_request"
        error_payload = {"code": "invalid_request", "message": message}
    return {
        "ok": ok,
        "status": status,
        "text": None,
        "error": error_payload,
        "errors": errors,
        "warnings": warnings,
        "normalized_payload": normalized_payload,
        "connections": connections,
        "config_text": config_text,
        "dry_run_trace": dry_run_trace,
        "schema_hint": schema_hint,
    }


def _schema_hint_response(result: dict) -> dict:
    ok = bool(result.get("ok"))
    errors = list(result.get("errors") or [])
    warnings = list(result.get("warnings") or [])
    raw_hint = result.get("schema_hint")
    hint = raw_hint if isinstance(raw_hint, dict) else {}
    fields = hint.get("fields")
    defaults = hint.get("suggested_defaults")
    notes = hint.get("notes")

    if ok:
        data = {
            "fields": list(fields) if isinstance(fields, list) else [],
            "defaults": dict(defaults) if isinstance(defaults, dict) else {},
            "notes": list(notes) if isinstance(notes, list) else [],
            "warnings": warnings,
        }
        return {"ok": True, "status": "success", "data": data, "error": None}

    message = "; ".join([str(e) for e in errors]) if errors else "schema_hint_failed"
    return {
        "ok": False,
        "status": "error",
        "data": None,
        "error": {
            "code": "schema_hint_failed",
            "message": message,
            "details": {"errors": errors, "warnings": warnings},
        },
    }


def _normalize_provider_keys(payload: dict) -> dict:
    if not isinstance(payload, dict):
        return {}

    normalized = dict(payload)

    def normalize_dict(target: dict) -> dict:
        out = dict(target)
        if not str(out.get("provider_id") or "").strip():
            provider_camel = str(out.get("providerId") or "").strip()
            provider_plain = str(out.get("provider") or "").strip()
            provider_value = provider_camel or provider_plain
            if provider_value:
                out["provider_id"] = provider_value
        return out

    normalized = normalize_dict(normalized)
    connection_payload = normalized.get("connection")
    if isinstance(connection_payload, dict):
        normalized["connection"] = normalize_dict(connection_payload)
    return normalized


def _maybe_parse_json_prompt(prompt: str) -> dict | None:
    s = str(prompt or "").strip()
    if not s.startswith("{"):
        return None
    try:
        value = json.loads(s)
    except Exception as exc:
        raise ValueError(str(exc))
    if isinstance(value, dict):
        return value
    raise ValueError("JSON prompt must be an object")


def _dispatch_op(payload: dict) -> dict:
    repo_root = _repo_root_from_tools_dir()
    if repo_root not in sys.path:
        sys.path.append(repo_root)

    from src.config.manager import ConfigManager
    from src.mcp_server.manager import ServerManager

    payload = _normalize_provider_keys(payload)
    op = str(payload.get("op") or "")
    cfg = ConfigManager()

    if op == "connections.list":
        mgr = ServerManager()
        return _connections_response(mgr.list_connections())

    if op == "connections.create":
        connection_payload = payload.get("connection")
        if not isinstance(connection_payload, dict):
            connection_payload = {}
        mgr = ServerManager()
        return _connections_response(mgr.create_connection(connection_payload))

    if op == "connections.preflight":
        connection_payload = payload.get("connection")
        if not isinstance(connection_payload, dict):
            connection_payload = {}
        mgr = ServerManager()
        return _connections_response(mgr.preflight_connection(connection_payload))

    if op == "connections.schema_hint":
        mgr = ServerManager()
        return _schema_hint_response(mgr.connections_schema_hint(payload))

    if op == "connections.copy_config":
        mgr = ServerManager()
        return _connections_response(mgr.copy_connection_config(payload))

    if op == "connections.dry_run":
        mgr = ServerManager()
        return _connections_response(mgr.dry_run_connection(payload))

    if op == "bridges.list":
        data = cfg._read_config()
        bridges = data.get("agents", [])
        return _ok(json.dumps({"bridges": bridges}, ensure_ascii=False))

    if op == "usage.recent":
        from src.data.usage_db import UsageDatabase
        from src.ui.usage_kpis import compute_usage_kpis

        limit = payload.get("limit")
        try:
            limit_n = int(limit) if limit is not None else 50
        except Exception:
            limit_n = 50
        limit_n = max(1, min(500, limit_n))

        db = UsageDatabase()
        rows = db.get_recent_usage(limit=limit_n)
        k = compute_usage_kpis(rows)
        total_requests = int(k.get("total_requests", 0) or 0)
        total_success = int(k.get("total_success", 0) or 0)
        total_cost = float(k.get("total_cost", 0.0) or 0.0)
        latency_values = k.get("latency_values") or []
        latency_ints: list[int] = []
        for v in latency_values:
            try:
                latency_ints.append(int(v))
            except Exception:
                pass
        avg_latency = int(round(sum(latency_ints) / len(latency_ints))) if latency_ints else None
        success_rate = (float(total_success) / float(total_requests) * 100.0) if total_requests > 0 else None
        out_rows: list[dict] = []
        for r in rows:
            out_rows.append(
                {
                    "timestamp": r.get("timestamp"),
                    "status": r.get("status"),
                    "error_type": r.get("error_type"),
                    "latency_ms": r.get("latency_ms"),
                    "tokens_input": r.get("tokens_input"),
                    "tokens_output": r.get("tokens_output"),
                    "cost_usd": r.get("cost_usd"),
                }
            )
        return _ok(
            json.dumps(
                {
                    "kpis": {
                        "total_requests": total_requests,
                        "success_rate": success_rate,
                        "total_cost_usd": total_cost,
                        "avg_latency_ms": avg_latency,
                    },
                    "rows": out_rows,
                },
                ensure_ascii=False,
            )
        )

    bridge_id = payload.get("bridge_id")
    if not isinstance(bridge_id, str) or not bridge_id.strip():
        return _fail("invalid_request", "bridge_id is required")
    bridge_id = bridge_id.strip()

    agent = cfg.get_agent(bridge_id)
    if not isinstance(agent, dict):
        return _fail("bridge_not_found", "bridge not found")

    mgr = ServerManager()

    if op == "bridges.toggle":
        action = str(payload.get("action") or "toggle")
        status = str(agent.get("status") or "stopped")
        if action == "toggle":
            action = "stop" if status == "running" else "start"
        if action == "start":
            mgr.start_agent(bridge_id)
        elif action == "stop":
            mgr.stop_agent(bridge_id)
        else:
            return _fail("invalid_request", "action must be start, stop, or toggle")
        updated = cfg.get_agent(bridge_id) or agent
        return _ok(json.dumps({"bridge": updated}, ensure_ascii=False))

    if op == "bridges.test":
        text = mgr.test_agent_connection(bridge_id)
        return _ok(str(text))

    if op == "bridges.config":
        name = str(agent.get("name") or "Bridge")
        port = agent.get("port")
        cfg_obj = {"mcpServers": {name: {"url": f"http://localhost:{port}/sse"}}}
        return _ok(json.dumps(cfg_obj, indent=2, ensure_ascii=False))

    return _fail("invalid_request", "unknown op")


def _dispatch(agent_id: str, prompt: str) -> dict:
    repo_root = _repo_root_from_tools_dir()
    if repo_root not in sys.path:
        sys.path.append(repo_root)

    from src.mcp_server.manager import ServerManager

    try:
        payload = _maybe_parse_json_prompt(prompt)
    except ValueError as exc:
        return {
            "ok": False,
            "status": "error",
            "text": None,
            "error": {
                "code": "dispatch_invalid_json",
                "message": str(exc),
            },
        }
    dry_run = False
    if isinstance(payload, dict):
        if isinstance(payload.get("op"), str):
            return _dispatch_op(payload)
        dry_run = bool(payload.get("dry_run"))

    mgr = ServerManager()
    result = mgr.execute_request_v1(agent_id=agent_id, prompt=prompt, dry_run=dry_run)
    text = result.get("text")
    if isinstance(text, str):
        text_out = text
    else:
        text_out = None
    
    out = {"ok": True, "status": str(result.get("status") or "success"), "text": text_out, "error": None}
    if dry_run:
        out["dry_run_data"] = result
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-file")
    args = parser.parse_args()

    if args.prompt and args.prompt_file:
        payload = _fail("prompt_args_conflict", "Use either --prompt or --prompt-file, not both.")
        sys.stdout.write(json.dumps(payload, ensure_ascii=False))
        return 2

    if not args.prompt and not args.prompt_file:
        payload = _fail("prompt_missing", "One of --prompt or --prompt-file is required.")
        sys.stdout.write(json.dumps(payload, ensure_ascii=False))
        return 2

    if args.prompt_file:
        try:
            prompt_text = Path(args.prompt_file).read_text(encoding="utf-8-sig").rstrip("\r\n")
        except Exception as exc:
            payload = _fail("prompt_file_read_failed", str(exc))
            sys.stdout.write(json.dumps(payload, ensure_ascii=False))
            return 2
    else:
        prompt_text = str(args.prompt)

    try:
        payload = _dispatch(agent_id=args.agent_id, prompt=prompt_text)
    except Exception as exc:
        payload = {
            "ok": False,
            "status": "error",
            "text": None,
            "error": {
                "code": getattr(exc, "error_type", exc.__class__.__name__),
                "message": str(exc),
            },
        }

    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
