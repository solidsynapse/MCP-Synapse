import json

import pytest

from src.mcp_server.agent_server import MCPAgentServer


def _make_server(executor):
    return MCPAgentServer(
        name="P510A-Test",
        port=0,
        project_id="test-project",
        location="us-central1",
        agent_id="test-agent",
        execute_request_v1=executor,
    )


def _parse_error(exc: Exception):
    payload = json.loads(str(exc))
    assert "error" in payload
    return payload["error"]


def test_generate_text_success_returns_non_empty_text_content():
    server = _make_server(lambda _agent_id, _prompt: {"status": "success", "text": "Birds can fly."})
    result = server._call_tool("generate_text", {"prompt": "hello"})

    assert len(result) == 1
    assert result[0].type == "text"
    assert result[0].text == "Birds can fly."


def test_generate_text_failure_returns_explicit_error_code_and_message():
    def _raise(_agent_id, _prompt):
        raise RuntimeError("Check your GCP credentials")

    server = _make_server(_raise)
    with pytest.raises(RuntimeError) as exc:
        server._call_tool("generate_text", {"prompt": "hello"})
    error = _parse_error(exc.value)

    assert error["code"] == "EXECUTION_FAILED"
    assert "Check your GCP credentials" in error["message"]


def test_generate_text_status_error_maps_to_provider_error_contract():
    server = _make_server(
        lambda _agent_id, _prompt: {"status": "error", "error_type": "APIError", "message": "Vertex AI request failed"}
    )
    with pytest.raises(RuntimeError) as exc:
        server._call_tool("generate_text", {"prompt": "hello"})
    error = _parse_error(exc.value)

    assert error["code"] == "PROVIDER_ERROR"
    assert error["message"] == "Vertex AI request failed"


def test_generate_text_requires_prompt_argument():
    server = _make_server(lambda _agent_id, _prompt: {"status": "success", "text": "ok"})
    with pytest.raises(ValueError) as exc:
        server._call_tool("generate_text", {"prompt": ""})
    error = _parse_error(exc.value)

    assert error["code"] == "INVALID_ARGUMENT"
    assert error["message"] == "prompt is required"
