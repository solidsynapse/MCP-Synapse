import sys
from pathlib import Path
import urllib.request

import pytest


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.providers.openai_contract_pr3 import (
    FakeOpenAIProviderClient,
    build_openai_chat_payload,
)


def _install_network_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*args, **kwargs):
        raise AssertionError("network_call_attempted")

    monkeypatch.setattr(urllib.request, "urlopen", boom, raising=True)


def test_pr3_contract_surface_and_request_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_network_guard(monkeypatch)
    payload = build_openai_chat_payload(model_id="gpt-4o-mini", prompt="hi")
    assert payload == {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "hi"}],
        "temperature": 0,
    }


def test_pr3_fake_provider_is_deterministic_and_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_network_guard(monkeypatch)
    client = FakeOpenAIProviderClient(model_id="m1")
    a = client.generate_content("Q")
    b = client.generate_content("Q")
    assert a == b
    assert a["text"] == "OPENAI_OFFLINE[m1]:Q"
    assert a["cost_usd"] is None


def test_pr3_fake_provider_streaming_is_not_supported(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_network_guard(monkeypatch)
    client = FakeOpenAIProviderClient(model_id="m1")
    with pytest.raises(NotImplementedError):
        client.generate_content("Q", stream=True)
