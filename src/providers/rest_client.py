from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


_HTTP_TIMEOUT_SECONDS = 30
_ALLOWED_AUTH_TYPES = {"none", "api_key_header", "bearer", "basic"}
_ALLOWED_METHODS = {"GET", "POST"}


class RestAPIError(RuntimeError):
    pass


class RestAPIHTTPError(RestAPIError):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = int(status_code)


class RestAPIResponseError(RestAPIError):
    pass


class RestAPIProviderClient:
    provider_id = "rest_api"

    def __init__(
        self,
        *,
        agent: dict[str, Any],
        model_id: str,
        endpoint: str,
        auth_type: str,
        method: str,
        response_field: str,
        credentials_path: str = "",
    ) -> None:
        self._agent = dict(agent)
        self.model_id = str(model_id or "custom_rest_api").strip() or "custom_rest_api"
        self._endpoint = str(endpoint or "").strip()
        self._auth_type = str(auth_type or "none").strip().lower() or "none"
        self._method = str(method or "POST").strip().upper() or "POST"
        self._response_field = str(response_field or "").strip()
        self._credentials_path = str(credentials_path or "").strip()

        if not self._endpoint:
            raise ValueError("Missing endpoint for rest_api")
        if not (self._endpoint.startswith("https://") or self._endpoint.startswith("http://")):
            raise ValueError("Invalid endpoint; expected http(s) URL")
        if self._auth_type not in _ALLOWED_AUTH_TYPES:
            raise ValueError("Invalid auth_type for rest_api")
        if self._method not in _ALLOWED_METHODS:
            raise ValueError("Invalid method for rest_api")
        if not self._response_field:
            raise ValueError("Missing response_field for rest_api")

    def generate_content(self, prompt: str, *, stream: bool = False) -> dict[str, Any]:
        if stream:
            raise NotImplementedError("rest_api streaming not implemented")

        headers = {"Accept": "application/json"}
        self._apply_auth(headers)
        url = self._endpoint
        data: bytes | None = None
        prompt_text = str(prompt)

        if self._method == "GET":
            url = self._append_query_param(url, "prompt", prompt_text)
        else:
            headers["Content-Type"] = "application/json"
            data = json.dumps({"prompt": prompt_text}).encode("utf-8")

        req = urllib.request.Request(
            url=url,
            data=data,
            headers=headers,
            method=self._method,
        )

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
            raise RestAPIHTTPError(status_code, f"HTTP {status_code}: {msg}") from http_exc
        except Exception as exc:
            raise RestAPIError(f"REST API unreachable at {self._endpoint}: {exc}") from exc

        try:
            parsed = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise RestAPIResponseError(f"Invalid JSON response: {exc}") from exc

        value = self._extract_response_field(parsed, self._response_field)
        if value is None:
            raise RestAPIResponseError(f"response_field not found: {self._response_field}")

        if isinstance(value, str):
            text = value
        elif isinstance(value, (int, float, bool)):
            text = str(value)
        else:
            text = json.dumps(value, ensure_ascii=True)

        return {
            "text": text,
            "tokens_input": None,
            "tokens_output": None,
            "cost_usd": 0.0,
            "cost_source": "UNKNOWN",
        }

    def _apply_auth(self, headers: dict[str, str]) -> None:
        if self._auth_type == "none":
            return
        secret = self._read_secret()
        if self._auth_type == "api_key_header":
            headers["x-api-key"] = secret
            return
        if self._auth_type == "bearer":
            headers["Authorization"] = f"Bearer {secret}"
            return
        if self._auth_type == "basic":
            token = base64.b64encode(secret.encode("utf-8")).decode("ascii")
            headers["Authorization"] = f"Basic {token}"

    def _read_secret(self) -> str:
        path = Path(self._credentials_path).expanduser()
        if not path.exists():
            raise ValueError(f"Credentials file does not exist: {path}")
        secret = path.read_text(encoding="utf-8").strip()
        if not secret:
            raise ValueError(f"Credentials file is empty: {path}")
        if self._auth_type == "basic" and ":" not in secret:
            raise ValueError("Basic auth credentials file must contain username:password")
        return secret

    @staticmethod
    def _append_query_param(url: str, key: str, value: str) -> str:
        parsed = urllib.parse.urlsplit(url)
        current = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        current.append((key, value))
        next_query = urllib.parse.urlencode(current)
        return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, next_query, parsed.fragment))

    @staticmethod
    def _extract_response_field(payload: Any, response_field: str) -> Any:
        current = payload
        for raw_part in str(response_field or "").split("."):
            part = raw_part.strip()
            if not part:
                continue
            if isinstance(current, list):
                try:
                    index = int(part)
                except Exception:
                    return None
                if index < 0 or index >= len(current):
                    return None
                current = current[index]
                continue
            if isinstance(current, dict):
                if part not in current:
                    return None
                current = current[part]
                continue
            return None
        return current
