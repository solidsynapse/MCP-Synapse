from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


_HTTP_TIMEOUT_SECONDS = 30
_DEFAULT_HF_ENDPOINT = "https://router.huggingface.co/v1"


class HuggingFaceProviderClient:
    provider_id = "huggingface"

    def __init__(self, agent: dict, model_id: str, credentials_path: str) -> None:
        self._agent = dict(agent)
        self.model_id = str(model_id)
        self._credentials_path = str(credentials_path)
        base = str(agent.get("hf_endpoint") or _DEFAULT_HF_ENDPOINT).strip()
        self._base = self._normalize_base_url(base)

    def generate_content(self, prompt: str, *, stream: bool = False) -> dict[str, Any]:
        if stream:
            raise NotImplementedError("huggingface streaming not implemented")


        if not self._is_network_enabled(self._agent.get("hf_enable_network")):
            raise NotImplementedError(
                "huggingface network gate is disabled; set agent config hf_enable_network: true to enable real calls"
            )

        token = self._read_token(self._credentials_path)
        url = f"{self._base}/chat/completions"
        payload = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": str(prompt)}],
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url=url,
            data=data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT_SECONDS) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as http_exc:
            status_code = int(getattr(http_exc, "code", 0) or 0)
            try:
                raw_err = http_exc.read()
            except Exception as read_exc:
                raise RuntimeError(
                    f"HTTP {status_code}: <failed to read response body: {read_exc}>"
                ) from read_exc
            snippet = self._decode_snippet(raw_err)
            raise RuntimeError(f"HTTP {status_code}: {snippet}")
        except Exception as exc:
            raise RuntimeError(str(exc)) from exc

        decoded = raw.decode("utf-8", errors="replace")
        try:
            parsed: Any = json.loads(decoded)
        except Exception as exc:
            snippet = self._decode_snippet(raw)
            raise RuntimeError(f"Invalid JSON response: {exc}; body={snippet}") from exc

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

    def _is_network_enabled(self, raw_value: Any) -> bool:
        if isinstance(raw_value, bool):
            return raw_value
        value = str(raw_value or "").strip().lower()
        return value in {"1", "true", "yes", "on"}

    def _read_token(self, credentials_path: str) -> str:
        path = Path(str(credentials_path)).expanduser()
        if not path.exists():
            raise ValueError(f"Token file does not exist: {path}")
        token = path.read_text(encoding="utf-8").strip()
        if not token:
            raise ValueError(f"Token file is empty: {path}")
        return token

    def _extract_text(self, parsed: Any) -> str:
        if isinstance(parsed, dict):
            if "error" in parsed:
                raise RuntimeError(str(parsed.get("error") or "Unknown error"))
            choices = parsed.get("choices")
            if isinstance(choices, list) and choices:
                first = choices[0]
                if isinstance(first, dict):
                    msg = first.get("message")
                    if isinstance(msg, dict) and "content" in msg:
                        return str(msg.get("content") or "")
                    if "text" in first:
                        return str(first.get("text") or "")
            if "generated_text" in parsed:
                return str(parsed.get("generated_text") or "")
        if isinstance(parsed, list) and parsed:
            first = parsed[0]
            if isinstance(first, dict) and "generated_text" in first:
                return str(first.get("generated_text") or "")
        raise RuntimeError("Malformed Hugging Face response")

    def _normalize_base_url(self, raw: str) -> str:
        base = str(raw or "").strip()
        if not base:
            base = _DEFAULT_HF_ENDPOINT
        base = base.rstrip("/")
        if base.endswith("/chat/completions"):
            return base[: -len("/chat/completions")]
        if base.endswith("/v1"):
            return base
        return f"{base}/v1"

    def _decode_snippet(self, raw: bytes, *, limit: int = 500) -> str:
        text = raw.decode("utf-8", errors="replace").strip()
        if len(text) > limit:
            return text[:limit]
        return text
