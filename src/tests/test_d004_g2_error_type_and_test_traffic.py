import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.usage_db import UsageDatabase
from src.data.usage_status import normalize_usage_error_type, normalize_usage_status
from src.ui.usage_filters import apply_test_traffic_filter


@pytest.mark.parametrize(
    "raw_error,expected",
    [
        ("APIError", "provider_error"),
        ("AzureOpenAIHTTPError", "provider_error"),
        ("CredentialError", "auth_error"),
        ("UnauthorizedError", "auth_error"),
        ("QuotaError", "rate_limit"),
        ("RateLimitError", "rate_limit"),
        ("TimeoutError", "timeout"),
        ("ConnectionError", "network_error"),
        ("ValueError", "validation_error"),
        ("cancelled", "cancelled"),
        ("unknown_error", "unknown_error"),
    ],
)
def test_d004_error_type_normalization(raw_error: str, expected: str) -> None:
    actual = normalize_usage_error_type(raw_error, status="error")
    assert actual == expected


def test_d004_cancelled_maps_status_and_error_type() -> None:
    status, error_type = normalize_usage_status("error", "CancelledError")
    assert status == "cancelled"
    assert error_type == "cancelled"


def test_d004_usage_db_log_usage_stores_canonical_error_type(tmp_path: Path) -> None:
    db_path = tmp_path / "usage.db"
    usage_db = UsageDatabase(db_path=db_path)
    ts = datetime(2026, 2, 19, 0, 0, 0, tzinfo=timezone.utc).isoformat()

    usage_db.log_usage(
        agent_id="a1",
        agent_name="A",
        tokens_input=1,
        tokens_output=1,
        cost_usd=0.01,
        timestamp=ts,
        status="error",
        error_type="APIError",
        request_id="r1",
    )

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT status, error_type FROM usage ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert row is not None
    assert row[0] == "error"
    assert row[1] == "provider_error"


def test_d004_usage_db_read_normalizes_legacy_error_type(tmp_path: Path) -> None:
    db_path = tmp_path / "usage.db"
    usage_db = UsageDatabase(db_path=db_path)
    ts = datetime(2026, 2, 19, 0, 0, 0, tzinfo=timezone.utc).isoformat()

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO usage(
                timestamp, agent_id, agent_name, tokens_input, tokens_output, cost_usd,
                latency_ms, status, error_type, request_id, provider, model_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ts,
                "a1",
                "A",
                1,
                1,
                0.01,
                None,
                "error",
                "APIError",
                "r1",
                "vertex",
                "m",
            ),
        )
        conn.commit()

    rows = usage_db.list_usage(limit=10)
    assert rows
    assert rows[0]["status"] == "error"
    assert rows[0]["error_type"] == "provider_error"


def test_d004_test_traffic_exclusion_default() -> None:
    rows = [
        {"agent_name": "prod", "status": "success"},
        {"agent_name": "_test_agent", "status": "success"},
    ]
    filtered = apply_test_traffic_filter(rows, include_test_traffic=False, agent_name_prefix="_test_")
    assert [r["agent_name"] for r in filtered] == ["prod"]

    rows2 = [
        {"agent_name": "prod", "status": "success"},
        {"agent_name": "_test_x", "status": "success"},
    ]
    filtered2 = apply_test_traffic_filter(rows2, include_test_traffic=False, agent_name_prefix="_test_")
    assert [r["agent_name"] for r in filtered2] == ["prod"]

    rows3 = [
        {"agent_name": "prod", "status": "success"},
        {"agent_name": "prod2", "status": "success"},
    ]
    filtered3 = apply_test_traffic_filter(rows3, include_test_traffic=False, agent_name_prefix="_test_")
    assert [r["agent_name"] for r in filtered3] == ["prod", "prod2"]


def test_d004_test_traffic_included_when_toggled() -> None:
    rows = [
        {"agent_name": "prod", "status": "success"},
        {"agent_name": "_test_x", "status": "success"},
    ]
    filtered = apply_test_traffic_filter(rows, include_test_traffic=True, agent_name_prefix="_test_")
    assert [r["agent_name"] for r in filtered] == ["prod", "_test_x"]
