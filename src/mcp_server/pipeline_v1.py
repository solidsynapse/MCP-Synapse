from __future__ import annotations

import logging
from dataclasses import dataclass
import time
import uuid
from typing import Any

from src.config.manager import ConfigManager
from src.data.credentials import CredentialManager
from src.data.usage_db import UsageDatabase
from src.providers.factory import ProviderFactory
from src.mcp_server.context_cache_p3_p3 import assemble_context_cached_request
from src.mcp_server.persona_lite_p3_p2 import assemble_persona_lite_request


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExecutionContextV1:
    agent: dict[str, Any]
    project_id: str
    location: str
    provider_id: str
    model_id: str
    credentials_path: str
    price_per_1m_input: float
    price_per_1m_output: float
    streaming: bool


@dataclass(frozen=True)
class ExecutionRequestV1:
    agent_id: str
    prompt: str


class PreflightGuardV1:
    def run(
        self,
        config: ConfigManager,
        creds: CredentialManager,
        request: ExecutionRequestV1,
    ) -> ExecutionContextV1:
        agent = config.get_agent(request.agent_id)
        if not agent:
            raise ValueError("Agent not found")
        cred_path = creds.get_credential(request.agent_id)
        if not cred_path:
            raise ValueError("No credentials configured for agent")
        provider_id = agent.get("provider_id") or agent.get("provider") or "vertex"
        streaming = bool(agent.get("streaming") or agent.get("stream") or False)
        return ExecutionContextV1(
            agent=agent,
            project_id=agent["project_id"],
            location=agent["location"],
            provider_id=str(provider_id),
            model_id=agent["model_id"],
            credentials_path=cred_path,
            price_per_1m_input=float(agent["price_per_1m_input"]),
            price_per_1m_output=float(agent["price_per_1m_output"]),
            streaming=streaming,
        )


class RouterV1:
    def route(self, context: ExecutionContextV1) -> ExecutionContextV1:
        return context


class ProviderAdapterV1:
    def execute(self, context: ExecutionContextV1, prompt: str) -> dict[str, Any]:
        request_id = str(uuid.uuid4())
        client = ProviderFactory.create(context.provider_id, context)
        cache_enabled = bool(context.agent.get("context_caching_enabled", True))
        if cache_enabled:
            assembled = assemble_context_cached_request(context.agent, prompt)
        else:
            assembled = assemble_persona_lite_request(context.agent, prompt)
            assembled["cache_hit"] = False
        provider_prompt = str(assembled.get("provider_prompt") or "")
        start = time.perf_counter()
        try:
            result = client.generate_content(provider_prompt, stream=context.streaming)
            latency_ms = int((time.perf_counter() - start) * 1000)
            if isinstance(result, dict):
                result["latency_ms"] = latency_ms
                result["status"] = "success"
                result["error_type"] = None
                result["request_id"] = request_id
                result["provider"] = str(getattr(client, "provider_id", context.provider_id))
                result["model_id"] = str(getattr(client, "model_id", context.model_id))
                result["context_cache_enabled"] = cache_enabled
                result["context_cache_hit"] = bool(assembled.get("cache_hit"))
            return result
        except Exception as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            try:
                setattr(exc, "latency_ms", latency_ms)
                setattr(exc, "status", "error")
                setattr(exc, "error_type", exc.__class__.__name__)
                setattr(exc, "request_id", request_id)
                setattr(exc, "provider", str(getattr(client, "provider_id", context.provider_id)))
                setattr(exc, "model_id", str(getattr(client, "model_id", context.model_id)))
            except Exception:
                pass
            raise


class ObserverV1:
    def observe(
        self,
        usage_db: UsageDatabase,
        context: ExecutionContextV1,
        result: dict[str, Any],
    ) -> None:
        try:
            tokens_in = int(result.get("tokens_input", 0) or 0)
            tokens_out = int(result.get("tokens_output", 0) or 0)
            cost = float(result.get("cost_usd", 0.0) or 0.0)
            latency_ms = result.get("latency_ms")
            status = result.get("status")
            error_type = result.get("error_type")
            request_id = result.get("request_id")
            provider = result.get("provider")
            model_id = result.get("model_id")
            usage_db.log_usage(
                agent_id=context.agent["id"],
                agent_name=context.agent["name"],
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                cost_usd=cost,
                latency_ms=int(latency_ms) if latency_ms is not None else None,
                status=str(status) if status is not None else None,
                error_type=str(error_type) if error_type is not None else None,
                request_id=str(request_id) if request_id is not None else None,
                provider=str(provider) if provider is not None else None,
                model_id=str(model_id) if model_id is not None else None,
            )
        except Exception as exc:
            logger.warning(
                "ObserverV1 failed for agent id=%s: %s",
                context.agent["id"],
                exc,
            )
