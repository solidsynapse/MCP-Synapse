from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from src.providers.cost_normalizer import normalize_cost_with_litellm


_DEFAULT_BASE_URL = "https://api.openai.com/v1"
_HTTP_TIMEOUT_SECONDS = 30
_GENERIC_HTTP_MESSAGE = "Request failed"
_GENERIC_UNREACHABLE_MESSAGE = "Service unreachable"
_GENERIC_INVALID_JSON_MESSAGE = "Invalid JSON response"
_GENERIC_MALFORMED_RESPONSE_MESSAGE = "Malformed response"
_GENERIC_API_KEY_FILE_MISSING_MESSAGE = "API key file does not exist"
_GENERIC_API_KEY_FILE_EMPTY_MESSAGE = "API key file is empty"


class OpenAIError(RuntimeError):
    pass


class OpenAIHTTPError(OpenAIError):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = int(status_code)


class OpenAIResponseError(OpenAIError):
    pass


class OpenAIProviderClient:
    provider_id = "openai"

    def __init__(
        self,
        *,
        agent: dict[str, Any],
        model_id: str,
        api_key_path: str,
    ) -> None:
        self.model_id = str(model_id)
        self._agent = dict(agent)
        base = str(agent.get("openai_base_url") or _DEFAULT_BASE_URL).strip()
        self._base = base.rstrip("/")
        self._api_key = self._read_api_key(api_key_path)

        if not self._base:
            raise ValueError("Missing base URL; set openai_base_url")
        if not (self._base.startswith("https://") or self._base.startswith("http://")):
            raise ValueError("Invalid openai_base_url; expected http(s) URL")
        if not self.model_id:
            raise ValueError("Missing model_id")

    def generate_content(self, prompt: str, *, stream: bool = False) -> dict[str, Any]:
        if stream:
            raise NotImplementedError("openai streaming not implemented")

        url = f"{self._base}/chat/completions"
        payload = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": str(prompt)}],
            "temperature": 0,
            "top_p": 1,
        }
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
            raise OpenAIHTTPError(status_code, f"HTTP {status_code}: {_GENERIC_HTTP_MESSAGE}") from http_exc
        except Exception as exc:
            raise OpenAIError(_GENERIC_UNREACHABLE_MESSAGE) from exc

        try:
            parsed = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise OpenAIResponseError(_GENERIC_INVALID_JSON_MESSAGE) from exc

        try:
            choices = parsed.get("choices") or []
            message = (choices[0] or {}).get("message") or {}
            text = str(message.get("content") or "")
        except Exception as exc:
            raise OpenAIResponseError(_GENERIC_MALFORMED_RESPONSE_MESSAGE) from exc

        usage = parsed.get("usage") or {}
        tokens_in = usage.get("prompt_tokens")
        tokens_out = usage.get("completion_tokens")
        try:
            tokens_in = int(tokens_in) if tokens_in is not None else None
        except Exception:
            tokens_in = None
        try:
            tokens_out = int(tokens_out) if tokens_out is not None else None
        except Exception:
            tokens_out = None

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
            raise ValueError(_GENERIC_API_KEY_FILE_MISSING_MESSAGE)
        key = path.read_text(encoding="utf-8").strip()
        if not key:
            raise ValueError(_GENERIC_API_KEY_FILE_EMPTY_MESSAGE)
        return key
