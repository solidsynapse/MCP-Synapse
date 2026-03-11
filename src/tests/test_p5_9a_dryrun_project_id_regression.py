from src.mcp_server.manager import ServerManager


class _DummyConfig:
    def __init__(self, connections: list[dict]) -> None:
        self._connections = list(connections)

    def list_connections(self) -> list[dict]:
        return list(self._connections)


def test_p5_9a_dry_run_uses_options_project_id_for_preflight(monkeypatch) -> None:
    connections = [
        {
            "id": "c-vertex-1",
            "connection_name": "VertexConn",
            "provider_id": "vertex",
            "model_id": "gemini-2.0-flash-001",
            "port": 5123,
            "options": {
                "project_id": "my-project-id",
                "location": "us-central1",
            },
        }
    ]
    mgr = ServerManager(config=_DummyConfig(connections))
    # Keep this test deterministic: validate preflight payload mapping only,
    # not external ADC/network availability.
    monkeypatch.setattr(mgr, "_run_vertex_preflight_probe", lambda **_kwargs: (True, None))

    result = mgr.dry_run_connection({"connection_id": "c-vertex-1"})

    errors = result.get("errors") or []
    assert "project_id is required" not in errors
    assert result.get("ok") is True
    trace = result.get("dry_run_trace") or {}
    preflight = trace.get("preflight_result") or {}
    assert preflight.get("errors_count") == 0
