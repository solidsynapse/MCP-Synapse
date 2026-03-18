import json
import sqlite3
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from src.config.manager import ConfigManager
from src.data.usage_db import UsageDatabase
from src.mcp_server.manager import ServerManager
from src.providers.factory import ProviderFactory
from src.providers.rest_client import RestAPIProviderClient


class _FakeHTTPResponse:
    def __init__(self, payload: dict) -> None:
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_factory_create_rest_client() -> None:
    agent = {
        "id": "rest-agent",
        "name": "REST Agent",
        "provider_id": "rest_api",
        "endpoint": "https://api.example.com/v1/respond",
        "auth_type": "none",
        "method": "POST",
        "response_field": "data.text",
    }

    ctx = MagicMock()
    ctx.agent = agent
    ctx.model_id = "custom_rest_api"
    ctx.credentials_path = ""

    client = ProviderFactory.create("rest_api", ctx)
    assert isinstance(client, RestAPIProviderClient)


def test_rest_connection_runtime_logs_usage_row(tmp_path: Path) -> None:
    db_path = tmp_path / "rest_usage.db"
    usage_db = UsageDatabase(db_path=db_path)

    connection = {
        "id": "rest-1",
        "connection_name": "Custom REST API",
        "provider_id": "rest_api",
        "model_id": "custom_rest_api",
        "endpoint": "https://api.example.com/v1/respond",
        "options": {
            "auth_type": "none",
            "method": "POST",
            "response_field": "data.text",
        },
    }

    mock_config = MagicMock()
    mock_config.get_connection.return_value = connection
    mock_config.get_policies_persona_state.return_value = ConfigManager.default_persona_state()
    mock_config.get_policies_optimizations_state.return_value = ConfigManager.default_optimizations_state()
    mock_config.get_resilience_budget_state.return_value = ConfigManager.default_resilience_budget_state()

    manager = ServerManager(config=mock_config, usage_db=usage_db)

    payload = {"data": {"text": "REST provider ok"}}
    with patch("src.providers.rest_client.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value = _FakeHTTPResponse(payload)
        result = manager.execute_connection_request_v1("rest-1", "hello")

    assert result["text"] == "REST provider ok"
    assert result["cost_usd"] == 0.0
    assert result["cost_source"] == "UNKNOWN"

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT provider, model_id, status, cost_usd, cost_source
            FROM usage
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    assert row is not None
    assert row[0] == "rest_api"
    assert row[1] == "custom_rest_api"
    assert row[2] == "success"
    assert float(row[3]) == 0.0
    assert row[4] == "UNKNOWN"
