# M001: SSOT migration + planning frame

**Vision:** Establish `.gsd/` as the active working SSOT for MCP Synapse by carrying forward the current project truth from the historical `docs/` archive, preserving the selected active decisions verbatim, defining the capability contract, and preparing the broader `v0.7.x` execution milestone without doing implementation work in M001.

## Success Criteria

- `.gsd/` contains a coherent working-layer view of the project’s current truth, active constraints, deferred items, and next action.
- The selected active decisions from the historical archive are preserved verbatim in `.gsd/DECISIONS.md`.
- `.gsd/REQUIREMENTS.md` explicitly carries the current release-hygiene open set, current deferrals, and current first-release scope truth.
- M002 is defined as the broader `v0.7.x` execution milestone, with runtime/public-surface hotfix closure ordered as the first high-risk slice.

## Key Risks / Unknowns

- Carry-forward drift — moving from `docs/` to `.gsd/` could accidentally change active product constraints.
- Planning-layer bloat — `.gsd/` could become another archive if too much historical material is copied verbatim outside the mandated decision set.
- Execution boundary confusion — M001 could accidentally absorb M002 implementation work if the planning/execution split is not enforced.

## Proof Strategy

- Carry-forward drift → retire in S01 by proving the required decision set is preserved verbatim and the current-scope truth is explicitly mapped into `.gsd/`.
- Planning-layer bloat → retire in S02 by proving requirements and milestone sequence capture active truth without importing the whole archive.
- Execution boundary confusion → retire in S03 by proving M002 is planned as the broader `v0.7.x` execution milestone while M001 remains planning-only.

## Verification Classes

- Contract verification: artifact checks on `.gsd/` files; verbatim comparison for carried decisions; requirement/roadmap/state consistency checks
- Integration verification: cross-check that PROJECT/REQUIREMENTS/DECISIONS/STATE/M001 roadmap agree on current truth and next milestone
- Operational verification: a fresh agent can start from `.gsd/STATE.md` and identify the next action without using `docs/` as active SSOT
- UAT / human verification: none

## Milestone Definition of Done

This milestone is complete only when all are true:

- active truth from the archive has been carried into `.gsd/` without modifying `docs/`
- selected active decisions are preserved verbatim in `.gsd/DECISIONS.md`
- the capability contract exists in `.gsd/REQUIREMENTS.md` and the RC-EXT release hygiene open set is explicitly visible under Active
- current truth is explicitly carried forward in REQUIREMENTS and STATE: Bedrock blocked/de-scoped, perf smoke deferred, English docs deferred, Usage Summary parity deferred
- D-032 is not copied verbatim, but its current-scope truth is reflected in REQUIREMENTS and STATE
- M002 is defined as the broader `v0.7.x` execution milestone and runtime/public-surface hotfix closure is its first high-risk slice
- a fresh agent can read `.gsd/STATE.md` and know what to do next

## Requirement Coverage

- Covers: R001, R002, R003, R013, R023
- Partially covers: R005
- Leaves for later: R004, R006, R007, R008, R009, R010, R011, R012, R022
- Orphan risks: none

## Slices

- [ ] **S01: Archive truth extraction and decision carry-forward** `risk:high` `depends:[]`
  > After this: `.gsd/DECISIONS.md` preserves the active selected decisions verbatim and `.gsd/` reflects the current first-release scope truth from the archive.
- [ ] **S02: Capability contract and milestone mapping** `risk:medium` `depends:[S01]`
  > After this: `.gsd/REQUIREMENTS.md` maps the active/deferred/out-of-scope contract and mirrors the archive-aligned `0.7 / 0.8 / 0.9 / 1.0` progression.
- [ ] **S03: M002 execution frame bootstrap** `risk:medium` `depends:[S01,S02]`
  > After this: M002 is planned as the broader `v0.7.x` execution milestone, with runtime/public-surface hotfix closure ordered as the first high-risk slice.
- [ ] **S04: State handoff and fresh-agent bootstrap** `risk:low` `depends:[S01,S02,S03]`
  > After this: `.gsd/STATE.md` and the milestone artifacts are enough for a fresh agent to continue without reconstructing active truth from `docs/`.

## Boundary Map

### S01 → S02

Produces:
- `.gsd/DECISIONS.md` → verbatim carry-forward of D-024, D-029, D-033, D-037, D-038, D-039
- `.gsd/PROJECT.md` → current project identity, current release lane, and milestone sequence baseline
- Current-scope truth set → Bedrock blocked/de-scoped; perf smoke deferred; English docs deferred; Usage Summary parity deferred

Consumes:
- nothing (first slice)

### S02 → S03

Produces:
- `.gsd/REQUIREMENTS.md` → active/deferred/out-of-scope capability contract
- M001 requirement coverage → mapping from bootstrap work to the archive-aligned milestone sequence
- M002 scope anchors → broader `v0.7.x` execution definition and RC-EXT open-set visibility

Consumes:
- `.gsd/DECISIONS.md` → active architectural and product-boundary constraints
- `.gsd/PROJECT.md` → current state and milestone sequence baseline

### S03 → S04

Produces:
- `M002` planning frame target → broader `v0.7.x` execution milestone with first high-risk runtime/public-surface hotfix slice
- Next-action target for state handoff → exact immediate planning continuation point

Consumes:
- `.gsd/REQUIREMENTS.md` → active requirements and deferred/current-scope truth
- `.gsd/DECISIONS.md` → governing constraints for later milestone planning

### S04 → Next Milestone

Produces:
- `.gsd/STATE.md` → active milestone/slice/task position, current blockers, recent decisions, and next action
- Fresh-agent bootstrap path → `.gsd/STATE.md` -> `M001` roadmap -> `M002` planning frame

Consumes:
- M001 roadmap and requirements artifacts
- Current-scope truth carried forward from the archive
