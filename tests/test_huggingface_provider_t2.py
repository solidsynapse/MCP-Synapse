import pytest

from src.providers.factory import ProviderFactory


class _Ctx:
    def __init__(self, agent: dict, model_id: str, credentials_path: str):
        self.agent = agent
        self.model_id = model_id
        self.credentials_path = credentials_path


def test_hf_stream_true_raises():
    client = ProviderFactory.create(
        "huggingface",
        _Ctx(agent={"hf_enable_network": True}, model_id="gpt2", credentials_path="C:\\dummy.txt"),
    )
    with pytest.raises(NotImplementedError) as excinfo:
        client.generate_content("hello", stream=True)
    assert "streaming" in str(excinfo.value)


def test_hf_gate_disabled_raises():
    client = ProviderFactory.create(
        "huggingface",
        _Ctx(agent={"hf_enable_network": False}, model_id="gpt2", credentials_path="C:\\dummy.txt"),
    )
    with pytest.raises(NotImplementedError) as excinfo:
        client.generate_content("hello", stream=False)
    msg = str(excinfo.value).lower()
    assert "gate" in msg
    assert "hf_enable_network" in msg
