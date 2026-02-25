import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.config.manager import ConfigManager
from src.data.credentials import CredentialManager
from src.mcp_server.manager import ServerManager
from src.vertex.client import VertexAIClient


def main() -> None:
    print("This test will make a real Vertex AI call.")
    print("You may incur a small cost.")
    project_id = input("Enter GCP Project ID: ").strip()
    cred_path = input("Enter path to service account JSON: ").strip()
    model_id = input("Enter model ID (e.g., gemini-1.5-flash-002): ").strip() or "gemini-1.5-flash-002"
    if not project_id or not cred_path:
        print("Missing inputs.")
        return

    root = ROOT
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    config_path = data_dir / "config.json"
    db_path = data_dir / "usage.db"

    config_manager = ConfigManager()
    agent = config_manager.add_agent(
        name="Phase2 Test Agent",
        project_id=project_id,
        location="us-central1",
        model_id=model_id,
        price_per_1m_input=5.0,
        price_per_1m_output=15.0,
    )

    credential_manager = CredentialManager()
    with open(cred_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    data["_file_path"] = cred_path
    tmp_path = data_dir / "phase2-credential.json"
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle)
    credential_manager.save_credential(agent["id"], tmp_path)

    server_manager = ServerManager()
    config = server_manager.start_agent(agent["id"])
    assert config and "mcpServers" in config
    print("Server running. MCP config:", config)

    client = VertexAIClient(
        project_id=project_id,
        location="us-central1",
        model_id=model_id,
        price_per_1m_input=5.0,
        price_per_1m_output=15.0,
        credentials_path=cred_path,
    )

    result = client.generate_content("Say hello from MCP Router Phase 2")
    tokens_in = result["tokens_input"]
    tokens_out = result["tokens_output"]
    cost = float(result["cost_usd"])
    assert tokens_in >= 0
    assert tokens_out >= 0
    assert cost >= 0.0
    print(f"✅ PHASE 2: ALL TESTS PASSED (Cost: ${cost:.4f})")

    server_manager.stop_agent(agent["id"])
    credential_manager.delete_credential(agent["id"])
    config_manager.remove_agent(agent["id"])

    try:
        config_path.unlink(missing_ok=True)
    except Exception:
        pass
    for _ in range(3):
        try:
            db_path.unlink(missing_ok=True)
            break
        except PermissionError:
            time.sleep(0.1)


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    main()
