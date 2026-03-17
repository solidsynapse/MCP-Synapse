# Retention and Deletion Policy

This document explains where MCP Synapse keeps local product data and how that data can be removed.

## Local data locations

The current desktop product stores its application data under the local `data/` directory in the product workspace.

Primary product data files:

- `data/config.json` for configuration and persisted settings
- `data/usage.db` for local usage history and usage-related reporting data
- `data/vault_index.json` for Vault entry metadata

Additional local Vault directories may exist:

- `data/vault_imports/` for managed local copies of imported credential files
- `data/vault_materialized/` only as a legacy recovery path for earlier Vault entries

## How deletion works

### Manual deletion

You can manually remove local product files from the `data/` directory when you want to clear configuration, usage records, or Vault metadata from the workspace.

### UI deletion

The current UI supports deletion for some local data surfaces:

- Vault entries can be deleted from the Vault UI flow
- Usage history can be cleared from the Usage History surface

If you remove only one product file, related data in other files may still remain until you delete those files too.

## Uninstall behavior

Removing the installed application does not automatically guarantee deletion of all local data files. Product data retention remains the user's responsibility unless a specific installer lane explicitly documents full data cleanup.

If you want complete local cleanup, remove the installed app and then manually review and delete the related local product data files and Vault entries.
