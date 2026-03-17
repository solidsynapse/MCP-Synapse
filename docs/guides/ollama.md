---
title: Ollama
description: Public-safe Ollama setup guidance for the current v0.6.x Early Access lane.
sidebar:
  label: Ollama
  order: 10
---

[Back to Providers](/docs/providers/)

Use this page to configure an Ollama connection for the current v0.6.x Early Access lane.

## Scope and release-lane context

This guide is for the current v0.6.x Early Access lane of `mcp synapse`.

Boundary conditions for this lane:
- BYOK/local-only
- not a hosted proxy service
- non-streaming for this lane
- no hidden retry, backoff, or silent fallback

This page covers a local Ollama connection flow, preflight, and a minimal validation check.

## Prerequisites

- A local `mcp synapse` runtime environment
- An MCP-capable IDE or client
- A local Ollama runtime or daemon running on your machine
- At least one local Ollama model already pulled
- Local loopback connectivity to your Ollama endpoint

## Core concepts

- The provider identifier for this guide is `ollama`.
- Default endpoint behavior is local (`http://127.0.0.1:11434`) unless explicitly overridden.
- Requests in this lane are non-streaming.
- Connection preflight should pass before IDE-side usage.
- This guide assumes local runtime-to-local Ollama flow.

## Setup steps

1. Start your local Ollama daemon or runtime.
2. Pull at least one model in Ollama.
3. Start your local `mcp synapse` runtime.
4. Open the Connections surface in `mcp synapse`.
5. Create a new Ollama connection.
6. Set the model identifier you pulled locally.
7. Use the local endpoint, either the default or an explicit local URL.
8. Save the connection.

## Connection settings

Use only settings that are clearly supported by your current build and UI.

Minimum operational settings:
- Provider: `ollama`
- Endpoint: local Ollama endpoint
- Model: a model that is already present locally

Avoid remote endpoint assumptions unless your environment explicitly supports them.

## Preflight and IDE integration

1. Run connection preflight in `mcp synapse`.
2. Confirm preflight reports success.
3. In your MCP-capable IDE, select the Ollama-backed route or connection.
4. Send a simple test prompt.
5. Confirm a normal text response is returned.

Start with a short deterministic prompt before longer interactions.

## Troubleshooting

### Daemon not reachable

- Confirm Ollama is running.
- Confirm the endpoint and port are correct and locally reachable.

### Model not found

- Pull the required model locally, then retry.
- Re-check model identifier spelling.

### Endpoint mismatch

- Verify local endpoint format.
- Avoid stale or custom endpoint values unless required.

### Preflight fails

- Resolve the explicit preflight error first.
- Re-run preflight before IDE testing.

## Security and key handling

- This flow is intended for local runtime operation.
- Keep local machine access controlled.
- Avoid sharing local runtime logs with sensitive prompt content.

Operational boundary reminder:
- `mcp synapse` in this lane is BYOK/local-only.
- It is not a hosted proxy service.

## Minimal checklist

- Ollama daemon is running locally
- Required model is already pulled
- Local `mcp synapse` runtime is running
- Provider is set to `ollama`
- Endpoint points to local Ollama
- Preflight passes
- IDE test prompt returns a normal response

## Related guidance

- [Install and Download](/docs/install-download/)
- [Security](/docs/security/)
