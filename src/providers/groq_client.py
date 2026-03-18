from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from src.providers.cost_normalizer import normalize_cost_with_litellm
from src.providers.groq_contract_pr5 import build_groq_chat_payload


_DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
_HTTP_TIMEOUT_SECONDS = 30
_GENERIC_HTTP_MESSAGE = "Request failed"
_GENERIC_UNREACHABLE_MESSAGE = "Service unreachable"
_GENERIC_INVALID_JSON_MESSAGE = "Invalid JSON response"
_GENERIC_MALFORMED_RESPONSE_MESSAGE = "Malformed response"
_GENERIC_MISSING_API_KEY_FILE = "API key file does not exist"
_GENERIC_EMPTY_API_KEY_FILE = "API key file is empty"


class GroqError(RuntimeError):
    pass


class GroqHTTPError(GroqError):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = int(status_code)


class GroqResponseError(GroqError):
    pass


class GroqProviderClient:
    provider_id = "groq"

    def __init__(
        self,
        *,
        agent: dict[str, Any],
        model_id: str,
        api_key_path: str,
    ) -> None:
        self.model_id = str(model_id)
        self._agent = dict(agent)
        base = str(agent.get("groq_base_url") or _DEFAULT_BASE_URL).strip()
        self._base = base.rstrip("/")
        self._api_key = self._read_api_key(api_key_path)

        if not self._base:
            raise ValueError("Missing groq_base_url")
        if not (self._base.startswith("https://") or self._base.startswith("http://")):
            raise ValueError("Invalid groq_base_url; expected http(s) URL")
        if not self.model_id:
            raise ValueError("Missing model_id")

    def generate_content(self, prompt: str, *, stream: bool = False) -> dict[str, Any]:
        if stream:
            raise NotImplementedError("groq streaming not implemented")

        url = f"{self._base}/chat/completions"
        payload = build_groq_chat_payload(model_id=self.model_id, prompt=str(prompt))
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url=url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT_SECONDS) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as http_exc:
            status_code = int(getattr(http_exc, "code", 0) or 0)
            raise GroqHTTPError(status_code, f"HTTP {status_code}: {_GENERIC_HTTP_MESSAGE}") from http_exc
        except Exception as exc:
            raise GroqError(_GENERIC_UNREACHABLE_MESSAGE) from exc

        try:
            parsed = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise GroqResponseError(_GENERIC_INVALID_JSON_MESSAGE) from exc

        try:
            choices = parsed.get("choices") or []
            message = (choices[0] or {}).get("message") or {}
            text = str(message.get("content") or "")
        except Exception as exc:
            raise GroqResponseError(_GENERIC_MALFORMED_RESPONSE_MESSAGE) from exc

        usage = parsed.get("usage") or {}
        tokens_in = self._coerce_int(usage.get("prompt_tokens"))
        tokens_out = self._coerce_int(usage.get("completion_tokens"))

        cost_result = normalize_cost_with_litellm(
            provider_id=self.provider_id,
            model_id=self.model_id,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            agent=self._agent,
        )

        return {
            "text": text,
            "tokens_input": tokens_in,
            "tokens_output": tokens_out,
            **cost_result,
        }

    def _read_api_key(self, api_key_path: str) -> str:
        path = Path(str(api_key_path)).expanduser()
        if not path.exists():
            raise ValueError(_GENERIC_MISSING_API_KEY_FILE)
        key = path.read_text(encoding="utf-8").strip()
        if not key:
            raise ValueError(_GENERIC_EMPTY_API_KEY_FILE)
        return key

    def _coerce_int(self, value: Any) -> int | None:
        try:
            return int(value) if value is not None else None
        except Exception:
            return None
