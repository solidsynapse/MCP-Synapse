import io
import json
import sqlite3
import sys
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from src.data.usage_db import UsageDatabase
from src.mcp_server.manager import ServerManager
from src.providers.factory import ProviderFactory
from src.providers.gemini_client import GeminiHTTPError, GeminiProviderClient


def _make_agent() -> dict:
    return {
        "id": "agent-gemini",
        "name": "Gemini Agent",
        "project_id": "unused",
        "location": "unused",
        "provider_id": "gemini",
        "model_id": "gemini-2.0-flash",
        "price_per_1m_input": 0.0,
        "price_per_1m_output": 0.0,
        "port": 5000,
        "status": "stopped",
        "gemini_base_url": "https://generativelanguage.googleapis.com/v1beta",
    }


class _FakeHTTPResponse:
    def __init__(self, payload: dict) -> None:
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_factory_create_gemini_returns_client(tmp_path: Path):
    agent = _make_agent()
    key_file = tmp_path / "key.txt"
    key_file.write_text("k", encoding="utf-8")

    ctx = MagicMock()
    ctx.agent = agent
    ctx.model_id = agent["model_id"]
    ctx.credentials_path = str(key_file)

    client = ProviderFactory.create("gemini", ctx)
    assert isinstance(client, GeminiProviderClient)


def test_gemini_success_logs_usage_row(tmp_path: Path):
    agent = _make_agent()
    key_file = tmp_path / "key.txt"
    key_file.write_text("k", encoding="utf-8")
    db_path = tmp_path / "usage.db"
    usage_db = UsageDatabase(db_path=db_path)

    mock_config = MagicMock()
    mock_creds = MagicMock()
    mock_config.get_agent.return_value = agent
    mock_creds.get_credential.return_value = str(key_file)
    manager = ServerManager(config=mock_config, creds=mock_creds, usage_db=usage_db)

    payload = {
        "candidates": [{"content": {"parts": [{"text": "hi"}]}}],
        "usageMetadata": {"promptTokenCount": 3, "candidatesTokenCount": 5},
    }
    with patch("src.providers.gemini_client.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value = _FakeHTTPResponse(payload)
        result = manager.execute_request_v1(agent["id"], "hello")

    assert result["text"] == "hi"
    assert result["tokens_input"] == 3
    assert result["tokens_output"] == 5
    assert result["cost_source"] in {"UNKNOWN", "ESTIMATED"}

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT provider, model_id, status, latency_ms, request_id, error_type
            FROM usage
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    assert row is not None
    assert row[0] == "gemini"
    assert row[1] == agent["model_id"]
    assert row[2] == "success"
    assert row[3] is not None and int(row[3]) >= 0
    assert row[4] is not None and str(row[4])
    assert row[5] is None


@pytest.mark.parametrize("status_code", [401, 403])
def test_gemini_http_error_raises_and_logs_error_row(tmp_path: Path, status_code: int):
    agent = _make_agent()
    key_file = tmp_path / "key.txt"
    key_file.write_text("k", encoding="utf-8")
    db_path = tmp_path / "usage.db"
    usage_db = UsageDatabase(db_path=db_path)

    mock_config = MagicMock()
    mock_creds = MagicMock()
    mock_config.get_agent.return_value = agent
    mock_creds.get_credential.return_value = str(key_file)
    manager = ServerManager(config=mock_config, creds=mock_creds, usage_db=usage_db)

    body = io.BytesIO(b'{"error":"invalid"}')
    http_err = urllib.error.HTTPError(
        url="https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
        code=status_code,
        msg="Unauthorized",
        hdrs=None,
        fp=body,
    )

    with patch("src.providers.gemini_client.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = http_err
        with pytest.raises(GeminiHTTPError) as excinfo:
            manager.execute_request_v1(agent["id"], "hello")

    assert f"HTTP {status_code}:" in str(excinfo.value)

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT provider, status, error_type, latency_ms
            FROM usage
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    assert row is not None
    assert row[0] == "gemini"
    assert row[1] == "error"
    assert row[2] == "provider_error"
    assert row[3] is not None and int(row[3]) >= 0


def test_gemini_streaming_raises_and_logs_error_row(tmp_path: Path):
    agent = _make_agent()
    agent["streaming"] = True
    key_file = tmp_path / "key.txt"
    key_file.write_text("k", encoding="utf-8")
    db_path = tmp_path / "usage.db"
    usage_db = UsageDatabase(db_path=db_path)

    mock_config = MagicMock()
    mock_creds = MagicMock()
    mock_config.get_agent.return_value = agent
    mock_creds.get_credential.return_value = str(key_file)
    manager = ServerManager(config=mock_config, creds=mock_creds, usage_db=usage_db)

    with patch("src.providers.gemini_client.urllib.request.urlopen") as mock_urlopen:
        with pytest.raises(NotImplementedError) as excinfo:
            manager.execute_request_v1(agent["id"], "hello")
        assert str(excinfo.value) == "gemini streaming not implemented"
        mock_urlopen.assert_not_called()

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT provider, status, error_type, latency_ms
            FROM usage
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    assert row is not None
    assert row[0] == "gemini"
    assert row[1] == "error"
    assert row[2] == "provider_error"
    assert row[3] is not None and int(row[3]) >= 0
