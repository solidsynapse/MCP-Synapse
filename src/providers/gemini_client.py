from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from src.providers.cost_normalizer import normalize_cost_with_litellm


_DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
_HTTP_TIMEOUT_SECONDS = 30
_GENERIC_HTTP_MESSAGE = "Request failed"
_GENERIC_UNREACHABLE_MESSAGE = "Service unreachable"
_GENERIC_INVALID_JSON_MESSAGE = "Invalid JSON response"
_GENERIC_MISSING_TEXT_MESSAGE = "Malformed response: missing text content"
_GENERIC_MISSING_API_KEY_FILE = "API key file does not exist"
_GENERIC_EMPTY_API_KEY_FILE = "API key file is empty"


class GeminiError(RuntimeError):
    pass


class GeminiHTTPError(GeminiError):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = int(status_code)


class GeminiResponseError(GeminiError):
    pass


class GeminiProviderClient:
    provider_id = "gemini"

    def __init__(
        self,
        *,
        agent: dict[str, Any],
        model_id: str,
        api_key_path: str,
    ) -> None:
        self.model_id = str(model_id)
        self._agent = dict(agent)
        base = str(agent.get("gemini_base_url") or _DEFAULT_BASE_URL).strip()
        self._base = base.rstrip("/")
        self._api_key = self._read_api_key(api_key_path)

        if not self._base:
            raise ValueError("Missing gemini_base_url")
        if not (self._base.startswith("https://") or self._base.startswith("http://")):
            raise ValueError("Invalid gemini_base_url; expected http(s) URL")
        if not self.model_id:
            raise ValueError("Missing model_id")

    def generate_content(self, prompt: str, *, stream: bool = False) -> dict[str, Any]:
        if stream:
            raise NotImplementedError("gemini streaming not implemented")

        url = f"{self._base}/models/{urllib.parse.quote(self.model_id, safe='')}:generateContent"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": str(prompt)}]}],
            "generationConfig": {"temperature": 0, "topP": 1},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url=url,
            data=data,
            headers={"Content-Type": "application/json", "x-goog-api-key": self._api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT_SECONDS) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as http_exc:
            status_code = int(getattr(http_exc, "code", 0) or 0)
            raise GeminiHTTPError(status_code, f"HTTP {status_code}: {_GENERIC_HTTP_MESSAGE}") from http_exc
        except Exception as exc:
            raise GeminiError(_GENERIC_UNREACHABLE_MESSAGE) from exc

        try:
            parsed = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise GeminiResponseError(_GENERIC_INVALID_JSON_MESSAGE) from exc

        text = self._extract_text(parsed)
        usage = parsed.get("usageMetadata") or {}
        tokens_in = self._coerce_int(usage.get("promptTokenCount"))
        tokens_out = self._coerce_int(usage.get("candidatesTokenCount"))

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
        candidates = parsed.get("candidates") if isinstance(parsed, dict) else None
        if isinstance(candidates, list) and candidates:
            content = (candidates[0] or {}).get("content") or {}
            parts = content.get("parts") if isinstance(content, dict) else None
            if isinstance(parts, list):
                texts: list[str] = []
                for part in parts:
                    if isinstance(part, dict) and "text" in part:
                        value = str(part.get("text") or "")
                        if value:
                            texts.append(value)
                if texts:
                    return "".join(texts)
        raise GeminiResponseError(_GENERIC_MISSING_TEXT_MESSAGE)

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
