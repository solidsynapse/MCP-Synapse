import copy

import src.mcp_server.manager as manager_module
from src.mcp_server.context_cache_p3_p3 import assemble_context_cached_request
from src.mcp_server.manager import ServerManager


class _FakeConfig:
    def __init__(self, persona_state: dict) -> None:
        self._persona_state = copy.deepcopy(persona_state)
        self._connection = {
            "id": "conn-1",
            "connection_name": "Conn One",
            "provider_id": "vertex",
            "model_id": "gemini-2.0-flash-001",
            "options": {
                "project_id": "test-project",
                "location": "us-central1",
            },
        }

    @staticmethod
    def default_persona_state() -> dict:
        return {
            "selected_persona_id": "default",
            "selected_target_id": "bridge_alpha",
            "applied_rows": [],
            "presets": [
                {"id": "preset_default", "name": "Default", "text": ""},
                {"id": "preset_analyst", "name": "Analyst", "text": ""},
                {"id": "preset_concise", "name": "Concise", "text": ""},
            ],
            "selected_preset_id": "preset_default",
        }

    def list_connections(self) -> list[dict]:
        return [copy.deepcopy(self._connection)]

    def get_connection(self, connection_id: str) -> dict | None:
        if str(connection_id or "").strip() == self._connection["id"]:
            return copy.deepcopy(self._connection)
        return None

    def get_policies_persona_state(self) -> dict:
        return copy.deepcopy(self._persona_state)

    def get_policies_optimizations_state(self) -> dict:
        return {
            "enabled": False,
            "context_caching_enabled": False,
            "request_dedup_enabled": False,
        }

    @staticmethod
    def default_optimizations_state() -> dict:
        return {
            "context_caching_enabled": False,
            "request_dedup_enabled": False,
        }

    def get_resilience_interceptors_state(self) -> dict:
        return {
            "enabled_by_id": {},
            "settings_by_id": {},
        }

    @staticmethod
    def default_resilience_interceptors_state() -> dict:
        return {
            "enabled_by_id": {},
            "settings_by_id": {},
        }


class _FakeUsageDb:
    def log_usage(self, **_kwargs) -> None:
        return None


def _run_request(monkeypatch, persona_state: dict, prompt: str = "hello") -> dict:
    captured: dict = {}

    class _FakeProviderAdapterV1:
        def execute(self, context, prompt_text: str) -> dict:
            assembled = assemble_context_cached_request(context.agent, prompt_text)
            captured["persona"] = context.agent.get("persona")
            captured["provider_prompt"] = assembled.get("provider_prompt")
            return {
                "text": "ok",
                "tokens_input": 1,
                "tokens_output": 1,
                "cost_usd": 0.0,
                "latency_ms": 1,
                "status": "success",
                "error_type": None,
                "request_id": "req-test",
                "provider": "vertex",
                "model_id": "gemini-2.0-flash-001",
            }

    monkeypatch.setattr(manager_module, "ProviderAdapterV1", _FakeProviderAdapterV1)

    manager = ServerManager(
        config=_FakeConfig(persona_state),
        creds=object(),
        usage_db=_FakeUsageDb(),
    )
    manager.execute_connection_request_v1("conn-1", prompt)
    return captured


def test_runtime_binding_prefers_applied_row_persona(monkeypatch):
    persona_text = "You are custom persona."
    persona_state = {
        "selected_persona_id": "default",
        "selected_target_id": "other-conn",
        "applied_rows": [
            {
                "id": "row-1",
                "persona_id": "preset_custom",
                "target_id": "conn-1",
                "applied_at": "2026-02-28T00:00:00Z",
            }
        ],
        "presets": [
            {"id": "preset_default", "name": "Default", "text": "fallback"},
            {"id": "preset_custom", "name": "Custom", "text": persona_text},
        ],
        "selected_preset_id": "preset_default",
    }

    captured = _run_request(monkeypatch=monkeypatch, persona_state=persona_state, prompt="Say hi")
    assert captured["persona"] == persona_text
    assert captured["provider_prompt"] == f"{persona_text}\n\nSay hi"


def test_runtime_binding_maps_legacy_selected_persona_to_preset_text(monkeypatch):
    default_text = "You are default persona text."
    persona_state = {
        "selected_persona_id": "default",
        "selected_target_id": "conn-1",
        "applied_rows": [],
        "presets": [
            {"id": "preset_default", "name": "Default", "text": default_text},
            {"id": "preset_custom", "name": "Custom", "text": "custom"},
        ],
        "selected_preset_id": "preset_default",
    }

    captured = _run_request(monkeypatch=monkeypatch, persona_state=persona_state, prompt="Ping")
    assert captured["persona"] == default_text
    assert captured["provider_prompt"] == f"{default_text}\n\nPing"


def test_runtime_binding_skips_persona_when_no_target_match(monkeypatch):
    persona_state = {
        "selected_persona_id": "default",
        "selected_target_id": "other-conn",
        "applied_rows": [],
        "presets": [
            {"id": "preset_default", "name": "Default", "text": "default-text"},
        ],
        "selected_preset_id": "preset_default",
    }

    captured = _run_request(monkeypatch=monkeypatch, persona_state=persona_state, prompt="Plain prompt")
    assert captured["persona"] is None
    assert captured["provider_prompt"] == "Plain prompt"
