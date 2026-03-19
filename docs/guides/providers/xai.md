---
title: xAI
description: Public-safe xAI/Grok setup guidance for the current v0.8.0 Early Access lane.
sidebar:
  label: xAI
  order: 25
---

[Back to Providers](/docs/providers/)

Use this page to configure an xAI/Grok connection for the current v0.8.0 Early Access lane.

## Scope and release-lane context

This guide is for the current v0.8.0 Early Access lane of `mcp synapse`.

Boundary conditions for this lane:
- BYOK/local-only
- not a hosted proxy service
- non-streaming for this lane
- no hidden retry, backoff, or silent fallback

This page covers a basic xAI/Grok connection flow for local runtime usage, preflight, and a minimal validation check.

## Prerequisites

- A local `mcp synapse` runtime environment
- An MCP-capable IDE or client
- An xAI API key that you control
- Access to at least one xAI model identifier you are allowed to use
- Outbound network access from your local machine to xAI endpoints

## Core concepts

- The provider identifier for this guide is `xai`.
- Authentication is key-based.
- xAI uses an OpenAI-compatible API surface in this lane.
- Requests in this lane are non-streaming.
- Connection preflight should pass before IDE-side usage.

## Setup steps

1. Start your local `mcp synapse` runtime.
2. Open the Connections surface in `mcp synapse`.
3. Create a new xAI/Grok connection.
4. Provide your key in the runtime-supported local credential path or method.
5. Set a valid model identifier such as `grok-3`.
6. Save the connection.

The expected default base URL for this provider family is `https://api.x.ai/v1`. Keep overrides explicit and valid if you customize them.

## Connection settings

Use only settings that are clearly supported by your current build and UI.

Minimum operational settings:
- Provider: `xai`
- Authentication: local key under BYOK control
- Model: `grok-3` or another valid xAI model you can access

Avoid adding optional tuning fields unless you have a confirmed operational need.

## Preflight and IDE integration

1. Run connection preflight in `mcp synapse`.
2. Confirm preflight reports success.
3. In your MCP-capable IDE, select the xAI-backed route or connection.
4. Send a simple test prompt.
5. Confirm a normal text response is returned.

Use one minimal prompt first, then expand to your real workload.

## Troubleshooting

### Auth failure

- Verify the API key is present, readable by the runtime path, and not empty.
- Rotate or re-enter the key if needed.

### Model access failure

- Confirm the model identifier is valid and accessible for your account.
- Try a known-good xAI model identifier in the same account.

### Endpoint issues

- Check that any custom base URL still points to the xAI API.
- Ensure local network egress to xAI is not blocked.

### Preflight fails

- Resolve the explicit preflight error first.
- Re-run preflight before IDE testing.

## Security and key handling

- Keep xAI keys local and out of source control.
- Do not commit secrets to repository files.
- Prefer least-privilege operational key handling where possible.
- Treat logs and screenshots as potentially sensitive.

Operational boundary reminder:
- `mcp synapse` in this lane is BYOK/local-only.
- It is not a hosted proxy service.

## Minimal checklist

- Local `mcp synapse` runtime is running
- xAI key is configured locally
- Provider is set to `xai`
- Model identifier is valid
- Preflight passes
- IDE test prompt returns a normal response
- No secrets are committed

## Related guidance

- [Install and Download](/docs/install-download/)
- [Security](/docs/security/)
