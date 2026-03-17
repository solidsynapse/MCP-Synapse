# AGENTS.md — MCP Synapse

## Language
- Respond to user: **Turkish**
- All file writes: **English**

---

## SSOT (normative — read before anything else)
- `.gsd/PROJECT.md` — what the project is right now
- `.gsd/DECISIONS.md` — locked architectural decisions (D-024, D-029, D-033, D-037, D-038, D-039)
- `.gsd/REQUIREMENTS.md` — active / deferred / out-of-scope capability contract
- `.gsd/STATE.md` — current position and next action
- `.gsd/milestones/` — milestone and slice plans
- `docs/UI_STYLE_GUIDE.md` — UI constraints (read-only reference)

> `docs/` is historical archive. Do not modify anything under `docs/`.

---

## Hard Rules

**Before any task:**
1. Read `.gsd/STATE.md` — know where you are.
2. Read the relevant milestone file under `.gsd/milestones/`.
3. Do not infer truth from chat history or prior PASS claims.

**Before any file edit:**
- Check `.gsd/DECISIONS.md` — does this change violate a locked decision?
- If yes: stop, report to user. Do not proceed.

**After any task:**
- Update `.gsd/STATE.md` to reflect current position.
- If a new architectural decision was made: append to `.gsd/DECISIONS.md`.

---

## What You Must Never Do
- Modify anything under `docs/`
- Add provider/network logic to UI layer (thin-shell boundary — D-024/D-029)
- Introduce shared-key or proxy-as-a-service patterns (D-033)
- Change version/milestone numbering without SSOT update (D-037)
- Invent new scope without updating `.gsd/REQUIREMENTS.md`
- Mark anything DONE without verifiable evidence

---

## Evidence Rule
Nothing is PASS unless: **current repo state + SSOT + evidence align.**

For any verification, write outputs to:
```
docs\evidence\<TASK_ID>_<yyyymmdd-hhmmss>\
```
Minimum: `commands_ran.txt`, `summary.txt`

---

## Default Behavior
- Default mode: **read and consult** — no edits without explicit user instruction.
- Scope: **narrow** — do the asked task only, nothing more.
- Prefer `REVALIDATE` over false `PASS`.

---

## Response Format
```
Verdict: PASS / FAIL / NARROW / BLOCKER / REVALIDATE
Evidence: (file refs or anchor proof)
Next: (1–2 bullets max)
```
