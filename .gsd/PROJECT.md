# Project

## What This Is

MCP Synapse is a provider-agnostic desktop MCP control plane and router. It provides a local-first desktop surface for configuring connections, dispatching requests, managing runtime operations, and observing usage, while the backend owns provider execution and routing.

## Current Stack

- Desktop shell: Tauri
- Frontend: SvelteKit + shadcn/ui
- Backend: Python
- Execution core: Pipeline V1
- Runtime stance: worker-primary packaged runtime, with legacy subprocess flow retained only as internal same-request fallback safety

## Release Lane

- Public release lane: `v0.6.x (Early Access)`
- Current observed build marker in runtime logs: `0.6.1`
- Next milestone lane: `v0.7.x`, focused on RC-EXT closure and packaging/install/uninstall readiness

## Active Providers

- Active first-release providers: `vertex`, `openai`, `azure_openai`, `huggingface`, `ollama`
- Implemented but not active on the first-release surface: `bedrock`
- Bedrock state: blocked by external quota/allowlist constraints and intentionally de-scoped/hidden from the first release

## Product Boundaries

- Operating model: BYOK + local-only orchestration
- UI rule: thin shell only; configure, dispatch, and render
- Provider/network logic: backend/core only
- Decision/archive rule: `docs/` is the historical archive; `.gsd/` is the active working layer

## Current Reality Summary

The historical SSOT in `docs/` already records release-gate closure, UI thin-shell constraints, provider policy, release versioning, licensing/distribution policy, and repository-surface policy. M001/S01 completed archive research and decision carry-forward preparation, but the S01 planning write-up was not produced because GSD auto-mode is currently broken on Windows. The next planning action moves to M002.
