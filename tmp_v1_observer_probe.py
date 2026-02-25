import os
import json
from pathlib import Path

from src.config.manager import ConfigManager
from src.data.credentials import CredentialManager
from src.data.usage_db import UsageDatabase
from src.mcp_server.pipeline_v1 import ExecutionRequestV1, PreflightGuardV1, RouterV1, ObserverV1

os.environ["MCP_ROUTER_USE_V1"] = "1"
os.environ.pop("MCP_ROUTER_V1_PCT", None)

cred_path = Path("data/phase2-credential.json")
if not cred_path.exists():
    raise SystemExit("Missing: data/phase2-credential.json")

cred = json.loads(cred_path.read_text(encoding="utf-8"))
project_id = cred.get("project_id") or cred.get("projectId") or "unknown-project"

config = ConfigManager()
creds = CredentialManager()
usage_db = UsageDatabase()

# Agent + credential kaydı oluştur (preflight bununla context üretecek)
agent = config.add_agent(
    name="V1 Probe (no-vertex)",
    project_id=str(project_id),
    location="us-central1",
    model_id="gemini-2.0-flash-001",
    price_per_1m_input=1.25,
    price_per_1m_output=2.5,
)
creds.save_credential(agent["id"], str(cred_path))

# V1 context üret (Preflight -> Router)
request = ExecutionRequestV1(agent_id=agent["id"], prompt="ping")
ctx = PreflightGuardV1().run(config, creds, request)
ctx = RouterV1().route(ctx)

# Provider yerine dummy result ver ve Observer ile DB’ye yazdır
dummy = {"text": "dummy-ok", "tokens_input": 10, "tokens_output": 5, "cost_usd": 0.000123, "latency_ms": 42}
ObserverV1().observe(usage_db, ctx, dummy)

print("DONE agent_id=", agent["id"])
