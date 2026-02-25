from __future__ import annotations

from typing import Any

from src.providers.base import ProviderClient
from src.vertex.client import VertexAIClient


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
        self._client = VertexAIClient(
            project_id=project_id,
            location=location,
            model_id=model_id,
            price_per_1m_input=price_per_1m_input,
            price_per_1m_output=price_per_1m_output,
            credentials_path=credentials_path,
        )

    def generate_content(self, prompt: str, *, stream: bool = False) -> dict[str, Any]:
        if stream:
            raise NotImplementedError("vertex streaming not implemented")
        return self._client.generate_content(prompt)
