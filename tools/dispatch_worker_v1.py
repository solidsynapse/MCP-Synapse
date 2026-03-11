import json
import sys
import time
from typing import Any

from headless_dispatch_v1 import _dispatch

ALLOWED_OPS = {
    "dashboard.get_state",
    "usage.recent",
    "connections.list",
    "connections.copy_config",
    "connections.schema_hint",
    "settings.get_state",
    "policies.persona.get_state",
    "policies.optimizations.get_state",
    "resilience.budget.get_state",
    "resilience.interceptors.get_state",
}


def _configure_stdio() -> None:
    try:
        reconfigure = getattr(sys.stdout, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _write_row(row: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(row, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _normalize_prompt(prompt_raw: Any) -> tuple[str, str]:
    if isinstance(prompt_raw, dict):
        payload = prompt_raw
    elif isinstance(prompt_raw, str):
        payload = json.loads(prompt_raw)
    else:
        raise ValueError("prompt must be a JSON object or JSON string")
    if not isinstance(payload, dict):
        raise ValueError("prompt must be a JSON object")
    op = str(payload.get("op") or "").strip()
    if op not in ALLOWED_OPS:
        raise ValueError(f"unsupported_op:{op}")
    return op, json.dumps(payload, ensure_ascii=False)


def main() -> int:
    _configure_stdio()
    for raw in sys.stdin:
        line = str(raw or "").strip()
        if not line:
            continue
        request_id: Any = None
        try:
            req = json.loads(line)
            if not isinstance(req, dict):
                raise ValueError("request must be a JSON object")
            request_id = req.get("id")
            if req.get("type") == "shutdown":
                _write_row({"id": request_id, "ok": True, "status": "shutdown"})
                return 0
            agent_id = str(req.get("agent_id") or "benchmark")
            op, prompt_text = _normalize_prompt(req.get("prompt"))
            t0 = time.perf_counter()
            payload = _dispatch(agent_id=agent_id, prompt=prompt_text)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            _write_row(
                {
                    "id": request_id,
                    "ok": True,
                    "op": op,
                    "elapsed_ms": round(elapsed_ms, 3),
                    "payload": payload,
                }
            )
        except Exception as exc:
            _write_row(
                {
                    "id": request_id,
                    "ok": False,
                    "elapsed_ms": 0.0,
                    "error": {"code": exc.__class__.__name__, "message": str(exc)},
                }
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
