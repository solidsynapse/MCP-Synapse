---
title: Install and Download
description: Access the current Windows release flow and review release integrity guidance for the current v0.8.0 Early Access lane.
sidebar:
  label: Install and Download
  order: 2
---

Use the official `v0.8.0` release package for the current Windows release in the current `v0.8.0` Early Access lane.

Related guidance: use [Download for Windows](/download/) for release access and [Providers](/docs/providers/) for provider-specific setup guidance.

## Release access

Use the official GitHub release page and the `v0.8.0` asset set for the current Windows release.

- Release page: [GitHub release `v0.8.0`](https://github.com/solidsynapse/MCP-Synapse/releases/tag/v0.8.0)
- NSIS installer: [`MCP Synapse_0.8.0_x64-setup.exe`](https://github.com/solidsynapse/MCP-Synapse/releases/download/v0.8.0/MCP%20Synapse_0.8.0_x64-setup.exe)
- MSI installer: [`MCP Synapse_0.8.0_x64_en-US.msi`](https://github.com/solidsynapse/MCP-Synapse/releases/download/v0.8.0/MCP%20Synapse_0.8.0_x64_en-US.msi)
- Hash manifest: [`SHA256SUMS.txt`](https://github.com/solidsynapse/MCP-Synapse/releases/download/v0.8.0/SHA256SUMS.txt)

## Release integrity

Public releases include a tag, SHA256, release notes, and explicit release notes/known-issues context while unsigned mode remains active.

- Tag: Published with the release.
- SHA256: Published with the release.
- Release notes: [`RELEASE_NOTES.md`](https://github.com/solidsynapse/MCP-Synapse/blob/main/docs/release/releases/v0.8.0/RELEASE_NOTES.md)
- What changed: [`WHAT_CHANGED.md`](https://github.com/solidsynapse/MCP-Synapse/blob/main/docs/release/releases/v0.8.0/WHAT_CHANGED.md)
- Known issues: [`KNOWN_ISSUES.md`](https://github.com/solidsynapse/MCP-Synapse/blob/main/docs/release/releases/v0.8.0/KNOWN_ISSUES.md)

## Signing status

While unsigned mode is active, unsigned status remains part of the release-operating model.

For `v0.8.0`, download only from the official release page and verify hashes from `SHA256SUMS.txt` before first run.

## Install flow summary

The current `v0.8.0` install flow is:

1. Download either the NSIS installer or the MSI package from the official `v0.8.0` release.
2. Verify the artifact hash against `SHA256SUMS.txt`.
3. Keep the default install destination unless your environment requires a custom path.
4. Launch MCP Synapse from the Start Menu shortcut after install completes.
5. Treat `mcp-synapse.exe` as the packaged app binary, not as a standalone public download artifact.

For the full release summary, use the linked `RELEASE_NOTES.md`, `WHAT_CHANGED.md`, and `KNOWN_ISSUES.md` pages in the `v0.8.0` release folder.

## Security disclosures

For security disclosures, contact [security@solidsynapse.com](mailto:security@solidsynapse.com).
