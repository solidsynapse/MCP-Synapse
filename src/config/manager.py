import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


class ConfigManager:
    def __init__(self) -> None:
        self._root = Path(__file__).resolve().parents[2]
        self._data_dir = self._root / "data"
        self._config_path = self._data_dir / "config.json"
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        self._data_dir.mkdir(parents=True, exist_ok=True)
        if not self._config_path.exists():
            self._write_config(
                {
                    "agents": [],
                    "connections": [],
                    "policies": {
                        "persona_state": self.default_persona_state(),
                        "optimizations_state": self.default_optimizations_state(),
                        "resilience_budget_state": self.default_resilience_budget_state(),
                        "resilience_interceptors_state": self.default_resilience_interceptors_state(),
                        "dashboard_state": self.default_dashboard_state(),
                        "settings_state": self.default_settings_state(),
                    },
                }
            )

    @staticmethod
    def _iso_utc_now() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def default_persona_state() -> dict:
        return {
            "selected_persona_id": "default",
            "selected_target_id": "bridge_alpha",
            "applied_rows": [],
            "presets": [
                {
                    "id": "preset_default",
                    "name": "Default",
                    "text": (
                        "You are MCP Synapse. Be accurate, neutral, and helpful. "
                        "If requirements are ambiguous, ask concise clarifying questions. "
                        "Avoid revealing secrets and avoid provider-specific claims unless explicitly given."
                    ),
                },
                {
                    "id": "preset_analyst",
                    "name": "Analyst",
                    "text": "You are an analytical assistant. Explain assumptions, trade-offs, and risks. Prefer structured bullet points.",
                },
                {
                    "id": "preset_concise",
                    "name": "Concise",
                    "text": "You are a concise assistant. Answer directly and avoid extra explanation unless asked.",
                },
            ],
            "selected_preset_id": "preset_default",
        }

    @staticmethod
    def default_optimizations_state() -> dict:
        return {
            "context_caching_enabled": False,
            "request_dedup_enabled": False,
        }

    @staticmethod
    def default_resilience_budget_state() -> dict:
        return {
            "selected_scope_id": "all",
            "limit_value": "",
            "unit": "usd_per_day",
            "applied_guards": [],
        }

    @staticmethod
    def default_resilience_interceptors_state() -> dict:
        return {
            "enabled_by_id": {
                "json_syntax_repair": False,
            },
            "settings_by_id": {
                "json_syntax_repair": {
                    "mode": "safe",
                    "max_attempts": 2,
                    "strict_json": True,
                    "note": "Deterministic resilience setting persisted in core state.",
                }
            },
        }

    @staticmethod
    def default_dashboard_state() -> dict:
        return {
            "kpis": [
                {"label": "Total Cost USD", "value": "$1,245.50", "icon": "$"},
                {"label": "Total Requests", "value": "1.2M", "icon": "R"},
                {"label": "Total Tokens", "value": "850M", "icon": "T"},
                {"label": "Success Rate %", "value": "99.8%", "icon": "S"},
                {"label": "Avg Latency ms", "value": "245ms", "icon": "L"},
                {"label": "Active Bridges count", "value": "12", "icon": "B"},
            ],
            "recent_requests": [
                {
                    "time": "Today, 08:03:18",
                    "status": "Success",
                    "provider": "Provider X",
                    "latency": "245ms",
                    "tokens": "100 / 850",
                    "cost": "$1,245.50",
                },
                {
                    "time": "Today, 08:03:51",
                    "status": "Success",
                    "provider": "Provider X",
                    "latency": "245ms",
                    "tokens": "100 / 220",
                    "cost": "$172.50",
                },
                {
                    "time": "Today, 08:03:34",
                    "status": "Error",
                    "provider": "Provider X",
                    "latency": "245ms",
                    "tokens": "4501 / 202",
                    "cost": "$115.00",
                },
                {
                    "time": "Today, 08:03:43",
                    "status": "Success",
                    "provider": "Provider X",
                    "latency": "245ms",
                    "tokens": "210 / 571",
                    "cost": "$17.00",
                },
            ],
            "top_expensive": [
                {"id": "id-8a255ac-abbb-a2ac892...", "cost": "$389.90"},
                {"id": "id-8567512-a756-b27b895...", "cost": "$323.00"},
                {"id": "id-8335769-a8ac-a48bb77...", "cost": "$206.00"},
                {"id": "id-83556a9-a83d-a79b895...", "cost": "$199.60"},
            ],
            "breakdown_legend": [
                {"name": "Provider A", "color": "var(--accent-base)", "cost": "$747.30"},
                {"name": "Provider B", "color": "#3b82f6", "cost": "$349.20"},
                {"name": "Provider C", "color": "#6366f1", "cost": "$149.00"},
            ],
            "trend_data": [
                {"label": "Day 1", "valueFormatted": "$98.20"},
                {"label": "Day 4", "valueFormatted": "$112.35"},
                {"label": "Day 7", "valueFormatted": "$105.10"},
                {"label": "Day 10", "valueFormatted": "$134.40"},
                {"label": "Day 13", "valueFormatted": "$128.00"},
                {"label": "Day 16", "valueFormatted": "$162.75"},
                {"label": "Day 19", "valueFormatted": "$149.30"},
                {"label": "Day 22", "valueFormatted": "$171.90"},
                {"label": "Day 25", "valueFormatted": "$158.60"},
                {"label": "Day 28", "valueFormatted": "$189.15"},
                {"label": "Day 30", "valueFormatted": "$176.25"},
            ],
            "quick_alerts": [
                {"level": "warning", "text": "High Latency on Provider X"},
                {"level": "info", "text": "Budget threshold nearing"},
            ],
        }

    @staticmethod
    def default_settings_state() -> dict:
        return {
            "data_retention": "3m",
            "port_mode": "auto",
            "port_min": "5000",
            "port_max": "6000",
        }

    def _read_config(self) -> dict:
        self._ensure_storage()
        with self._config_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_config(self, data: dict) -> None:
        with self._config_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)

    def add_agent(
        self,
        name: str,
        project_id: str,
        location: str,
        model_id: str,
        price_per_1m_input: float,
        price_per_1m_output: float,
        port: int | None = None,
        status: str = "stopped",
    ) -> dict:
        config = self._read_config()
        agents = config.get("agents", [])
        assigned_port = port or self.get_next_available_port()
        agent = {
            "id": str(uuid.uuid4()),
            "name": name,
            "project_id": project_id,
            "location": location,
            "model_id": model_id,
            "price_per_1m_input": float(price_per_1m_input),
            "price_per_1m_output": float(price_per_1m_output),
            "port": int(assigned_port),
            "status": status,
        }
        agents.insert(0, agent)
        config["agents"] = agents
        self._write_config(config)
        return agent

    def add_connection(
        self,
        connection_name: str,
        provider_id: str,
        model_id: str,
        endpoint: str | None = None,
        credentials_path: str | None = None,
        port: int | None = None,
        options: dict | None = None,
    ) -> dict:
        config = self._read_config()
        connections = config.get("connections", [])
        assigned_port = int(port) if port is not None else self.get_next_available_connection_port()
        connection = {
            "id": str(uuid.uuid4()),
            "connection_name": connection_name,
            "provider_id": provider_id,
            "model_id": model_id,
            "port": assigned_port,
        }
        if endpoint:
            connection["endpoint"] = endpoint
        if credentials_path:
            connection["credentials_path"] = credentials_path
        if isinstance(options, dict) and options:
            connection["options"] = dict(options)
        connections.insert(0, connection)
        config["connections"] = connections
        self._write_config(config)
        return connection

    def list_connections(self) -> list[dict]:
        config = self._read_config()
        connections = list(config.get("connections", []) or [])
        connections.sort(
            key=lambda value: (
                str(value.get("connection_name") or "").strip().lower(),
                str(value.get("id") or ""),
            )
        )
        return connections

    def remove_connection(self, connection_id: str) -> bool:
        config = self._read_config()
        connections = config.get("connections", [])
        remaining = [connection for connection in connections if connection.get("id") != connection_id]
        if len(remaining) == len(connections):
            return False
        config["connections"] = remaining
        self._write_config(config)
        return True

    def update_connection_status(self, connection_id: str, status: str) -> dict | None:
        if status not in ("running", "stopped"):
            return None
        config = self._read_config()
        connections = config.get("connections", [])
        updated = None
        for connection in connections:
            if connection.get("id") == connection_id:
                connection["status"] = status
                updated = connection
                break
        if updated is None:
            return None
        config["connections"] = connections
        self._write_config(config)
        return updated

    def get_connection(self, connection_id: str) -> dict | None:
        config = self._read_config()
        for connection in config.get("connections", []) or []:
            if isinstance(connection, dict) and connection.get("id") == connection_id:
                return dict(connection)
        return None

    def update_connection_runtime(
        self,
        connection_id: str,
        status: str,
        endpoint: str | None = None,
        runtime_pid: int | None = None,
    ) -> dict | None:
        if status not in ("running", "stopped"):
            return None
        config = self._read_config()
        connections = config.get("connections", [])
        updated = None
        for connection in connections:
            if connection.get("id") != connection_id:
                continue
            connection["status"] = status
            if endpoint:
                connection["endpoint"] = str(endpoint)
            elif status == "stopped":
                connection.pop("endpoint", None)
            if runtime_pid is not None:
                connection["runtime_pid"] = int(runtime_pid)
            else:
                connection.pop("runtime_pid", None)
            updated = connection
            break
        if updated is None:
            return None
        config["connections"] = connections
        self._write_config(config)
        return dict(updated)

    def update_connection(
        self,
        connection_id: str,
        connection_name: str,
        provider_id: str,
        model_id: str,
        endpoint: str | None = None,
        credentials_path: str | None = None,
        options: dict | None = None,
    ) -> dict | None:
        config = self._read_config()
        connections = config.get("connections", [])
        updated = None
        for connection in connections:
            if connection.get("id") != connection_id:
                continue
            connection["connection_name"] = str(connection_name)
            connection["provider_id"] = str(provider_id)
            connection["model_id"] = str(model_id)
            if endpoint:
                connection["endpoint"] = str(endpoint)
            else:
                connection.pop("endpoint", None)
            if credentials_path:
                connection["credentials_path"] = str(credentials_path)
            else:
                connection.pop("credentials_path", None)
            if isinstance(options, dict) and options:
                connection["options"] = dict(options)
            else:
                connection.pop("options", None)
            updated = connection
            break
        if updated is None:
            return None
        config["connections"] = connections
        self._write_config(config)
        return dict(updated)

    def get_agent(self, agent_id: str) -> dict | None:
        config = self._read_config()
        for agent in config.get("agents", []):
            if agent.get("id") == agent_id:
                return agent
        return None

    def update_agent_status(self, agent_id: str, status: str) -> dict | None:
        config = self._read_config()
        updated = None
        for agent in config.get("agents", []):
            if agent.get("id") == agent_id:
                agent["status"] = status
                updated = agent
                break
        if updated:
            self._write_config(config)
        return updated

    def remove_agent(self, agent_id: str) -> bool:
        config = self._read_config()
        agents = config.get("agents", [])
        remaining = [agent for agent in agents if agent.get("id") != agent_id]
        if len(remaining) == len(agents):
            return False
        config["agents"] = remaining
        self._write_config(config)
        return True

    def get_next_available_port(self, start: int = 5000, end: int = 6000) -> int:
        config = self._read_config()
        used_ports = {agent.get("port") for agent in config.get("agents", [])}
        for port in range(start, end + 1):
            if port not in used_ports:
                return port
        raise RuntimeError("No available ports in the configured range.")

    def get_next_available_connection_port(self, start: int = 5000, end: int = 6000) -> int:
        config = self._read_config()
        used_ports = {agent.get("port") for agent in config.get("agents", [])}
        for connection in config.get("connections", []) or []:
            if isinstance(connection, dict) and "port" in connection:
                used_ports.add(connection.get("port"))
        for port in range(start, end + 1):
            if port not in used_ports:
                return port
        raise RuntimeError("No available ports in the configured range.")

    def get_allowed_models(self) -> list[str]:
        config = self._read_config()
        models = config.get("allowed_models")
        default_model = "gemini-2.0-flash-001"
        default_allowed = [default_model, "gemini-1.5-flash-002"]
        if isinstance(models, list) and models:
            allowed: list[str] = []
            for value in models:
                s = str(value)
                if s not in allowed:
                    allowed.append(s)
            if default_model not in allowed:
                allowed.append(default_model)
            return allowed
        return default_allowed

    def get_policies_persona_state(self) -> dict:
        config = self._read_config()
        policies = config.get("policies")
        if not isinstance(policies, dict):
            policies = {}
        state = policies.get("persona_state")
        if not isinstance(state, dict):
            state = self.default_persona_state()
            policies["persona_state"] = state
            config["policies"] = policies
            self._write_config(config)
        return dict(state)

    def set_policies_persona_state(self, state: dict) -> dict:
        config = self._read_config()
        policies = config.get("policies")
        if not isinstance(policies, dict):
            policies = {}
        policies["persona_state"] = dict(state)
        config["policies"] = policies
        self._write_config(config)
        return dict(state)

    def get_policies_optimizations_state(self) -> dict:
        config = self._read_config()
        policies = config.get("policies")
        if not isinstance(policies, dict):
            policies = {}
        state = policies.get("optimizations_state")
        if not isinstance(state, dict):
            state = self.default_optimizations_state()
            policies["optimizations_state"] = state
            config["policies"] = policies
            self._write_config(config)
        return dict(state)

    def set_policies_optimizations_state(self, state: dict) -> dict:
        config = self._read_config()
        policies = config.get("policies")
        if not isinstance(policies, dict):
            policies = {}
        policies["optimizations_state"] = dict(state)
        config["policies"] = policies
        self._write_config(config)
        return dict(state)

    def get_resilience_budget_state(self) -> dict:
        config = self._read_config()
        policies = config.get("policies")
        if not isinstance(policies, dict):
            policies = {}
        state = policies.get("resilience_budget_state")
        if not isinstance(state, dict):
            state = self.default_resilience_budget_state()
            policies["resilience_budget_state"] = state
            config["policies"] = policies
            self._write_config(config)
        return dict(state)

    def set_resilience_budget_state(self, state: dict) -> dict:
        config = self._read_config()
        policies = config.get("policies")
        if not isinstance(policies, dict):
            policies = {}
        policies["resilience_budget_state"] = dict(state)
        config["policies"] = policies
        self._write_config(config)
        return dict(state)

    def get_resilience_interceptors_state(self) -> dict:
        config = self._read_config()
        policies = config.get("policies")
        if not isinstance(policies, dict):
            policies = {}
        state = policies.get("resilience_interceptors_state")
        if not isinstance(state, dict):
            state = self.default_resilience_interceptors_state()
            policies["resilience_interceptors_state"] = state
            config["policies"] = policies
            self._write_config(config)
        return dict(state)

    def set_resilience_interceptors_state(self, state: dict) -> dict:
        config = self._read_config()
        policies = config.get("policies")
        if not isinstance(policies, dict):
            policies = {}
        policies["resilience_interceptors_state"] = dict(state)
        config["policies"] = policies
        self._write_config(config)
        return dict(state)

    def get_dashboard_state(self) -> dict:
        config = self._read_config()
        policies = config.get("policies")
        if not isinstance(policies, dict):
            policies = {}
        state = policies.get("dashboard_state")
        if not isinstance(state, dict):
            state = self.default_dashboard_state()
            policies["dashboard_state"] = state
            config["policies"] = policies
            self._write_config(config)
        return dict(state)

    def set_dashboard_state(self, state: dict) -> dict:
        config = self._read_config()
        policies = config.get("policies")
        if not isinstance(policies, dict):
            policies = {}
        policies["dashboard_state"] = dict(state)
        config["policies"] = policies
        self._write_config(config)
        return dict(state)

    def get_settings_state(self) -> dict:
        config = self._read_config()
        policies = config.get("policies")
        if not isinstance(policies, dict):
            policies = {}
        state = policies.get("settings_state")
        if not isinstance(state, dict):
            state = self.default_settings_state()
            policies["settings_state"] = state
            config["policies"] = policies
            self._write_config(config)
        return dict(state)

    def set_settings_state(self, state: dict) -> dict:
        config = self._read_config()
        policies = config.get("policies")
        if not isinstance(policies, dict):
            policies = {}
        policies["settings_state"] = dict(state)
        config["policies"] = policies
        self._write_config(config)
        return dict(state)
