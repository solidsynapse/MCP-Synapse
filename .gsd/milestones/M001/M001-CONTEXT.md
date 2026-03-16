# M001: SSOT migration + planning frame — Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

## Project Description

MCP Synapse is a brownfield desktop MCP router/control plane with a Tauri shell, a SvelteKit frontend, and a Python backend that owns Pipeline V1 routing and provider execution. The repository already contains a substantial historical SSOT and evidence archive under `docs/`. M001 does not change runtime behavior. Its job is to establish `.gsd/` as the active working SSOT, carry forward current truth, preserve the selected active decisions verbatim, and prepare the next milestone for real execution work.

## Why This Milestone

The project already has release history, active architecture constraints, and an evidence-backed archive, but the active working layer needs to move into `.gsd/` so future planning and execution stop depending on reconstructing state from historical documents. This milestone exists to make current truth explicit, preserve locked decisions, and create a clean planning frame before any new implementation work begins.

## User-Visible Outcome

### When this milestone is complete, the user can:

- open `.gsd/` and understand the current project truth, active constraints, deferred items, and next milestone without re-reading the archive
- hand the repo to a fresh agent and have it start from `.gsd/STATE.md` and the new milestone files instead of rebuilding context from `docs/`

### Entry point / environment

- Entry point: `.gsd/PROJECT.md`, `.gsd/REQUIREMENTS.md`, `.gsd/DECISIONS.md`, `.gsd/STATE.md`
- Environment: local dev / repository planning layer
- Live dependencies involved: none

## Completion Class

- Contract complete means: the `.gsd/` working layer exists, active decisions are carried forward verbatim where required, requirements are mapped, and milestone sequencing matches the archive progression.
- Integration complete means: the working SSOT, current state, and next milestone plan agree with one another and reflect the current truth from the archive.
- Operational complete means: a fresh agent can start from `.gsd/STATE.md` and continue without relying on hidden chat context.

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- the active working truth from `docs/` has been carried into `.gsd/` without modifying the archive
- selected active decisions (D-024, D-029, D-033, D-037, D-038, D-039) are preserved verbatim in `.gsd/DECISIONS.md`
- current truth is explicitly represented in `.gsd/REQUIREMENTS.md` and `.gsd/STATE.md`, including Bedrock blocked/de-scoped, perf smoke deferred, English docs deferred, Usage Summary parity deferred, and the broader `v0.7.x` execution truth for M002

## Risks and Unknowns

- Archive drift vs current truth — historical files contain both normative decisions and historical checkpoints; M001 must carry forward only the active working truth.
- Over-migration risk — copying too much from `docs/` would turn `.gsd/` into another archive instead of a working layer.
- Under-migration risk — dropping active constraints would cause execution drift in later milestones.

## Existing Codebase / Prior Art

- `docs/DECISIONS.md` — historical decisions register; active selected decisions must be preserved verbatim
- `docs/STATUS.md` — current truth snapshot, open release-hygiene set, deferred items, Bedrock block/de-scope, and current release lane
- `docs/TASKS.md` — historical task decomposition and open-set signals
- `docs/ARCHITECTURE_LOG.md` — legacy-to-Pipeline-V1 evolution context
- `README.md` — current public product-facing surface

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R001 — establishes `.gsd/` as active working SSOT
- R002 — preserves active decisions verbatim
- R003 — re-establishes current state in `.gsd/`
- R013 — mirrors the archive-aligned `0.7 / 0.8 / 0.9 / 1.0` progression
- R023 — preserves the BYOK + local-only boundary

## Scope

### In Scope

- migrate active planning truth from `docs/` into `.gsd/`
- preserve selected decisions verbatim in `.gsd/DECISIONS.md`
- define requirements and milestone sequencing in `.gsd/`
- create the planning frame for M002 as the broader `v0.7.x` execution milestone

### Out of Scope / Non-Goals

- runtime hotfix implementation or verification
- release docs or repo-surface implementation work
- packaging/install/uninstall execution work
- provider expansion or Bedrock unblock work

## Technical Constraints

- `docs/` stays read-only historical archive
- M001 is planning-only; no runtime or product implementation changes
- selected decisions must be preserved verbatim, not summarized
- `.gsd/` must mirror the existing archive progression instead of replacing it with a new milestone model

## Integration Points

- `docs/DECISIONS.md` — source for verbatim decision carry-forward
- `docs/STATUS.md` — source for current truth and deferred/open items
- `docs/TASKS.md` — source for carry-forward of pending/open work signals
- `README.md` — source for current public-facing product truth

## Open Questions

- none for M001 bootstrap — user clarified decision carry-forward set, active/deferred requirement set, and milestone sequencing
