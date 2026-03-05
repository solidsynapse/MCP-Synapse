from __future__ import annotations

from src.mcp_server.manager import ServerManager


class _FakeConfig:
    def __init__(self, *, interceptors_enabled: bool) -> None:
        self._connection = {
            "id": "conn_test",
            "connection_name": "TEST0X",
            "provider_id": "openai",
            "model_id": "gpt-4o-mini",
            "options": {},
        }
        self._interceptors_enabled = bool(interceptors_enabled)

    def get_connection(self, connection_id: str):
        if str(connection_id) == "conn_test":
            return dict(self._connection)
        return None

    @staticmethod
    def default_resilience_interceptors_state() -> dict:
        return {
            "enabled_by_id": {"json_syntax_repair": False},
            "settings_by_id": {
                "json_syntax_repair": {
                    "mode": "safe",
                    "max_attempts": 2,
                    "strict_json": True,
                    "note": "test",
                }
            },
        }

    def get_resilience_interceptors_state(self) -> dict:
        state = self.default_resilience_interceptors_state()
        state["enabled_by_id"]["json_syntax_repair"] = self._interceptors_enabled
        return state

    @staticmethod
    def default_optimizations_state() -> dict:
        return {"context_caching_enabled": False, "request_dedup_enabled": False}

    def get_policies_optimizations_state(self) -> dict:
        return self.default_optimizations_state()

    @staticmethod
    def default_persona_state() -> dict:
        return {"selected_persona_id": "default", "selected_target_id": "all", "applied_rows": [], "presets": []}

    def get_policies_persona_state(self) -> dict:
        return self.default_persona_state()

    def list_connections(self) -> list[dict]:
        return [dict(self._connection)]


class _FakeUsageDb:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def log_usage(self, **kwargs) -> None:
        self.rows.append(dict(kwargs))


def test_interceptor_repairs_malformed_json_when_enabled(monkeypatch) -> None:
    usage = _FakeUsageDb()
    manager = ServerManager(config=_FakeConfig(interceptors_enabled=True), creds=object(), usage_db=usage)
    monkeypatch.setattr(manager, "_resolve_persona_text_for_connection", lambda _: "")

    def _fake_execute(_self, _context, _prompt):
        return {
            "text": "{\"ok\": true,}",
            "tokens_input": 3,
            "tokens_output": 4,
            "cost_usd": 0.0,
            "latency_ms": 9,
            "status": "success",
            "error_type": None,
            "request_id": "req-1",
            "provider": "openai",
            "model_id": "gpt-4o-mini",
        }

    monkeypatch.setattr("src.mcp_server.manager.ProviderAdapterV1.execute", _fake_execute)

    result = manager.execute_connection_request_v1("conn_test", "Return strict json")
    assert str(result.get("text")) == "{\"ok\": true}"
    trace = result.get("interceptor_json_syntax_repair")
    assert isinstance(trace, dict)
    assert trace.get("enabled") is True
    assert trace.get("applied") is True
    assert len(usage.rows) == 1


def test_interceptor_does_not_modify_text_when_disabled(monkeypatch) -> None:
    usage = _FakeUsageDb()
    manager = ServerManager(config=_FakeConfig(interceptors_enabled=False), creds=object(), usage_db=usage)
    monkeypatch.setattr(manager, "_resolve_persona_text_for_connection", lambda _: "")

    def _fake_execute(_self, _context, _prompt):
        return {
            "text": "{\"ok\": true,}",
            "tokens_input": 3,
            "tokens_output": 4,
            "cost_usd": 0.0,
            "latency_ms": 9,
            "status": "success",
            "error_type": None,
            "request_id": "req-2",
            "provider": "openai",
            "model_id": "gpt-4o-mini",
        }

    monkeypatch.setattr("src.mcp_server.manager.ProviderAdapterV1.execute", _fake_execute)

    result = manager.execute_connection_request_v1("conn_test", "Return strict json")
    assert str(result.get("text")) == "{\"ok\": true,}"
    trace = result.get("interceptor_json_syntax_repair")
    assert isinstance(trace, dict)
    assert trace.get("enabled") is False
    assert trace.get("applied") is False
    assert len(usage.rows) == 1
