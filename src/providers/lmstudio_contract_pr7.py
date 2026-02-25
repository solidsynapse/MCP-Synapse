from __future__ import annotations

from typing import Any


def build_lmstudio_chat_payload(*, model_id: str, prompt: str) -> dict[str, Any]:
    return {
        "model": str(model_id),
        "messages": [{"role": "user", "content": str(prompt)}],
        "temperature": 0,
    }


class FakeLMStudioProviderClient:
    provider_id = "lmstudio"

    def __init__(self, model_id: str) -> None:
        self.model_id = str(model_id)

    def generate_content(self, prompt: str, *, stream: bool = False) -> dict[str, Any]:
        if stream:
            raise NotImplementedError("lmstudio streaming not supported")
        text = f"LMSTUDIO_OFFLINE[{self.model_id}]:{str(prompt)}"
        return {
            "text": text,
            "tokens_input": None,
            "tokens_output": None,
            "cost_usd": None,
        }
