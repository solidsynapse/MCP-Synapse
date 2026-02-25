from __future__ import annotations


from datetime import datetime, timedelta, timezone


def apply_test_traffic_filter(
    rows: list[dict],
    *,
    include_test_traffic: bool,
    agent_name_prefix: str = "_test_",
) -> list[dict]:
    prefix = str(agent_name_prefix or "").strip()
    if not prefix:
        return rows

    has_marker = False
    for row in rows:
        name = str((row or {}).get("agent_name") or "")
        if name.startswith(prefix):
            has_marker = True
            break

    if not has_marker:
        return rows
    if include_test_traffic:
        return rows

    filtered: list[dict] = []
    for row in rows:
        name = str((row or {}).get("agent_name") or "")
        if name.startswith(prefix):
            continue
        filtered.append(row)
    return filtered


def parse_usage_timestamp_utc(value: object) -> datetime | None:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    text = str(value or "").strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text)
    except Exception:
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except Exception:
            return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def apply_usage_agent_filter(
    rows: list[dict],
    *,
    selected_agent: str | None,
) -> list[dict]:
    agent = str(selected_agent or "").strip()
    if not agent or agent == "All Bridges":
        return rows
    return [row for row in rows if str((row or {}).get("agent_name") or "") == agent]


def apply_usage_date_range_filter(
    rows: list[dict],
    *,
    date_filter: str | None,
    now_utc: datetime,
) -> list[dict]:
    label = str(date_filter or "").strip() or "All time"
    cutoff: datetime | None = None
    if label == "Last 1h":
        cutoff = now_utc - timedelta(hours=1)
    elif label == "Last 4h":
        cutoff = now_utc - timedelta(hours=4)
    elif label == "Last 24h":
        cutoff = now_utc - timedelta(hours=24)
    elif label == "Last 7d":
        cutoff = now_utc - timedelta(days=7)
    elif label == "Last 30d":
        cutoff = now_utc - timedelta(days=30)
    if cutoff is None:
        return rows

    filtered: list[dict] = []
    for row in rows:
        ts = parse_usage_timestamp_utc((row or {}).get("timestamp"))
        if ts is None:
            continue
        if ts >= cutoff:
            filtered.append(row)
    return filtered


def compute_filtered_usage_rows(
    master_rows: list[dict],
    *,
    selected_agent: str | None,
    date_filter: str | None,
    include_test_traffic: bool,
    now_utc: datetime | None = None,
    agent_name_prefix: str = "_test_",
) -> list[dict]:
    now = now_utc or datetime.now(timezone.utc)
    rows = list(master_rows or [])
    rows = apply_usage_date_range_filter(rows, date_filter=date_filter, now_utc=now)
    rows = apply_usage_agent_filter(rows, selected_agent=selected_agent)
    rows = apply_test_traffic_filter(
        rows,
        include_test_traffic=include_test_traffic,
        agent_name_prefix=agent_name_prefix,
    )
    return rows
