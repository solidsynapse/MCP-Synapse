from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


_DEFAULT_BASE_URL = "http://127.0.0.1:11434"
_HTTP_TIMEOUT_SECONDS = 5


class OllamaProviderError(RuntimeError):
    pass


class OllamaProviderClient:
    provider_id = "ollama"

    def __init__(self, agent: dict, model_id: str) -> None:
        self._agent = dict(agent)
        self.model_id = str(model_id)
        base = str(self._agent.get("ollama_base_url") or _DEFAULT_BASE_URL).strip()
        self._base = base.rstrip("/")

    def generate_content(self, prompt: str, *, stream: bool = False) -> dict[str, Any]:
        if stream:
            raise NotImplementedError("ollama streaming not supported")

        url = f"{self._base}/v1/chat/completions"
        payload = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": str(prompt)}],
            "temperature": 0,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url=url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT_SECONDS) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as http_exc:
            status_code = int(getattr(http_exc, "code", 0) or 0)
            try:
                raw_err = http_exc.read()
            except Exception:
                raw_err = b""
            snippet = self._decode_snippet(raw_err)
            raise OllamaProviderError(f"Ollama HTTP {status_code}: {snippet}") from http_exc
        except Exception as exc:
            raise OllamaProviderError(f"Ollama unreachable at {self._base}: {exc}") from exc

        decoded = raw.decode("utf-8", errors="replace")
        try:
            parsed: Any = json.loads(decoded)
        except Exception as exc:
            snippet = self._decode_snippet(raw)
            raise OllamaProviderError(f"Invalid JSON response: {exc}; body={snippet}") from exc

        text = self._extract_text(parsed)
        usage = parsed.get("usage") if isinstance(parsed, dict) else None
        tokens_in = usage.get("prompt_tokens") if isinstance(usage, dict) else None
        tokens_out = usage.get("completion_tokens") if isinstance(usage, dict) else None
        return {
            "text": text,
            "tokens_input": tokens_in,
            "tokens_output": tokens_out,
            "cost_usd": None,
        }

    def _extract_text(self, parsed: Any) -> str:
        if isinstance(parsed, dict):
            choices = parsed.get("choices")
            if isinstance(choices, list) and choices:
                first = choices[0]
                if isinstance(first, dict):
                    msg = first.get("message")
                    if isinstance(msg, dict) and "content" in msg:
                        return str(msg.get("content") or "")
                    if "text" in first:
                        return str(first.get("text") or "")
        raise OllamaProviderError("Malformed Ollama response")

    def _decode_snippet(self, raw: bytes, *, limit: int = 500) -> str:
        text = raw.decode("utf-8", errors="replace").strip()
        if len(text) > limit:
            return text[:limit]
        return text
