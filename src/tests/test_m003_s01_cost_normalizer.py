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


def test_cost_normalizer_uses_registered_model_prices(monkeypatch):
    registered: dict[str, dict[str, float]] = {}

    def fake_register_model(payload):
        registered.update(payload)

    def fake_completion_cost(**kwargs):
        model_data = registered[kwargs["model"]]
        return (
            kwargs["prompt_tokens"] * model_data["input_cost_per_token"]
            + kwargs["completion_tokens"] * model_data["output_cost_per_token"]
        )

    fake_litellm = SimpleNamespace(
        register_model=fake_register_model,
        completion_cost=fake_completion_cost,
    )
    monkeypatch.setattr(
        "src.providers.cost_normalizer._load_litellm_runtime",
        lambda: (fake_litellm, fake_completion_cost),
    )

    result = normalize_cost_with_litellm(
        provider_id="openai",
        model_id="gpt-4o-mini",
        tokens_input=1_000_000,
        tokens_output=1_000_000,
    )

    assert result["cost_source"] == "ESTIMATED"
    assert result["cost_usd"] == 0.75


def test_cost_normalizer_returns_unknown_when_completion_cost_fails(monkeypatch):
    def fake_completion_cost(**kwargs):
        raise RuntimeError("pricing unavailable")

    fake_litellm = SimpleNamespace(register_model=lambda payload: None, completion_cost=fake_completion_cost)
    monkeypatch.setattr(
        "src.providers.cost_normalizer._load_litellm_runtime",
        lambda: (fake_litellm, fake_completion_cost),
    )

    result = normalize_cost_with_litellm(
        provider_id="vertex",
        model_id="gemini-1.5-flash-002",
        tokens_input=50,
        tokens_output=25,
        price_per_1m_input=0.075,
        price_per_1m_output=0.30,
    )

    assert result["cost_usd"] is None
    assert result["cost_source"] == "UNKNOWN"
