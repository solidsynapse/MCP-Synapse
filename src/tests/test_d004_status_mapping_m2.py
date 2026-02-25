import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.usage_status import normalize_usage_status
from src.ui.usage_kpis import compute_usage_kpis


@pytest.mark.parametrize(
    "status,error_type,expected_status,expected_error_type",
    [
        ("success", None, "success", None),
        ("SUCCESS", None, "success", None),
        ("ok", None, "success", None),
        ("error", None, "error", "unknown_error"),
        ("FAILED", None, "error", "unknown_error"),
        (None, None, "unknown", None),
        ("", None, "unknown", None),
        ("canceled", None, "cancelled", "cancelled"),
        ("cancelled", None, "cancelled", "cancelled"),
        (None, "cancelled", "cancelled", "cancelled"),
        ("error", "CancelledError", "cancelled", "cancelled"),
    ],
)
def test_d004_normalize_usage_status(status, error_type, expected_status, expected_error_type) -> None:
    actual_status, actual_error_type = normalize_usage_status(status, error_type)
    assert actual_status == expected_status
    assert actual_error_type == expected_error_type


def test_d004_kpi_counts_use_canonical_statuses_only() -> None:
    rows = [
        {"status": "ok", "tokens_input": 1, "tokens_output": 2, "cost_usd": 0.1},
        {"status": "SUCCESS", "tokens_input": 3, "tokens_output": 4, "cost_usd": 0.2},
        {"status": None, "tokens_input": 5, "tokens_output": 6, "cost_usd": 0.3},
        {"status": "error", "tokens_input": 7, "tokens_output": 8, "cost_usd": 0.4},
        {"status": "canceled", "tokens_input": 9, "tokens_output": 10, "cost_usd": 0.5},
    ]
    kpis = compute_usage_kpis(rows)

    assert kpis["total_requests"] == 5
    assert kpis["total_tokens"] == (1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10)
    assert float(kpis["total_cost"]) == pytest.approx(1.5)
    assert kpis["total_success"] == 2
