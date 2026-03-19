---
title: Security
description: Public-safe security guidance for the current v0.8.x Early Access lane.
sidebar:
  label: Security
  order: 4
---

This page describes public-safe security guidance for the current `v0.8.x` Early Access lane.

Use [security@solidsynapse.com](mailto:security@solidsynapse.com) for security reports.

## Security scope and release-lane context

Security review and disclosure handling on this site apply to the current `v0.8.x` Early Access lane.

Read this page alongside release notes and release integrity details.

## Report a vulnerability

Report vulnerabilities privately to [security@solidsynapse.com](mailto:security@solidsynapse.com).

- Include affected version or build.
- Include reproduction steps.
- Include expected versus observed behavior.
- Include impact and redacted logs or screenshots.
- Do not post unpatched security issues publicly first.

## Disclosure process

We acknowledge receipt, triage severity, and coordinate remediation and disclosure timing.

Security-relevant fixes are published through official release notes.

## Current security posture and product boundaries

- mcp synapse uses a BYOK/local-only operating model.
- Provider and REST-source calls are user-configured and remain within configured provider or endpoint boundaries.
- The product path is non-streaming for this lane.
- The product path uses no hidden retry, backoff, or silent fallback.
- mcp synapse is not a hosted proxy service.

## Release integrity and unsigned status

This release lane is temporarily unsigned; Windows SmartScreen warnings may appear.

Download from the official channel, verify hashes from [`docs/release/releases/v0.8.0/SHA256SUMS.txt`](https://github.com/solidsynapse/MCP-Synapse/blob/main/docs/release/releases/v0.8.0/SHA256SUMS.txt), and review the current release notes.

Commercial code signing remains outside the current lane. Until that changes, hash verification stays part of the expected release workflow.

## In-scope and out-of-scope report types

- In scope: vulnerabilities in mcp synapse source, packaging, and official release artifacts.
- In scope: security-impacting behavior in local credential handling, dispatch boundaries, REST adapter behavior, and release integrity surface.
- Out of scope: third-party provider platform incidents outside this repository.
- Out of scope: reports containing unredacted real secrets.
