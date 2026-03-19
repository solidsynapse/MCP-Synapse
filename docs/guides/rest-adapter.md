---
title: REST Adapter
description: Public-safe Custom REST API setup guidance for the current v0.8.0 Early Access lane.
sidebar:
  label: REST Adapter
  order: 12
---

Use this page to configure a Custom REST API connection for the current v0.8.0 Early Access lane.

## Scope and release-lane context

This guide is for the current v0.8.0 Early Access lane of `mcp synapse`.

Boundary conditions for this lane:
- BYOK/local-only
- not a hosted proxy service
- non-streaming for this lane
- no hidden retry, backoff, or silent fallback

This page covers the REST adapter snapshot surface: endpoint URL, authentication mode, HTTP method, response-field mapping, preflight, and a minimal validation check.

## Prerequisites

- A local `mcp synapse` runtime environment
- An MCP-capable IDE or client
- A reachable REST API endpoint you control or are authorized to use
- Any required credentials for that endpoint
- A known response field that contains the text or value you want surfaced

## Core concepts

- The provider identifier for this guide is `rest_api`.
- The REST adapter is for explicit HTTP request/response mapping, not provider SDK usage.
- Supported auth choices in this lane are limited to the runtime-supported local form options.
- Cost is not priced like model providers in this lane; usage rows record `UNKNOWN` cost state.
- Connection preflight should pass before IDE-side usage.

## Setup steps

1. Start your local `mcp synapse` runtime.
2. Open the Connections surface in `mcp synapse`.
3. Create a new `Custom REST API` connection.
4. Enter the endpoint URL.
5. Choose the auth type that matches the endpoint.
6. Choose the method (`GET` or `POST`) that matches the endpoint contract.
7. Set the response-field mapping to the field you want returned.
8. Save the connection.

Keep the mapping simple at first. Use a response field you already know exists in a normal success response.

## Connection settings

Use only settings that are clearly supported by your current build and UI.

Minimum operational settings:
- Provider: `rest_api`
- Endpoint URL: explicit and valid
- Auth type: `none`, `api_key_header`, `bearer`, or `basic` when supported by your current build
- Method: `GET` or `POST`
- Response field: a valid field path in the returned JSON body

Avoid adding extra request complexity until the minimal path works.

## Preflight and IDE integration

1. Run connection preflight in `mcp synapse`.
2. Confirm preflight reports success.
3. In your MCP-capable IDE, select the REST-backed route or connection.
4. Send a simple request prompt that triggers the mapped endpoint path.
5. Confirm the mapped value is returned as expected.

Use a stable endpoint first, then expand to live workflow data.

## Troubleshooting

### Auth failure

- Verify the credential value is present, readable by the runtime path, and not empty.
- Re-check header type or credential formatting if you use key-based auth.

### Response mapping failure

- Confirm the response field exists in the returned JSON body.
- Start with a shallow field before attempting a deeper nested mapping.

### Endpoint issues

- Verify the endpoint URL is correct and reachable from the local machine.
- Confirm the selected method matches the server contract.

### Preflight fails

- Resolve the explicit preflight error first.
- Re-run preflight before IDE testing.

## Security and key handling

- Keep REST API credentials local and out of source control.
- Do not commit secrets to repository files.
- Prefer least-privilege operational key handling where possible.
- Treat logs and screenshots as potentially sensitive.

Operational boundary reminder:
- `mcp synapse` in this lane is BYOK/local-only.
- It is not a hosted proxy service.
- REST adapter calls remain local runtime actions, not a shared service.

## Minimal checklist

- Local `mcp synapse` runtime is running
- Endpoint URL is valid
- Auth mode matches the target API
- Method matches the target API
- Response field mapping is valid
- Preflight passes
- IDE test returns the mapped value
- No secrets are committed

## Related guidance

- [Install and Download](/docs/install-download/)
- [Security](/docs/security/)
- [Feature Reference](/docs/feature-reference/)

## Use case examples

- Fintech market data snapshots
- DevOps status and CI result lookups
- Healthcare scheduling or operational record lookups
- E-commerce inventory or order-state queries
