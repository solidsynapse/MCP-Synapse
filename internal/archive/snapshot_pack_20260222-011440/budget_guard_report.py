from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.data.budget_guard_report import BudgetThresholds, compute_budget_guard_report, utc_day_window_iso8601
from src.data.usage_db import UsageDatabase


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Budget guard monitor-only report (no enforcement).")
    p.add_argument("--date", default="", help="UTC day as YYYY-MM-DD. Defaults to today's UTC date.")
    p.add_argument("--db-path", default="", help="Optional override for usage.db path.")
    p.add_argument("--max-cost-usd", default="", help="Optional max daily cost threshold (decimal).")
    p.add_argument("--max-tokens-in", default="", help="Optional max daily input tokens threshold (int).")
    p.add_argument("--max-tokens-out", default="", help="Optional max daily output tokens threshold (int).")
    return p.parse_args(argv)


def _today_utc_day() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _parse_decimal_opt(value: str) -> Decimal | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return Decimal(raw)
    except Exception:
        return None


def _parse_int_opt(value: str) -> int | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except Exception:
        return None


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    utc_day = str(args.date or "").strip() or _today_utc_day()
    try:
        date.fromisoformat(utc_day)
    except Exception:
        sys.stderr.write("Invalid --date (expected YYYY-MM-DD)\n")
        return 2

    thresholds = BudgetThresholds(
        max_cost_usd=_parse_decimal_opt(args.max_cost_usd),
        max_tokens_in=_parse_int_opt(args.max_tokens_in),
        max_tokens_out=_parse_int_opt(args.max_tokens_out),
    )

    start_ts, end_ts = utc_day_window_iso8601(utc_day)
    db_path = str(args.db_path or "").strip() or None
    usage_db = UsageDatabase(db_path=db_path)
    rows = usage_db.list_usage(start_timestamp=start_ts, end_timestamp=end_ts, limit=500000, most_recent=False)

    report = compute_budget_guard_report(rows, utc_day=utc_day, thresholds=thresholds)
    sys.stdout.write(json.dumps(report, sort_keys=True, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
