import logging
from typing import Dict

from src.config.manager import ConfigManager
from src.data.credentials import CredentialManager
from src.data.usage_db import UsageDatabase
from src.mcp_server.agent_server import MCPAgentServer
from src.mcp_server.pipeline_v1 import (
    ExecutionRequestV1,
    PreflightGuardV1,
    RouterV1,
    ProviderAdapterV1,
    ObserverV1,
)
from src.providers.factory import ProviderFactory
from src.mcp_server.pipeline_v1 import ExecutionContextV1


logger = logging.getLogger(__name__)


class ServerManager:
    def __init__(
        self,
        config: ConfigManager | None = None,
        creds: CredentialManager | None = None,
        usage_db: UsageDatabase | None = None,
    ) -> None:
        self._config = config or ConfigManager()
        self._creds = creds or CredentialManager()
        self._usage_db = usage_db or UsageDatabase()
        self.active_agents: Dict[str, MCPAgentServer] = {}

    def create_agent(
        self,
        name: str,
        model_id: str,
        credentials_path: str,
        project_id: str,
    ) -> dict:
        logger.info("Creating agent name=%s project_id=%s", name, project_id)
        agent = self._config.add_agent(
            name=name,
            project_id=project_id,
            location="us-central1",
            model_id=model_id,
            price_per_1m_input=0.0,
            price_per_1m_output=0.0,
            port=None,
        )
        self._creds.save_credential(agent["id"], credentials_path)

        server = MCPAgentServer(
            name=agent["name"],
            port=int(agent["port"]),
            project_id=agent["project_id"],
            location=agent["location"],
            agent_id=agent["id"],
            execute_request_v1=self.execute_request_v1,
        )
        self.active_agents[agent["id"]] = server

        logger.info(
            "Agent created id=%s name=%s port=%s",
            agent["id"],
            agent["name"],
            agent["port"],
        )
        return agent

    def start_agent(self, agent_id: str) -> dict:
        logger.info("Starting agent id=%s", agent_id)
        agent = self._config.get_agent(agent_id)
        if not agent:
            raise ValueError("Agent not found")

        server = self.active_agents.get(agent_id)
        if server is None:
            server = MCPAgentServer(
                name=agent["name"],
                port=int(agent["port"]),
                project_id=agent["project_id"],
                location=agent["location"],
                agent_id=agent_id,
                execute_request_v1=self.execute_request_v1,
            )
            self.active_agents[agent_id] = server

        started = server.start()
        if not started:
            logger.error(
                "Failed to start agent id=%s on port=%s",
                agent_id,
                agent["port"],
            )
            raise RuntimeError(f"Failed to start agent on port {agent['port']}")

        self._config.update_agent_status(agent_id, "running")
        config = server.get_mcp_config()
        logger.info("Agent id=%s started successfully", agent_id)
        return config

    def stop_agent(self, agent_id: str) -> None:
        logger.info("Stopping agent id=%s", agent_id)
        server = self.active_agents.get(agent_id)
        if server:
            server.stop()
            self._config.update_agent_status(agent_id, "stopped")
            del self.active_agents[agent_id]
            logger.info("Agent id=%s stopped", agent_id)

    def stop_all(self) -> None:
        logger.info("Stopping all agents")
        for agent_id, server in list(self.active_agents.items()):
            server.stop()
            self._config.update_agent_status(agent_id, "stopped")
            del self.active_agents[agent_id]
        logger.info("All agents stopped")

    def test_agent_connection(self, agent_id: str) -> str:
        agent = self._config.get_agent(agent_id)
        if not agent:
            raise ValueError("Agent not found")

        cred_path = self._creds.get_credential(agent_id)
        if not cred_path:
            raise ValueError("No credentials configured for agent")

        provider_id = agent.get("provider_id") or agent.get("provider") or "vertex"
        logger.info(
            "Testing provider connection for agent id=%s project_id=%s provider_id=%s",
            agent_id,
            agent["project_id"],
            provider_id,
        )

        context = ExecutionContextV1(
            agent=agent,
            project_id=agent["project_id"],
            location=agent["location"],
            provider_id=str(provider_id),
            model_id=agent["model_id"],
            credentials_path=cred_path,
            price_per_1m_input=float(agent["price_per_1m_input"]),
            price_per_1m_output=float(agent["price_per_1m_output"]),
            streaming=False,
        )
        client = ProviderFactory.create(context.provider_id, context)
        result = client.generate_content(
            "Reply with exactly three words: 'Connection is Successful'. Do not add any other text."
        )
        text = str(result.get("text", ""))
        try:
            tokens_in = int(result.get("tokens_input", 0) or 0)
            tokens_out = int(result.get("tokens_output", 0) or 0)
            cost = float(result.get("cost_usd", 0.0) or 0.0)
            try:
                self._usage_db.log_usage(
                    agent_id=agent_id,
                    agent_name=f"_test_{agent['name']}",
                    tokens_input=tokens_in,
                    tokens_output=tokens_out,
                    cost_usd=cost,
                    status="success",
                )
            except Exception as db_exc:
                logger.warning(
                    "Failed to log usage for agent id=%s: %s",
                    agent_id,
                    db_exc,
                )
        except Exception as exc:
            logger.warning(
                "Failed to extract usage metrics for agent id=%s: %s",
                agent_id,
                exc,
            )
        logger.info("Provider connection test succeeded for agent id=%s", agent_id)
        return text

    def execute_request_v1(self, agent_id: str, prompt: str, dry_run: bool = False) -> dict[str, object]:
        request = ExecutionRequestV1(agent_id=agent_id, prompt=prompt)
        preflight = PreflightGuardV1()
        context = preflight.run(self._config, self._creds, request)

        if dry_run:
            return {
                "text": "DRY_RUN_OK",
                "tokens_input": 0,
                "tokens_output": 0,
                "cost_usd": 0.0,
                "latency_ms": 0,
                "status": "success",
                "error_type": None,
                "request_id": "dry-run-id",
                "provider": context.provider_id,
                "model_id": context.model_id,
                "dry_run": True,
                "payload_summary": {
                    "provider_id": context.provider_id,
                    "model_id": context.model_id,
                    "agent_id": agent_id,
                }
            }

        router = RouterV1()
        routed_context = router.route(context)
        provider = ProviderAdapterV1()
        observer = ObserverV1()
        try:
            result = provider.execute(routed_context, prompt)
        except Exception as exc:
            error_result: dict[str, object] = {
                "text": "",
                "tokens_input": 0,
                "tokens_output": 0,
                "cost_usd": 0.0,
                "latency_ms": getattr(exc, "latency_ms", None),
                "status": "error",
                "error_type": getattr(exc, "error_type", exc.__class__.__name__),
                "request_id": getattr(exc, "request_id", None),
                "provider": getattr(exc, "provider", None),
                "model_id": getattr(exc, "model_id", routed_context.model_id),
            }
            observer.observe(self._usage_db, routed_context, error_result)
            raise
        observer.observe(self._usage_db, routed_context, result)
        return result
