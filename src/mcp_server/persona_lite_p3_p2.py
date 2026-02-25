from __future__ import annotations

from typing import Any


def assemble_persona_lite_request(agent: dict[str, Any], prompt: str) -> dict[str, Any]:
    persona = agent.get("persona")
    if persona is None:
        return {
            "messages": [{"role": "user", "content": str(prompt)}],
            "provider_prompt": str(prompt),
        }

    if not isinstance(persona, str):
        raise ValueError("invalid_persona")

    persona_clean = persona.strip()
    if not persona_clean:
        return {
            "messages": [{"role": "user", "content": str(prompt)}],
            "provider_prompt": str(prompt),
        }

    user_prompt = str(prompt)
    return {
        "messages": [
            {"role": "system", "content": persona_clean},
            {"role": "user", "content": user_prompt},
        ],
        "provider_prompt": persona_clean + "\n\n" + user_prompt,
    }
