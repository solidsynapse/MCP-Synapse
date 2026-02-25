import sys
from pathlib import Path
import types
import urllib.request

import pytest


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.mcp_server.persona_lite_p3_p2 import assemble_persona_lite_request


def _install_network_guards(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*args, **kwargs):
        raise AssertionError("network_call_attempted")

    monkeypatch.setattr(urllib.request, "urlopen", boom, raising=True)

    req = types.SimpleNamespace(get=boom, post=boom, request=boom)
    httpx = types.SimpleNamespace(get=boom, post=boom, request=boom, Client=object)

    monkeypatch.setitem(sys.modules, "requests", req)
    monkeypatch.setitem(sys.modules, "httpx", httpx)


def test_p3_p2_noop_when_persona_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_network_guards(monkeypatch)
    agent = {"id": "a1"}
    prompt = "hello"
    out = assemble_persona_lite_request(agent, prompt)
    assert out["messages"] == [{"role": "user", "content": "hello"}]
    assert out["provider_prompt"] == "hello"


def test_p3_p2_injects_system_when_persona_present(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_network_guards(monkeypatch)
    agent = {"id": "a1", "persona": "You are concise."}
    prompt = "hello"
    out = assemble_persona_lite_request(agent, prompt)
    assert out["messages"][0] == {"role": "system", "content": "You are concise."}
    assert out["messages"][1] == {"role": "user", "content": "hello"}
    assert out["provider_prompt"] == "You are concise.\n\nhello"


def test_p3_p2_determinism_identical_inputs(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_network_guards(monkeypatch)
    agent = {"id": "a1", "persona": "X"}
    prompt = "Y"
    a = assemble_persona_lite_request(agent, prompt)
    b = assemble_persona_lite_request(agent, prompt)
    assert a == b


def test_p3_p2_invalid_persona_type_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_network_guards(monkeypatch)
    agent = {"id": "a1", "persona": 123}
    with pytest.raises(ValueError) as exc:
        assemble_persona_lite_request(agent, "hi")
    assert str(exc.value) == "invalid_persona"
