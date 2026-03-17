---
title: Release Notes
description: Review how release notes fit into the public release record for the current v0.6.x Early Access lane.
sidebar:
  label: Release Notes
  order: 3
---

Use the official `v0.6.1` release notes for the current Windows release in the current `v0.6.x` Early Access lane.

Related guidance: use [Download for Windows](/download/) for release access and [Install and Download](/docs/install-download/) for release integrity context.

## Current release notes

Official notes for the current release:

- [`RELEASE_NOTES.md` for `v0.6.1`](https://github.com/solidsynapse/MCP-Synapse/blob/main/docs/release/releases/v0.6.1/RELEASE_NOTES.md)

## v0.6.1 highlights

The current `v0.6.1` release closes the packaged runtime hotfix verification set and synchronizes the public release surface.

- Worker-default ON behavior was revalidated on the packaged path.
- Worker ON/OFF/fallback smoke was revalidated.
- Packaged clean first-run and no-dispatch-regression smoke were revalidated.
- RC-EXT hygiene closure is recorded for health alerts, shortcuts baseline, security hygiene, and debuggability minimum.
- Windows packaging readiness, clean install, and clean uninstall were revalidated for the current NSIS and MSI artifacts.

## Release integrity

Public releases include a tag, SHA256, and release notes.

- Tag: Published with the release.
- SHA256: Published with the release.
- Release notes: Published with the release.
- Supporting release files for `v0.6.1` include `INSTALL_RUN_NOTES.md`, `KNOWN_ISSUES.md`, `TRUST_SECURITY.md`, `WHAT_CHANGED.md`, and `UNSIGNED_NOTICE.md`.

## Signing status

While unsigned mode is active, unsigned status is explicitly disclosed.

For `v0.6.1`, review the release-specific unsigned notice alongside the release notes:

- [`UNSIGNED_NOTICE.md`](https://github.com/solidsynapse/MCP-Synapse/blob/main/docs/release/releases/v0.6.1/UNSIGNED_NOTICE.md)

## Security disclosures

For security disclosures, contact [security@solidsynapse.com](mailto:security@solidsynapse.com).
