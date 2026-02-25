from __future__ import annotations

from typing import Any


def build_ollama_chat_payload(*, model_id: str, prompt: str) -> dict[str, Any]:
    return {
        "model": str(model_id),
        "messages": [{"role": "user", "content": str(prompt)}],
        "temperature": 0,
    }


class FakeOllamaProviderClient:
    provider_id = "ollama"

    def __init__(self, model_id: str) -> None:
        self.model_id = str(model_id)

    def generate_content(self, prompt: str, *, stream: bool = False) -> dict[str, Any]:
        if stream:
            raise NotImplementedError("ollama streaming not supported")
        text = f"OLLAMA_OFFLINE[{self.model_id}]:{str(prompt)}"
        return {
            "text": text,
            "tokens_input": None,
            "tokens_output": None,
            "cost_usd": None,
        }
