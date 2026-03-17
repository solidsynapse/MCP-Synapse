from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from src.providers.cost_normalizer import normalize_cost_with_litellm


_HTTP_TIMEOUT_SECONDS = 30


class AzureOpenAIError(RuntimeError):
    pass


class AzureOpenAIHTTPError(AzureOpenAIError):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = int(status_code)


class AzureOpenAIResponseError(AzureOpenAIError):
    pass


class AzureOpenAIProviderClient:
    provider_id = "azure_openai"

    def __init__(
        self,
        *,
        agent: dict[str, Any],
        model_id: str,
        api_key_path: str,
    ) -> None:
        self.model_id = str(model_id)
        self._agent = dict(agent)
        self._endpoint = str(agent.get("azure_endpoint") or "").strip()
        self._api_version = str(agent.get("azure_api_version") or "").strip()
        self._deployment = str(agent.get("deployment_name") or agent.get("azure_deployment") or self.model_id).strip()
        self._api_key = self._read_api_key(api_key_path)

        if not self._endpoint:
            raise ValueError("Missing agent config: azure_endpoint")
        if not (self._endpoint.startswith("https://") or self._endpoint.startswith("http://")):
            raise ValueError("Invalid azure_endpoint; expected http(s) URL")
        if not self._api_version:
            raise ValueError("Missing agent config: azure_api_version")
        if not self._deployment:
            raise ValueError("Missing deployment; set deployment_name or model_id")

        self._endpoint = self._endpoint.rstrip("/")

    def generate_content(self, prompt: str, *, stream: bool = False) -> dict[str, Any]:
        if stream:
            raise NotImplementedError("azure_openai streaming not implemented")

        url = (
            f"{self._endpoint}/openai/deployments/{urllib.parse.quote(self._deployment)}"
            f"/chat/completions?api-version={urllib.parse.quote(self._api_version)}"
        )
        payload = {
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
                "api-key": self._api_key,
            },
            method="POST",
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
            raise AzureOpenAIHTTPError(status_code, f"HTTP {status_code}: {msg}")
        except Exception as exc:
            raise AzureOpenAIError(str(exc))

        try:
            parsed = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise AzureOpenAIResponseError(f"Invalid JSON response: {exc}")

        try:
            choices = parsed.get("choices") or []
            message = (choices[0] or {}).get("message") or {}
            text = str(message.get("content") or "")
        except Exception as exc:
            raise AzureOpenAIResponseError(f"Malformed response: {exc}")

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
            raise ValueError(f"API key file does not exist: {path}")
        key = path.read_text(encoding="utf-8").strip()
        if not key:
            raise ValueError(f"API key file is empty: {path}")
        return key
