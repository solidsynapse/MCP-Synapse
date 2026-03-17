from __future__ import annotations

import json
from typing import Any


_DEFAULT_CAPABILITY_TYPES = ("text",)
_PROVIDER_CAPABILITY_TYPES: dict[str, tuple[str, ...]] = {
    "vertex": ("text",),
    "openai": ("text",),
    "azure_openai": ("text",),
    "huggingface": ("text",),
    "ollama": ("text",),
    "bedrock": ("text",),
}


def _normalize_provider_id(value: Any) -> str:
    return str(value or "").strip().lower()


def resolve_capability_types(provider_id: Any) -> list[str]:
    normalized = _normalize_provider_id(provider_id)
    values = _PROVIDER_CAPABILITY_TYPES.get(normalized, _DEFAULT_CAPABILITY_TYPES)
    return [str(v) for v in values if str(v).strip()]


def build_mcp_server_entry(*, port: int, provider_id: Any = None) -> dict[str, Any]:
    capability_types = resolve_capability_types(provider_id)
    return {
        "url": f"http://localhost:{int(port)}/sse",
        "type": "sse",
        "capabilities": {"tools": {}},
        "x_mcp_synapse": {
            "capability_types": capability_types,
        },
    }


def build_mcp_config(agent: dict[str, Any]) -> dict[str, Any]:
    raw_name = agent.get("name")
    if not isinstance(raw_name, str):
        raise ValueError("invalid_agent_name")
    name = raw_name.strip()
    if not name:
        raise ValueError("invalid_agent_name")

    if "port" not in agent:
        raise ValueError("missing_agent_port")
    port = int(agent["port"])

    return {
        "mcpServers": {
            name: build_mcp_server_entry(
                port=port,
                provider_id=agent.get("provider_id"),
            )
        }
    }


def build_mcp_config_json(agent: dict[str, Any]) -> str:
    cfg = build_mcp_config(agent)
    return json.dumps(cfg, indent=2, sort_keys=True)
