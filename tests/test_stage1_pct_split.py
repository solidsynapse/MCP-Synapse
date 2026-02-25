import os

import pytest

from src.mcp_server.agent_server import MCPAgentServer


def _mk_server(*, agent_id="A1", has_v1=True, on_call=None):
    def stub_v1(aid: str, prompt: str):
        if on_call is not None:
            on_call(aid, prompt)
        return {"text": f"V1_OK aid={aid} len={len(prompt)}"}

    return MCPAgentServer(
        name="t",
        port=0,
        project_id="x",
        location="x",
        agent_id=agent_id,
        execute_request_v1=(stub_v1 if has_v1 else None),
    )


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("MCP_ROUTER_USE_V1", raising=False)
    monkeypatch.delenv("MCP_ROUTER_V1_PCT", raising=False)


def test_generate_text_routes_to_v1_and_does_not_retry():
    calls: list[tuple[str, str]] = []

    def on_call(aid: str, prompt: str) -> None:
        calls.append((aid, prompt))

    srv = _mk_server(agent_id="A1", has_v1=True, on_call=on_call)

    os.environ["MCP_ROUTER_USE_V1"] = "1"
    os.environ["MCP_ROUTER_V1_PCT"] = "0"

    out = srv._generate_text("hello")[0].text
    assert out.startswith("V1_OK")
    assert calls == [("A1", "hello")]


def test_generate_text_requires_v1_wiring():
    srv = _mk_server(agent_id="A1", has_v1=False)
    with pytest.raises(RuntimeError, match="V1 execution is not configured"):
        srv._generate_text("hello")
