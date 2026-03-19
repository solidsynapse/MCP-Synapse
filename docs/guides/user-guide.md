---
title: User Guide
description: Step-by-step getting started guide for the current MCP Synapse v0.8.0 Windows release.
sidebar:
  label: User Guide
  order: 3
---

This guide describes the current MCP Synapse desktop product surface for the `v0.8.0` Windows release. It is written for developers who want a step-by-step path from install to first working connection without relying on hidden defaults or hosted relay infrastructure.

MCP Synapse is BYOK and local-first. You bring your own provider account and credentials, the app does not maintain a shared key pool, and the desktop product does not proxy your requests through a hosted MCP Synapse cloud.

## 1. Prerequisites

Before you install MCP Synapse, make sure the following are ready:

- Windows 10 or Windows 11
- One supported AI provider account or REST API endpoint with valid credentials
- Permission to install a desktop app on your machine

The current `v0.8.0` provider and source surface includes:

- Vertex AI
- OpenAI
- Azure OpenAI
- HuggingFace
- Ollama
- Anthropic
- Groq
- Gemini
- OpenRouter
- DeepSeek
- xAI/Grok
- Custom REST API

Bedrock is visible as `Early Access`, but runtime proof is still incomplete in the current lane.

## 2. Install

Use the official `v0.8.0` release package:

- NSIS installer: `MCP Synapse_0.8.0_x64-setup.exe`
- MSI installer: `MCP Synapse_0.8.0_x64_en-US.msi`
- SHA256 manifest: `SHA256SUMS.txt`

Release page:

- `https://github.com/solidsynapse/MCP-Synapse/releases/tag/v0.8.0`

### SmartScreen and unsigned release handling

This release lane remains temporarily unsigned. That means Windows SmartScreen may warn you before first launch even when the package is expected and intact.

If SmartScreen appears:

1. Confirm that you downloaded the installer from the official `v0.8.0` release page.
2. Verify the installer hash against `SHA256SUMS.txt`.
3. Use the Windows "More info" path only after the hash and source both match.

### SHA256 verification

Use PowerShell to verify the downloaded artifact before first run:

```powershell
Get-FileHash 'C:\Path\To\MCP Synapse_0.8.0_x64-setup.exe' -Algorithm SHA256
```

Or, if you downloaded the MSI:

```powershell
Get-FileHash 'C:\Path\To\MCP Synapse_0.8.0_x64_en-US.msi' -Algorithm SHA256
```

Compare the hash output with the matching entry in `SHA256SUMS.txt`.

### Install flow

1. Download either the NSIS installer or the MSI package from the official `v0.8.0` release.
2. Verify the package hash before running it.
3. Keep the default install location unless your environment requires a custom path.
4. Finish setup and launch MCP Synapse from the Start Menu shortcut.

For release-specific asset references, see [Release Notes](/docs/release-notes/) and the `v0.8.0` release assets.

## 3. First Connection

After installation, open MCP Synapse and go to the **Connections** page.

### Create a connection

The Connections surface is where you create, edit, start, stop, and delete provider-backed or REST-backed connections. It also exposes schema-guided forms, preflight validation, and MCP config export.

When creating a connection, the exact fields depend on the provider or source you choose. Common examples:

- Vertex AI: `project_id`, `location`, `model_id`, and a service-account JSON credentials path
- OpenAI: `model_id` and `api_key`
- Azure OpenAI: `endpoint`, `deployment_name`, `api_key`, and the required API version when requested
- Anthropic: `model_id` and `api_key`
- Groq: `model_id` and `api_key`
- Gemini: `model_id` and a Google AI Studio API key
- OpenRouter: `base_url`, `model_id`, and `api_key`
- DeepSeek: `model_id` and `api_key`
- xAI/Grok: `model_id` and `api_key`
- Custom REST API: endpoint URL, auth type, method, and response-field mapping

### Enter credentials

Credentials stay local to your machine. MCP Synapse does not operate a shared key pool and does not silently move secrets into a hosted service.

For repeated use, you can save credentials through the Vault helper. Vault is keyring-backed and local-only.

### Run preflight

Before you rely on a connection, use **Preflight**. This validates that the current provider form, credentials, endpoint configuration, and basic runtime reachability are coherent enough for the connection to start.

If preflight fails, fix that first. Do not assume the connection will behave correctly later if the validation step is already red.

### Copy Config

After the connection is valid, use **Copy Config**. MCP Synapse generates the JSON snippet you can paste into your IDE MCP configuration.

The app does not edit your IDE config file for you. It gives you the exact MCP JSON so you can paste it into the tool you actually use.

## 4. Using the App

### Dashboard

The Dashboard is the quick operational view. It shows cost, latency-adjacent operational visibility, health alerts, recent requests, KPI cards, cost trends, and budget state so you can see current behavior without opening deeper tools first.

It is a read-oriented surface. It does not secretly retry, reroute, or repair provider behavior behind your back.

### Usage Summary and History

The Usage surfaces are for request visibility and reporting. You can filter, inspect recent records, and export CSV data when you need a local audit trail or a quick handoff to analysis tools.

Cost visibility stays explicit through the `cost_source` state:

- `ACTUAL` means the provider supplied real usage pricing data
- `ESTIMATED` means the app calculated a best-effort estimate
- `UNKNOWN` means pricing could not be resolved and is not silently treated as zero

### Policies

The current Policies surface includes:

- Persona Lite
- Optimizations

Persona Lite applies deterministic preset-based system prompt behavior. Optimizations currently expose context caching and request deduplication controls.

This surface is intentionally narrow. Full policy orchestration and advanced persona tooling are not part of the current lane.

### Resilience

The current Resilience surface includes:

- Interceptors
- Budget Guard

Interceptors currently cover persisted JSON syntax-repair behavior. Budget Guard supports `monitor`, `block`, and `throttle` in the current lane, so it can remain observational or become an explicit enforcement surface depending on your setting.

### Vault

Vault helps you save, list, select, and delete local credential entries. It is keyring-backed and local-only.

Vault selection is metadata-first. The UI does not expose raw secrets back through the response surface.

## 5. Troubleshooting

### Preflight FAIL

If preflight fails:

1. Re-check the provider-specific or REST-specific fields.
2. Confirm the credential source is the one you intended to use.
3. Verify the selected model, endpoint, region, project, deployment name, or response field mapping is valid for that connection type.
4. Re-run preflight before attempting to start or export the connection.

### SmartScreen blocker

If Windows blocks launch:

1. Confirm the installer came from the official `v0.8.0` release page.
2. Verify the SHA256 hash.
3. Proceed only after source and hash both match.

### Provider or source connection error

If the connection starts but runtime requests fail:

1. Re-check the credential fields for the selected provider or REST source.
2. Confirm the model, deployment, region, endpoint, or mapping is valid in your account or target API.
3. For local providers such as Ollama, confirm the local runtime is actually running.
4. Re-run preflight and review the connection settings instead of guessing.

### Known issues

Before you treat a behavior as a new bug, review the current release-known issues:

- [`KNOWN_ISSUES.md`](https://github.com/solidsynapse/MCP-Synapse/blob/main/docs/release/releases/v0.8.0/KNOWN_ISSUES.md)

Current known issues include Bedrock remaining Early Access without full runtime proof, wave-2 providers other than Groq not being individually runtime-tested by the development team, and Claude Code CLI compatibility not yet being verified.
