# 00_PROTOCOL — IDE ↔ ChatGPT Working Protocol (v1)

## Goal (must not drift)
Solid Synapse aims to be a universal bridge/router across providers — not tied to Vertex — especially for providers that do not offer native MCP inside IDEs.

## SSOT (single source of truth)
Only these files are SSOT:
- docs/STATUS.md
- docs/PLAN.md
- docs/TASKS.md
- docs/DECISIONS.md
- docs/ARCHITECTURE_EVOLUTION_LOG.md

Any claim must be backed by evidence: file+line or command output.

## Agent contracts (NOT SSOT)
- docs/internal/agents/*.md define agent behavior and boundaries.
- They must not conflict with SSOT.

## Evidence standard
For each meaningful step, create:
- docs/evidence/<TASK_OR_TEST>_<timestamp>/
  - _meta.txt (stores the evidence folder path)
  - 3–10 evidence files (linenum dumps / grep outputs / test outputs)
“Done evidence” must reference that folder.

## Roles
- Solo Coder (Orchestrator/Main Coder): implements + runs commands + produces evidence; may call Verifier/Debugger.
- IDE Verifier: validates evidence only; if missing, requests the minimum commands.
- IDE Debugger: 3 hypotheses, 3 minimal experiments, expected outputs, rollback.
- ChatGPT Supervisor+Gatekeeper: decides “close / not close” using SSOT + evidence only; emits SSOT edit blocks when needed.

## Scope boundary
- No second verifier on ChatGPT side (avoid drift/dupe).
- No code patches from ChatGPT side; code/evidence work happens in IDE.
- No scope expansion without an explicit TASKS backlog item (Supervisor decides).
