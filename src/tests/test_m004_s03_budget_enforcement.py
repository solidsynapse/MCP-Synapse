from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.mcp_server.manager import BudgetEnforcementError, ServerManager


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class _FakeBudgetConfig:
    def __init__(self, *, enforcement_mode: str = "monitor") -> None:
        self._connection = {
            "id": "conn_test",
            "connection_name": "Budget Test",
            "provider_id": "openai",
            "model_id": "gpt-4o-mini",
            "options": {},
        }
        self._budget_state = {
            "selected_scope_id": "conn_test",
            "limit_value": "10",
            "unit": "usd_per_day",
            "enforcement_mode": enforcement_mode,
            "applied_guards": [
                {
                    "id": "guard_1",
                    "scope_id": "conn_test",
                    "limit_value": "10",
                    "unit": "usd_per_day",
                    "applied_at": "2026-03-18T00:00:00Z",
                }
            ],
        }

    @staticmethod
    def default_resilience_budget_state() -> dict:
        return {
            "selected_scope_id": "all",
            "limit_value": "",
            "unit": "usd_per_day",
            "enforcement_mode": "monitor",
            "applied_guards": [],
        }

    def get_resilience_budget_state(self) -> dict:
        return dict(self._budget_state)

    def set_resilience_budget_state(self, state: dict) -> dict:
        self._budget_state = dict(state)
        return dict(self._budget_state)

    def get_connection(self, connection_id: str):
        if str(connection_id) == "conn_test":
            return dict(self._connection)
        return None

    def list_connections(self) -> list[dict]:
        return [dict(self._connection)]

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
        return self.default_optimizations_state()

    @staticmethod
    def default_persona_state() -> dict:
        return {"selected_persona_id": "default", "selected_target_id": "all", "applied_rows": [], "presets": []}

    def get_policies_persona_state(self) -> dict:
        return self.default_persona_state()


class _FakeUsageDb:
    def __init__(self, consumed_cost: float) -> None:
        self.consumed_cost = float(consumed_cost)
        self.logged_rows: list[dict] = []

    def list_usage(self, limit: int = 200, most_recent: bool = False) -> list[dict]:
        return [
            {
                "timestamp": _utc_now(),
                "agent_id": "conn_test",
                "agent_name": "Budget Test",
                "tokens_input": 10,
                "tokens_output": 10,
                "cost_usd": self.consumed_cost,
                "status": "success",
                "error_type": None,
                "request_id": "req-prev",
                "provider": "openai",
                "model_id": "gpt-4o-mini",
            }
        ]

    def log_usage(self, **kwargs) -> None:
        self.logged_rows.append(dict(kwargs))


def test_budget_state_rejects_invalid_enforcement_mode():
    manager = ServerManager(config=_FakeBudgetConfig(), creds=object(), usage_db=_FakeUsageDb(consumed_cost=0))
    payload = {
        "state": {
            "selected_scope_id": "all",
            "limit_value": "5",
            "unit": "usd_per_day",
            "enforcement_mode": "shadow",
            "applied_guards": [],
        }
    }

    result = manager.set_resilience_budget_state(payload)
    assert result["ok"] is False
    assert result["error_code"] == "invalid_resilience_budget_state"
    assert "enforcement_mode must be one of: monitor, block, throttle" in list(result.get("errors") or [])


def test_budget_block_mode_rejects_request_and_logs_error(monkeypatch):
    usage = _FakeUsageDb(consumed_cost=12.0)
    manager = ServerManager(
        config=_FakeBudgetConfig(enforcement_mode="block"),
        creds=object(),
        usage_db=usage,
    )
    monkeypatch.setattr(manager, "_resolve_persona_text_for_connection", lambda _: "")

    def _unexpected_execute(_self, _context, _prompt):
        raise AssertionError("provider_execute_should_not_run_when_budget_is_blocked")

    monkeypatch.setattr("src.mcp_server.manager.ProviderAdapterV1.execute", _unexpected_execute)

    with pytest.raises(BudgetEnforcementError) as excinfo:
        manager.execute_connection_request_v1("conn_test", "hello")

    assert "Budget enforcement block active" in str(excinfo.value)
    assert len(usage.logged_rows) == 1
    assert usage.logged_rows[0]["status"] == "error"
    assert usage.logged_rows[0]["error_type"] == "budget_guard_blocked"


def test_budget_throttle_mode_delays_then_executes(monkeypatch):
    usage = _FakeUsageDb(consumed_cost=12.0)
    manager = ServerManager(
        config=_FakeBudgetConfig(enforcement_mode="throttle"),
        creds=object(),
        usage_db=usage,
    )
    monkeypatch.setattr(manager, "_resolve_persona_text_for_connection", lambda _: "")

    sleep_calls: list[float] = []

    def _fake_sleep(seconds: float) -> None:
        sleep_calls.append(float(seconds))

    def _fake_execute(_self, _context, _prompt):
        return {
            "text": "ok",
            "tokens_input": 1,
            "tokens_output": 1,
            "cost_usd": 0.1,
            "latency_ms": 9,
            "status": "success",
            "error_type": None,
            "request_id": "req-live",
            "provider": "openai",
            "model_id": "gpt-4o-mini",
        }

    monkeypatch.setattr("src.mcp_server.manager.time.sleep", _fake_sleep)
    monkeypatch.setattr("src.mcp_server.manager.ProviderAdapterV1.execute", _fake_execute)

    result = manager.execute_connection_request_v1("conn_test", "hello")

    assert sleep_calls == [float(manager._BUDGET_THROTTLE_DELAY_SECONDS)]
    assert result["budget_enforcement_mode"] == "throttle"
    assert result["budget_enforcement_triggered"] is True
    assert result["budget_enforcement_delay_ms"] == int(manager._BUDGET_THROTTLE_DELAY_SECONDS * 1000)
    assert len(usage.logged_rows) == 1
    assert usage.logged_rows[0]["status"] == "success"
