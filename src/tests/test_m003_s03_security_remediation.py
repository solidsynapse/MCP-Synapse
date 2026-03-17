from src.mcp_server.manager import ServerManager
from tools import headless_dispatch_v1
class _VaultMetadataStub:
    def get_entry_metadata(self, entry_id: str) -> dict[str, object]:
        assert entry_id == "vault-1"
        return {
            "id": "vault-1",
            "type": "api_key",
            "mode": "plain",
            "source_name": "",
            "managed_path_present": False,
        }


def test_m003_s03_vault_read_returns_metadata_only() -> None:
    mgr = ServerManager(vault=_VaultMetadataStub())

    result = mgr.vault_read({"entry_id": "vault-1"})

    assert result["ok"] is True
    assert result["data"] == {
        "id": "vault-1",
        "type": "api_key",
        "mode": "plain",
        "source_name": "",
        "managed_path_present": False,
    }
    assert "secret" not in result["data"]


def test_m003_s03_dispatch_invalid_json_is_generic() -> None:
    result = headless_dispatch_v1._dispatch(agent_id="agent-1", prompt="{")

    assert result["ok"] is False
    assert result["error"] == {
        "code": "dispatch_invalid_json",
        "message": "Invalid JSON request.",
    }


def test_m003_s03_public_prompt_file_error_message_is_generic() -> None:
    message = headless_dispatch_v1._public_error_message("prompt_file_read_failed")

    assert message == "Prompt file could not be read."


def test_m003_s03_error_sanitizer_redacts_secret_and_paths() -> None:
    raw = (
        "failed at C:\\Users\\Serdar\\secret.json using api_key=ABC123 "
        "and /tmp/secret/file.txt via \\\\server\\share\\creds.txt"
    )

    sanitized = ServerManager._sanitize_error_raw(raw)

    assert "ABC123" not in sanitized
    assert "C:\\Users\\Serdar\\secret.json" not in sanitized
    assert "/tmp/secret/file.txt" not in sanitized
    assert "\\\\server\\share\\creds.txt" not in sanitized
    assert sanitized.count("[REDACTED_PATH]") == 3


def test_m003_s03_headless_uses_shared_sanitizer() -> None:
    raw = "open failed for /tmp/private/input.json"

    sanitized = headless_dispatch_v1._sanitize_error_detail(raw)

    assert sanitized == "open failed for [REDACTED_PATH]"
