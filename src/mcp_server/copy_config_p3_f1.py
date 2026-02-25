from __future__ import annotations

import json
from typing import Any


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

    return {"mcpServers": {name: {"url": f"http://localhost:{port}/sse"}}}


def build_mcp_config_json(agent: dict[str, Any]) -> str:
    cfg = build_mcp_config(agent)
    return json.dumps(cfg, indent=2, sort_keys=True)
