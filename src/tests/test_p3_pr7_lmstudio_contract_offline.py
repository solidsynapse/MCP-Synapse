import sys
from pathlib import Path
import http.client
import socket
import urllib.request

import pytest


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.providers.lmstudio_contract_pr7 import (
    FakeLMStudioProviderClient,
    build_lmstudio_chat_payload,
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


def test_pr7_contract_surface_and_request_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_network_guard(monkeypatch)
    payload = build_lmstudio_chat_payload(model_id="local-model", prompt="hi")
    assert payload == {
        "model": "local-model",
        "messages": [{"role": "user", "content": "hi"}],
        "temperature": 0,
    }


def test_pr7_fake_provider_is_deterministic_and_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_network_guard(monkeypatch)
    client = FakeLMStudioProviderClient(model_id="m1")
    a = client.generate_content("Q")
    b = client.generate_content("Q")
    assert a == b
    assert a["text"] == "LMSTUDIO_OFFLINE[m1]:Q"
    assert a["cost_usd"] is None


def test_pr7_fake_provider_streaming_is_not_supported(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_network_guard(monkeypatch)
    client = FakeLMStudioProviderClient(model_id="m1")
    with pytest.raises(NotImplementedError):
        client.generate_content("Q", stream=True)
