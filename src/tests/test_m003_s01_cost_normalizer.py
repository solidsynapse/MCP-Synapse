from __future__ import annotations

from types import SimpleNamespace

from src.providers.cost_normalizer import normalize_cost_with_litellm


def test_cost_normalizer_returns_unknown_when_litellm_is_unavailable(monkeypatch):
    monkeypatch.setattr(
        "src.providers.cost_normalizer._load_litellm_runtime",
        lambda: (None, None),
    )

    result = normalize_cost_with_litellm(
        provider_id="openai",
        model_id="gpt-4o-mini",
        tokens_input=12,
        tokens_output=8,
    )

    assert result["cost_usd"] is None
    assert result["cost_source"] == "UNKNOWN"


def test_cost_normalizer_uses_cost_per_token_with_registered_model_prices(monkeypatch):
    registered: dict[str, dict[str, float]] = {}

    def fake_register_model(payload):
        registered.update(payload)

    def fake_cost_per_token(**kwargs):
        model_data = registered[kwargs["model"]]
        return (
            kwargs["prompt_tokens"] * model_data["input_cost_per_token"],
            kwargs["completion_tokens"] * model_data["output_cost_per_token"],
        )

    fake_litellm = SimpleNamespace(
        register_model=fake_register_model,
        cost_per_token=fake_cost_per_token,
    )
    monkeypatch.setattr(
        "src.providers.cost_normalizer._load_litellm_runtime",
        lambda: (fake_litellm, fake_cost_per_token),
    )

    result = normalize_cost_with_litellm(
        provider_id="openai",
        model_id="gpt-4o-mini",
        tokens_input=1_000_000,
        tokens_output=1_000_000,
    )

    assert result["cost_source"] == "ESTIMATED"
    assert result["cost_usd"] == 0.75


def test_cost_normalizer_falls_back_to_manual_prices_when_cost_per_token_fails(monkeypatch):
    def fake_cost_per_token(**kwargs):
        raise RuntimeError("pricing unavailable")

    fake_litellm = SimpleNamespace(register_model=lambda payload: None, cost_per_token=fake_cost_per_token)
    monkeypatch.setattr(
        "src.providers.cost_normalizer._load_litellm_runtime",
        lambda: (fake_litellm, fake_cost_per_token),
    )

    result = normalize_cost_with_litellm(
        provider_id="openai",
        model_id="gpt-4.1-mini",
        tokens_input=1_000_000,
        tokens_output=1_000_000,
    )

    assert result["cost_usd"] == 2.0
    assert result["cost_source"] == "ESTIMATED"


def test_cost_normalizer_returns_unknown_when_cost_per_token_fails_without_manual_prices(monkeypatch):
    def fake_cost_per_token(**kwargs):
        raise RuntimeError("pricing unavailable")

    fake_litellm = SimpleNamespace(register_model=lambda payload: None, cost_per_token=fake_cost_per_token)
    monkeypatch.setattr(
        "src.providers.cost_normalizer._load_litellm_runtime",
        lambda: (fake_litellm, fake_cost_per_token),
    )

    result = normalize_cost_with_litellm(
        provider_id="bedrock",
        model_id="unsupported-model",
        tokens_input=50,
        tokens_output=25,
    )

    assert result["cost_usd"] is None
    assert result["cost_source"] == "UNKNOWN"
