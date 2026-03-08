# Hugging Face -> MCP Synapse -> Local IDE (MCP) User Guide

This guide shows how to run **Hugging Face Router (OpenAI-compatible)** models through **MCP Synapse** and consume the connection from a **local IDE MCP client** (agent/coder).

> Scope (current implementation)
>
> - Hugging Face access path: **OpenAI-compatible chat (non-streaming)** via `https://router.huggingface.co/v1`
> - Auth: **Hugging Face Access Token**
> - Safety rail: **HF network gate** (explicit allow) must be enabled per-connection.

---

## Table of contents

1. [Prerequisites](#prerequisites)
2. [Step 1 - Create a Hugging Face access token](#step-1--create-a-hugging-face-access-token)
3. [Step 2 - Choose a model ID that the HF router can serve](#step-2--choose-a-model-id-that-the-hf-router-can-serve)
4. [Step 3 - Create a Hugging Face connection in MCP Synapse](#step-3--create-a-hugging-face-connection-in-mcp-synapse)
5. [Step 4 - Export MCP config and connect your IDE](#step-4--export-mcp-config-and-connect-your-ide)
6. [Step 5 - Validate end-to-end (Synapse + IDE)](#step-5--validate-end-to-end-synapse--ide)
7. [Troubleshooting](#troubleshooting)
8. [Security & hygiene](#security--hygiene)

---

## Prerequisites

- A Hugging Face account.
- **MCP Synapse** installed and running locally.
- A local IDE/client that supports **MCP** and allows pasting/editing an MCP server config snippet.
- Outbound HTTPS access to:
  - `https://router.huggingface.co`
  - `https://huggingface.co` (optional, for token validation endpoints)

---

## Step 1 - Create a Hugging Face access token

1. Open Hugging Face **Settings -> Access Tokens**.
2. Create a new token.
3. Recommended settings:
   - **Token type:** *Fine-grained* (recommended) or *Read* (if available).
   - **Permissions:** ensure **Inference** calls are allowed.
     - If you see multiple "Inference" checkboxes, enable the one that allows **making calls** (not just managing endpoints).

4. Copy the token value **once** (HF shows it only at creation time).
5. Save it **locally** as a plain text file containing **only the token** on a single line, e.g.:

   ```text
   hf_*************************************
   ```

### Token file location recommendation

- Windows: `C:\Users\<you>\Desktop\HF_TOKEN.txt` (temporary) -> move to a safer folder later.
- Never commit this file to git.
- If MCP Synapse Vault is available, you can store it there instead of a local file (recommended).

### Quick token self-check (optional)

In PowerShell:

```powershell
$token = (Get-Content C:\path\to\HF_TOKEN.txt -Raw).Trim()
Invoke-RestMethod -Method Get `
  -Uri "https://huggingface.co/api/whoami-v2" `
  -Headers @{ Authorization = "Bearer $token" }
```

If it returns your username, the token is valid.

---

## Step 2 - Choose a model ID that the HF router can serve

MCP Synapse uses the **OpenAI-compatible** Hugging Face router. The easiest way to confirm available models is to list them via the router API:

```powershell
$token = (Get-Content C:\path\to\HF_TOKEN.txt -Raw).Trim()
$r = Invoke-RestMethod -Method Get `
  -Uri "https://router.huggingface.co/v1/models" `
  -Headers @{ Authorization = "Bearer $token" }

$r.data | Select-Object -First 30 id | Format-Table -AutoSize
```

### Model ID formats you may see

- Basic: `meta-llama/Llama-3.1-8B-Instruct`
- Provider-pinned (recommended when routing is unstable):
  - `deepseek-ai/DeepSeek-R1-0528:together`
  - `meta-llama/Llama-3.1-8B-Instruct:novita`

**Why provider-pinned can matter:**
Some providers behind the router may be blocked or unavailable from your network/region and return errors like **403**. Pinning to a provider that works for you avoids "random provider selection."

### Recommendation (practical)

Start with a smaller, commonly available model from the router list, then upgrade later.

- Good starting point: a listed `meta-llama/*` or `Qwen/*` model.
- If you see 403/Cloudflare blocks, retry the same model **with a provider suffix** (e.g., `:together`, `:novita`).

---

## Step 3 - Create a Hugging Face connection in MCP Synapse

Open **MCP Synapse -> Connections -> New Connection** and select **Hugging Face**.

Fill the form:

### Required

- **Connection name:** stable identifier (used in exported MCP config)
  - Example: `HFtest`
- **Model ID:** pick from `GET /v1/models`
  - Example: `deepseek-ai/DeepSeek-R1-0528:together`
  - or `meta-llama/Llama-3.1-8B-Instruct:novita`
- **Credentials path:** point to your token file
  - Example: `C:\Users\<you>\Secrets\HF_TOKEN.txt`
  - or click **Vault** and select the stored secret
- **Enable HF network calls:** **Enabled**
  - This is the safety gate. If left **Disabled**, live calls are blocked.

### Optional

- **Endpoint / Base URL:** leave blank to use default,
  or set explicitly to:

  ```text
  https://router.huggingface.co/v1
  ```

> Tip: If you see a 404 later, verify your base URL ends with `/v1`.

### Validate with Preflight

- Click **Preflight**.
- Expected:
  - **PASS** when network calls are Enabled and the token path resolves.
  - **FAIL** when network calls are Disabled.

### Create

- Click **Create Connection**.

---

## Step 4 - Export MCP config and connect your IDE

In **Connections**, locate your HF connection row and click **Copy** (or **Copy config**) to copy the MCP server snippet.

### Add to your IDE MCP config

Where you paste depends on the IDE, but typically you maintain an `mcpServers` JSON object.

1. Open the IDE's MCP config file/location.
2. Paste/merge the snippet under `mcpServers`.
3. Save + reload the IDE so the MCP server restarts.

**Verify in the IDE:**

- A tool appears under the server name (e.g., `HFtest/generate_text`).

---

## Step 5 - Validate end-to-end (Synapse + IDE)

### A) IDE smoke test

Send a trivial prompt through the MCP tool:

- `hi`
- `how are you?`

Expected: a normal model response.

### B) Synapse runtime observability

In MCP Synapse:

- **Dashboard** shows request count increasing.
- **Usage / Summary** lists **provider = huggingface** and your connection.
- **History** shows the request rows and filters work.

---

## Troubleshooting

### 1) "huggingface network gate is disabled"

**Cause:** Safety rail is working; outbound HF calls are blocked.

**Fix:** Edit the connection -> set **Enable HF network calls = Enabled** -> Save -> retry.

---

### 2) HTTP 404: Not Found

Common causes:

- Base URL missing `/v1`
- Wrong path used (must be `/v1/chat/completions` for OpenAI-compatible)

**Fix checklist**

1. Set endpoint explicitly to `https://router.huggingface.co/v1`
2. Confirm your model ID exists in `GET /v1/models`
3. Smoke test direct call:

```powershell
$token = (Get-Content C:\path\to\HF_TOKEN.txt -Raw).Trim()
$headers = @{ Authorization = "Bearer $token"; "Content-Type"="application/json" }
$body = @{ model="meta-llama/Llama-3.1-8B-Instruct"; messages=@(@{role="user"; content="hi"}) } |
  ConvertTo-Json -Depth 6

Invoke-RestMethod -Method Post `
  -Uri "https://router.huggingface.co/v1/chat/completions" `
  -Headers $headers `
  -Body $body
```

If PowerShell is 200 OK but Synapse is 404, collect logs + your endpoint/model and share with the supervisor.

---

### 3) HTTP 401 / "Invalid username or password"

**Cause:** invalid token, wrong file, or hidden whitespace.

**Fix:**

```powershell
$t = (Get-Content C:\path\to\HF_TOKEN.txt -Raw).Trim()
Invoke-RestMethod -Method Get -Uri "https://huggingface.co/api/whoami-v2" -Headers @{ Authorization="Bearer $t" }
```

---

### 4) HTTP 403: Access denied (often provider-specific)

You may see an error mentioning a downstream provider domain (e.g., Cloudflare block).

**Fix:** Use a provider-pinned model ID, e.g. `...:together` or `...:novita`, or pick a different model.

---

### 5) Model claims "I am ChatGPT" or misidentifies itself

Many open models will hallucinate identity. Treat the selected **Model ID** as ground truth and validate via your logs/usage.

---

## Security & hygiene

- Prefer **Vault** over plaintext token files.
- Never commit tokens to git.
- Rotate tokens if you suspect exposure.

---

## Minimal checklist

- [ ] Token created with inference permission
- [ ] Token saved to file (single line) or stored in Vault
- [ ] Model ID confirmed via `GET https://router.huggingface.co/v1/models`
- [ ] Connection created in MCP Synapse
  - [ ] Enable HF network calls = Enabled
  - [ ] Endpoint = default or `https://router.huggingface.co/v1`
- [ ] Preflight PASS
- [ ] IDE config updated with Copy config snippet
- [ ] IDE tool call PASS
- [ ] Dashboard/Usage/History show provider+model PASS

