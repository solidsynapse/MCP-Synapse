from __future__ import annotations

from typing import Any

from src.providers.base import ProviderClient
from src.vertex.client import VertexAIClient


def _parse_positive_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except Exception:
        return None
    if parsed <= 0:
        return None
    return parsed


def _vertex_unit_prices(model_id: str) -> tuple[float, float] | None:
    model = str(model_id or "").strip().lower()
    if model.startswith("gemini-2.0-flash"):
        return (0.10, 0.40)
    if model.startswith("gemini-1.5-flash"):
        return (0.075, 0.30)
    if model.startswith("gemini-3-flash"):
        return (0.20, 0.80)
    if model.startswith("gemini-3-pro"):
        return (1.25, 5.00)
    return None


class VertexProviderClient:
    provider_id = "vertex"

    def __init__(
        self,
        *,
        project_id: str,
        location: str,
        model_id: str,
        price_per_1m_input: float,
        price_per_1m_output: float,
        credentials_path: str,
    ) -> None:
        self.model_id = model_id
        resolved_input = _parse_positive_float(price_per_1m_input)
        resolved_output = _parse_positive_float(price_per_1m_output)
        fallback_prices = _vertex_unit_prices(self.model_id)
        self._pricing_available = False
        if resolved_input is not None and resolved_output is not None:
            self._pricing_available = True
        elif fallback_prices is not None:
            resolved_input, resolved_output = fallback_prices
            self._pricing_available = True
        else:
            resolved_input = 0.0
            resolved_output = 0.0
        self._client = VertexAIClient(
            project_id=project_id,
            location=location,
            model_id=model_id,
            price_per_1m_input=float(resolved_input),
            price_per_1m_output=float(resolved_output),
            credentials_path=credentials_path,
        )

    def generate_content(
        self,
        prompt: str,
        *,
        stream: bool = False,
        max_output_tokens: int | None = None,
    ) -> dict[str, Any]:
        if stream:
            raise NotImplementedError("vertex streaming not implemented")
        result = self._client.generate_content(prompt, max_output_tokens=max_output_tokens)
        if not isinstance(result, dict):
            return result
        tokens_in = result.get("tokens_input")
        tokens_out = result.get("tokens_output")
        total = 0
        try:
            total = int(tokens_in or 0) + int(tokens_out or 0)
        except Exception:
            total = 0
        if total > 0 and not self._pricing_available and result.get("cost_source") == "UNKNOWN":
            result["cost_usd"] = None
        return result
