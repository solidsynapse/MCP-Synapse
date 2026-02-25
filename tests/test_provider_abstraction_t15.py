import sqlite3
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import uuid

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from src.data.usage_db import UsageDatabase
from src.mcp_server.manager import ServerManager
from src.providers.factory import ProviderFactory


class FakeProviderError(RuntimeError):
    pass


class FakeProviderClient:
    provider_id = "fake"

    def __init__(self, context: object) -> None:
        self.model_id = str(getattr(context, "model_id"))

    def generate_content(self, prompt: str, *, stream: bool = False) -> dict:
        if prompt == "RAISE":
            raise FakeProviderError("boom")
        return {
            "text": "fake-ok",
            "tokens_input": 1,
            "tokens_output": 2,
            "cost_usd": 0.01,
        }


def _make_agent(provider_id: str) -> dict:
    return {
        "id": "agent-1",
        "name": "Test Agent",
        "project_id": "test-project",
        "location": "us-central1",
        "provider_id": provider_id,
        "model_id": "test-model",
        "price_per_1m_input": 1.0,
        "price_per_1m_output": 2.0,
        "port": 5000,
        "status": "stopped",
    }


def test_selecting_vertex_uses_vertex_client():
    agent = _make_agent("vertex")
    mock_config = MagicMock()
    mock_creds = MagicMock()
    mock_usage = MagicMock()
    mock_config.get_agent.return_value = agent
    mock_creds.get_credential.return_value = "/path/to/creds.json"
    manager = ServerManager(config=mock_config, creds=mock_creds, usage_db=mock_usage)

    with patch("src.providers.vertex_client.VertexAIClient") as mock_vertex:
        mock_vertex.return_value.generate_content.return_value = {
            "text": "ok",
            "tokens_input": 1,
            "tokens_output": 1,
            "cost_usd": 0.01,
        }
        manager.execute_request_v1(agent["id"], "hello")

    assert mock_vertex.call_count == 1
    mock_vertex.return_value.generate_content.assert_called_once_with("hello")


def test_selecting_fake_routes_through_fake_client_and_writes_usage_row(tmp_path: Path, monkeypatch):
    monkeypatch.setitem(ProviderFactory._registry, "fake", lambda ctx: FakeProviderClient(ctx))
    agent = _make_agent("fake")
    db_path = tmp_path / "usage.db"
    usage_db = UsageDatabase(db_path=db_path)
    mock_config = MagicMock()
    mock_creds = MagicMock()
    mock_config.get_agent.return_value = agent
    mock_creds.get_credential.return_value = "/path/to/creds.json"
    manager = ServerManager(config=mock_config, creds=mock_creds, usage_db=usage_db)

    manager.execute_request_v1(agent["id"], "hello")

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT provider, model_id, status, latency_ms, request_id
            FROM usage
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    assert row is not None
    assert row[0] == "fake"
    assert row[1] == agent["model_id"]
    assert row[2] == "success"
    assert row[3] is not None and int(row[3]) >= 0
    assert row[4] is not None and uuid.UUID(str(row[4]))


def test_fake_failure_writes_error_row_and_observer_failure_does_not_mask_provider_error(
    tmp_path: Path, monkeypatch
):
    monkeypatch.setitem(ProviderFactory._registry, "fake", lambda ctx: FakeProviderClient(ctx))
    agent = _make_agent("fake")
    db_path = tmp_path / "usage.db"
    usage_db = UsageDatabase(db_path=db_path)
    mock_config = MagicMock()
    mock_creds = MagicMock()
    mock_config.get_agent.return_value = agent
    mock_creds.get_credential.return_value = "/path/to/creds.json"

    class FailingUsageDB(UsageDatabase):
        def log_usage(self, *args, **kwargs):
            raise Exception("DB failure")

    manager = ServerManager(config=mock_config, creds=mock_creds, usage_db=FailingUsageDB(db_path=db_path))

    with pytest.raises(FakeProviderError):
        manager.execute_request_v1(agent["id"], "RAISE")

    with sqlite3.connect(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM usage").fetchone()

    assert count is not None
    assert int(count[0]) == 0

    manager2 = ServerManager(config=mock_config, creds=mock_creds, usage_db=usage_db)
    with pytest.raises(FakeProviderError):
        manager2.execute_request_v1(agent["id"], "RAISE")

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT provider, model_id, status, error_type, latency_ms
            FROM usage
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    assert row is not None
    assert row[0] == "fake"
    assert row[1] == agent["model_id"]
    assert row[2] == "error"
    assert row[3] == "provider_error"
    assert row[4] is not None and int(row[4]) >= 0
