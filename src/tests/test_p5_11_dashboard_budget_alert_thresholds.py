from __future__ import annotations

from datetime import datetime, timezone

from src.mcp_server.manager import ServerManager


class _FakeConfig:
    def __init__(self, connections: list[dict], budget_state: dict) -> None:
        self._connections = [dict(item) for item in connections]
        self._budget_state = dict(budget_state)

    @staticmethod
    def default_resilience_budget_state() -> dict:
        return {
            "selected_scope_id": "all",
            "limit_value": "",
            "unit": "usd_per_day",
            "applied_guards": [],
        }

    def list_connections(self) -> list[dict]:
        return [dict(item) for item in self._connections]

    def get_resilience_budget_state(self) -> dict:
        return dict(self._budget_state)

    def get_dashboard_state(self) -> dict:
        # Keep test fixture aligned with manager dashboard state reads and
        # reduce sample thresholds so budget alerts can be asserted with small fixtures.
        return {
            "health_alerts_config": {
                "window_rows": 500,
                "min_samples_total": 1,
                "min_samples_success": 1,
                "success_rate_warning_pct": 95,
                "success_rate_critical_pct": 85,
                "latency_warning_ms": 8000,
                "latency_critical_ms": 15000,
                "budget_warning_pct": 75,
                "budget_critical_pct": 90,
            }
        }


class _FakeUsageDb:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = [dict(item) for item in rows]

    def get_recent_usage(self, limit: int = 500) -> list[dict]:
        return [dict(item) for item in self._rows[: int(limit)]]


def _iso_now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def test_dashboard_quick_alerts_include_budget_warning_and_danger() -> None:
    now = _iso_now_utc()
    rows = [
        {
            "timestamp": now,
            "agent_id": "conn_test0x",
            "agent_name": "TEST0X",
            "tokens_input": 1200,
            "tokens_output": 800,
            "cost_usd": 96.0,
            "latency_ms": 420,
            "status": "success",
            "provider": "vertex",
            "request_id": "r-1",
        },
        {
            "timestamp": now,
            "agent_id": "conn_other",
            "agent_name": "OTHER",
            "tokens_input": 2200,
            "tokens_output": 3000,
            "cost_usd": 4.0,
            "latency_ms": 350,
            "status": "success",
            "provider": "vertex",
            "request_id": "r-2",
        },
    ]
    config = _FakeConfig(
        connections=[
            {"id": "conn_test0x", "connection_name": "TEST0X", "status": "running"},
            {"id": "conn_other", "connection_name": "OTHER", "status": "stopped"},
        ],
        budget_state={
            "selected_scope_id": "all",
            "limit_value": "",
            "unit": "usd_per_day",
            "applied_guards": [
                {
                    "id": "g-1",
                    "scope_id": "conn_test0x",
                    "limit_value": "100",
                    "unit": "usd_per_day",
                    "applied_at": now,
                },
                {
                    "id": "g-2",
                    "scope_id": "all",
                    "limit_value": "8000",
                    "unit": "tokens_per_day",
                    "applied_at": now,
                },
            ],
        },
    )
    manager = ServerManager(config=config, creds=object(), usage_db=_FakeUsageDb(rows))

    state = manager.get_dashboard_state().get("result")
    assert isinstance(state, dict)
    quick_alerts = state.get("quick_alerts")
    assert isinstance(quick_alerts, list)

    assert any(
        str(item.get("level")) == "critical"
        and "Budget threshold critical" in str(item.get("text"))
        and "TEST0X" in str(item.get("text"))
        and "USD/day" in str(item.get("detail"))
        for item in quick_alerts
        if isinstance(item, dict)
    )
    assert any(
        str(item.get("level")) == "critical"
        and "Budget threshold critical" in str(item.get("text"))
        and "All Bridges" in str(item.get("text"))
        and "tokens/day" in str(item.get("detail"))
        for item in quick_alerts
        if isinstance(item, dict)
    )


def test_dashboard_quick_alerts_keep_no_active_when_budget_not_near_threshold() -> None:
    now = _iso_now_utc()
    rows = [
        {
            "timestamp": now,
            "agent_id": "conn_test0x",
            "agent_name": "TEST0X",
            "tokens_input": 100,
            "tokens_output": 200,
            "cost_usd": 5.0,
            "latency_ms": 210,
            "status": "success",
            "provider": "vertex",
            "request_id": "r-3",
        }
    ]
    config = _FakeConfig(
        connections=[{"id": "conn_test0x", "connection_name": "TEST0X", "status": "running"}],
        budget_state={
            "selected_scope_id": "all",
            "limit_value": "",
            "unit": "usd_per_day",
            "applied_guards": [
                {
                    "id": "g-3",
                    "scope_id": "conn_test0x",
                    "limit_value": "20",
                    "unit": "usd_per_day",
                    "applied_at": now,
                },
                {
                    "id": "g-4",
                    "scope_id": "all",
                    "limit_value": "5000",
                    "unit": "tokens_per_day",
                    "applied_at": now,
                },
            ],
        },
    )
    manager = ServerManager(config=config, creds=object(), usage_db=_FakeUsageDb(rows))

    state = manager.get_dashboard_state().get("result")
    assert isinstance(state, dict)
    quick_alerts = state.get("quick_alerts")
    assert isinstance(quick_alerts, list)
    assert len(quick_alerts) == 1
    first = quick_alerts[0]
    assert isinstance(first, dict)
    assert first.get("level") == "info"
    assert first.get("text") == "No active health alerts."

