from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import anyio

import mcp.types as types
from mcp.client.sse import sse_client


@dataclass(frozen=True)
class ProbeResult:
    initialize_request: dict[str, Any]
    initialize_response: dict[str, Any]
    tools_list_request: dict[str, Any]
    tools_list_response: dict[str, Any]
    tools_call_request: dict[str, Any]
    tools_call_response: dict[str, Any]


def _utc_timestamp_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _dump_json(path: Path, obj: dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


_REDACT_KEYS = {"authorization", "api_key", "apikey", "token", "secret", "password", "credentials"}


def _redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        redacted: dict[str, Any] = {}
        for k, v in obj.items():
            if isinstance(k, str) and k.lower() in _REDACT_KEYS:
                redacted[k] = "<redacted>"
            else:
                redacted[k] = _redact(v)
        return redacted
    if isinstance(obj, list):
        return [_redact(v) for v in obj]
    return obj


def _jsonrpc_message_payload(msg: types.JSONRPCMessage) -> dict[str, Any]:
    return msg.root.model_dump(by_alias=True, mode="json", exclude_none=True)


async def _send_message(
    write_stream: Any,
    msg: types.JSONRPCMessage,
) -> dict[str, Any]:
    payload = _jsonrpc_message_payload(msg)
    await write_stream.send(msg)
    return payload


async def _recv_response_for_id(
    read_stream: Any,
    request_id: str | int,
    timeout_seconds: float,
) -> dict[str, Any]:
    with anyio.fail_after(timeout_seconds):
        async for msg in read_stream:
            if isinstance(msg, Exception):
                raise msg
            root = msg.root
            if isinstance(root, (types.JSONRPCResponse, types.JSONRPCError)) and root.id == request_id:
                return _jsonrpc_message_payload(msg)
    raise RuntimeError(f"Stream closed before response id={request_id}")


def _pick_tool_and_args(tools: Iterable[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    tools_list = list(tools)
    if not tools_list:
        raise RuntimeError("tools/list returned empty tool list")

    tool = tools_list[0]
    name = str(tool.get("name", ""))
    schema = tool.get("inputSchema") or {}
    required = schema.get("required") or []
    props = schema.get("properties") or {}

    args: dict[str, Any] = {}
    if name == "generate_text":
        return name, {"prompt": "ping"}

    for req_key in required:
        prop_schema = props.get(req_key) or {}
        t = prop_schema.get("type")
        if t == "string":
            args[req_key] = "probe"
        elif t == "integer":
            args[req_key] = 0
        elif t == "number":
            args[req_key] = 0.0
        elif t == "boolean":
            args[req_key] = False
        elif t == "array":
            args[req_key] = []
        elif t == "object":
            args[req_key] = {}
        else:
            args[req_key] = "probe"

    return name, args


def _assert_jsonrpc_success(label: str, payload: dict[str, Any]) -> None:
    if "error" in payload:
        raise RuntimeError(f"{label} returned JSON-RPC error: {payload.get('error')}")


async def _run_probe(url: str, read_timeout_seconds: float) -> ProbeResult:
    async with sse_client(url=url, timeout=5, sse_read_timeout=read_timeout_seconds) as (
        read_stream,
        write_stream,
    ):
        init_id = 0
        tools_list_id = 1
        tools_call_id = 2

        init_params = {
            "protocolVersion": types.LATEST_PROTOCOL_VERSION,
            "capabilities": {"roots": {"listChanged": True}},
            "clientInfo": {"name": "mcp-router-probe", "version": "0"},
        }
        init_msg = types.JSONRPCMessage(
            types.JSONRPCRequest(
                jsonrpc="2.0",
                id=init_id,
                method="initialize",
                params=init_params,
            )
        )
        initialize_request = await _send_message(write_stream, init_msg)
        initialize_response = await _recv_response_for_id(
            read_stream, request_id=init_id, timeout_seconds=read_timeout_seconds
        )
        _assert_jsonrpc_success("initialize", initialize_response)

        initialized_msg = types.JSONRPCMessage(
            types.JSONRPCNotification(
                jsonrpc="2.0",
                method="notifications/initialized",
                params=None,
            )
        )
        await _send_message(write_stream, initialized_msg)

        tools_list_msg = types.JSONRPCMessage(
            types.JSONRPCRequest(
                jsonrpc="2.0",
                id=tools_list_id,
                method="tools/list",
                params=None,
            )
        )
        tools_list_request = await _send_message(write_stream, tools_list_msg)
        tools_list_response = await _recv_response_for_id(
            read_stream, request_id=tools_list_id, timeout_seconds=read_timeout_seconds
        )
        _assert_jsonrpc_success("tools/list", tools_list_response)

        tools = (tools_list_response.get("result") or {}).get("tools") or []
        if not isinstance(tools, list) or len(tools) == 0:
            raise RuntimeError("tools/list response did not include a non-empty tools list")

        tool_name, tool_args = _pick_tool_and_args([t for t in tools if isinstance(t, dict)])
        tools_call_msg = types.JSONRPCMessage(
            types.JSONRPCRequest(
                jsonrpc="2.0",
                id=tools_call_id,
                method="tools/call",
                params={"name": tool_name, "arguments": tool_args},
            )
        )
        tools_call_request = await _send_message(write_stream, tools_call_msg)
        tools_call_response = await _recv_response_for_id(
            read_stream, request_id=tools_call_id, timeout_seconds=read_timeout_seconds
        )

        return ProbeResult(
            initialize_request=initialize_request,
            initialize_response=initialize_response,
            tools_list_request=tools_list_request,
            tools_list_response=tools_list_response,
            tools_call_request=tools_call_request,
            tools_call_response=tools_call_response,
        )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Headless MCP SSE probe (raw JSON-RPC dumps).")
    endpoint_group = p.add_mutually_exclusive_group(required=True)
    endpoint_group.add_argument(
        "--url",
        help="MCP SSE endpoint URL (e.g. http://localhost:5055/sse).",
    )
    endpoint_group.add_argument(
        "--start-local-server",
        action="store_true",
        help="Start a local MCPAgentServer in-process and probe it.",
    )
    p.add_argument(
        "--port",
        type=int,
        default=5055,
        help="Local server port (only with --start-local-server).",
    )
    p.add_argument(
        "--server-name",
        default="ProbeServer",
        help="Local server name (only with --start-local-server).",
    )
    p.add_argument(
        "--project-id",
        default="test-project",
        help="Local server project_id (only with --start-local-server).",
    )
    p.add_argument(
        "--location",
        default="us-central1",
        help="Local server location (only with --start-local-server).",
    )
    p.add_argument(
        "--out-dir",
        default="",
        help="Output directory for dumps. Default: docs/evidence/T2X_mcp_probe_<ts>/mcp_probe/",
    )
    p.add_argument(
        "--read-timeout-seconds",
        type=float,
        default=30.0,
        help="Max seconds to wait for each JSON-RPC response.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    server = None
    if getattr(args, "start_local_server", False):
        from src.mcp_server.agent_server import MCPAgentServer

        def _execute_request_v1(agent_id: str, prompt: str) -> dict[str, object]:
            return {"text": "pong"}

        server = MCPAgentServer(
            name=str(args.server_name),
            port=int(args.port),
            project_id=str(args.project_id),
            location=str(args.location),
            agent_id="probe-agent",
            execute_request_v1=_execute_request_v1,
        )
        started = server.start()
        if not started:
            raise SystemExit(1)
        url = f"http://localhost:{int(args.port)}/sse"
    else:
        url = str(args.url or "").strip()
        if not url:
            raise SystemExit(2)

    if args.out_dir:
        out_dir = Path(args.out_dir)
    else:
        out_dir = (
            Path("docs")
            / "evidence"
            / f"T2X_mcp_probe_{_utc_timestamp_compact()}"
            / "mcp_probe"
        )

    _ensure_dir(out_dir)

    try:
        result = anyio.run(_run_probe, url, float(args.read_timeout_seconds))
    finally:
        if server is not None:
            server.stop()

    _dump_json(out_dir / "initialize.request.json", _redact(result.initialize_request))
    _dump_json(out_dir / "initialize.response.json", _redact(result.initialize_response))
    _dump_json(out_dir / "tools_list.request.json", _redact(result.tools_list_request))
    _dump_json(out_dir / "tools_list.response.json", _redact(result.tools_list_response))
    _dump_json(out_dir / "tools_call.request.json", _redact(result.tools_call_request))
    _dump_json(out_dir / "tools_call.response.json", _redact(result.tools_call_response))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
