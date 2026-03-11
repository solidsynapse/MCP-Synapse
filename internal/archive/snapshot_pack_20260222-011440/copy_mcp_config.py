from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.config.manager import ConfigManager
from src.mcp_server.agent_server import MCPAgentServer


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Headless MCP config snippet generator (deterministic, no secrets)."
    )
    p.add_argument("--agent-id", required=True, help="Agent id from data/config.json.")
    p.add_argument(
        "--out",
        default="",
        help="Optional output file path. If omitted, only prints to stdout.",
    )
    return p.parse_args(argv)


def _dump_bytes(config: dict) -> bytes:
    payload = json.dumps(config, sort_keys=True, indent=2) + "\n"
    return payload.encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    agent_id = str(args.agent_id).strip()
    if not agent_id:
        return 2

    cfg = ConfigManager()
    agent = cfg.get_agent(agent_id)
    if not agent:
        sys.stderr.write(f"Agent not found: {agent_id}\n")
        return 2

    server = MCPAgentServer(
        name=str(agent["name"]),
        port=int(agent["port"]),
        project_id=str(agent["project_id"]),
        location=str(agent["location"]),
        agent_id=agent_id,
        execute_request_v1=None,
    )
    snippet = server.get_mcp_config()
    out_bytes = _dump_bytes(snippet)

    out_path = str(args.out or "").strip()
    if out_path:
        Path(out_path).write_bytes(out_bytes)

    sys.stdout.buffer.write(out_bytes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
