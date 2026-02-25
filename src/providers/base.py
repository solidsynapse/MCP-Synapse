from __future__ import annotations

from typing import Any, Protocol


class ProviderClient(Protocol):
    provider_id: str
    model_id: str

    def generate_content(self, prompt: str, *, stream: bool = False) -> dict[str, Any]: ...

