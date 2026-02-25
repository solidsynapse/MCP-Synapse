import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from src.config.manager import ConfigManager
from src.ui.main_window import _update_agent_config_fields


def _make_temp_config(tmp_path: Path) -> ConfigManager:
    cfg = ConfigManager()
    cfg._data_dir = tmp_path
    cfg._config_path = tmp_path / "config.json"
    cfg._data_dir.mkdir(parents=True, exist_ok=True)
    cfg._write_config({"agents": []})
    return cfg


def _write_agent(cfg: ConfigManager, agent: dict) -> None:
    data = cfg._read_config()
    data["agents"] = [agent]
    cfg._write_config(data)


def test_ui_config_update_does_not_mutate_provider_fields(tmp_path: Path):
    cfg = _make_temp_config(tmp_path)
    agent = {
        "id": "agent-1",
        "name": "A",
        "project_id": "p",
        "location": "us-central1",
        "model_id": "dep-1",
        "price_per_1m_input": 0.0,
        "price_per_1m_output": 0.0,
        "port": 5000,
        "status": "stopped",
        "provider_id": "azure_openai",
        "azure_endpoint": "https://example.openai.azure.com",
        "azure_api_version": "2024-02-15-preview",
    }
    _write_agent(cfg, agent)

    updated = _update_agent_config_fields(
        cfg,
        agent["id"],
        name="B",
        project_id="p2",
        model_id="dep-2",
    )
    assert updated["name"] == "B"
    assert updated["project_id"] == "p2"
    assert updated["model_id"] == "dep-2"
    assert updated.get("provider_id") == "azure_openai"
    assert updated.get("azure_endpoint") == "https://example.openai.azure.com"
    assert updated.get("azure_api_version") == "2024-02-15-preview"

    cfg2 = ConfigManager()
    cfg2._data_dir = tmp_path
    cfg2._config_path = cfg._config_path
    loaded = cfg2.get_agent(agent["id"])
    assert loaded is not None
    assert loaded.get("provider_id") == "azure_openai"
    assert loaded.get("azure_endpoint") == "https://example.openai.azure.com"
    assert loaded.get("azure_api_version") == "2024-02-15-preview"

    raw = (tmp_path / "config.json").read_text(encoding="utf-8")
    assert "SECRET" not in raw
    assert "api-key" not in raw
