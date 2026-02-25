import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ui.usage_filters import compute_filtered_usage_rows, parse_usage_timestamp_utc
from src.ui.usage_dropdowns import build_usage_bridge_option_specs


@pytest.mark.parametrize(
    "value,expected_iso",
    [
        ("2026-02-19T00:00:00Z", "2026-02-19T00:00:00+00:00"),
        ("2026-02-19T00:00:00+00:00", "2026-02-19T00:00:00+00:00"),
        ("2026-02-19T00:00:00", "2026-02-19T00:00:00+00:00"),
    ],
)
def test_g4_parse_usage_timestamp_utc(value: str, expected_iso: str) -> None:
    dt = parse_usage_timestamp_utc(value)
    assert dt is not None
    assert dt.tzinfo is not None
    assert dt.astimezone(timezone.utc).isoformat() == expected_iso


def test_g4_date_range_filter_last_1h_is_deterministic() -> None:
    now = datetime(2026, 2, 19, 1, 0, 0, tzinfo=timezone.utc)
    master_rows = [
        {"timestamp": "2026-02-18T23:59:59Z", "agent_name": "A"},
        {"timestamp": "2026-02-19T00:10:00+00:00", "agent_name": "A"},
        {"timestamp": "2026-02-19T00:30:00", "agent_name": "B"},
    ]

    filtered = compute_filtered_usage_rows(
        master_rows,
        selected_agent="All Bridges",
        date_filter="Last 1h",
        include_test_traffic=True,
        now_utc=now,
    )

    assert [r["agent_name"] for r in filtered] == ["A", "B"]


def test_g4_bridge_filter_is_deterministic() -> None:
    now = datetime(2026, 2, 19, 1, 0, 0, tzinfo=timezone.utc)
    master_rows = [
        {"timestamp": "2026-02-19T00:10:00Z", "agent_name": "A"},
        {"timestamp": "2026-02-19T00:20:00Z", "agent_name": "B"},
        {"timestamp": "2026-02-19T00:30:00Z", "agent_name": "B"},
    ]

    filtered = compute_filtered_usage_rows(
        master_rows,
        selected_agent="B",
        date_filter="All time",
        include_test_traffic=True,
        now_utc=now,
    )

    assert [r["agent_name"] for r in filtered] == ["B", "B"]


def test_g4_bridge_filter_exact_match_is_based_on_selected_value() -> None:
    now = datetime(2026, 2, 19, 1, 0, 0, tzinfo=timezone.utc)
    master_rows = [
        {"timestamp": "2026-02-19T00:10:00Z", "agent_name": "A"},
        {"timestamp": "2026-02-19T00:11:00Z", "agent_name": "_test_A"},
        {"timestamp": "2026-02-19T00:12:00Z", "agent_name": "A2"},
        {"timestamp": "2026-02-19T00:13:00Z", "agent_name": "_test_A2"},
    ]

    filtered_a = compute_filtered_usage_rows(
        master_rows,
        selected_agent="A",
        date_filter="All time",
        include_test_traffic=True,
        now_utc=now,
        agent_name_prefix="_test_",
    )
    filtered_test_a = compute_filtered_usage_rows(
        master_rows,
        selected_agent="_test_A",
        date_filter="All time",
        include_test_traffic=True,
        now_utc=now,
        agent_name_prefix="_test_",
    )

    assert [r["agent_name"] for r in filtered_a] == ["A"]
    assert [r["agent_name"] for r in filtered_test_a] == ["_test_A"]


def test_g4_toggle_reversibility_and_master_invariant() -> None:
    now = datetime(2026, 2, 19, 1, 0, 0, tzinfo=timezone.utc)
    master_rows = [
        {"timestamp": "2026-02-19T00:10:00Z", "agent_name": "prod"},
        {"timestamp": "2026-02-19T00:20:00Z", "agent_name": "_test_x"},
    ]
    master_snapshot = list(master_rows)

    off_rows_1 = compute_filtered_usage_rows(
        master_rows,
        selected_agent="All Bridges",
        date_filter="All time",
        include_test_traffic=False,
        now_utc=now,
        agent_name_prefix="_test_",
    )
    on_rows = compute_filtered_usage_rows(
        master_rows,
        selected_agent="All Bridges",
        date_filter="All time",
        include_test_traffic=True,
        now_utc=now,
        agent_name_prefix="_test_",
    )
    off_rows_2 = compute_filtered_usage_rows(
        master_rows,
        selected_agent="All Bridges",
        date_filter="All time",
        include_test_traffic=False,
        now_utc=now,
        agent_name_prefix="_test_",
    )

    assert [r["agent_name"] for r in off_rows_1] == ["prod"]
    assert [r["agent_name"] for r in on_rows] == ["prod", "_test_x"]
    assert [r["agent_name"] for r in off_rows_2] == ["prod"]
    assert master_rows == master_snapshot


def test_g4_selecting_test_bridge_requires_include_toggle() -> None:
    now = datetime(2026, 2, 19, 1, 0, 0, tzinfo=timezone.utc)
    master_rows = [
        {"timestamp": "2026-02-19T00:10:00Z", "agent_name": "_test_A"},
        {"timestamp": "2026-02-19T00:11:00Z", "agent_name": "A"},
    ]

    off_rows = compute_filtered_usage_rows(
        master_rows,
        selected_agent="_test_A",
        date_filter="All time",
        include_test_traffic=False,
        now_utc=now,
        agent_name_prefix="_test_",
    )
    on_rows = compute_filtered_usage_rows(
        master_rows,
        selected_agent="_test_A",
        date_filter="All time",
        include_test_traffic=True,
        now_utc=now,
        agent_name_prefix="_test_",
    )

    assert [r["agent_name"] for r in off_rows] == []
    assert [r["agent_name"] for r in on_rows] == ["_test_A"]


def test_g4d_bridge_options_preserve_selected_key() -> None:
    specs, selected = build_usage_bridge_option_specs(
        config_agents=[{"name": "A"}],
        usage_rows=[{"agent_name": "A"}],
        selected_key="_test_A",
        test_prefix="_test_",
    )

    keys = [k for k, _ in specs]
    assert selected == "_test_A"
    assert "_test_A" in keys
    assert ("_test_A", "A (test)") in specs
