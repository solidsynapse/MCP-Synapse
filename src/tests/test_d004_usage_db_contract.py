import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.usage_db import UsageDatabase


def test_d004_end_is_exclusive_for_list_usage_and_list_agent_names(tmp_path: Path) -> None:
    db_path = tmp_path / "usage.db"
    usage_db = UsageDatabase(db_path=db_path)

    start_dt = datetime(2026, 2, 19, 0, 0, 0, tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(hours=1)
    mid_dt = start_dt + timedelta(minutes=30)

    start_ts = start_dt.isoformat()
    end_ts = end_dt.isoformat()
    mid_ts = mid_dt.isoformat()

    usage_db.log_usage(
        agent_id="a1",
        agent_name="Included",
        tokens_input=1,
        tokens_output=1,
        cost_usd=0.01,
        timestamp=start_ts,
        request_id="r-start",
        status="success",
    )
    usage_db.log_usage(
        agent_id="a1",
        agent_name="Included",
        tokens_input=2,
        tokens_output=2,
        cost_usd=0.02,
        timestamp=mid_ts,
        request_id="r-mid",
        status="success",
    )
    usage_db.log_usage(
        agent_id="a2",
        agent_name="EndOnly",
        tokens_input=3,
        tokens_output=3,
        cost_usd=0.03,
        timestamp=end_ts,
        request_id="r-end",
        status="success",
    )

    rows = usage_db.list_usage(start_timestamp=start_ts, end_timestamp=end_ts, limit=50)
    timestamps = [r["timestamp"] for r in rows]
    assert start_ts in timestamps
    assert mid_ts in timestamps
    assert end_ts not in timestamps

    agent_names = usage_db.list_agent_names(start_timestamp=start_ts, end_timestamp=end_ts)
    assert "Included" in agent_names
    assert "EndOnly" not in agent_names


def test_d004_list_usage_stable_order_by_timestamp_then_request_id(tmp_path: Path) -> None:
    db_path = tmp_path / "usage.db"
    usage_db = UsageDatabase(db_path=db_path)

    t0 = datetime(2026, 2, 19, 0, 0, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(hours=1)
    t2 = t0 + timedelta(hours=2)

    ts0 = t0.isoformat()
    ts1 = t1.isoformat()
    end_ts = t2.isoformat()

    usage_db.log_usage(
        agent_id="a1",
        agent_name="A",
        tokens_input=10,
        tokens_output=0,
        cost_usd=0.01,
        timestamp=ts1,
        request_id="b",
        status="success",
    )
    usage_db.log_usage(
        agent_id="a1",
        agent_name="A",
        tokens_input=20,
        tokens_output=0,
        cost_usd=0.02,
        timestamp=ts0,
        request_id="b",
        status="success",
    )
    usage_db.log_usage(
        agent_id="a1",
        agent_name="A",
        tokens_input=30,
        tokens_output=0,
        cost_usd=0.03,
        timestamp=ts0,
        request_id="a",
        status="success",
    )
    usage_db.log_usage(
        agent_id="a1",
        agent_name="A",
        tokens_input=111,
        tokens_output=0,
        cost_usd=0.04,
        timestamp=ts0,
        request_id=None,
        status="success",
    )
    usage_db.log_usage(
        agent_id="a1",
        agent_name="A",
        tokens_input=222,
        tokens_output=0,
        cost_usd=0.05,
        timestamp=ts0,
        request_id=None,
        status="success",
    )

    rows = usage_db.list_usage(start_timestamp=ts0, end_timestamp=end_ts, limit=50)
    key_rows = [(r["timestamp"], r.get("request_id"), int(r["tokens_input"])) for r in rows]

    assert key_rows == [
        (ts0, None, 111),
        (ts0, None, 222),
        (ts0, "a", 30),
        (ts0, "b", 20),
        (ts1, "b", 10),
    ]

