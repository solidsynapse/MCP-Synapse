---
title: OpenRouter
description: Public-safe OpenRouter setup guidance for the current v0.8.0 Early Access lane.
sidebar:
  label: OpenRouter
  order: 23
---

[Back to Providers](/docs/providers/)

Use this page to configure an OpenRouter connection for the current v0.8.0 Early Access lane.

## Scope and release-lane context

This guide is for the current v0.8.0 Early Access lane of `mcp synapse`.

Boundary conditions for this lane:
- BYOK/local-only
- not a hosted proxy service
- non-streaming for this lane
- no hidden retry, backoff, or silent fallback

This page covers a basic OpenRouter connection flow for local runtime usage, preflight, and a minimal validation check.

## Prerequisites

- A local `mcp synapse` runtime environment
- An MCP-capable IDE or client
- An OpenRouter API key that you control
- Access to at least one OpenRouter model identifier you are allowed to use
- Outbound network access from your local machine to OpenRouter endpoints

## Core concepts

- The provider identifier for this guide is `openrouter`.
- Authentication is key-based.
- OpenRouter uses an OpenAI-compatible API surface in this lane.
- Requests in this lane are non-streaming.
- Connection preflight should pass before IDE-side usage.

## Setup steps

1. Start your local `mcp synapse` runtime.
2. Open the Connections surface in `mcp synapse`.
3. Create a new OpenRouter connection.
4. Provide your key in the runtime-supported local credential path or method.
5. Set a valid model identifier such as `openai/gpt-4o-mini`.
6. Save the connection.

The expected default base URL for this provider family is `https://api.openrouter.ai/v1`. Keep overrides explicit and valid if you customize them.

## Connection settings

Use only settings that are clearly supported by your current build and UI.

Minimum operational settings:
- Provider: `openrouter`
- Authentication: local key under BYOK control
- Base URL: `https://api.openrouter.ai/v1`
- Model: `openai/gpt-4o-mini` or another valid OpenRouter-routed model you can access

Avoid adding optional tuning fields unless you have a confirmed operational need.

## Preflight and IDE integration

1. Run connection preflight in `mcp synapse`.
2. Confirm preflight reports success.
3. In your MCP-capable IDE, select the OpenRouter-backed route or connection.
4. Send a simple test prompt.
5. Confirm a normal text response is returned.

Use one minimal prompt first, then expand to your real workload.

## Troubleshooting

### Auth failure

- Verify the API key is present, readable by the runtime path, and not empty.
- Rotate or re-enter the key if needed.

### Model access failure

- Confirm the model identifier is valid and accessible for your account.
- Try a known-good OpenRouter model identifier in the same account.

### Endpoint issues

- Check that any custom base URL still points to the OpenRouter API.
- Ensure local network egress to OpenRouter is not blocked.

### Preflight fails

- Resolve the explicit preflight error first.
- Re-run preflight before IDE testing.

## Security and key handling

- Keep OpenRouter keys local and out of source control.
- Do not commit secrets to repository files.
- Prefer least-privilege operational key handling where possible.
- Treat logs and screenshots as potentially sensitive.

Operational boundary reminder:
- `mcp synapse` in this lane is BYOK/local-only.
- It is not a hosted proxy service.

## Minimal checklist

- Local `mcp synapse` runtime is running
- OpenRouter key is configured locally
- Provider is set to `openrouter`
- Base URL is valid
- Model identifier is valid
- Preflight passes
- IDE test prompt returns a normal response
- No secrets are committed

## Related guidance

- [Install and Download](/docs/install-download/)
- [Security](/docs/security/)
