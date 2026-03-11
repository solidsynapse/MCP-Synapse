import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from src.providers.factory import ProviderFactory


def _make_context(*, agent: dict, model_id: str = "test-model", credentials_path: str = "/path/to/creds") -> SimpleNamespace:
    return SimpleNamespace(
        agent=dict(agent),
        model_id=str(model_id),
        credentials_path=str(credentials_path),
    )


def test_provider_factory_can_create_bedrock_provider():
    client = ProviderFactory.create(
        "bedrock",
        _make_context(
            agent={"aws_region": "us-east-1"},
            model_id="test-model",
            credentials_path="/path/to/creds",
        ),
    )
    assert getattr(client, "provider_id") == "bedrock"
    assert getattr(client, "model_id") == "test-model"


def test_bedrock_stream_true_raises_not_implemented():
    client = ProviderFactory.create(
        "bedrock",
        _make_context(
            agent={"aws_region": "us-east-1"},
            model_id="test-model",
            credentials_path="/path/to/creds",
        ),
    )
    with pytest.raises(NotImplementedError) as excinfo:
        client.generate_content("hello", stream=True)
    assert "streaming" in str(excinfo.value)


def test_bedrock_manual_credentials_missing_keys_raises_value_error():
    client = ProviderFactory.create(
        "bedrock",
        _make_context(
            agent={"aws_region": "us-east-1", "credential_source": "manual"},
            model_id="amazon.titan-text-express-v1",
            credentials_path="/path/to/creds",
        ),
    )
    with pytest.raises(ValueError) as excinfo:
        client.generate_content("hello", stream=False)
    msg = str(excinfo.value)
    assert "aws_access_key_id" in msg
    assert "aws_secret_access_key" in msg


def test_bedrock_dependency_imports_work():
    import importlib

    assert importlib.import_module("boto3") is not None
    assert importlib.import_module("botocore") is not None


def test_bedrock_enabled_calls_invoke_model_and_restores_env(monkeypatch, tmp_path: Path):
    import os

    creds = tmp_path / "aws_creds"
    creds.write_text("[default]\naws_access_key_id=AKIA...\naws_secret_access_key=SECRET\n", encoding="utf-8")

    class FakeBody:
        def __init__(self, b: bytes) -> None:
            self._b = b

        def read(self) -> bytes:
            return self._b

    class FakeClient:
        def invoke_model(self, *, modelId: str, contentType: str, accept: str, body: bytes):
            assert modelId == "amazon.titan-text-express-v1"
            assert contentType == "application/json"
            assert accept == "application/json"
            assert isinstance(body, (bytes, bytearray))
            assert os.environ.get("AWS_SHARED_CREDENTIALS_FILE") == str(creds)
            return {"body": FakeBody(b'{"results":[{"outputText":"ok"}]}')}

    class FakeSession:
        def __init__(self, *, region_name: str | None = None) -> None:
            self._region_name = region_name

        def client(self, service_name: str, *, region_name: str | None = None):
            assert service_name == "bedrock-runtime"
            assert region_name == "us-east-1"
            return FakeClient()

    import boto3

    monkeypatch.setattr(boto3.session, "Session", FakeSession)

    old = os.environ.get("AWS_SHARED_CREDENTIALS_FILE")
    os.environ["AWS_SHARED_CREDENTIALS_FILE"] = "sentinel"
    try:
        client = ProviderFactory.create(
            "bedrock",
            _make_context(
                agent={"aws_region": "us-east-1", "bedrock_enable_network": True},
                model_id="amazon.titan-text-express-v1",
                credentials_path=str(creds),
            ),
        )
        out = client.generate_content("hello", stream=False)
        assert out["text"] == "ok"
        assert out["tokens_input"] is None
        assert out["tokens_output"] is None
        assert out["cost_usd"] is None
        assert os.environ.get("AWS_SHARED_CREDENTIALS_FILE") == "sentinel"
    finally:
        if old is None:
            os.environ.pop("AWS_SHARED_CREDENTIALS_FILE", None)
        else:
            os.environ["AWS_SHARED_CREDENTIALS_FILE"] = old
