import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_OPS = ("dashboard.get_state", "usage.recent", "connections.list")
AGENT_BY_OP = {
    "dashboard.get_state": "dashboard",
    "usage.recent": "usage",
    "connections.list": "connections",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _headless_path() -> Path:
    return _repo_root() / "tools" / "headless_dispatch_v1.py"


def _worker_path() -> Path:
    return _repo_root() / "tools" / "dispatch_worker_v1.py"


def _prompt_for_op(op: str) -> dict[str, Any]:
    if op == "dashboard.get_state":
        return {"op": op}
    if op == "usage.recent":
        return {"op": op, "limit": 200}
    if op == "connections.list":
        return {"op": op}
    raise ValueError(f"unsupported_op:{op}")


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    rank = (len(xs) - 1) * p
    lo = int(rank)
    hi = min(lo + 1, len(xs) - 1)
    frac = rank - lo
    return xs[lo] * (1.0 - frac) + xs[hi] * frac


def _stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {"min_ms": 0.0, "max_ms": 0.0, "p50_ms": 0.0, "p95_ms": 0.0}
    return {
        "min_ms": round(min(values), 3),
        "max_ms": round(max(values), 3),
        "p50_ms": round(_percentile(values, 0.50), 3),
        "p95_ms": round(_percentile(values, 0.95), 3),
    }


def _signature_for_parity(op: str, payload: dict[str, Any]) -> dict[str, Any]:
    error_obj = payload.get("error") if isinstance(payload.get("error"), dict) else {}
    sig: dict[str, Any] = {
        "ok": bool(payload.get("ok")),
        "status": str(payload.get("status") or ""),
        "error_code": str(error_obj.get("code") or ""),
    }
    if op == "dashboard.get_state":
        result = payload.get("result")
        if isinstance(result, dict):
            sig["result_keys"] = sorted(result.keys())
        else:
            sig["result_keys"] = []
    elif op == "usage.recent":
        text = payload.get("text")
        if isinstance(text, str):
            try:
                parsed = json.loads(text)
            except Exception:
                parsed = {}
        else:
            parsed = {}
        kpis = parsed.get("kpis") if isinstance(parsed.get("kpis"), dict) else {}
        rows = parsed.get("rows")
        sig["kpi_keys"] = sorted(kpis.keys())
        sig["rows_is_list"] = isinstance(rows, list)
    elif op == "connections.list":
        rows = payload.get("connections")
        sig["connections_is_list"] = isinstance(rows, list)
        if isinstance(rows, list) and rows and isinstance(rows[0], dict):
            sig["first_connection_keys"] = sorted(rows[0].keys())
        else:
            sig["first_connection_keys"] = []
    return sig


def _gain_pct(a: float, b: float) -> float:
    if a <= 0:
        return 0.0
    return round(((a - b) / a) * 100.0, 3)


def _run_subprocess_call(op: str, timeout_s: float) -> dict[str, Any]:
    prompt = _prompt_for_op(op)
    tmp = tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False)
    tmp_path = Path(tmp.name)
    try:
        tmp.write(json.dumps(prompt, ensure_ascii=False))
        tmp.flush()
        tmp.close()
        cmd = [
            sys.executable,
            str(_headless_path()),
            "--agent-id",
            AGENT_BY_OP[op],
            "--prompt-file",
            str(tmp_path),
        ]
        t0 = time.perf_counter()
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
            env=env,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        stdout_text = str(proc.stdout or "").strip()
        parsed: dict[str, Any] | None = None
        if stdout_text:
            try:
                candidate = json.loads(stdout_text)
                if isinstance(candidate, dict):
                    parsed = candidate
            except Exception:
                parsed = None
        request_ok = bool(parsed and parsed.get("ok"))
        return {
            "elapsed_ms": round(elapsed_ms, 3),
            "request_ok": request_ok,
            "payload": parsed,
            "exit_code": int(proc.returncode),
            "stderr_tail": (proc.stderr or "").strip()[-400:],
        }
    except subprocess.TimeoutExpired:
        return {
            "elapsed_ms": round(timeout_s * 1000.0, 3),
            "request_ok": False,
            "payload": None,
            "exit_code": 124,
            "stderr_tail": "timeout",
        }
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


