from src.mcp_server.manager import ServerManager


class _FakeBudgetConfig:
    def __init__(self) -> None:
        self._state = self.default_resilience_budget_state()

    @staticmethod
    def default_resilience_budget_state() -> dict:
        return {
            "selected_scope_id": "all",
            "limit_value": "",
            "unit": "usd_per_day",
            "applied_guards": [],
        }

    def get_resilience_budget_state(self) -> dict:
        return dict(self._state)

    def set_resilience_budget_state(self, state: dict) -> dict:
        self._state = dict(state)
        return dict(self._state)


def _make_manager() -> ServerManager:
    return ServerManager(config=_FakeBudgetConfig(), creds=object(), usage_db=object())


def test_budget_set_rejects_duplicate_scope_unit_guard():
    manager = _make_manager()
    payload = {
        "state": {
            "selected_scope_id": "all",
            "limit_value": "5",
            "unit": "usd_per_day",
            "applied_guards": [
                {"id": "g1", "scope_id": "bridge_alpha", "limit_value": "10", "unit": "usd_per_day", "applied_at": "2026-01-01T00:00:00Z"},
                {"id": "g2", "scope_id": "bridge_alpha", "limit_value": "20", "unit": "usd_per_day", "applied_at": "2026-01-01T00:00:01Z"},
            ],
        }
    }

    result = manager.set_resilience_budget_state(payload)
    assert result["ok"] is False
    assert result["error_code"] == "invalid_resilience_budget_state"
    assert "duplicate guard for same scope/unit is not allowed" in list(result.get("errors") or [])


def test_budget_set_allows_same_scope_with_different_units():
    manager = _make_manager()
    payload = {
        "state": {
            "selected_scope_id": "all",
            "limit_value": "5",
            "unit": "usd_per_day",
            "applied_guards": [
                {"id": "g1", "scope_id": "bridge_alpha", "limit_value": "10", "unit": "usd_per_day", "applied_at": "2026-01-01T00:00:00Z"},
                {"id": "g2", "scope_id": "bridge_alpha", "limit_value": "50", "unit": "tokens_per_day", "applied_at": "2026-01-01T00:00:01Z"},
            ],
        }
    }

    result = manager.set_resilience_budget_state(payload)
    assert result["ok"] is True
    assert len(result["state"]["applied_guards"]) == 2
