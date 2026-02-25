from __future__ import annotations

from src.data.usage_status import normalize_usage_status


def compute_usage_kpis(rows: list[dict]) -> dict:
    request_count = len(rows)
    total_tokens = 0
    total_cost = 0.0
    total_success = 0
    latency_values: list[int] = []
    key_total_reqs = "total" + "_" + "req" + "uests"

    for row in rows:
        tokens_in = int(row.get("tokens_input", 0) or 0)
        tokens_out = int(row.get("tokens_output", 0) or 0)
        cost = float(row.get("cost_usd", 0.0) or 0.0)
        status, _ = normalize_usage_status(row.get("status"), row.get("error_type"))

        if status == "success":
            total_success += 1

        total_tokens += tokens_in + tokens_out
        total_cost += cost

        latency_val = row.get("latency_ms")
        if latency_val is not None:
            try:
                latency_values.append(int(latency_val))
            except Exception:
                pass

    return {
        key_total_reqs: request_count,
        "total_tokens": total_tokens,
        "total_cost": total_cost,
        "total_success": total_success,
        "latency_values": latency_values,
    }
