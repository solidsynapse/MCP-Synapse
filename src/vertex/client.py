from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from threading import Lock
from time import monotonic
from typing import Any

from src.config.manager import ConfigManager

logger = logging.getLogger(__name__)

class CredentialError(Exception): ...


class QuotaError(Exception): ...


class APIError(Exception): ...


class VertexAIClient:
    _CREDENTIALS_CACHE_TTL_SECONDS = 300.0
    _credentials_cache: dict[str, tuple[float, Any]] = {}
    _credentials_cache_lock = Lock()

    def __init__(
        self,
        project_id: str,
        location: str,
        model_id: str,
        price_per_1m_input: float,
        price_per_1m_output: float,
        credentials_path: str | None = None,
    ) -> None:
        self.project_id = project_id
        self.location = location
        self.model_id = model_id
        config = ConfigManager()
        is_allowed, strict_mode, allowed_models = config.is_model_allowed("vertex", self.model_id)
        if not is_allowed:
            raise APIError(
                "Model '" + self.model_id + "' is not allowed. Allowed models: "
                + ", ".join(allowed_models)
            )
        if not strict_mode and allowed_models and self.model_id not in allowed_models:
            logger.warning(
                "Vertex model '%s' is not in verified catalog; proceeding because strict mode is disabled.",
                self.model_id,
            )
        self.price_in = float(price_per_1m_input)
        self.price_out = float(price_per_1m_output)
        from vertexai import init as vertex_init
        from vertexai.preview.generative_models import GenerativeModel

        creds: Any | None = None
        if credentials_path:
            p = Path(credentials_path).expanduser().resolve()
            if not p.exists():
                raise CredentialError("Check your GCP credentials path")
            creds = self._load_cached_credentials(p)
        try:
            vertex_init(project=self.project_id, location=self.location, credentials=creds)
        except Exception as exc:
            raise APIError(self._format_provider_error("Failed to initialize Vertex AI", exc)) from exc
        try:
            self._model = GenerativeModel(self.model_id)
        except Exception as exc:
            raise APIError(self._format_provider_error("Failed to initialize Vertex model", exc)) from exc

    @classmethod
    def _load_cached_credentials(cls, credential_path: Path) -> Any:
        from google.oauth2.service_account import Credentials

        cache_key = str(credential_path).lower()
        now = monotonic()
        with cls._credentials_cache_lock:
            cached = cls._credentials_cache.get(cache_key)
            if cached and (now - float(cached[0])) <= cls._CREDENTIALS_CACHE_TTL_SECONDS:
                return cached[1]
        try:
            creds = Credentials.from_service_account_file(str(credential_path))
        except Exception as exc:
            raise CredentialError("Check your GCP credentials") from exc
        with cls._credentials_cache_lock:
            cls._credentials_cache[cache_key] = (now, creds)
        return creds

    @staticmethod
    def _safe_text(value: Any) -> str:
        return str(value).encode("ascii", "backslashreplace").decode("ascii")

    def _extract_error_payload(self, exc: Exception) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": exc.__class__.__name__,
            "message": self._safe_text(str(exc)),
        }
        for key in ("code", "details", "reason", "errors"):
            if not hasattr(exc, key):
                continue
            try:
                raw_value = getattr(exc, key)
                if callable(raw_value):
                    raw_value = raw_value()
                payload[key] = self._safe_text(raw_value)
            except Exception:
                continue
        response = getattr(exc, "response", None)
        if response is not None:
            try:
                payload["response_status"] = int(getattr(response, "status_code", 0) or 0)
            except Exception:
                pass
            try:
                body = getattr(response, "text", None)
                if body:
                    payload["response_text"] = self._safe_text(body)[:1500]
            except Exception:
                pass
        return payload

    def _classify_error(self, exc: Exception, payload: dict[str, Any]) -> str:
        from google.api_core.exceptions import InvalidArgument, NotFound, PermissionDenied, ResourceExhausted

        text = str(payload.get("message") or "").lower()
        if isinstance(exc, ResourceExhausted):
            return "quota/rate-limit issue"
        if isinstance(exc, PermissionDenied):
            return "permission/auth issue"
        if isinstance(exc, InvalidArgument):
            return "invalid request (model_id/region/payload)"
        if isinstance(exc, NotFound):
            return "resource/model not found"
        quota_signals = (
            "quota",
            "rate limit",
            "too many requests",
            "429",
            "resource exhausted",
        )
        if any(signal in text for signal in quota_signals):
            return "quota/rate-limit issue"
        if "permission" in text or "forbidden" in text or "unauthorized" in text:
            return "permission/auth issue"
        if "not found" in text or "404" in text:
            return "resource/model not found"
        if "invalid" in text or "unsupported" in text:
            return "invalid request (model_id/region/payload)"
        return "provider/runtime issue"

    def _format_provider_error(self, prefix: str, exc: Exception) -> str:
        payload = self._extract_error_payload(exc)
        logger.error("Vertex raw error payload: %s", json.dumps(payload, ensure_ascii=True))
        cause = self._classify_error(exc, payload)
        message = str(payload.get("message") or "").strip()
        return f"{prefix}: {cause}; raw={message}"

    def _calc_cost(self, tokens_in: int, tokens_out: int) -> float:
        cost = (tokens_in / 1_000_000.0) * self.price_in + (tokens_out / 1_000_000.0) * self.price_out
        return float(f"{cost:.6f}")

    def generate_content(
        self,
        prompt: str,
        timeout: int = 30,
        max_output_tokens: int | None = None,
    ) -> dict[str, Any]:
        from google.api_core.exceptions import PermissionDenied, ResourceExhausted
        from vertexai.preview.generative_models import GenerationConfig

        request_kwargs: dict[str, Any] = {}
        if isinstance(max_output_tokens, int) and max_output_tokens > 0:
            request_kwargs["generation_config"] = GenerationConfig(
                max_output_tokens=max_output_tokens,
                temperature=0.0,
            )
        try:
            resp = self._model.generate_content(prompt, **request_kwargs)
        except PermissionDenied as exc:
            raise CredentialError(self._format_provider_error("Check your GCP credentials", exc)) from exc
        except ResourceExhausted as exc:
            raise QuotaError(self._format_provider_error("Quota exceeded. Try later or adjust limits", exc)) from exc
        except Exception as exc:
            raise APIError(self._format_provider_error("Vertex AI request failed", exc)) from exc

        input_tokens = 0
        output_tokens = 0
        try:
            if hasattr(resp, "usage_metadata") and resp.usage_metadata:
                input_tokens = int(getattr(resp.usage_metadata, "prompt_token_count", 0) or 0)
                output_tokens = int(getattr(resp.usage_metadata, "candidates_token_count", 0) or 0)
            else:
                import tiktoken
                enc = tiktoken.get_encoding("cl100k_base")
                input_tokens = len(enc.encode(prompt))
                output_tokens = len(enc.encode(getattr(resp, "text", "") or ""))
                logger.warning(
                    "Usage metadata missing. Estimated tokens: in=%s, out=%s",
                    input_tokens,
                    output_tokens,
                )
        except Exception as e:
            err_safe = str(e).encode("ascii", "backslashreplace").decode("ascii")
            logger.warning("Could not extract usage metadata (%s). Cost will be $0", err_safe)
            input_tokens = 0
            output_tokens = 0

        text = ""
        try:
            text_candidate = getattr(resp, "text", None)
            if text_candidate:
                text = str(text_candidate)
        except Exception:
            text = ""
        if not text:
            try:
                candidates = getattr(resp, "candidates", [])
                if candidates and candidates[0].content.parts:
                    part = candidates[0].content.parts[0]
                    text = getattr(part, "text", "") or str(part)
            except Exception:
                text = ""

        cost = self._calc_cost(input_tokens, output_tokens)
        return {
            "text": text or "",
            "tokens_input": input_tokens,
            "tokens_output": output_tokens,
            "cost_usd": cost,
        }

    def test_connection(self) -> bool:
        try:
            result = self.generate_content("ping", timeout=15)
            ok = isinstance(result, dict) and result.get("tokens_input", 0) >= 0
            return bool(ok)
        except (CredentialError, QuotaError, APIError):
            return False
