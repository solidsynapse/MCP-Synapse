---
title: Azure OpenAI
description: Publication-safe Azure OpenAI setup guidance for the current v0.6.x Early Access lane.
sidebar:
  label: Azure OpenAI
  order: 6
---

[Back to Providers](/docs/providers/)

Use this page to configure an Azure OpenAI connection for the current v0.6.x Early Access lane.

## Scope and release-lane context

This guide covers Azure OpenAI connection setup for the current v0.6.x Early Access lane.

- mcp synapse remains BYOK/local-only.
- mcp synapse is not a hosted proxy service.
- The product path is non-streaming for this lane.
- The product path uses no hidden retry, backoff, or silent fallback.

## Prerequisites

- You need an active Azure subscription, Azure portal access, mcp synapse running locally, and an MCP-capable IDE.
- Store API keys locally or in a vault reference and do not commit secrets.

## Core Azure contract

Azure runtime calls use deployment name; do not treat raw model name as the runtime identifier.

## Setup steps

- Create Azure OpenAI resource, retrieve endpoint and key, and create a deployment.
- Use the exact deployment name in `mcp synapse`.

## Credentials handling

- `credentials_path` accepts a local key file or a vault reference.
- Key files should contain only the raw key value.

## Create connection and run preflight

- Fill required fields: `connection_name`, `deployment_name`, `azure_endpoint`, `azure_api_version`, and `credentials_path`.
- Run preflight before create.
- Use edit and preflight reconfirmation when updating.

## IDE integration and smoke validation

- Copy generated MCP config into IDE `mcpServers`, save, and reload.
- Validate with a simple test prompt and review dashboard or usage records.

Validation outcomes may vary by environment and provider-side conditions.

## Troubleshooting

- Troubleshoot by category: quota or capacity, deployment-not-found, authentication or path errors, and deployment deprecation.
- Re-check deployment name, endpoint, and credentials formatting first.
- Re-run preflight after correcting connection fields.

Quota, billing, and capacity outcomes may vary by subscription, region, and account policy.

## Security and operations notes

- Do not commit API keys.
- Use a vault reference where possible and rotate keys.
- Keep BYOK/local-only explicit.
- Keep not a hosted proxy service explicit.
- Keep non-streaming for this lane explicit.
- No hidden retry, backoff, or silent fallback on the product path.

## Minimum connection contract

- `connection_name`
- `deployment_name`
- `azure_endpoint`
- `azure_api_version`
- `credentials_path`

AAD token and managed identity production flow are out of scope for this guide.

## Related guidance

- [Install and Download](/docs/install-download/)
- [Security](/docs/security/)
