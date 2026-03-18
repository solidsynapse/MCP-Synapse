from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from src.providers.anthropic_contract_pr4 import build_anthropic_messages_payload
from src.providers.cost_normalizer import normalize_cost_with_litellm


_DEFAULT_BASE_URL = "https://api.anthropic.com/v1"
_DEFAULT_API_VERSION = "2023-06-01"
_DEFAULT_MAX_TOKENS = 1024
_HTTP_TIMEOUT_SECONDS = 30
_GENERIC_HTTP_MESSAGE = "Request failed"
_GENERIC_UNREACHABLE_MESSAGE = "Service unreachable"
_GENERIC_INVALID_JSON_MESSAGE = "Invalid JSON response"
_GENERIC_MALFORMED_RESPONSE_MESSAGE = "Malformed response"
_GENERIC_MISSING_TEXT_MESSAGE = "Malformed response: missing text content"
_GENERIC_MISSING_API_KEY_FILE = "API key file does not exist"
_GENERIC_EMPTY_API_KEY_FILE = "API key file is empty"


class AnthropicError(RuntimeError):
    pass


class AnthropicHTTPError(AnthropicError):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = int(status_code)


class AnthropicResponseError(AnthropicError):
    pass


class AnthropicProviderClient:
    provider_id = "anthropic"

    def __init__(
        self,
        *,
        agent: dict[str, Any],
        model_id: str,
        api_key_path: str,
    ) -> None:
        self.model_id = str(model_id)
        self._agent = dict(agent)
        base = str(agent.get("anthropic_base_url") or _DEFAULT_BASE_URL).strip()
        self._base = base.rstrip("/")
        self._api_version = str(agent.get("anthropic_api_version") or _DEFAULT_API_VERSION).strip()
        self._max_tokens = self._resolve_max_tokens(agent.get("anthropic_max_tokens"))
        self._api_key = self._read_api_key(api_key_path)

        if not self._base:
            raise ValueError("Missing anthropic_base_url")
        if not (self._base.startswith("https://") or self._base.startswith("http://")):
            raise ValueError("Invalid anthropic_base_url; expected http(s) URL")
        if not self._api_version:
            raise ValueError("Missing anthropic_api_version")
        if not self.model_id:
            raise ValueError("Missing model_id")

    def generate_content(self, prompt: str, *, stream: bool = False) -> dict[str, Any]:
        if stream:
            raise NotImplementedError("anthropic streaming not implemented")

        url = f"{self._base}/messages"
        payload = build_anthropic_messages_payload(
            model_id=self.model_id,
            prompt=str(prompt),
            max_tokens=self._max_tokens,
        )
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url=url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self._api_key,
                "anthropic-version": self._api_version,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT_SECONDS) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as http_exc:
            status_code = int(getattr(http_exc, "code", 0) or 0)
            raise AnthropicHTTPError(status_code, f"HTTP {status_code}: {_GENERIC_HTTP_MESSAGE}") from http_exc
        except Exception as exc:
            raise AnthropicError(_GENERIC_UNREACHABLE_MESSAGE) from exc

        try:
            parsed = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise AnthropicResponseError(_GENERIC_INVALID_JSON_MESSAGE) from exc

        text = self._extract_text(parsed)
        usage = parsed.get("usage") or {}
        tokens_in = self._coerce_int(usage.get("input_tokens"))
        tokens_out = self._coerce_int(usage.get("output_tokens"))

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

    def _extract_text(self, parsed: Any) -> str:
        content = parsed.get("content") if isinstance(parsed, dict) else None
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if not isinstance(item, dict):
                    continue
                if str(item.get("type") or "").strip().lower() != "text":
                    continue
                value = str(item.get("text") or "")
                if value:
                    parts.append(value)
            if parts:
                return "".join(parts)
        raise AnthropicResponseError(_GENERIC_MISSING_TEXT_MESSAGE)

    def _read_api_key(self, api_key_path: str) -> str:
        path = Path(str(api_key_path)).expanduser()
        if not path.exists():
            raise ValueError(_GENERIC_MISSING_API_KEY_FILE)
        key = path.read_text(encoding="utf-8").strip()
        if not key:
            raise ValueError(_GENERIC_EMPTY_API_KEY_FILE)
        return key

    def _resolve_max_tokens(self, raw: Any) -> int:
        try:
            value = int(raw) if raw is not None else _DEFAULT_MAX_TOKENS
        except Exception:
            value = _DEFAULT_MAX_TOKENS
        return max(1, value)

    def _coerce_int(self, value: Any) -> int | None:
        try:
            return int(value) if value is not None else None
        except Exception:
            return None
