---
title: Hugging Face
description: Public-safe Hugging Face Router guidance for the current v0.6.x Early Access lane.
sidebar:
  label: Hugging Face
  order: 7
---

[Back to Providers](/docs/providers/)

Use this page to configure the Hugging Face OpenAI-compatible chat path for the current v0.6.x Early Access lane.

## Scope and release-lane context

This guide covers the Hugging Face OpenAI-compatible chat path for the current v0.6.x Early Access lane.

Current scope is non-streaming for this lane and chat-only (`/v1/chat/completions`).

- mcp synapse remains BYOK/local-only.
- mcp synapse is not a hosted proxy service.
- The product path is non-streaming for this lane.
- The product path uses no hidden retry, backoff, or silent fallback.

## Prerequisites

- You need a Hugging Face account, local mcp synapse runtime, and an MCP-capable IDE.
- Outbound HTTPS to Hugging Face router endpoints is required.

## Create token

- Create a Hugging Face access token with inference call permissions.
- Store the token as a single-line local secret or a vault reference.
- Do not commit tokens to git.

## Choose model ID

- Model IDs can be enumerated from `GET /v1/models`.
- Provider-suffixed IDs can help when a specific downstream route is unavailable.
- Treat provider and network behavior as environment-dependent.

## Create connection in mcp synapse

- Set connection name, model ID, credentials path, and enable HF network calls.
- HF network gate must be enabled for live calls.
- Use preflight to validate before create.

## IDE config integration

- Copy the generated server snippet and merge it under your IDE `mcpServers` config.
- Reload IDE after save.

## End-to-end validation

- Run a simple prompt and verify dashboard, usage, or history entries.
- Use this as operational validation, not a permanent quality guarantee.

## Troubleshooting

- Troubleshoot by class: network gate disabled, endpoint path mismatch, token validity, and provider-side access constraints.
- Provider-suffixed model IDs may help in some access scenarios.
- Provider availability can vary by account, route, region, or downstream provider conditions.
- Re-run preflight after correcting connection settings.

## Security and key handling

- Prefer a vault reference over plaintext token files.
- Rotate tokens if exposure is suspected.
- Keep BYOK/local-only explicit.
- Keep not a hosted proxy service explicit.
- Keep non-streaming for this lane explicit.
- No hidden retry, backoff, or silent fallback on the product path.

## Minimal checklist

- Use the checklist as an operational completion aid.
- Confirm OpenAI-compatible chat path scope.
- Confirm token source and credentials path.
- Confirm HF network gate is enabled for live calls.
- Confirm endpoint path and IDE configuration were reloaded.

## Related guidance

- [Install and Download](/docs/install-download/)
- [Security](/docs/security/)
