---
title: Gemini
description: Public-safe Gemini setup guidance for the current v0.8.0 Early Access lane.
sidebar:
  label: Gemini
  order: 22
---

[Back to Providers](/docs/providers/)

Use this page to configure a Gemini connection for the current v0.8.0 Early Access lane.

## Scope and release-lane context

This guide is for the current v0.8.0 Early Access lane of `mcp synapse`.

Boundary conditions for this lane:
- BYOK/local-only
- not a hosted proxy service
- non-streaming for this lane
- no hidden retry, backoff, or silent fallback

This page covers a basic Gemini connection flow for local runtime usage, preflight, and a minimal validation check.

## Prerequisites

- A local `mcp synapse` runtime environment
- An MCP-capable IDE or client
- A Google AI Studio API key that you control
- Access to at least one Gemini model identifier you are allowed to use
- Outbound network access from your local machine to Gemini endpoints

## Core concepts

- The provider identifier for this guide is `gemini`.
- Authentication is key-based through Google AI Studio, not Vertex AI.
- Requests in this lane are non-streaming.
- Connection preflight should pass before IDE-side usage.
- Provider credentials stay under your local control.

## Setup steps

1. Start your local `mcp synapse` runtime.
2. Open the Connections surface in `mcp synapse`.
3. Create a new Gemini connection.
4. Provide your Google AI Studio API key in the runtime-supported local credential path or method.
5. Set a valid model identifier such as `gemini-1.5-flash`.
6. Save the connection.

Do not use Vertex-only project or service-account settings for this provider guide. This path is for the Google AI Studio API-key flow.

## Connection settings

Use only settings that are clearly supported by your current build and UI.

Minimum operational settings:
- Provider: `gemini`
- Authentication: Google AI Studio API key under BYOK control
- Model: `gemini-1.5-flash` or another valid Gemini model you can access

Avoid adding optional tuning fields unless you have a confirmed operational need.

## Preflight and IDE integration

1. Run connection preflight in `mcp synapse`.
2. Confirm preflight reports success.
3. In your MCP-capable IDE, select the Gemini-backed route or connection.
4. Send a simple test prompt.
5. Confirm a normal text response is returned.

Use one minimal prompt first, then expand to your real workload.

## Troubleshooting

### Auth failure

- Verify the API key is present, readable by the runtime path, and not empty.
- Rotate or re-enter the key if needed.

### Model access failure

- Confirm the model identifier is valid and accessible for your account.
- Try a known-good Gemini model identifier in the same account.

### Endpoint issues

- Check endpoint or base URL formatting if customized.
- Ensure local network egress to Google AI Studio endpoints is not blocked.

### Preflight fails

- Resolve the explicit preflight error first.
- Re-run preflight before IDE testing.

## Security and key handling

- Keep Google AI Studio API keys local and out of source control.
- Do not commit secrets to repository files.
- Prefer least-privilege operational key handling where possible.
- Treat logs and screenshots as potentially sensitive.

Operational boundary reminder:
- `mcp synapse` in this lane is BYOK/local-only.
- It is not a hosted proxy service.

## Minimal checklist

- Local `mcp synapse` runtime is running
- Gemini key is configured locally
- Provider is set to `gemini`
- Model identifier is valid
- Preflight passes
- IDE test prompt returns a normal response
- No secrets are committed

## Related guidance

- [Install and Download](/docs/install-download/)
- [Security](/docs/security/)
