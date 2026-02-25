# Azure API key provisioning (Phase 1.5)

This document captures the Phase 1.5 constraint: Azure API key provisioning is performed **outside the UI**.

## What is stored
- The keyring stores an **absolute file path** (not the key itself).
- The Azure provider reads that file as UTF-8, applies strip(), and treats empty as a hard error.

## Step 1 — Create the key file
Create a UTF-8 text file that contains ONLY the raw Azure API key:

- Example path: C:\secrets\azure_api_key.txt
- Content: <RAW_AZURE_API_KEY>

## Step 2 — Write the key-file path into keyring for an agent_id
Edit the placeholders:
- <AGENT_ID>
- <ABS_KEY_FILE_PATH>

Run:

```powershell
Set-Location C:\mcp-router

$agentId = "<AGENT_ID>"
$keyFile = "<ABS_KEY_FILE_PATH>"

$env:MCP_AGENT_ID = $agentId
$env:MCP_KEY_FILE = $keyFile

@'
from src.data.credentials import CredentialManager
import keyring, os

cm = CredentialManager()
agent_id = os.environ["MCP_AGENT_ID"]
key_file = os.environ["MCP_KEY_FILE"]

service = f"{cm.SERVICE_PREFIX}_{agent_id}"
keyring.set_password(service, "credentials_path", key_file)
print("OK:", service, "-> credentials_path =", key_file)
'@ | .\venv\Scripts\python.exe

Remove-Item Env:\MCP_AGENT_ID -ErrorAction SilentlyContinue
Remove-Item Env:\MCP_KEY_FILE -ErrorAction SilentlyContinue
```

## Step 3 — Verify
```powershell
Set-Location C:\mcp-router

$agentId = "<AGENT_ID>"
$env:MCP_AGENT_ID = $agentId

@'
from src.data.credentials import CredentialManager
import os
cm = CredentialManager()
print(cm.get_credential(os.environ["MCP_AGENT_ID"]))
'@ | .\venv\Scripts\python.exe

Remove-Item Env:\MCP_AGENT_ID -ErrorAction SilentlyContinue
```

## Notes
- Phase 1.5 does NOT redesign CredentialManager.
- Phase 1.5 does NOT change routing architecture.
- Missing/invalid path MUST NOT trigger any silent fallback.
