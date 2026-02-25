# MCP Synapse (formerly MCP Router)

Local-first, BYOK routing layer with a thin-shell UI.

## What this repo is
MCP Synapse is a local-first control plane for:
- managing connections (bridges) and generating IDE config snippets
- dispatching requests to the headless/core surface
- viewing usage and policy/resilience controls

**Thin-shell rule:** The UI is a lightweight shell (form state + dispatch + render).  
Provider/network logic stays in core.

## Status
- UI: page-by-page replication + UI-only stubs (no provider calls)
- Wiring: single-entrypoint dispatch path exists; preflight/persisted config is next

SSOT (source of truth): docs/DECISIONS.md, docs/STATUS.md, docs/TASKS.md

## Quick start (dev)
### UI (SvelteKit/Tauri)
From ui-tauri/:
- 
pm run dev
- 
pm run check
- 
pm run build
- 
pm run tauri

### Python (core/headless)
- Requirements: equirements.txt
- Tests: python -m pytest -q

## Security
- Secrets must never be committed.
- Local-only artifacts (evidence, DBs, credentials) are ignored via .gitignore.

## Repo
This repository is currently private (pre-release).
