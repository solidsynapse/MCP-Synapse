from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.data.usage_db import UsageDatabase
from src.data.usage_export import usage_rows_to_csv_text
from src.data.usage_export_service import export_usage_db_to_csv_file


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Headless usage CSV export (deterministic).")
    p.add_argument(
        "--out",
        default="",
        help="Optional output file path. If omitted, prints CSV to stdout.",
    )
    p.add_argument("--limit", type=int, default=2000)
    p.add_argument("--most-recent", type=int, default=1, help="1 (default) or 0")
    p.add_argument("--agent-id", default="")
    p.add_argument("--agent-name", default="")
    p.add_argument("--start-timestamp", default="")
    p.add_argument("--end-timestamp", default="")
    p.add_argument("--db-path", default="", help="Optional override for usage.db path.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    db_path = str(args.db_path or "").strip() or None
    usage_db = UsageDatabase(db_path=db_path)

    out_path = str(args.out or "").strip()
    if out_path:
        export_usage_db_to_csv_file(
            usage_db,
            out_path,
            limit=int(args.limit),
            most_recent=bool(int(args.most_recent)),
            agent_id=str(args.agent_id or "").strip() or None,
            agent_name=str(args.agent_name or "").strip() or None,
            start_timestamp=str(args.start_timestamp or "").strip() or None,
            end_timestamp=str(args.end_timestamp or "").strip() or None,
        )
        return 0

    rows = usage_db.list_usage(
        agent_id=str(args.agent_id or "").strip() or None,
        agent_name=str(args.agent_name or "").strip() or None,
        start_timestamp=str(args.start_timestamp or "").strip() or None,
        end_timestamp=str(args.end_timestamp or "").strip() or None,
        limit=int(args.limit),
        most_recent=bool(int(args.most_recent)),
    )
    sys.stdout.write(usage_rows_to_csv_text(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
