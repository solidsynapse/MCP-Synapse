import sys
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from src.mcp_server.manager import ServerManager
from src.mcp_server.pipeline_v1 import ExecutionContextV1


def _make_agent() -> dict:
    return {
        "id": "agent-1",
        "name": "Test Agent",
        "project_id": "test-project",
        "location": "us-central1",
        "provider_id": "vertex",
        "model_id": "gemini-2.0-flash-001",
        "price_per_1m_input": 1.0,
        "price_per_1m_output": 2.0,
        "port": 5000,
        "status": "stopped",
    }


def test_preflight_hard_gate_agent_not_found():
    mock_config = MagicMock()
    mock_creds = MagicMock()
    mock_usage = MagicMock()
    mock_config.get_agent.return_value = None

    manager = ServerManager(config=mock_config, creds=mock_creds, usage_db=mock_usage)

    with patch("src.providers.factory.ProviderFactory.create") as mock_create:
        with pytest.raises(ValueError):
            manager.execute_request_v1("agent-1", "hello")
        mock_create.assert_not_called()


def test_preflight_hard_gate_missing_credentials():
    agent = _make_agent()
    mock_config = MagicMock()
    mock_creds = MagicMock()
    mock_usage = MagicMock()
    mock_config.get_agent.return_value = agent
    mock_creds.get_credential.return_value = None

    manager = ServerManager(config=mock_config, creds=mock_creds, usage_db=mock_usage)

    with patch("src.providers.factory.ProviderFactory.create") as mock_create:
        with pytest.raises(ValueError):
            manager.execute_request_v1(agent["id"], "hello")
        mock_create.assert_not_called()


def test_execution_context_immutability():
    agent = _make_agent()
    ctx = ExecutionContextV1(
        agent=agent,
        project_id=agent["project_id"],
        location=agent["location"],
        provider_id="vertex",
        model_id=agent["model_id"],
        credentials_path="/path/to/creds.json",
        price_per_1m_input=float(agent["price_per_1m_input"]),
        price_per_1m_output=float(agent["price_per_1m_output"]),
        streaming=False,
    )

    with pytest.raises((FrozenInstanceError, AttributeError)):
        ctx.project_id = "other-project"  # type: ignore[attr-defined]


def test_observer_isolation():
    agent = _make_agent()
    mock_config = MagicMock()
    mock_creds = MagicMock()
    mock_usage = MagicMock()
    mock_config.get_agent.return_value = agent
    mock_creds.get_credential.return_value = "/path/to/creds.json"
    mock_usage.log_usage.side_effect = Exception("DB failure")

    manager = ServerManager(config=mock_config, creds=mock_creds, usage_db=mock_usage)

    fake_result = {
        "text": "ok",
        "tokens_input": 10,
        "tokens_output": 5,
        "cost_usd": 0.123,
    }

    with patch("src.providers.vertex_client.VertexAIClient") as mock_vertex:
        mock_vertex.return_value.generate_content.return_value = fake_result

        result = manager.execute_request_v1(agent["id"], "hello")

        mock_vertex.return_value.generate_content.assert_called_once_with("hello")
        mock_usage.log_usage.assert_called_once()
        assert result == fake_result


def test_successful_end_to_end_pipeline():
    agent = _make_agent()
    mock_config = MagicMock()
    mock_creds = MagicMock()
    mock_usage = MagicMock()
    mock_config.get_agent.return_value = agent
    mock_creds.get_credential.return_value = "/path/to/creds.json"

    manager = ServerManager(config=mock_config, creds=mock_creds, usage_db=mock_usage)

    fake_result = {
        "text": "response text",
        "tokens_input": 42,
        "tokens_output": 84,
        "cost_usd": 0.456,
    }

    with patch("src.providers.vertex_client.VertexAIClient") as mock_vertex:
        mock_vertex.return_value.generate_content.return_value = fake_result

        result = manager.execute_request_v1(agent["id"], "prompt text")

        mock_vertex.return_value.generate_content.assert_called_once_with("prompt text")
        mock_usage.log_usage.assert_called_once()
        assert result == fake_result
