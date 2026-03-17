---
title: Install and Download
description: Access the current Windows release flow and review release integrity guidance for the current v0.6.x Early Access lane.
sidebar:
  label: Install and Download
  order: 2
---

Use the official `v0.6.1` release package for the current Windows release in the current `v0.6.x` Early Access lane.

Related guidance: use [Download for Windows](/download/) for release access and [Providers](/docs/providers/) for provider-specific setup guidance.

## Release access

Use the official GitHub release page and the `v0.6.1` asset set for the current Windows release.

- Release page: [GitHub release `v0.6.1`](https://github.com/solidsynapse/MCP-Synapse/releases/tag/v0.6.1)
- NSIS installer: [`MCP Synapse_0.6.1_x64-setup.exe`](https://github.com/solidsynapse/MCP-Synapse/releases/download/v0.6.1/MCP%20Synapse_0.6.1_x64-setup.exe)
- MSI installer: [`MCP Synapse_0.6.1_x64_en-US.msi`](https://github.com/solidsynapse/MCP-Synapse/releases/download/v0.6.1/MCP%20Synapse_0.6.1_x64_en-US.msi)
- Hash manifest: [`SHA256SUMS.txt`](https://github.com/solidsynapse/MCP-Synapse/releases/download/v0.6.1/SHA256SUMS.txt)

## Release integrity

Public releases include a tag, SHA256, release notes, and explicit unsigned guidance while unsigned mode is active.

- Tag: Published with the release.
- SHA256: Published with the release.
- Release notes: Published with the release.
- Install/run notes: [`INSTALL_RUN_NOTES.md`](https://github.com/solidsynapse/MCP-Synapse/blob/main/docs/release/releases/v0.6.1/INSTALL_RUN_NOTES.md)

## Signing status

While unsigned mode is active, unsigned status is explicitly disclosed.

For `v0.6.1`, review the release-specific unsigned notice before first run:

- [`UNSIGNED_NOTICE.md`](https://github.com/solidsynapse/MCP-Synapse/blob/main/docs/release/releases/v0.6.1/UNSIGNED_NOTICE.md)

## Install flow summary

The current `v0.6.1` install flow is:

1. Download either the NSIS installer or the MSI package from the official `v0.6.1` release.
2. Verify the artifact hash against `SHA256SUMS.txt`.
3. Keep the default install destination unless your environment requires a custom path.
4. Launch MCP Synapse from the Start Menu shortcut after install completes.
5. Treat `mcp-synapse.exe` as the packaged app binary, not as a standalone public download artifact.

For the full packaged-runtime guidance, use [`INSTALL_RUN_NOTES.md`](https://github.com/solidsynapse/MCP-Synapse/blob/main/docs/release/releases/v0.6.1/INSTALL_RUN_NOTES.md).

## Security disclosures

For security disclosures, contact [security@solidsynapse.com](mailto:security@solidsynapse.com).
