# 00_PROTOCOL — IDE ↔ ChatGPT Workflow (v1)

## North Star
Product goal: become a universal bridge/router across providers that do NOT offer native MCP inside IDEs — without being tied to Vertex.

## SSOT (single source of truth)
Only these files define truth:
- docs/STATUS.md
- docs/PLAN.md
- docs/TASKS.md
- docs/DECISIONS.md
- docs/ARCHITECTURE_EVOLUTION_LOG.md

Any claim must be backed by evidence: file+line or command output.

## Evidence standard
- For each meaningful step, create: `docs/evidence/<TASK_ID>_<slug>_<timestamp>/`
  - _meta.txt (stores the evidence folder path)
  - 3–10 evidence files (linenum dumps / grep outputs / test outputs)
- “Done evidence” must reference that folder.

## ID discipline
- No new IDs unless the current maximum ID is proven by file+line.
- Never reuse an ID with a different meaning.

## Hard role boundaries
- IDE Builder: makes changes + runs tests/commands + produces evidence.
- IDE Verifier: validates evidence only; if missing, requests the minimum commands.
- ChatGPT Supervisor+Gatekeeper: decides “close / not close” using SSOT + evidence only; emits SSOT edit blocks when needed.
- IDE Debugger: 3 hypotheses / 3 experiments / rollback.

## Supervisor output format (strict)
Output ONLY:
- Decision
- Actions
- Verification
- Rollback
