import sys
from pathlib import Path
import urllib.request

import pytest


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.mcp_server.copy_config_p3_f1 import build_mcp_config, build_mcp_config_json


def _install_network_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*args, **kwargs):
        raise AssertionError("network_call_attempted")

    monkeypatch.setattr(urllib.request, "urlopen", boom, raising=True)


def test_p3_f1_builds_expected_shape_and_is_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_network_guard(monkeypatch)
    agent = {
        "id": "a1",
        "name": "AgentOne",
        "project_id": "p",
        "location": "l",
        "model_id": "m",
        "port": 5055,
        "price_per_1m_input": 0.0,
        "price_per_1m_output": 0.0,
    }
    cfg = build_mcp_config(agent)
    assert cfg == {"mcpServers": {"AgentOne": {"url": "http://localhost:5055/sse"}}}

    s = build_mcp_config_json(agent)
    assert '"project_id"' not in s
    assert '"location"' not in s
    assert '"model_id"' not in s
    assert "http://localhost:5055/sse" in s


def test_p3_f1_deterministic_json(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_network_guard(monkeypatch)
    agent = {"name": "A", "port": 5000, "project_id": "x", "location": "y", "model_id": "z"}
    a = build_mcp_config_json(agent)
    b = build_mcp_config_json(dict(agent))
    assert a == b


def test_p3_f1_missing_fields_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_network_guard(monkeypatch)
    with pytest.raises(ValueError):
        build_mcp_config_json({"port": 5000})
    with pytest.raises(ValueError):
        build_mcp_config_json({"name": "A"})
    with pytest.raises(ValueError):
        build_mcp_config_json({"name": "   ", "port": 5000})