class WorkerClient:
    def __init__(self, timeout_s: float):
        self._timeout_s = timeout_s
        self._next_id = 1
        cmd = [sys.executable, "-u", str(_worker_path())]
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        self._proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            env=env,
        )

    def request(self, op: str) -> dict[str, Any]:
        if self._proc.stdin is None or self._proc.stdout is None:
            return {
                "elapsed_ms": 0.0,
                "request_ok": False,
                "payload": None,
                "exit_code": -1,
                "stderr_tail": "worker_io_not_available",
            }
        req_id = self._next_id
        self._next_id += 1
        req = {"id": req_id, "agent_id": AGENT_BY_OP[op], "prompt": _prompt_for_op(op)}
        t0 = time.perf_counter()
        try:
            self._proc.stdin.write(json.dumps(req, ensure_ascii=False) + "\n")
            self._proc.stdin.flush()
            line = self._proc.stdout.readline()
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            if not line:
                return {
                    "elapsed_ms": round(elapsed_ms, 3),
                    "request_ok": False,
                    "payload": None,
                    "exit_code": self._proc.poll() if self._proc.poll() is not None else -1,
                    "stderr_tail": "empty_worker_stdout",
                }
            parsed = json.loads(line)
            payload = parsed.get("payload") if isinstance(parsed, dict) else None
            request_ok = bool(
                isinstance(parsed, dict) and parsed.get("ok") and isinstance(payload, dict) and payload.get("ok")
            )
            return {
                "elapsed_ms": round(elapsed_ms, 3),
                "request_ok": request_ok,
                "payload": payload if isinstance(payload, dict) else None,
                "exit_code": 0,
                "stderr_tail": "",
            }
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            return {
                "elapsed_ms": round(elapsed_ms, 3),
                "request_ok": False,
                "payload": None,
                "exit_code": -1,
                "stderr_tail": str(exc),
            }

    def close(self) -> None:
        try:
            if self._proc.stdin:
                self._proc.stdin.write(json.dumps({"id": -1, "type": "shutdown"}) + "\n")
                self._proc.stdin.flush()
        except Exception:
            pass
        try:
            self._proc.terminate()
            self._proc.wait(timeout=2.0)
        except Exception:
            try:
                self._proc.kill()
            except Exception:
                pass


def _run_mode(mode: str, ops: list[str], warmup: int, iters: int, timeout_s: float) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {op: [] for op in ops}
    if mode == "A":
        for op in ops:
            for _ in range(warmup):
                _run_subprocess_call(op, timeout_s=timeout_s)
            for _ in range(iters):
                out[op].append(_run_subprocess_call(op, timeout_s=timeout_s))
        return out
    worker = WorkerClient(timeout_s=timeout_s)
    try:
        for op in ops:
            for _ in range(warmup):
                worker.request(op)
            for _ in range(iters):
                out[op].append(worker.request(op))
    finally:
        worker.close()
    return out


def _summarize_mode(records_by_op: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for op, records in records_by_op.items():
        lat = [float(r.get("elapsed_ms") or 0.0) for r in records]
        err = sum(1 for r in records if not bool(r.get("request_ok")))
        n = len(records)
        summary[op] = {
            **_stats(lat),
            "n": n,
            "errors": err,
            "error_rate": round((err / n) if n else 0.0, 4),
        }
    return summary


def _representative_signature(op: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    for r in records:
        payload = r.get("payload")
        if isinstance(payload, dict) and payload.get("ok"):
            return _signature_for_parity(op, payload)
    for r in records:
        payload = r.get("payload")
        if isinstance(payload, dict):
            return _signature_for_parity(op, payload)
    return {"ok": False, "status": "no_payload", "error_code": "no_payload"}


def _parity_by_op(
    ops: list[str], a_records: dict[str, list[dict[str, Any]]], b_records: dict[str, list[dict[str, Any]]]
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for op in ops:
        a_sig = _representative_signature(op, a_records[op])
        b_sig = _representative_signature(op, b_records[op])
        out[op] = {"ok": a_sig == b_sig, "a_signature": a_sig, "b_signature": b_sig}
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ops", nargs="+", default=list(ALLOWED_OPS))
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--iters", type=int, default=8)
    parser.add_argument("--timeout-seconds", type=float, default=90.0)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    ops = [str(op).strip() for op in args.ops if str(op).strip()]
    invalid = [op for op in ops if op not in ALLOWED_OPS]
    if invalid:
        raise SystemExit(f"unsupported ops: {invalid}")

    a_records = _run_mode("A", ops, warmup=max(0, args.warmup), iters=max(1, args.iters), timeout_s=args.timeout_seconds)
    b_records = _run_mode("B", ops, warmup=max(0, args.warmup), iters=max(1, args.iters), timeout_s=args.timeout_seconds)

    a_summary = _summarize_mode(a_records)
    b_summary = _summarize_mode(b_records)
    parity = _parity_by_op(ops, a_records, b_records)

    per_op: dict[str, Any] = {}
    p95_gains: list[float] = []
    parity_all_ok = True
    for op in ops:
        gain = {
            "p50_pct": _gain_pct(float(a_summary[op]["p50_ms"]), float(b_summary[op]["p50_ms"])),
            "p95_pct": _gain_pct(float(a_summary[op]["p95_ms"]), float(b_summary[op]["p95_ms"])),
        }
        p95_gains.append(float(gain["p95_pct"]))
        parity_all_ok = parity_all_ok and bool(parity[op]["ok"])
        per_op[op] = {
            "A": a_summary[op],
            "B": b_summary[op],
            "parity": parity[op],
            "net_gain_pct": gain,
        }

    avg_p95_gain = round(statistics.mean(p95_gains), 3) if p95_gains else 0.0
    worker_worth_integrating = bool(parity_all_ok and avg_p95_gain >= 30.0)

    report = {
        "meta": {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "python": sys.version.split()[0],
            "cwd": os.getcwd(),
            "ops": ops,
            "warmup": int(max(0, args.warmup)),
            "iters": int(max(1, args.iters)),
        },
        "results": per_op,
        "overall": {
            "avg_p95_net_gain_pct": avg_p95_gain,
            "parity_all_ok": parity_all_ok,
            "decision": "worker spike worth integrating"
            if worker_worth_integrating
            else "worker spike not worth integrating",
        },
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
