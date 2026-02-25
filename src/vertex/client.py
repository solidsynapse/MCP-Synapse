from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from google.api_core.exceptions import PermissionDenied, ResourceExhausted
from google.oauth2.service_account import Credentials
from vertexai import init as vertex_init
from vertexai.generative_models import GenerativeModel

from src.config.manager import ConfigManager

class CredentialError(Exception): ...


class QuotaError(Exception): ...


class APIError(Exception): ...


class VertexAIClient:
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
        allowed_models = config.get_allowed_models()
        if self.model_id not in allowed_models:
            raise APIError(
                "Model '" + self.model_id + "' is not allowed. Allowed models: "
                + ", ".join(allowed_models)
            )
        self.price_in = float(price_per_1m_input)
        self.price_out = float(price_per_1m_output)
        creds: Credentials | None = None
        if credentials_path:
            p = Path(credentials_path).expanduser().resolve()
            if not p.exists():
                raise CredentialError("Check your GCP credentials path")
            try:
                creds = Credentials.from_service_account_file(str(p))
            except Exception as exc:
                raise CredentialError("Check your GCP credentials") from exc
        try:
            vertex_init(project=self.project_id, location=self.location, credentials=creds)
        except Exception as exc:
            raise APIError("Failed to initialize Vertex AI") from exc
        self._model = GenerativeModel(self.model_id)

    def _calc_cost(self, tokens_in: int, tokens_out: int) -> float:
        cost = (tokens_in / 1_000_000.0) * self.price_in + (tokens_out / 1_000_000.0) * self.price_out
        return float(f"{cost:.6f}")

    def generate_content(self, prompt: str, timeout: int = 30) -> dict[str, Any]:
        try:
            resp = self._model.generate_content(prompt)
        except PermissionDenied as exc:
            raise CredentialError("Check your GCP credentials") from exc
        except ResourceExhausted as exc:
            raise QuotaError("Quota exceeded. Try later or adjust limits") from exc
        except Exception as exc:
            raise APIError("Vertex AI request failed") from exc

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
                print(f"⚠️  WARNING: Usage metadata missing. Estimated tokens: in={input_tokens}, out={output_tokens}")
        except Exception as e:
            print(f"⚠️  WARNING: Could not extract usage metadata: {e}. Cost will be $0")
            input_tokens = 0
            output_tokens = 0

        text = getattr(resp, "text", None)
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
