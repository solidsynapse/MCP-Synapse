import sys
from pathlib import Path
import http.client
import socket
import urllib.request

import pytest


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.providers.anthropic_contract_pr4 import (
    FakeAnthropicProviderClient,
    build_anthropic_messages_payload,
)


def _install_network_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*args, **kwargs):
        raise AssertionError("network_call_attempted")

    monkeypatch.setattr(urllib.request, "urlopen", boom, raising=True)
    monkeypatch.setattr(socket, "create_connection", boom, raising=True)
    monkeypatch.setattr(http.client.HTTPConnection, "request", boom, raising=True)
    monkeypatch.setattr(http.client.HTTPSConnection, "request", boom, raising=True)

    try:
        import requests  # type: ignore

        monkeypatch.setattr(requests, "request", boom, raising=True)
    except Exception:
        pass

    try:
        import httpx  # type: ignore

        monkeypatch.setattr(httpx, "request", boom, raising=True)
    except Exception:
        pass


def test_pr4_contract_surface_and_request_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_network_guard(monkeypatch)
    payload = build_anthropic_messages_payload(
        model_id="claude-3-5-sonnet-latest",
        prompt="hi",
        max_tokens=16,
    )
    assert payload == {
        "model": "claude-3-5-sonnet-latest",
        "max_tokens": 16,
        "messages": [{"role": "user", "content": "hi"}],
        "temperature": 0,
    }


def test_pr4_fake_provider_is_deterministic_and_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_network_guard(monkeypatch)
    client = FakeAnthropicProviderClient(model_id="m1", max_tokens=16)
    a = client.generate_content("Q")
    b = client.generate_content("Q")
    assert a == b
    assert a["text"] == "ANTHROPIC_OFFLINE[m1;max_tokens=16]:Q"
    assert a["cost_usd"] is None


def test_pr4_fake_provider_streaming_is_not_supported(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_network_guard(monkeypatch)
    client = FakeAnthropicProviderClient(model_id="m1", max_tokens=16)
    with pytest.raises(NotImplementedError):
        client.generate_content("Q", stream=True)
