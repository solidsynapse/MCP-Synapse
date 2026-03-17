import json
import logging
import socket
import threading
import time
from typing import Any, Callable, List

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import EmbeddedResource, ImageContent, TextContent, Tool
from starlette.applications import Starlette
from starlette.routing import Mount, Route

from src.mcp_server.copy_config_p3_f1 import build_mcp_server_entry


logger = logging.getLogger(__name__)


class MCPAgentServer:
    def __init__(
        self,
        name: str,
        port: int,
        project_id: str,
        location: str,
        agent_id: str | None = None,
        execute_request_v1: Callable[[str, str], dict[str, object]] | None = None,
    ) -> None:
        self._name = name
        self._port = int(port)
        self._project_id = project_id
        self._location = location

        # V1 wiring (optional)
        self._agent_id = agent_id
        self._execute_request_v1 = execute_request_v1

        self._mcp = Server(name=self._name)
        self._tools = self._create_tools()
        self._register_mcp_handlers()
        self._app = self._create_app()
        self._server = None
        self._thread = None

        logger.info(
            "Initialized MCPAgentServer name=%s port=%s project_id=%s location=%s",
            self._name,
            self._port,
            self._project_id,
            self._location,
        )

    def _create_tools(self) -> List[Tool]:
        return [
            Tool(
                name="generate_text",
                description=(
                    "Generate text using the agent's configured provider and model. "
                    "Use this for ALL text generation tasks."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                        }
                    },
                    "required": ["prompt"],
                },
            )
        ]

    def _register_mcp_handlers(self) -> None:
        @self._mcp.list_tools()
        async def _list_tools():
            return self._tools

        @self._mcp.call_tool()
        async def _call_tool(name: str, arguments: dict[str, Any]):
            return self._call_tool(name, arguments)

    def _tool_error(self, code: str, message: str) -> str:
        payload = {"error": {"code": str(code), "message": str(message)}}
        return json.dumps(payload, ensure_ascii=False)

    def _call_tool(self, name: str, arguments: dict[str, Any]) -> List[TextContent]:
        if name == "generate_text":
            prompt = str(arguments.get("prompt") or "").strip()
            if not prompt:
                raise ValueError(self._tool_error("INVALID_ARGUMENT", "prompt is required"))
            return self._generate_text(prompt)
        raise ValueError(self._tool_error("UNKNOWN_TOOL", f"Unknown tool: {name}"))

    def _generate_text(self, prompt: str) -> List[TextContent]:
        agent_id = self._agent_id
        prompt_len = len(prompt)

        if not agent_id or self._execute_request_v1 is None:
            logger.error(
                "routing=v1_missing_prereq agent_id=%s prompt_len=%s",
                agent_id,
                prompt_len,
            )
            raise RuntimeError(
                self._tool_error(
                    "V1_NOT_CONFIGURED",
                    "V1 execution is not configured for this MCPAgentServer instance",
                )
            )

        logger.info(
            "routing=v1 agent_id=%s prompt_len=%s",
            agent_id,
            prompt_len,
        )
        try:
            result = self._execute_request_v1(agent_id, prompt)
        except Exception as exc:
            message = str(exc).strip() or exc.__class__.__name__
            raise RuntimeError(self._tool_error("EXECUTION_FAILED", message)) from exc

        if isinstance(result, dict):
            status = str(result.get("status") or "").strip().lower()
            if status == "error":
                message = str(
                    result.get("error")
                    or result.get("error_message")
                    or result.get("message")
                    or result.get("error_type")
                    or "Provider execution failed"
                ).strip()
                raise RuntimeError(self._tool_error("PROVIDER_ERROR", message))
            text = str(result.get("text") or result.get("output") or result.get("message") or "")
        else:
            text = str(result)

        value = str(text or "").strip()
        if not value:
            raise RuntimeError(self._tool_error("EMPTY_RESPONSE", "Provider returned empty text content"))
        return [TextContent(type="text", text=value)]


    def _create_app(self) -> Starlette:
        transport = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with transport.connect_sse(
                request.scope,
                request.receive,
                request._send,
            ) as streams:
                init_opts = self._mcp.create_initialization_options()
                await self._mcp.run(streams[0], streams[1], init_opts)

        routes = [
            Route("/sse", endpoint=handle_sse),
            Mount("/messages", app=transport.handle_post_message),
        ]
        return Starlette(routes=routes)

    def start(self) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", self._port)) == 0:
                logger.error("Port %s is already in use", self._port)
                return False

        logger.info("Starting MCPAgentServer '%s' on port %s", self._name, self._port)

        def run_server() -> None:
            try:
                import uvicorn

                config = uvicorn.Config(
                    self._app,
                    host="127.0.0.1",
                    port=self._port,
                    log_level="info",
                )
                self._server = uvicorn.Server(config)
                self._server.run()
            except Exception as exc:
                logger.exception("Error in MCPAgentServer '%s' thread: %s", self._name, exc)

        self._thread = threading.Thread(target=run_server, daemon=True)
        self._thread.start()

        deadline = time.time() + 5.0
        while time.time() < deadline:
            if self.is_running():
                logger.info("MCPAgentServer '%s' started on port %s", self._name, self._port)
                return True
            time.sleep(0.1)

        logger.error("Timed out while starting MCPAgentServer '%s' on port %s", self._name, self._port)
        return self.is_running()

    def stop(self) -> None:
        logger.info("Stopping MCPAgentServer '%s' on port %s", self._name, self._port)
        if self._server:
            self._server.should_exit = True
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self._server = None
        self._thread = None
        logger.info("MCPAgentServer '%s' stopped", self._name)

    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def get_mcp_config(self) -> dict:
        return {
            "mcpServers": {
                self._name: build_mcp_server_entry(port=self._port)
            }
        }
