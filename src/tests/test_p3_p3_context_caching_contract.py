import sys
from pathlib import Path
import types
import urllib.request

import pytest


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.mcp_server.context_cache_p3_p3 import (
    assemble_context_cached_request,
    reset_context_cache_for_tests,
)


def _install_network_guards(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*args, **kwargs):
        raise AssertionError("network_call_attempted")

    monkeypatch.setattr(urllib.request, "urlopen", boom, raising=True)

    req = types.SimpleNamespace(get=boom, post=boom, request=boom)
    httpx = types.SimpleNamespace(get=boom, post=boom, request=boom, Client=object)

    monkeypatch.setitem(sys.modules, "requests", req)
    monkeypatch.setitem(sys.modules, "httpx", httpx)


def test_p3_p3_noop_when_caching_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_network_guards(monkeypatch)
    reset_context_cache_for_tests()
    agent = {"id": "a1"}
    out1 = assemble_context_cached_request(agent, "hello")
    out2 = assemble_context_cached_request(agent, "hello")
    assert out1["messages"] == [{"role": "user", "content": "hello"}]
    assert out1["provider_prompt"] == "hello"
    assert out1 == out2


def test_p3_p3_cache_hit_returns_identical_assembled_request(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_network_guards(monkeypatch)
    reset_context_cache_for_tests()
    agent = {"id": "a1", "persona": "P"}
    out1 = assemble_context_cached_request(agent, "Q")
    out2 = assemble_context_cached_request(agent, "Q")
    assert out1["messages"] == out2["messages"]
    assert out1["provider_prompt"] == out2["provider_prompt"]
    assert out1.get("cache_hit") is False
    assert out2.get("cache_hit") is True


def test_p3_p3_cache_miss_recomputes(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_network_guards(monkeypatch)
    reset_context_cache_for_tests()
    agent = {"id": "a1", "persona": "P"}
    out1 = assemble_context_cached_request(agent, "Q1")
    out2 = assemble_context_cached_request(agent, "Q2")
    assert out1["provider_prompt"] != out2["provider_prompt"]
    assert out1.get("cache_hit") is False
    assert out2.get("cache_hit") is False


def test_p3_p3_determinism_same_input_same_output(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_network_guards(monkeypatch)
    reset_context_cache_for_tests()
    agent = {"id": "a1", "persona": "P"}
    a = assemble_context_cached_request(agent, "Q")
    reset_context_cache_for_tests()
    b = assemble_context_cached_request(agent, "Q")
    assert a["messages"] == b["messages"]
    assert a["provider_prompt"] == b["provider_prompt"]
