# Privacy Notice

This privacy notice applies to the current MCP Synapse desktop product surface.

MCP Synapse is a local-first desktop application. It does not operate as a hosted shared service, and it does not send your application data to an MCP Synapse cloud backend as part of normal runtime use.

## Local-only operation

MCP Synapse runs on your machine and stores its local product data in the local application workspace.

The product does not include telemetry, background analytics upload, or a hosted key pool. Provider calls run under your own provider account and credentials.

## What the app stores locally

The app may store the following local product data:

- Configuration data in `data/config.json`
- Usage records in `data/usage.db`
- Vault metadata in `data/vault_index.json`

For imported credential-file entries, the product may also keep a managed local file copy under `data/vault_imports/` so the selected credential-path workflow continues to work after import.

## What the app does not store in product files

The app does not store the following items in `config.json`, `usage.db`, or `vault_index.json`:

- Prompt content
- Response content
- Plaintext credentials

Non-import secrets are stored through the local operating system keyring instead of plain text product files.

## Telemetry

MCP Synapse does not include product telemetry in the current release lane.

## Deletion

You can manually delete local product files from the application data directory if you want to remove stored configuration or usage records.

Vault entries can be removed from the UI through the Vault delete flow. Deleting a Vault entry removes its local metadata entry and attempts to remove the related keyring secret and any managed imported credential file associated with that entry.
