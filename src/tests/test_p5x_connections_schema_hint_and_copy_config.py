import json

from src.mcp_server.manager import ServerManager


class _DummyConfig:
    def __init__(self, connections: list[dict]) -> None:
        self._connections = list(connections)

    def list_connections(self) -> list[dict]:
        return list(self._connections)


def test_p5x_schema_hint_vertex_requires_project_id() -> None:
    mgr = ServerManager(config=_DummyConfig([]))
    hint = mgr.connections_schema_hint({"provider_id": "vertex"})
    assert hint["ok"] is True
    schema = hint["schema_hint"]
    fields = schema["fields"]
    assert any(f.get("id") == "project_id" and f.get("required") is True for f in fields)


def test_p5x_preflight_enforces_schema_required_fields() -> None:
    mgr = ServerManager(config=_DummyConfig([]))
    result = mgr.preflight_connection(
        {
            "connection_name": "C",
            "provider_id": "vertex",
            "model_id": "m",
        }
    )
    assert result["ok"] is False
    assert "project_id is required" in (result.get("errors") or [])


def test_p5x_copy_config_url_only_and_verbose_modes() -> None:
    connections = [
        {
            "id": "c1",
            "connection_name": "ConnOne",
            "provider_id": "openai",
            "model_id": "gpt-4o-mini",
            "port": 5123,
            "credentials_path": r"C:\secret\path.json",
        }
    ]
    mgr = ServerManager(config=_DummyConfig(connections))

    url_only = mgr.copy_connection_config({"connection_id": "c1"})
    assert url_only["ok"] is True
    cfg = json.loads(url_only["config_text"])
    assert cfg == {"mcpServers": {"ConnOne": {"url": "http://localhost:5123/sse"}}}
    assert "provider_id" not in url_only["config_text"]
    assert "credentials_path" not in url_only["config_text"]

    verbose = mgr.copy_connection_config({"connection_id": "c1", "verbose": True})
    assert verbose["ok"] is True
    cfg2 = json.loads(verbose["config_text"])
    assert cfg2["mcpServers"]["ConnOne"]["url"] == "http://localhost:5123/sse"
    assert cfg2["mcpServers"]["ConnOne"]["provider_id"] == "openai"
