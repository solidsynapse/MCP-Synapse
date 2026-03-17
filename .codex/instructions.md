# Codex Instructions — MCP Synapse

## Before Starting Any Task
1. Read `AGENTS.md` — rules and boundaries.
2. Read `.gsd/STATE.md` — current position.
3. Read the relevant slice plan under `.gsd/milestones/`.
4. If the task touches UI: read `docs/UI_STYLE_GUIDE.md`.

## Code Style
- Minimal diff — change only what is needed for the task.
- No speculative refactoring outside task scope.
- No new dependencies without explicit user approval.
- Preserve existing naming conventions in each layer (Python backend, Svelte frontend, Rust shell).

## After Any Code Change
- Run `pytest -q` from repo root — confirm no regressions.
- If UI changed: verify affected route renders without errors.
- Update `.gsd/STATE.md` if task is complete.

## Commit Format
```
<type>(<scope>): <short description>

type: feat | fix | docs | refactor | test | chore
scope: backend | ui | shell | infra | ssot
```

## Ask Before Doing
- Changing file structure or moving files
- Adding a new dependency
- Modifying anything under `docs/`
- Making a change that affects more than one layer at once

## When Unsure
- Stop and ask. Do not guess.
- Prefer `REVALIDATE` over marking something done.
- Narrow scope beats broad fix.
