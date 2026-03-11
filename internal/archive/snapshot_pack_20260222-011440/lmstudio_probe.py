from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any


_DEFAULT_BASE_URL = "http://127.0.0.1:1234/v1"
_HTTP_TIMEOUT_SECONDS = 15


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Headless LM Studio probe (non-streaming).")
    p.add_argument("--base-url", default=_DEFAULT_BASE_URL, help=f"Base URL (default {_DEFAULT_BASE_URL}).")
    p.add_argument("--model", default="", help="Model id. If omitted, the first model is discovered via GET /models.")
    p.add_argument("--prompt", required=True, help="Prompt text.")
    return p.parse_args(argv)


def _http_json(url: str, *, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers: dict[str, str] = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url=url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT_SECONDS) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as http_exc:
        body = ""
        try:
            body = http_exc.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        status_code = int(getattr(http_exc, "code", 0) or 0)
        msg = body.strip() or str(http_exc)
        raise RuntimeError(f"HTTP {status_code}: {msg}") from http_exc
    except Exception as exc:
        raise RuntimeError(str(exc)) from exc

    try:
        parsed = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Invalid JSON response: {exc}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("Invalid JSON response: expected object")
    return parsed


def _discover_first_model(base_url: str) -> str:
    url = f"{base_url.rstrip('/')}/models"
    parsed = _http_json(url, method="GET")
    data = parsed.get("data") or []
    if not isinstance(data, list) or not data:
        raise RuntimeError("No models returned by GET /models")
    for item in data:
        if isinstance(item, dict):
            mid = item.get("id")
            if isinstance(mid, str) and mid.strip():
                return mid.strip()
    raise RuntimeError("No usable model id found in GET /models")


def _chat_completion(base_url: str, *, model_id: str, prompt: str) -> str:
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": str(prompt)}],
        "temperature": 0,
        "top_p": 1,
    }
    parsed = _http_json(url, method="POST", payload=payload)
    try:
        choices = parsed.get("choices") or []
        message = (choices[0] or {}).get("message") or {}
        text = str(message.get("content") or "")
    except Exception as exc:
        raise RuntimeError(f"Malformed response: {exc}") from exc
    return text


def _emit(base_url: str, model_id: str, exit_code: int, text_or_error: str) -> None:
    sys.stdout.write(f"EXIT_CODE={int(exit_code)}\n")
    sys.stdout.write(f"BASE_URL={base_url}\n")
    sys.stdout.write(f"MODEL={model_id}\n")
    sys.stdout.write("---\n")
    sys.stdout.write(str(text_or_error))
    if not str(text_or_error).endswith("\n"):
        sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    base_url = str(args.base_url or "").strip()
    prompt = str(args.prompt or "")
    model_id = str(args.model or "").strip()

    if not base_url:
        _emit(base_url, model_id, 2, "Missing base URL")
        return 2

    try:
        if not model_id:
            model_id = _discover_first_model(base_url)
        text = _chat_completion(base_url, model_id=model_id, prompt=prompt)
    except Exception as exc:
        _emit(base_url, model_id, 1, f"LM Studio unreachable at {base_url}: {exc}")
        return 1

    _emit(base_url, model_id, 0, text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
