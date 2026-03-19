---
title: Bedrock
description: Public-safe Bedrock Early Access setup guidance for the current v0.8.0 Early Access lane.
sidebar:
  label: Bedrock
  order: 26
---

[Back to Providers](/docs/providers/)

Use this page to configure a Bedrock connection for the current v0.8.0 Early Access lane.

## Scope and release-lane context

This guide is for the current v0.8.0 Early Access lane of `mcp synapse`.

Boundary conditions for this lane:
- BYOK/local-only
- not a hosted proxy service
- non-streaming for this lane
- no hidden retry, backoff, or silent fallback

This provider is `Early Access`. The adapter exists in the product surface, but runtime behavior has not been proven by the development team in this lane.

## Prerequisites

- A local `mcp synapse` runtime environment
- An MCP-capable IDE or client
- AWS credentials that you control
- A valid AWS region
- Access to at least one Bedrock model identifier you are allowed to use
- Outbound network access from your local machine to AWS Bedrock endpoints

## Core concepts

- The provider identifier for this guide is `bedrock`.
- Authentication is AWS-credential based.
- Region is required.
- Requests in this lane are non-streaming.
- Connection preflight should pass before IDE-side usage.
- Runtime proof for this provider is still incomplete.

## Setup steps

1. Start your local `mcp synapse` runtime.
2. Open the Connections surface in `mcp synapse`.
3. Create a new Bedrock connection.
4. Provide AWS credentials through the runtime-supported local credential path or method.
5. Set a valid AWS region.
6. Set a Bedrock model identifier you are allowed to use.
7. Save the connection.

Because this provider is still Early Access, treat setup as provisional until your own account-specific preflight and runtime checks succeed.

## Connection settings

Use only settings that are clearly supported by your current build and UI.

Minimum operational settings:
- Provider: `bedrock`
- Authentication: local AWS credentials under BYOK control
- Region: required
- Model: a valid Bedrock model identifier you can access

Avoid adding optional tuning fields unless you have a confirmed operational need.

## Preflight and IDE integration

1. Run connection preflight in `mcp synapse`.
2. Confirm preflight reports success before any IDE test.
3. In your MCP-capable IDE, select the Bedrock-backed route or connection only after preflight is clean.
4. Send a simple test prompt.
5. Treat any runtime success as account-specific until broader runtime proof exists.

Use one minimal prompt first, then expand to your real workload.

## Troubleshooting

### Auth failure

- Verify the AWS credentials are present, readable by the runtime path, and not empty.
- Re-check the credential source if you use a file-based setup.

### Model access failure

- Confirm the model identifier is valid and available in your account and region.
- Account-specific quota or access policy can block an otherwise valid model.

### Endpoint issues

- Verify the configured region is correct.
- Ensure local network egress to AWS Bedrock endpoints is not blocked.

### Preflight fails

- Resolve the explicit preflight error first.
- Re-run preflight before IDE testing.

## Security and key handling

- Keep AWS credentials local and out of source control.
- Do not commit secrets to repository files.
- Prefer least-privilege operational key handling where possible.
- Treat logs and screenshots as potentially sensitive.

Operational boundary reminder:
- `mcp synapse` in this lane is BYOK/local-only.
- It is not a hosted proxy service.
- Early Access does not mean provider support is fully proven.

## Minimal checklist

- Local `mcp synapse` runtime is running
- AWS credentials are configured locally
- Provider is set to `bedrock`
- Region is set
- Model identifier is valid
- Preflight passes
- IDE test is attempted only after preflight success
- No secrets are committed

## Related guidance

- [Install and Download](/docs/install-download/)
- [Security](/docs/security/)
