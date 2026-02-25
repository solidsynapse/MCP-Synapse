import hashlib
import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from src.mcp_server.manager import ServerManager
from src.providers.factory import ProviderFactory


def _make_agent(*, provider_id: str, model_id: str) -> dict[str, Any]:
    return {
        "id": "agent-offline-pr4-1",
        "name": "Offline Fake Provider Agent PR4",
        "project_id": "offline-project",
        "location": "us-central1",
        "provider_id": provider_id,
        "model_id": model_id,
        "price_per_1m_input": 0.0,
        "price_per_1m_output": 0.0,
        "port": 5000,
        "status": "stopped",
        "streaming": False,
    }


def _normalized_hash(result: dict[str, Any]) -> str:
    normalized = dict(result)
    normalized["latency_ms"] = 0
    normalized["request_id"] = "fixed"
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compute_pr4_determinism_hash(prompt: str = "hello offline pr4") -> str:
    class FakeProviderClient:
        provider_id = "anthropic_fake"

        def __init__(self) -> None:
            self.model_id = "anthropic-fake-model-1"
            self.returned_snapshot: dict[str, Any] | None = None

        def generate_content(self, prompt: str, *, stream: bool = False) -> dict[str, Any]:
            if stream:
                raise NotImplementedError("anthropic_fake streaming not implemented")
            out = {
                "text": f"ANTHROPIC_FAKE:{prompt}",
                "tokens_input": 1,
                "tokens_output": 1,
                "cost_usd": 0.0,
            }
            self.returned_snapshot = dict(out)
            return out

    fake = FakeProviderClient()

    def _factory(_: Any) -> Any:
        return fake

    prev_factory = ProviderFactory._registry.get("anthropic_fake")
    ProviderFactory.register("anthropic_fake", _factory)
    try:
        agent = _make_agent(provider_id="anthropic_fake", model_id=fake.model_id)
        mock_config = MagicMock()
        mock_creds = MagicMock()
        mock_usage = MagicMock()
        mock_config.get_agent.return_value = agent
        mock_creds.get_credential.return_value = "unused_credentials_path"

        manager = ServerManager(config=mock_config, creds=mock_creds, usage_db=mock_usage)

        result1 = manager.execute_request_v1(agent["id"], prompt)
        result2 = manager.execute_request_v1(agent["id"], prompt)

        assert isinstance(result1, dict)
        assert "text" in result1 and str(result1["text"])
        for k in ("status", "error_type", "latency_ms", "provider", "model_id", "request_id"):
            assert k in result1

        assert result1["status"] == "success"
        assert result1["error_type"] is None
        assert result1["provider"] == "anthropic_fake"
        assert result1["model_id"] == fake.model_id
        assert result1["tokens_input"] == 1
        assert result1["tokens_output"] == 1
        assert float(result1["cost_usd"]) == 0.0

        assert fake.returned_snapshot is not None
        for reserved in ("status", "error_type", "latency_ms", "provider", "model_id", "request_id"):
            assert reserved not in fake.returned_snapshot

        h1 = _normalized_hash(result1)
        h2 = _normalized_hash(result2)
        assert h1 == h2
        return h1
    finally:
        if prev_factory is None:
            ProviderFactory._registry.pop("anthropic_fake", None)
        else:
            ProviderFactory.register("anthropic_fake", prev_factory)


def test_pr4_i0_offline_fake_provider_anthropic_end_to_end_deterministic():
    h1 = compute_pr4_determinism_hash()
    h2 = compute_pr4_determinism_hash()
    assert h1 == h2
