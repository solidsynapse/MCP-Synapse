from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Literal


CostSource = Literal["ACTUAL", "ESTIMATED", "UNKNOWN"]

_DEFAULT_OPENAI_PRICES: tuple[tuple[str, tuple[float, float]], ...] = (
    ("gpt-4o-mini", (0.15, 0.60)),
    ("gpt-4.1-mini", (0.40, 1.60)),
    ("gpt-4.1-nano", (0.10, 0.40)),
    ("gpt-4o", (2.50, 10.00)),
)

_DEFAULT_AZURE_PRICES: tuple[tuple[str, tuple[float, float]], ...] = (
    ("gpt-4o-mini", (0.165, 0.66)),
    ("gpt-4.1-mini", (0.44, 1.76)),
    ("gpt-4.1-nano", (0.11, 0.44)),
    ("gpt-4o", (2.75, 11.00)),
)

_DEFAULT_VERTEX_PRICES: tuple[tuple[str, tuple[float, float]], ...] = (
    ("gemini-2.0-flash", (0.10, 0.40)),
    ("gemini-1.5-flash", (0.075, 0.30)),
    ("gemini-3-flash", (0.20, 0.80)),
    ("gemini-3-pro", (1.25, 5.00)),
)

_DEFAULT_PRICES: dict[str, tuple[tuple[str, tuple[float, float]], ...]] = {
    "openai": _DEFAULT_OPENAI_PRICES,
    "azure_openai": _DEFAULT_AZURE_PRICES,
    "vertex": _DEFAULT_VERTEX_PRICES,
}


def _parse_positive_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except Exception:
        return None
    if parsed <= 0:
        return None
    return parsed


def _coerce_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except Exception:
        return None


def _coerce_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except Exception:
        return None


def _match_default_prices(provider_id: str, model_id: str) -> tuple[float | None, float | None]:
    model = str(model_id or "").strip().lower()
    table = _DEFAULT_PRICES.get(provider_id, ())
    for prefix, prices in table:
        if model.startswith(prefix):
            return prices
    return (None, None)


def _resolve_provider_prices(
    *,
    provider_id: str,
    model_id: str,
    agent: dict[str, Any] | None,
    price_per_1m_input: Any,
    price_per_1m_output: Any,
) -> tuple[float | None, float | None]:
    explicit_in = _parse_positive_float(price_per_1m_input)
    explicit_out = _parse_positive_float(price_per_1m_output)
    if explicit_in is not None and explicit_out is not None:
        return explicit_in, explicit_out

    agent = agent or {}
    if provider_id == "openai":
        override_in = _parse_positive_float(agent.get("openai_price_per_1m_input"))
        override_out = _parse_positive_float(agent.get("openai_price_per_1m_output"))
    elif provider_id == "azure_openai":
        override_in = _parse_positive_float(agent.get("azure_price_per_1m_input"))
        override_out = _parse_positive_float(agent.get("azure_price_per_1m_output"))
    else:
        override_in = None
        override_out = None

    if override_in is None:
        override_in = _parse_positive_float(agent.get("price_per_1m_input"))
    if override_out is None:
        override_out = _parse_positive_float(agent.get("price_per_1m_output"))
    if override_in is not None and override_out is not None:
        return override_in, override_out

    return _match_default_prices(provider_id, model_id)


def _sanitize_model_label(provider_id: str, model_id: str) -> str:
    raw = str(model_id or "").strip() or "unknown_model"
    safe = "".join(ch if ch.isalnum() else "_" for ch in raw).strip("_")
    if not safe:
        safe = "unknown_model"
    return f"mcp_synapse__{provider_id}__{safe}"


def _canonical_model_name(provider_id: str, model_id: str) -> str:
    provider = str(provider_id or "").strip().lower()
    model = str(model_id or "").strip()
    if not model:
        return model
    if provider == "azure_openai":
        return f"azure/{model}"
    if provider == "vertex":
        return f"vertex_ai/{model}"
    return model


def _custom_model_payload(
    *,
    provider_id: str,
    model_id: str,
    unit_in: float | None,
    unit_out: float | None,
) -> tuple[str, dict[str, Any] | None]:
    if unit_in is None or unit_out is None:
        return _canonical_model_name(provider_id, model_id), None
    alias = _sanitize_model_label(provider_id, model_id)
    payload = {
        "model": alias,
        "input_cost_per_token": unit_in / 1_000_000.0,
        "output_cost_per_token": unit_out / 1_000_000.0,
        "litellm_provider": provider_id,
    }
    return alias, payload


