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
from src.providers.deepseek_client import DeepSeekHTTPError, DeepSeekProviderClient
from src.providers.factory import ProviderFactory
from src.providers.openrouter_client import OpenRouterHTTPError, OpenRouterProviderClient
from src.providers.xai_client import XAIHTTPError, XAIProviderClient


def _make_agent(provider_id: str) -> dict:
    base_urls = {
        "openrouter": "https://api.openrouter.ai/v1",
        "deepseek": "https://api.deepseek.com/v1",
        "xai": "https://api.x.ai/v1",
    }
    model_ids = {
        "openrouter": "openai/gpt-4o-mini",
        "deepseek": "deepseek-chat",
        "xai": "grok-2-latest",
    }
    agent = {
        "id": f"agent-{provider_id}",
        "name": f"{provider_id.title()} Agent",
        "project_id": "unused",
        "location": "unused",
        "provider_id": provider_id,
        "model_id": model_ids[provider_id],
        "price_per_1m_input": 0.0,
        "price_per_1m_output": 0.0,
        "port": 5000,
        "status": "stopped",
        f"{provider_id}_base_url": base_urls[provider_id],
    }
    if provider_id == "openrouter":
        agent["openrouter_http_referer"] = "https://example.test"
        agent["openrouter_x_title"] = "MCP Synapse Test"
    return agent


class _FakeHTTPResponse:
    def __init__(self, payload: dict) -> None:
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.mark.parametrize(
    ("provider_id", "client_cls"),
    [
        ("openrouter", OpenRouterProviderClient),
        ("deepseek", DeepSeekProviderClient),
        ("xai", XAIProviderClient),
    ],
)
def test_factory_create_openai_compatible_wave2_client(
    tmp_path: Path, provider_id: str, client_cls: type
):
    agent = _make_agent(provider_id)
    key_file = tmp_path / f"{provider_id}.txt"
    key_file.write_text("k", encoding="utf-8")

    ctx = MagicMock()
    ctx.agent = agent
    ctx.model_id = agent["model_id"]
    ctx.credentials_path = str(key_file)

    client = ProviderFactory.create(provider_id, ctx)
    assert isinstance(client, client_cls)


@pytest.mark.parametrize("provider_id", ["openrouter", "deepseek", "xai"])
def test_openai_compatible_wave2_success_logs_usage_row(tmp_path: Path, provider_id: str):
    agent = _make_agent(provider_id)
    key_file = tmp_path / f"{provider_id}.txt"
    key_file.write_text("k", encoding="utf-8")
    db_path = tmp_path / f"{provider_id}.db"
    usage_db = UsageDatabase(db_path=db_path)

    mock_config = MagicMock()
    mock_creds = MagicMock()
    mock_config.get_agent.return_value = agent
    mock_creds.get_credential.return_value = str(key_file)
    manager = ServerManager(config=mock_config, creds=mock_creds, usage_db=usage_db)

    payload = {
        "choices": [{"message": {"content": "hi"}}],
        "usage": {"prompt_tokens": 3, "completion_tokens": 5},
    }
    with patch(f"src.providers.{provider_id}_client.urllib.request.urlopen") as mock_urlopen:
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
    assert row[0] == provider_id
    assert row[1] == agent["model_id"]
    assert row[2] == "success"
    assert row[3] is not None and int(row[3]) >= 0
    assert row[4] is not None and str(row[4])
    assert row[5] is None


@pytest.mark.parametrize(
    ("provider_id", "error_cls", "url"),
    [
        ("openrouter", OpenRouterHTTPError, "https://api.openrouter.ai/v1/chat/completions"),
        ("deepseek", DeepSeekHTTPError, "https://api.deepseek.com/v1/chat/completions"),
        ("xai", XAIHTTPError, "https://api.x.ai/v1/chat/completions"),
    ],
)
@pytest.mark.parametrize("status_code", [401, 403])
def test_openai_compatible_wave2_http_error_raises_and_logs_error_row(
    tmp_path: Path,
    provider_id: str,
    error_cls: type,
    url: str,
    status_code: int,
):
    agent = _make_agent(provider_id)
    key_file = tmp_path / f"{provider_id}.txt"
    key_file.write_text("k", encoding="utf-8")
    db_path = tmp_path / f"{provider_id}.db"
    usage_db = UsageDatabase(db_path=db_path)

    mock_config = MagicMock()
    mock_creds = MagicMock()
    mock_config.get_agent.return_value = agent
    mock_creds.get_credential.return_value = str(key_file)
    manager = ServerManager(config=mock_config, creds=mock_creds, usage_db=usage_db)

    body = io.BytesIO(b'{"error":"invalid"}')
    http_err = urllib.error.HTTPError(
        url=url,
        code=status_code,
        msg="Unauthorized",
        hdrs=None,
        fp=body,
    )

    with patch(f"src.providers.{provider_id}_client.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = http_err
        with pytest.raises(error_cls) as excinfo:
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
    assert row[0] == provider_id
    assert row[1] == "error"
    assert row[2] == "provider_error"
    assert row[3] is not None and int(row[3]) >= 0


@pytest.mark.parametrize("provider_id", ["openrouter", "deepseek", "xai"])
def test_openai_compatible_wave2_streaming_raises_and_logs_error_row(
    tmp_path: Path, provider_id: str
):
    agent = _make_agent(provider_id)
    agent["streaming"] = True
    key_file = tmp_path / f"{provider_id}.txt"
    key_file.write_text("k", encoding="utf-8")
    db_path = tmp_path / f"{provider_id}.db"
    usage_db = UsageDatabase(db_path=db_path)

    mock_config = MagicMock()
    mock_creds = MagicMock()
    mock_config.get_agent.return_value = agent
    mock_creds.get_credential.return_value = str(key_file)
    manager = ServerManager(config=mock_config, creds=mock_creds, usage_db=usage_db)

    with patch(f"src.providers.{provider_id}_client.urllib.request.urlopen") as mock_urlopen:
        with pytest.raises(NotImplementedError) as excinfo:
            manager.execute_request_v1(agent["id"], "hello")
        assert str(excinfo.value) == f"{provider_id} streaming not implemented"
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
    assert row[0] == provider_id
    assert row[1] == "error"
    assert row[2] == "provider_error"
    assert row[3] is not None and int(row[3]) >= 0
