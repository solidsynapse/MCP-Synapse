# Security Policy

## Supported Release Line

Security review and disclosure handling currently apply to the active Early Access release lane:

- `v0.6.x`

Versioning policy and release lane constraints are tracked in [`docs/DECISIONS.md`](docs/DECISIONS.md).

## Reporting a Vulnerability

Report vulnerabilities privately to:

- **security@solidsynapse.com**

Include:

- Affected version/build
- Reproduction steps
- Expected behavior vs observed behavior
- Impact assessment
- Logs or screenshots with secrets redacted

Do not post unpatched security issues publicly first.

## Disclosure Expectations

- We acknowledge receipt and triage severity.
- We coordinate remediation and disclosure timing.
- We publish security-relevant fixes through official release notes.

## Security Posture (Current)

- Local-first operation and BYOK credential model
- Provider calls are user-configured and stay within configured provider boundaries
- Deterministic product-path behavior (no hidden retry/backoff or silent fallback per SSOT)

## Unsigned Early Access Notice

This release lane is temporarily unsigned. Windows SmartScreen may show warnings before first run.

Before running a release artifact:

1. Download from the official release channel.
2. Verify hashes from [`docs/release/releases/v0.6.1/SHA256SUMS.txt`](docs/release/releases/v0.6.1/SHA256SUMS.txt).
3. Review [`docs/release/releases/v0.6.1/UNSIGNED_NOTICE.md`](docs/release/releases/v0.6.1/UNSIGNED_NOTICE.md).

## Scope

In scope:

- Vulnerabilities in MCP Synapse source code, packaging, and official release artifacts
- Security-impacting behavior in dispatch boundaries, local credential handling, and release integrity surface

Out of scope:

- Third-party provider platform incidents outside this repository
- Issues requiring unsupported environment modifications
- Reports that include unredacted real secrets
