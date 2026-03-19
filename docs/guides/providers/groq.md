---
title: Groq
description: Public-safe Groq setup guidance for the current v0.8.0 Early Access lane.
sidebar:
  label: Groq
  order: 21
---

[Back to Providers](/docs/providers/)

Use this page to configure a Groq connection for the current v0.8.0 Early Access lane.

## Scope and release-lane context

This guide is for the current v0.8.0 Early Access lane of `mcp synapse`.

Boundary conditions for this lane:
- BYOK/local-only
- not a hosted proxy service
- non-streaming for this lane
- no hidden retry, backoff, or silent fallback

This page covers a basic Groq connection flow for local runtime usage, preflight, and a minimal validation check.

## Prerequisites

- A local `mcp synapse` runtime environment
- An MCP-capable IDE or client
- A Groq API key that you control
- Access to at least one Groq model identifier you are allowed to use
- Outbound network access from your local machine to Groq endpoints

## Core concepts

- The provider identifier for this guide is `groq`.
- Authentication is key-based.
- Groq exposes an OpenAI-compatible API surface in this lane.
- Requests in this lane are non-streaming.
- Connection preflight should pass before IDE-side usage.

## Setup steps

1. Start your local `mcp synapse` runtime.
2. Open the Connections surface in `mcp synapse`.
3. Create a new Groq connection.
4. Provide your key in the runtime-supported local credential path or method.
5. Set a valid model identifier such as `llama-3.3-70b-versatile`.
6. Save the connection.

If your environment allows custom endpoint configuration, keep it explicit and valid for Groq API usage. Groq also offers a free tier in some account plans, but model access still depends on your account state.

## Connection settings

Use only settings that are clearly supported by your current build and UI.

Minimum operational settings:
- Provider: `groq`
- Authentication: local key under BYOK control
- Model: `llama-3.3-70b-versatile` or another valid Groq model you can access

Avoid adding optional tuning fields unless you have a confirmed operational need.

## Preflight and IDE integration

1. Run connection preflight in `mcp synapse`.
2. Confirm preflight reports success.
3. In your MCP-capable IDE, select the Groq-backed route or connection.
4. Send a simple test prompt.
5. Confirm a normal text response is returned.

Use one minimal prompt first, then expand to your real workload.

## Troubleshooting

### Auth failure

- Verify the API key is present, readable by the runtime path, and not empty.
- Rotate or re-enter the key if needed.

### Model access failure

- Confirm the model identifier is valid and accessible for your account.
- Try a known-good Groq model identifier in the same account.

### Endpoint issues

- Check endpoint or base URL formatting if customized.
- Ensure local network egress to Groq is not blocked.

### Preflight fails

- Resolve the explicit preflight error first.
- Re-run preflight before IDE testing.

## Security and key handling

- Keep Groq keys local and out of source control.
- Do not commit secrets to repository files.
- Prefer least-privilege operational key handling where possible.
- Treat logs and screenshots as potentially sensitive.

Operational boundary reminder:
- `mcp synapse` in this lane is BYOK/local-only.
- It is not a hosted proxy service.

## Minimal checklist

- Local `mcp synapse` runtime is running
- Groq key is configured locally
- Provider is set to `groq`
- Model identifier is valid
- Preflight passes
- IDE test prompt returns a normal response
- No secrets are committed

## Related guidance

- [Install and Download](/docs/install-download/)
- [Security](/docs/security/)
