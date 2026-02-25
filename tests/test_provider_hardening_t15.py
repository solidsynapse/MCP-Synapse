import inspect
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from src.mcp_server.pipeline_v1 import PreflightGuardV1, ExecutionRequestV1, ProviderAdapterV1
from src.providers.factory import ProviderFactory


def _make_agent_without_provider_fields() -> dict:
    return {
        "id": "agent-1",
        "name": "Test Agent",
        "project_id": "test-project",
        "location": "us-central1",
        "model_id": "test-model",
        "price_per_1m_input": 1.0,
        "price_per_1m_output": 2.0,
        "port": 5000,
        "status": "stopped",
    }


def test_config_defaults_provider_id_and_streaming():
    agent = _make_agent_without_provider_fields()
    mock_config = MagicMock()
    mock_creds = MagicMock()
    mock_config.get_agent.return_value = agent
    mock_creds.get_credential.return_value = "/path/to/creds.json"
    request = ExecutionRequestV1(agent_id=agent["id"], prompt="hello")

    ctx = PreflightGuardV1().run(mock_config, mock_creds, request)

    assert ctx.provider_id == "vertex"
    assert ctx.streaming is False


def test_provider_factory_unknown_provider_raises_clear_error():
    with pytest.raises(ValueError) as excinfo:
        ProviderFactory.create("unknown_provider", object())
    assert "Unknown provider_id" in str(excinfo.value)


def test_provider_adapter_uses_factory_and_has_no_vertex_direct_instantiation():
    src = inspect.getsource(ProviderAdapterV1.execute)
    assert "ProviderFactory.create" in src
    assert "VertexAIClient" not in src