@lru_cache(maxsize=1)
def _load_litellm_runtime() -> tuple[Any | None, Any | None]:
    os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
    try:
        import litellm  # type: ignore
    except Exception:
        return None, None

    cost_per_token = getattr(litellm, "cost_per_token", None)
    if not callable(cost_per_token):
        return litellm, None
    return litellm, cost_per_token


def _try_cost_per_token(
    cost_per_token: Any,
    *,
    model_name: str,
    provider_id: str,
    tokens_input: int,
    tokens_output: int,
) -> float | None:
    attempts = (
        {
            "model": model_name,
            "prompt_tokens": tokens_input,
            "completion_tokens": tokens_output,
            "custom_llm_provider": provider_id,
        },
        {
            "model": model_name,
            "prompt_tokens": tokens_input,
            "completion_tokens": tokens_output,
        },
    )
    for kwargs in attempts:
        try:
            result = cost_per_token(**kwargs)
        except TypeError:
            continue
        except Exception:
            return None
        if isinstance(result, tuple) and len(result) == 2:
            input_cost = _coerce_float(result[0])
            output_cost = _coerce_float(result[1])
            if input_cost is None or output_cost is None:
                continue
            return input_cost + output_cost
        value = _coerce_float(result)
        if value is not None:
            return value
    return None


def _estimate_cost_from_unit_prices(
    *,
    input_tokens: int,
    output_tokens: int,
    unit_in: float | None,
    unit_out: float | None,
) -> float | None:
    if unit_in is None or unit_out is None:
        return None
    return (float(input_tokens) * (unit_in / 1_000_000.0)) + (float(output_tokens) * (unit_out / 1_000_000.0))


def normalize_cost_with_litellm(
    *,
    provider_id: str,
    model_id: str,
    tokens_input: Any,
    tokens_output: Any,
    agent: dict[str, Any] | None = None,
    price_per_1m_input: Any = None,
    price_per_1m_output: Any = None,
    actual_cost_usd: Any = None,
) -> dict[str, Any]:
    actual = _coerce_float(actual_cost_usd)
    if actual is not None:
        return {"cost_usd": float(f"{actual:.6f}"), "cost_source": "ACTUAL"}

    input_tokens = _coerce_int(tokens_input)
    output_tokens = _coerce_int(tokens_output)
    if input_tokens is None or output_tokens is None:
        return {"cost_usd": None, "cost_source": "UNKNOWN"}

    total_tokens = input_tokens + output_tokens
    if total_tokens <= 0:
        return {"cost_usd": 0.0, "cost_source": "ESTIMATED"}

    unit_in, unit_out = _resolve_provider_prices(
        provider_id=provider_id,
        model_id=model_id,
        agent=agent,
        price_per_1m_input=price_per_1m_input,
        price_per_1m_output=price_per_1m_output,
    )
    manual_cost = _estimate_cost_from_unit_prices(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        unit_in=unit_in,
        unit_out=unit_out,
    )

    litellm, cost_per_token = _load_litellm_runtime()
    if litellm is None or cost_per_token is None:
        return {"cost_usd": None, "cost_source": "UNKNOWN"}

    model_name, custom_payload = _custom_model_payload(
        provider_id=provider_id,
        model_id=model_id,
        unit_in=unit_in,
        unit_out=unit_out,
    )

    register_model = getattr(litellm, "register_model", None)
    if custom_payload is not None and callable(register_model):
        try:
            register_model({model_name: custom_payload})
        except Exception:
            return {"cost_usd": None, "cost_source": "UNKNOWN"}

    cost = _try_cost_per_token(
        cost_per_token,
        model_name=model_name,
        provider_id=provider_id,
        tokens_input=input_tokens,
        tokens_output=output_tokens,
    )
    if cost is None:
        if manual_cost is None:
            return {"cost_usd": None, "cost_source": "UNKNOWN"}
        return {"cost_usd": float(f"{manual_cost:.6f}"), "cost_source": "ESTIMATED"}
    return {"cost_usd": float(f"{cost:.6f}"), "cost_source": "ESTIMATED"}
