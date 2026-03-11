# MCP Synapse

MCP Synapse is a local-first control plane for MCP connections and request routing. It provides a unified desktop surface to manage connections, apply policy and resilience controls, and inspect usage while keeping provider execution in the backend core.

## Early Access Status

This repository is in the `v0.6.x` Early Access release lane.

- Current release package: [`docs/release/releases/v0.6.0-rc.1/`](docs/release/releases/v0.6.0-rc.1/)
- Binding project SSOT: [`docs/DECISIONS.md`](docs/DECISIONS.md), [`docs/STATUS.md`](docs/STATUS.md), [`docs/TASKS.md`](docs/TASKS.md)

## Why MCP Synapse Exists

- Provider-agnostic operational surface for MCP connection management and routing controls
- Local-first, BYOK posture for credentials and runtime operation
- Deterministic request handling with explicit error behavior
- Consolidated policy, resilience, and usage visibility in one desktop app

## Key Capabilities

- Connection lifecycle operations (create, edit, start, stop, delete)
- Dashboard and usage visibility for request-level operations
- Policy surfaces (Persona, Optimizations)
- Resilience surfaces (Budget Guards, Interceptors)
- Packaged desktop runtime with release integrity artifacts

## Architecture Boundaries

- UI is a thin shell: collect state, dispatch requests, render results
- Production UI request path goes through a single dispatch entrypoint
- Provider and network logic remain in backend core under `src/`
- No hidden retry/backoff or silent fallback on product paths (per SSOT)

## Security Model (Local-First / BYOK)

- Credentials are user-owned and managed locally
- Runtime behavior is designed to be explicit and deterministic
- Security reporting and disclosure policy: [`SECURITY.md`](SECURITY.md)
- Release trust note: [`docs/release/releases/v0.6.0-rc.1/TRUST_SECURITY.md`](docs/release/releases/v0.6.0-rc.1/TRUST_SECURITY.md)

## Install and Verify Release Integrity

- Install/run notes: [`docs/release/releases/v0.6.0-rc.1/INSTALL_RUN_NOTES.md`](docs/release/releases/v0.6.0-rc.1/INSTALL_RUN_NOTES.md)
- Release notes: [`docs/release/releases/v0.6.0-rc.1/RELEASE_NOTES.md`](docs/release/releases/v0.6.0-rc.1/RELEASE_NOTES.md)
- What changed: [`docs/release/releases/v0.6.0-rc.1/WHAT_CHANGED.md`](docs/release/releases/v0.6.0-rc.1/WHAT_CHANGED.md)
- SHA256 checksums: [`docs/release/releases/v0.6.0-rc.1/SHA256SUMS.txt`](docs/release/releases/v0.6.0-rc.1/SHA256SUMS.txt)
- Unsigned notice: [`docs/release/releases/v0.6.0-rc.1/UNSIGNED_NOTICE.md`](docs/release/releases/v0.6.0-rc.1/UNSIGNED_NOTICE.md)

PowerShell hash verification example:

```powershell
Get-FileHash -Algorithm SHA256 .\MCP Synapse_0.6.0-rc.1_x64-setup.exe
```

Compare the output hash with `SHA256SUMS.txt`.

## Documentation and Support

- Product docs: https://mcpsynapse.dev/docs
- Feedback: https://mcpsynapse.dev/feedback
- About: https://mcpsynapse.dev
- Check for updates: https://mcpsynapse.dev/download
- Product issues: GitHub Issues
- Security reports: [`SECURITY.md`](SECURITY.md)
