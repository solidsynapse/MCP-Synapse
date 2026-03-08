# Azure OpenAI -> MCP Synapse -> Local IDE (MCP) User Guide

This guide is for first-time users who want to connect Azure OpenAI to MCP Synapse and use it from a local IDE MCP client.

Scope:
- Provider: Azure OpenAI
- Runtime mode: non-streaming
- Auth path: API key via file or Vault reference
- Contract: Azure uses deployment name (not raw model name)

---

## Table of Contents

1. Prerequisites
2. What You Build
3. Critical Azure Concepts
4. Step 1 - Create Azure OpenAI Resource
5. Step 2 - Get Endpoint and API Key
6. Step 3 - Create Deployment
7. Step 4 - Prepare Credentials for Synapse
8. Step 5 - Create Azure Connection in MCP Synapse
9. Step 6 - Add MCP Config to IDE
10. Step 7 - End-to-End Smoke Test
11. Troubleshooting
12. Security and Operations Notes
13. Minimum Connection Contract
14. Publish Screenshot Checklist

---

## 1) Prerequisites

- Active Azure subscription
- Access to Azure Portal
- MCP Synapse installed and running locally
- Local IDE/client with MCP support
- A local file location to store your Azure API key (or use Synapse Vault)

Practical note:
- Trial subscriptions may have strict quota/capacity limits.
- Pay-As-You-Go may be required for stable runtime tests.

---

## 2) What You Build

Working chain:

Azure OpenAI Resource -> Deployment -> MCP Synapse Connection -> IDE MCP Server -> Live prompt response

---

## 3) Critical Azure Concepts

- Resource: your Azure OpenAI service instance
- Model family: for example `gpt-4o-mini`
- Deployment: the callable deployment inside your resource

Important:
- Azure calls are made with deployment name.
- Do not treat "model ID" as the runtime identifier for Azure.

---

## 4) Step 1 - Create Azure OpenAI Resource

In Azure Portal:

1. Search for Azure OpenAI.
2. Select Create.
3. Fill Subscription, Resource Group, Region, and Resource Name.
4. Use pricing tier supported by your subscription (commonly Standard S0).
5. Review + Create.

Wait until provisioning finishes.

---

## 5) Step 2 - Get Endpoint and API Key

Open your Azure OpenAI resource and go to Keys and Endpoint.

Collect:
- Endpoint, example: `https://<resource-name>.openai.azure.com/`
- Key1 or Key2

Key1 is usually enough for initial setup.

---

## 6) Step 3 - Create Deployment

In Azure AI Foundry/Studio:

1. Choose a model family (example: `gpt-4o-mini`).
2. Choose deployment type supported by your quota.
3. Configure TPM/capacity.
4. Set deployment name (example: `mcp-gpt-4o-mini`).

You must use this deployment name in MCP Synapse.

---

## 7) Step 4 - Prepare Credentials for Synapse

Option A - File path:
- Create a file, for example: `C:\secrets\azure_openai_key.txt`
- Put only the API key on one line
- No quotes, no `KEY=`, no trailing comments

Option B - Vault:
- Save the key in MCP Synapse Vault
- Use the generated `vault://...` reference

---

## 8) Step 5 - Create Azure Connection in MCP Synapse

Open:
Connections -> New Connection -> Provider: Azure OpenAI

Fill fields:

Required:
- Connection name
- Deployment name
- Endpoint / Base URL
- API version (default may be prefilled, but keep visible and editable)
- Credentials path (file path or `vault://...` reference)

Then:
1. Click Preflight
2. Expect Preflight OK
3. Click Create Connection

Edit flow test (recommended):
- Open Edit Connection
- Change one non-critical field (or keep same), Save
- Run Preflight again to confirm stable update path

---

## 9) Step 6 - Add MCP Config to IDE

1. In Connections list, click Copy config for your Azure connection.
2. Open IDE MCP config location.
3. Paste/merge snippet under `mcpServers`.
4. Save and reload IDE (or restart MCP client).

Expected:
- A tool appears for this server (for example `<name>/generate_text`).

---

## 10) Step 7 - End-to-End Smoke Test

In IDE, send a simple prompt through Azure tool:
- `hi`
- `how are you?`

In MCP Synapse, verify:
- Dashboard records a new row
- Usage Summary/History records provider as Azure OpenAI
- Connection and model/deployment identity appear correctly in usage views

If all pass, chain is validated.

---

## 11) Troubleshooting

### A) `capacity` or `TPM` related failures

Cause:
- Deployment quota/capacity not sufficient

Fix:
- Recheck deployment capacity
- Try supported deployment type
- Verify subscription plan and quota visibility

### B) 404 or deployment-not-found

Cause:
- Wrong deployment name
- Region/resource mismatch

Fix:
- Copy deployment name exactly
- Confirm deployment is in same Azure resource/region

### C) Auth failed

Cause:
- Wrong endpoint
- Invalid key file content
- Wrong credentials path

Fix:
- Re-copy endpoint from Azure Keys and Endpoint
- Ensure key file contains only raw key
- Re-test Preflight

### D) Model/deployment deprecation

Cause:
- Deployment target no longer valid

Fix:
- Create a new deployment on a currently supported model
- Update connection deployment name

---

## 12) Security and Operations Notes

- Do not commit API keys to git.
- Keep secrets in Vault when possible.
- Use key rotation (Key1/Key2) for safer operations.
- Keep BYOK/local-only boundary clear:
  - Credentials belong to user organization account.
  - Do not operate as shared key pool or proxy-as-a-service.

---

## 13) Minimum Connection Contract

Azure OpenAI connection must provide:

- `connection_name`
- `deployment_name`
- `azure_endpoint`
- `azure_api_version`
- `credentials_path` (file path or `vault://...`)

Out of current scope:
- AAD token / managed identity production flow

---

## 14) Publish Screenshot Checklist

For website/docs publishing, include:

1. Azure Keys and Endpoint screen
2. Azure deployment creation screen
3. MCP Synapse New Connection (Azure) screen
4. MCP Synapse Preflight OK state
5. IDE MCP config with pasted server snippet
6. IDE successful tool response
7. MCP Synapse Usage/History row for Azure call

When these seven screenshots are added, this guide is publish-ready.
