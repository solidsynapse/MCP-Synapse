import gc
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import keyring
from keyring.backend import KeyringBackend
from keyring.errors import PasswordDeleteError

from src.config.manager import ConfigManager
from src.data.credentials import CredentialManager
from src.data.usage_db import UsageDatabase


class InMemoryKeyring(KeyringBackend):
    priority = 1

    def __init__(self) -> None:
        self._store = {}

    def get_password(self, service, username):
        return self._store.get((service, username))

    def set_password(self, service, username, password):
        self._store[(service, username)] = password

    def delete_password(self, service, username):
        key = (service, username)
        if key in self._store:
            del self._store[key]
        else:
            raise PasswordDeleteError("Credential not found.")


def main() -> None:
    root = ROOT
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    config_path = data_dir / "config.json"
    db_path = data_dir / "usage.db"
    cred_path = data_dir / "test-credential.json"

    config_path.unlink(missing_ok=True)
    db_path.unlink(missing_ok=True)
    cred_path.unlink(missing_ok=True)

    keyring.set_keyring(InMemoryKeyring())

    with cred_path.open("w", encoding="utf-8") as handle:
        json.dump({"type": "service_account", "project_id": "test-project", "private_key": "-----BEGIN PRIVATE KEY-----\nTEST\n-----END PRIVATE KEY-----\n", "client_email": "test@example.com"}, handle)

    config_manager = ConfigManager()
    agent = config_manager.add_agent(
        name="Test Agent",
        project_id="test-project",
        location="us-central1",
        model_id="test-model",
        price_per_1m_input=1.25,
        price_per_1m_output=2.5,
    )
    fetched = config_manager.get_agent(agent["id"])
    assert fetched is not None
    assert fetched["name"] == "Test Agent"

    credential_manager = CredentialManager()
    credential_manager.save_credential(agent["id"], cred_path)
    stored = credential_manager.get_credential(agent["id"])
    assert stored is not None
    assert str(Path(stored).resolve()) == str(cred_path.resolve())
    with open(stored, "r", encoding="utf-8") as f:
        stored_json = json.load(f)
    assert stored_json["project_id"] == "test-project"

    usage_db = UsageDatabase()
    try:
        usage_db.log_usage(
            agent_id=agent["id"],
            agent_name=agent["name"],
            tokens_input=1000,
            tokens_output=500,
            cost_usd=0.0125,
        )
        total_cost = usage_db.get_total_cost()
        recent = usage_db.get_recent_usage()
        assert total_cost > 0
        assert recent
    finally:
        credential_manager.delete_credential(agent["id"])
        usage_db.close()
        del usage_db
        gc.collect()

        config_path.unlink(missing_ok=True)
        for _ in range(3):
            try:
                db_path.unlink(missing_ok=True)
                break
            except PermissionError:
                time.sleep(0.1)
        cred_path.unlink(missing_ok=True)

    print("✅ PHASE 1: ALL TESTS PASSED")


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    main()
