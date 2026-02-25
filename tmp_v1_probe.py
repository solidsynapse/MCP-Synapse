import os, time, threading, requests
from src.config.manager import ConfigManager
from src.data.credentials import CredentialManager
from src.data.usage_db import UsageDatabase
from src.mcp_server.manager import ServerManager

# stdout encoding
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

cfg = ConfigManager()
cred = CredentialManager()
usage = UsageDatabase()
mgr = ServerManager(cfg, cred, usage)

# config.json'da agent yoksa bir tane yarat
agents = cfg._read_config().get("agents", [])
if not agents:
    a = cfg.add_agent(
        name="ProbeAgent",
        project_id="test-project",
        location="us-central1",
        model_id="gemini-2.0-flash-001",
        price_per_1m_input=1.0,
        price_per_1m_output=2.0,
        port=5055,
        status="stopped",
    )
    agents = [a]

agent = agents[0]

# creds path mevcut bir json olmalı (senin ortamında var olanı kullanıyorum)
# NOT: Bu sadece path validation için. Vertex'e gerçekten gidemezse request fail olabilir; yine de routing/v1 logunu alırız.
cred_path = "data/phase2-credential.json"
cred.save_credential(agent["id"], cred_path)

# server başlat
mgr.start_agent(agent["id"])

# v1'e zorla
os.environ["MCP_ROUTER_USE_V1"] = "1"
os.environ.pop("MCP_ROUTER_V1_PCT", None)

print("agent_id=", agent["id"], "port=", agent["port"])

# MCP tool endpoint'i yerine agent_server içindeki route handler'a HTTP ile basit istek (SSE değil).
# Eğer bu endpoint yoksa/uyuşmazsa hata verir; biz yine de routing log + db varlığını kontrol edeceğiz.
import urllib.request
try:
    # agent_server Starlette mount'unda /messages/ var; burada basit bir GET ile server ayakta mı diye yoklayalım
    urllib.request.urlopen(f"http://127.0.0.1:{agent['port']}/", timeout=3).read()
except Exception as e:
    print("probe_http_error=", repr(e))

print("DONE")
