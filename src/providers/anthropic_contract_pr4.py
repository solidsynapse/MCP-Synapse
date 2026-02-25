from __future__ import annotations

from typing import Any


def build_anthropic_messages_payload(
    *,
    model_id: str,
    prompt: str,
    max_tokens: int,
) -> dict[str, Any]:
    return {
        "model": str(model_id),
        "max_tokens": int(max_tokens),
        "messages": [{"role": "user", "content": str(prompt)}],
        "temperature": 0,
    }


class FakeAnthropicProviderClient:
    provider_id = "anthropic"

    def __init__(self, model_id: str, *, max_tokens: int) -> None:
        self.model_id = str(model_id)
        self.max_tokens = int(max_tokens)

    def generate_content(self, prompt: str, *, stream: bool = False) -> dict[str, Any]:
        if stream:
            raise NotImplementedError("anthropic streaming not supported")
        text = f"ANTHROPIC_OFFLINE[{self.model_id};max_tokens={self.max_tokens}]:{str(prompt)}"
        return {
            "text": text,
            "tokens_input": None,
            "tokens_output": None,
            "cost_usd": None,
        }
