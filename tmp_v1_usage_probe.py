import json
import os
from pathlib import Path

from src.config.manager import ConfigManager
from src.data.credentials import CredentialManager
from src.data.usage_db import UsageDatabase
from src.mcp_server.manager import ServerManager
from src.mcp_server.agent_server import MCPAgentServer

os.environ["MCP_ROUTER_USE_V1"] = "1"
os.environ.pop("MCP_ROUTER_V1_PCT", None)

cred_path = Path("data/phase2-credential.json")
if not cred_path.exists():
    raise SystemExit("Missing: data/phase2-credential.json")

cred = json.loads(cred_path.read_text(encoding="utf-8"))
project_id = cred.get("project_id") or cred.get("projectId") or "unknown-project"

config_mgr = ConfigManager()
usage_db = UsageDatabase()
cred_mgr = CredentialManager()
server_mgr = ServerManager(config_mgr, cred_mgr, usage_db)

agent = server_mgr.create_agent(
    name="V1 Probe",
    model_id="gemini-2.0-flash-001",
    credentials_path=str(cred_path),
    project_id=str(project_id),
)

srv = MCPAgentServer(
    name=agent["name"],
    port=0,
    project_id=agent["project_id"],
    location=agent["location"],
    agent_id=agent["id"],
    execute_request_v1=server_mgr.execute_request_v1,
)

out = srv._generate_text("ping")
print("probe_text=", getattr(out[0], "text", str(out)))
print("agent_id=", agent["id"])
print("DONE")
