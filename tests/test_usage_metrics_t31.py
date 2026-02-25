import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from src.data.usage_db import UsageDatabase
from src.mcp_server.manager import ServerManager
from src.vertex.client import APIError


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


def test_v1_success_writes_operational_row(tmp_path: Path):
    agent = _make_agent()
    db_path = tmp_path / "usage.db"
    usage_db = UsageDatabase(db_path=db_path)
    mock_config = MagicMock()
    mock_creds = MagicMock()
    mock_config.get_agent.return_value = agent
    mock_creds.get_credential.return_value = "/path/to/creds.json"
    manager = ServerManager(config=mock_config, creds=mock_creds, usage_db=usage_db)

    fake_result = {
        "text": "ok",
        "tokens_input": 10,
        "tokens_output": 5,
        "cost_usd": 0.123,
    }

    with patch("src.providers.vertex_client.VertexAIClient") as mock_vertex:
        mock_vertex.return_value.generate_content.return_value = fake_result
        manager.execute_request_v1(agent["id"], "hello")

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT status, latency_ms, error_type, request_id, provider, model_id,
                   tokens_input, tokens_output, cost_usd
            FROM usage
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    assert row is not None
    assert row[0] == "success"
    assert row[1] is not None and int(row[1]) >= 0
    assert row[2] is None
    assert row[3] is not None and str(row[3])
    assert row[4] == "vertex"
    assert row[5] == agent["model_id"]
    assert int(row[6]) == 10
    assert int(row[7]) == 5
    assert float(row[8]) == pytest.approx(0.123)


def test_v1_failure_writes_error_row_with_latency_and_error_type(tmp_path: Path):
    agent = _make_agent()
    db_path = tmp_path / "usage.db"
    usage_db = UsageDatabase(db_path=db_path)
    mock_config = MagicMock()
    mock_creds = MagicMock()
    mock_config.get_agent.return_value = agent
    mock_creds.get_credential.return_value = "/path/to/creds.json"
    manager = ServerManager(config=mock_config, creds=mock_creds, usage_db=usage_db)

    with patch("src.providers.vertex_client.VertexAIClient") as mock_vertex:
        mock_vertex.return_value.generate_content.side_effect = APIError("boom")
        with pytest.raises(APIError):
            manager.execute_request_v1(agent["id"], "hello")

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT status, latency_ms, error_type, request_id
            FROM usage
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    assert row is not None
    assert row[0] == "error"
    assert row[1] is not None and int(row[1]) >= 0
    assert row[2] == "provider_error"
    assert row[3] is not None and str(row[3])


def test_list_usage_filters_by_agent_and_date_range(tmp_path: Path):
    db_path = tmp_path / "usage.db"
    usage_db = UsageDatabase(db_path=db_path)
    now = datetime.now(timezone.utc)
    old_ts = (now - timedelta(days=10)).isoformat()
    new_ts = (now - timedelta(hours=1)).isoformat()

    usage_db.log_usage(
        agent_id="a1",
        agent_name="A",
        tokens_input=1,
        tokens_output=1,
        cost_usd=0.01,
        timestamp=old_ts,
        status="success",
    )
    usage_db.log_usage(
        agent_id="a1",
        agent_name="A",
        tokens_input=2,
        tokens_output=2,
        cost_usd=0.02,
        timestamp=new_ts,
        status="success",
    )
    usage_db.log_usage(
        agent_id="b1",
        agent_name="B",
        tokens_input=3,
        tokens_output=3,
        cost_usd=0.03,
        timestamp=new_ts,
        status="success",
    )

    start = (now - timedelta(days=1)).isoformat()
    end = now.isoformat()
    rows = usage_db.list_usage(agent_name="A", start_timestamp=start, end_timestamp=end, limit=50)

    assert len(rows) == 1
    assert rows[0]["agent_name"] == "A"
    assert rows[0]["timestamp"] == new_ts
