from src.mcp_server.manager import ServerManager
import src.mcp_server.manager as manager_module


class _DummyConfig:
    def __init__(self) -> None:
        self.status_updates: list[tuple[str, str]] = []

    def update_agent_status(self, agent_id: str, status: str) -> None:
        self.status_updates.append((agent_id, status))

    def list_connections(self) -> list[dict]:
        return []


class _RuntimeConfig:
    def __init__(self) -> None:
        self.updated: list[tuple[str, str, object, object]] = []
        self._connections = [
            {
                "id": "conn-1",
                "connection_name": "Wave 2 Runtime",
                "provider_id": "groq",
                "model_id": "llama-3.3-70b-versatile",
                "port": 5510,
                "status": "running",
                "runtime_pid": 4242,
                "runtime_endpoint": "http://127.0.0.1:5510/sse",
            }
        ]

    def update_agent_status(self, agent_id: str, status: str) -> None:
        return None

    def list_connections(self) -> list[dict]:
        return [dict(value) for value in self._connections]

    def update_connection_runtime(
        self,
        connection_id: str,
        status: str,
        endpoint: str | None = None,
        runtime_pid: int | None = None,
    ) -> dict | None:
        self.updated.append((connection_id, status, endpoint, runtime_pid))
        return {"id": connection_id, "status": status}


class _FakeServer:
    def __init__(self) -> None:
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


def test_stop_all_stops_agents_and_connection_runtimes(monkeypatch) -> None:
    config = _DummyConfig()
    manager = ServerManager(config=config, creds=object(), usage_db=object())
    fake_server = _FakeServer()
    manager.active_agents = {"agent-1": fake_server}

    stop_all_connections_called: list[bool] = []

    def _fake_stop_all_connections() -> dict[str, object]:
        stop_all_connections_called.append(True)
        return {"ok": True, "errors": [], "warnings": [], "connections": []}

    monkeypatch.setattr(manager, "stop_all_connections", _fake_stop_all_connections)

    manager.stop_all()

    assert fake_server.stopped is True
    assert config.status_updates == [("agent-1", "stopped")]
    assert manager.active_agents == {}
    assert stop_all_connections_called == [True]


def test_stop_all_connections_force_kills_runtime_pids(monkeypatch) -> None:
    config = _RuntimeConfig()
    manager = ServerManager(config=config, creds=object(), usage_db=object())

    terminated_pids: list[int] = []

    def _fake_terminate(pid: int) -> tuple[bool, str]:
        terminated_pids.append(int(pid))
        return True, ""

    monkeypatch.setattr(manager, "_terminate_runtime_process", _fake_terminate)
    monkeypatch.setattr(manager, "_runtime_proc_alive", lambda pid: False)
    monkeypatch.setattr(manager, "_endpoint_reachable", lambda port: False)
    monkeypatch.setattr(manager, "_listener_pid_for_port", lambda port: None)

    result = manager.stop_all_connections()

    assert result["ok"] is True
    assert terminated_pids == [4242]
    assert config.updated == [("conn-1", "stopped", None, None)]


def test_runtime_command_prefers_python_exe_on_windows(monkeypatch) -> None:
    monkeypatch.setattr(manager_module.os, "name", "nt", raising=False)
    monkeypatch.setattr(manager_module.sys, "executable", r"C:\Python311\pythonw.exe", raising=False)
    monkeypatch.setattr(manager_module.Path, "exists", lambda self: True, raising=False)

    command = ServerManager._runtime_command("conn-1", "Runtime", 5510)

    assert command[0].lower().endswith("python.exe")


def test_reset_all_connection_runtime_state_on_startup_clears_persisted_running_state(monkeypatch) -> None:
    config = _RuntimeConfig()
    manager = ServerManager(config=config, creds=object(), usage_db=object())

    terminated_pids: list[int] = []

    def _fake_terminate(pid: int) -> tuple[bool, str]:
        terminated_pids.append(int(pid))
        return True, ""

    monkeypatch.setattr(manager, "_terminate_runtime_process", _fake_terminate)
    monkeypatch.setattr(manager, "_runtime_proc_alive", lambda pid: False)
    monkeypatch.setattr(manager, "_endpoint_reachable", lambda port: False)
    monkeypatch.setattr(manager, "_listener_pid_for_port", lambda port: None)

    result = manager.reset_all_connection_runtime_state_on_startup()

    assert result["ok"] is True
    assert result["changed"] == 1
    assert terminated_pids == [4242]
    assert config.updated == [("conn-1", "stopped", None, None), ("conn-1", "stopped", None, None)]
