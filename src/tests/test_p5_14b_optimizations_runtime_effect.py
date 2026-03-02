from __future__ import annotations

from src.mcp_server.manager import ServerManager
from src.mcp_server.pipeline_v1 import ExecutionContextV1, ProviderAdapterV1


class _FakeConfig:
    def __init__(self, *, context_caching_enabled: bool, request_dedup_enabled: bool) -> None:
        self._connection = {
            "id": "conn_test",
            "connection_name": "TEST0X",
            "provider_id": "openai",
            "model_id": "gpt-4o-mini",
            "options": {},
        }
        self._context_caching_enabled = bool(context_caching_enabled)
        self._request_dedup_enabled = bool(request_dedup_enabled)

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
        return self.default_resilience_interceptors_state()

    @staticmethod
    def default_optimizations_state() -> dict:
        return {"context_caching_enabled": False, "request_dedup_enabled": False}

    def get_policies_optimizations_state(self) -> dict:
        return {
            "context_caching_enabled": self._context_caching_enabled,
            "request_dedup_enabled": self._request_dedup_enabled,
        }

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


def test_provider_adapter_skips_context_cache_when_disabled(monkeypatch) -> None:
    class _FakeClient:
        provider_id = "openai"
        model_id = "gpt-4o-mini"

        def generate_content(self, provider_prompt: str, stream: bool = False):
            assert provider_prompt == "persona::hello"
            return {"text": "ok", "tokens_input": 1, "tokens_output": 1, "cost_usd": 0.0}

    monkeypatch.setattr("src.mcp_server.pipeline_v1.ProviderFactory.create", lambda *_args, **_kwargs: _FakeClient())
    monkeypatch.setattr(
        "src.mcp_server.pipeline_v1.assemble_context_cached_request",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("context_cache_called_when_disabled")),
    )
    monkeypatch.setattr(
        "src.mcp_server.pipeline_v1.assemble_persona_lite_request",
        lambda _agent, _prompt: {"messages": [{"role": "user", "content": "hello"}], "provider_prompt": "persona::hello"},
    )

    context = ExecutionContextV1(
        agent={"id": "a1", "name": "A1", "persona": "P", "context_caching_enabled": False},
        project_id="p",
        location="us-central1",
        provider_id="openai",
        model_id="gpt-4o-mini",
        credentials_path="",
        price_per_1m_input=0.0,
        price_per_1m_output=0.0,
        streaming=False,
    )
    result = ProviderAdapterV1().execute(context, "hello")
    assert result.get("context_cache_enabled") is False
    assert result.get("context_cache_hit") is False


def test_manager_request_dedup_returns_cached_result(monkeypatch) -> None:
    usage = _FakeUsageDb()
    manager = ServerManager(
        config=_FakeConfig(context_caching_enabled=False, request_dedup_enabled=True),
        creds=object(),
        usage_db=usage,
    )
    monkeypatch.setattr(manager, "_resolve_persona_text_for_connection", lambda _: "")

    calls = {"count": 0}

    def _fake_execute(_self, _context, _prompt):
        calls["count"] += 1
        return {
            "text": "provider-response",
            "tokens_input": 12,
            "tokens_output": 5,
            "cost_usd": 0.42,
            "latency_ms": 101,
            "status": "success",
            "error_type": None,
            "request_id": "req-live-1",
            "provider": "openai",
            "model_id": "gpt-4o-mini",
        }

    monkeypatch.setattr("src.mcp_server.manager.ProviderAdapterV1.execute", _fake_execute)

    first = manager.execute_connection_request_v1("conn_test", "same prompt")
    second = manager.execute_connection_request_v1("conn_test", "same prompt")

    assert calls["count"] == 1
    assert first.get("request_dedup_enabled") is True
    assert first.get("request_dedup_hit") is False
    assert second.get("request_dedup_enabled") is True
    assert second.get("request_dedup_hit") is True
    assert str(second.get("text")) == "provider-response"
    assert float(second.get("cost_usd") or 0.0) == 0.0
    assert len(usage.rows) == 2
