---
title: Vertex AI
description: Public-safe Vertex AI setup guidance for the current v0.6.x Early Access lane.
sidebar:
  label: Vertex AI
  order: 8
---

[Back to Providers](/docs/providers/)

Use this page to configure a Vertex AI connection for the current v0.6.x Early Access lane.

## Scope and release-lane context

This guide covers Google Cloud Vertex AI connection setup for the current v0.6.x Early Access lane.

- Provider: Google Cloud Vertex AI
- Auth path: Service Account JSON key file
- Contract: valid Project ID plus Model ID
- Runtime path: non-streaming for this lane
- mcp synapse remains BYOK/local-only.
- mcp synapse is not a hosted proxy service.
- The product path is non-streaming for this lane.
- The product path uses no hidden retry, backoff, or silent fallback.

## Prerequisites

- Active Google Cloud account and project
- Access to Google Cloud Console
- mcp synapse installed and running locally
- Local IDE/client with MCP support
- Billing-enabled project may be required for live API usage, depending on account and plan

## Core concepts

Working chain:

Google Cloud Project -> Service Account (JSON Auth) -> mcp synapse connection -> IDE MCP server -> prompt response

- Project ID: unique identifier for your target GCP project
- Service Account: machine identity used by local runtime
- Model ID: technical model identifier entered in connection settings

Important:
- Project ID and credentials context must match.
- Model ID should be taken from current Vertex model listings.

## Setup steps

### Enable the Vertex AI API

In Google Cloud Console:

1. Search for **Vertex AI API**.
2. Open the API page.
3. Click **Enable**.

### Create a service account

1. Go to **IAM & Admin** -> **Service Accounts**.
2. Click **Create Service Account**.
3. Enter a service account name.
4. Continue.

### Assign permissions

1. Open role selection.
2. Assign **Vertex AI User** (or a broader role only if required by your organization).
3. Complete role assignment.

### Create and download a JSON key

1. Open the created service account.
2. Go to **Keys**.
3. Click **Add Key** -> **Create new key**.
4. Select **JSON** and create key.
5. Save the file in a secure local folder.

Security note:
- Never commit this JSON file to public repositories.
- Treat the file as sensitive secret material.

## Project and model validation

You can obtain Project ID from:
- Project selector in Google Cloud Console
- `project_id` field in the JSON key file
- Project Info section in Cloud Dashboard

Validation rule:
- Project ID entered in `mcp synapse` must match the credential and project context exactly.

To establish the model connection:

1. Open **Vertex AI -> Model Garden**.
2. Select a model.
3. Copy the model technical identifier (Model ID).
4. Enter the Model ID in the `mcp synapse` connection form.

Availability note:
- Model availability and access can vary by account, region, and rollout state.
- If you receive not-found or access errors, try another currently available model and re-run preflight.

## Connection settings

- **Location**:
  - Start with a common default region (for example `us-central1`) unless your organization requires a different region.
- **Endpoint / Base URL**:
  - Keep the default unless your environment requires custom routing, private connectivity, or an API gateway.

Guidance:
- Treat region and endpoint choices as environment-specific configuration.

## Preflight and IDE integration

1. Run **Preflight** in mcp synapse.
2. If preflight succeeds, click **Create Connection**.
3. Copy the generated MCP config snippet from Connections.
4. Paste it into IDE MCP settings and reload the IDE or client.
5. Send a simple test prompt.
6. Verify request visibility in dashboard or usage views.

## Troubleshooting

### Access, permission, or not-found errors

Checks:
- Recheck Project ID
- Recheck credentials path or file
- Recheck the exact Model ID
- Confirm account, region, and model access status
- Re-run preflight

### Authentication failures

Checks:
- Confirm the credentials file path
- Confirm valid JSON key file content
- Confirm the correct project context
- Re-run preflight after correcting credentials details

### Region or endpoint issues

Checks:
- Revert to the default endpoint if a custom endpoint is unnecessary
- Confirm region and resource alignment
- Re-run preflight after correcting region or endpoint settings

## Security and key handling

- Keep credentials local and private
- Do not commit secret files
- Rotate keys if exposure is suspected
- Keep BYOK/local-only explicit.
- Keep not a hosted proxy service explicit.
- Keep non-streaming for this lane explicit.
- No hidden retry, backoff, or silent fallback on the product path.

## Minimal checklist

- [ ] Vertex AI API enabled
- [ ] Service account created
- [ ] Required role assigned
- [ ] JSON key generated and stored securely
- [ ] Project ID verified
- [ ] Model ID selected
- [ ] Preflight successful
- [ ] Connection created
- [ ] IDE MCP config updated
- [ ] End-to-end prompt test completed
- [ ] Usage visibility verified

## Related guidance

- [Install and Download](/docs/install-download/)
- [Security](/docs/security/)
