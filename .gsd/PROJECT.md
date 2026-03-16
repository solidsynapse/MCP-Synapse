# Project

## What This Is

MCP Synapse is a provider-agnostic desktop MCP router/control plane. It uses a Tauri shell with a SvelteKit frontend and a Python backend that owns Pipeline V1 routing, provider execution, usage tracking, and operational policy surfaces. The product is already in the `v0.6.x` Early Access lane and the current job is to establish `.gsd/` as the active working SSOT while preserving `docs/` as a read-only historical archive.

## Core Value

A local-first, BYOK MCP control plane that routes and manages provider-backed AI execution through a deterministic backend core while keeping the desktop UI as a thin shell.

## Current State

Current release lane is `v0.6.x (Early Access)`. Active first-release providers are OpenAI, Azure OpenAI, Vertex AI, HuggingFace, and Ollama. Bedrock is currently blocked by external quota/allowlist constraints and is de-scoped/hidden from the first-release surface. The repo already contains a substantial historical SSOT in `docs/`, including release gating, architecture decisions, UI thin-shell constraints, release integrity policy, and the current open release-hygiene set. `.gsd/` is now the active working layer; `docs/` remains the historical archive and must not be modified or deleted as part of this bootstrap.

## Architecture / Key Patterns

- Desktop shell: Tauri
- Frontend: SvelteKit
- Backend/core: Python
- Routing core: Pipeline V1
- UI rule: thin shell only — configure, dispatch, render
- Provider/network logic rule: backend/core only
- Product boundary: BYOK + local-only
- Runtime rule: deterministic behavior, no silent fallback/retry/backoff on product paths unless explicitly authorized
- Verification rule: evidence-first; decisions require rationale and work requires proof

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [ ] M001: SSOT migration + planning frame — Move active truth from `docs/` into `.gsd/`, preserve locked decisions verbatim, establish requirements/state/roadmaps, and prepare execution without changing runtime behavior.
- [ ] M002: v0.7.x release closure and readiness — Close the broader `0.7` execution lane: runtime/public-surface hotfix closure, release hygiene, packaging, install/uninstall readiness, and repo/release surface sync.
- [ ] M003: v0.8.x hardening baseline — Close provider/security/performance/documentation hardening work for the post-`0.7` lane.
- [ ] M004: v0.9.x to v1.0.0 progression — Drive domain-agnostic migration-readiness and the path toward execution-fabric completion.
