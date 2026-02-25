from __future__ import annotations

from collections import OrderedDict
from typing import Any

from src.mcp_server.persona_lite_p3_p2 import assemble_persona_lite_request


_MAX_ENTRIES = 256


class _LRUCache:
    def __init__(self, max_entries: int) -> None:
        self._max_entries = int(max_entries)
        self._data: OrderedDict[str, dict[str, Any]] = OrderedDict()

    def get(self, key: str) -> dict[str, Any] | None:
        value = self._data.get(key)
        if value is None:
            return None
        self._data.move_to_end(key, last=True)
        return value

    def put(self, key: str, value: dict[str, Any]) -> None:
        self._data[key] = value
        self._data.move_to_end(key, last=True)
        while len(self._data) > self._max_entries:
            self._data.popitem(last=False)

    def clear(self) -> None:
        self._data.clear()


_CACHE = _LRUCache(max_entries=_MAX_ENTRIES)


def reset_context_cache_for_tests() -> None:
    _CACHE.clear()


def assemble_context_cached_request(agent: dict[str, Any], prompt: str) -> dict[str, Any]:
    persona = agent.get("persona")
    if persona is None:
        out = assemble_persona_lite_request(agent, prompt)
        out["cache_hit"] = False
        return out

    if not isinstance(persona, str):
        raise ValueError("invalid_persona")

    persona_clean = persona.strip()
    if not persona_clean:
        out = assemble_persona_lite_request(agent, prompt)
        out["cache_hit"] = False
        return out

    agent_id = str(agent.get("id") or "")
    key = _cache_key(agent_id, persona_clean, str(prompt))
    hit = _CACHE.get(key)
    if hit is not None:
        out = dict(hit)
        out["cache_hit"] = True
        return out

    out = assemble_persona_lite_request(agent, prompt)
    stable = {
        "messages": out["messages"],
        "provider_prompt": out["provider_prompt"],
    }
    _CACHE.put(key, stable)
    out["cache_hit"] = False
    return out


def _cache_key(agent_id: str, persona: str, prompt: str) -> str:
    return (
        f"{len(agent_id)}:{agent_id}|"
        f"{len(persona)}:{persona}|"
        f"{len(prompt)}:{prompt}"
    )
