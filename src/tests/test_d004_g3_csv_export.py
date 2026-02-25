import sys
import csv
import io
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ui.usage_export import EXPORT_USAGE_COLUMNS, usage_rows_to_csv_text


def test_d004_g3_csv_header_and_column_order() -> None:
    csv_text = usage_rows_to_csv_text([])
    header_line = csv_text.splitlines()[0]
    assert header_line == ",".join(EXPORT_USAGE_COLUMNS)


def test_d004_g3_csv_sorting_and_serialization() -> None:
    rows = [
        {
            "id": 3,
            "timestamp": "2026-02-19T00:00:00+00:00",
            "agent_name": "Z",
            "provider": "p",
            "model_id": "m",
            "request_id": "b",
            "status": "success",
            "error_type": None,
            "latency_ms": None,
            "tokens_input": 1,
            "tokens_output": 2,
            "cost_usd": 1.5,
        },
        {
            "id": 2,
            "timestamp": "2026-02-19T00:00:00+00:00",
            "agent_name": "Y",
            "provider": "p",
            "model_id": "m",
            "request_id": "a",
            "status": "error",
            "error_type": "provider_error",
            "latency_ms": 10,
            "tokens_input": 3,
            "tokens_output": 4,
            "cost_usd": 0.123,
        },
        {
            "id": 1,
            "timestamp": "2026-02-18T23:00:00Z",
            "agent_name": "X",
            "provider": None,
            "model_id": None,
            "request_id": None,
            "status": None,
            "error_type": None,
            "latency_ms": 0,
            "tokens_input": None,
            "tokens_output": None,
            "cost_usd": None,
        },
        {
            "id": 4,
            "timestamp": "2026-02-19T00:00:00",
            "agent_name": "W",
            "provider": "p",
            "model_id": "m",
            "request_id": None,
            "status": "success",
            "error_type": None,
            "latency_ms": 5,
            "tokens_input": 9,
            "tokens_output": 8,
            "cost_usd": 2.0,
        },
    ]

    csv_text = usage_rows_to_csv_text(rows)
    parsed = list(csv.reader(io.StringIO(csv_text)))

    assert parsed[0] == EXPORT_USAGE_COLUMNS
    assert parsed[1] == [
        "",
        "",
        "",
        "",
        "",
        "0",
        "",
        "",
        "",
        "2026-02-18T23:00:00+00:00",
        "X",
    ]
    assert parsed[2] == [
        "p",
        "m",
        "",
        "success",
        "",
        "5",
        "9",
        "8",
        "2.0",
        "2026-02-19T00:00:00+00:00",
        "W",
    ]
    assert parsed[3] == [
        "p",
        "m",
        "a",
        "error",
        "provider_error",
        "10",
        "3",
        "4",
        "0.123",
        "2026-02-19T00:00:00+00:00",
        "Y",
    ]
    assert parsed[4] == [
        "p",
        "m",
        "b",
        "success",
        "",
        "",
        "1",
        "2",
        "1.5",
        "2026-02-19T00:00:00+00:00",
        "Z",
    ]
