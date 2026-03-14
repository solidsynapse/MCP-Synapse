from __future__ import annotations

from typing import Any, Callable

from src.providers.base import ProviderClient


ProviderClientFactory = Callable[[Any], ProviderClient]


class ProviderFactory:
    _registry: dict[str, ProviderClientFactory] = {}

    @classmethod
    def register(cls, provider_id: str, factory: ProviderClientFactory) -> None:
        cls._registry[str(provider_id)] = factory

    @classmethod
    def create(cls, provider_id: str, context: Any) -> ProviderClient:
        provider_key = str(provider_id or "vertex")
        factory = cls._registry.get(provider_key)
        if factory is None:
            raise ValueError(f"Unknown provider_id: {provider_key}")
        return factory(context)


def _vertex_factory(context: Any) -> ProviderClient:
    from src.providers.vertex_client import VertexProviderClient

    return VertexProviderClient(
        project_id=str(getattr(context, "project_id")),
        location=str(getattr(context, "location")),
        model_id=str(getattr(context, "model_id")),
        price_per_1m_input=float(getattr(context, "price_per_1m_input")),
        price_per_1m_output=float(getattr(context, "price_per_1m_output")),
        credentials_path=str(getattr(context, "credentials_path")),
    )


ProviderFactory.register("vertex", _vertex_factory)


def _azure_openai_factory(context: Any) -> ProviderClient:
    from src.providers.azure_openai_client import AzureOpenAIProviderClient

    agent = getattr(context, "agent")
    return AzureOpenAIProviderClient(
        agent=dict(agent),
        model_id=str(getattr(context, "model_id")),
        api_key_path=str(getattr(context, "credentials_path")),
    )


ProviderFactory.register("azure_openai", _azure_openai_factory)


def _bedrock_factory(context: Any) -> ProviderClient:
    from src.providers.bedrock_client import BedrockProviderClient

    agent = getattr(context, "agent")
    return BedrockProviderClient(
        agent=dict(agent),
        model_id=str(getattr(context, "model_id")),
        credentials_path=str(getattr(context, "credentials_path")),
    )


ProviderFactory.register("bedrock", _bedrock_factory)


def _huggingface_factory(context: Any) -> ProviderClient:
    from src.providers.huggingface_client import HuggingFaceProviderClient

    agent = getattr(context, "agent")
    return HuggingFaceProviderClient(
        agent=dict(agent),
        model_id=str(getattr(context, "model_id")),
        credentials_path=str(getattr(context, "credentials_path")),
    )


ProviderFactory.register("huggingface", _huggingface_factory)


def _ollama_factory(context: Any) -> ProviderClient:
    from src.providers.ollama_client import OllamaProviderClient

    agent = getattr(context, "agent")
    return OllamaProviderClient(
        agent=dict(agent),
        model_id=str(getattr(context, "model_id")),
    )


ProviderFactory.register("ollama", _ollama_factory)


def _openai_factory(context: Any) -> ProviderClient:
    from src.providers.openai_client import OpenAIProviderClient

    agent = getattr(context, "agent")
    return OpenAIProviderClient(
        agent=dict(agent),
        model_id=str(getattr(context, "model_id")),
        api_key_path=str(getattr(context, "credentials_path")),
    )


ProviderFactory.register("openai", _openai_factory)
