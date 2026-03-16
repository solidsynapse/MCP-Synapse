# M001/S01 — Research

**Date:** 2026-03-16

## Summary

S01 is a verification-focused planning slice, not an implementation slice. The working-layer artifacts that matter for this slice already exist: `.gsd/DECISIONS.md` contains the required carry-forward decisions, `.gsd/PROJECT.md` states the current release lane and first-release provider truth, `.gsd/REQUIREMENTS.md` assigns S01 ownership for `R001`, `R002`, and `R023`, and `.gsd/STATE.md` already gives a fresh-agent next action. For this slice, the real work is to prove that these artifacts faithfully carry forward active truth from the archive without turning `.gsd/` into another copy of `docs/`.

The planner should target the active requirements this slice owns or supports: `R001` (`.gsd/` becomes the active working SSOT), `R002` (selected decisions preserved verbatim), `R023` (BYOK + local-only boundary preserved), and S01’s support contribution to `R003` (current project truth visible in working-layer state). Archive evidence for the current-scope truth is concentrated in `docs/STATUS.md`, with supporting framing in `README.md` and `docs/DECISIONS.md`. The highest-risk failure mode is drift in the carried-forward decision text, so the first planner task should be an exact proof pass on the mandated decision set.

## Recommendation

Use a proof-and-lock approach. Do not reopen broad archive migration, do not modify `docs/`, and do not plan any runtime work under S01. Decompose the slice into small verification tasks that compare the selected decision set in `.gsd/DECISIONS.md` against `docs/DECISIONS.md`, then confirm that the archive’s current-scope truth is explicitly visible in `.gsd/PROJECT.md`, `.gsd/REQUIREMENTS.md`, and `.gsd/STATE.md`.

Order the work around the non-negotiable constraints. First prove `R002` by validating D-024, D-029, D-033, D-037, D-038, and D-039 are preserved verbatim in `.gsd/DECISIONS.md`. Next prove the working-layer current truth needed for `R001` and S01’s support of `R003`: `v0.6.x (Early Access)` lane, `.gsd/` as active SSOT, Bedrock blocked/de-scoped from first release, perf smoke deferred, English docs deferred, Usage Summary parity deferred, and M002 framed as the broader `v0.7.x` execution milestone. Treat `R023` as part of the same pass by verifying the BYOK + local-only boundary remains explicit in both the carried decision text and product-facing/project-facing summaries.

## Implementation Landscape

### Key Files

- `.gsd/DECISIONS.md` — primary S01 proof target; contains the carry-forward block for D-024, D-029, D-033, D-037, D-038, and D-039, plus a non-verbatim note explaining that D-032 truth is carried elsewhere.
- `.gsd/PROJECT.md` — working-layer project identity and milestone baseline; already states `v0.6.x (Early Access)`, `.gsd/` as active SSOT, the BYOK/local-first positioning, and Bedrock as blocked/de-scoped from the first-release surface.
- `.gsd/REQUIREMENTS.md` — ownership map and capability contract; S01 owns `R001`, `R002`, and `R023`, while `R003` is primarily owned by S04 but explicitly supported by S01. Also records the deferred/current-scope truth set planners must preserve.
- `.gsd/STATE.md` — fresh-agent bootstrap target; already includes current milestone/slice/task, recent decision summary, and the exact next action to create `S01-PLAN.md`.
- `docs/DECISIONS.md` — archive-side source for verbatim comparison of D-024, D-029, D-033, D-037, D-038, and D-039. Use only as comparison input, not as a target for edits.
- `docs/STATUS.md` — main archive source for current-scope truth. The critical lines are the current release lane, Bedrock external blocker/de-scope, the RC-EXT open set, and the carry-forward deferred items: perf smoke, English docs, and Usage Summary parity polish.
- `README.md` — public product-facing cross-check for current surface truth: early-access lane, local-first/BYOK posture, thin-shell framing, and release-integrity/product-first positioning.
- `.gsd/milestones/M001/M001-ROADMAP.md` — authoritative slice contract. Its S01 “After this” statement defines the actual outcome to prove.
- `.gsd/milestones/M001/M001-CONTEXT.md` — milestone rationale and source mapping; useful for planner wording and acceptance framing.
- `.gsd/milestones/M002/M002-CONTEXT.md` — confirms the D-032-related current-scope truth that M002 is the broader `v0.7.x` execution milestone and not a narrow hotfix-only milestone.

### Build Order

1. Prove exact decision carry-forward in `.gsd/DECISIONS.md`.
   - Compare D-024, D-029, D-033, D-037, D-038, and D-039 against `docs/DECISIONS.md`.
   - This is the highest-risk and least-forgiving requirement because `R002` demands verbatim preservation, not semantic equivalence.
2. Prove current-scope truth carry-forward across the working layer.
   - Check `.gsd/PROJECT.md`, `.gsd/REQUIREMENTS.md`, and `.gsd/STATE.md` against the archive signals in `docs/STATUS.md` and `README.md`.
   - Focus only on the milestone-mandated truth set: `.gsd/` as active SSOT, current release lane, Bedrock blocked/de-scoped, perf smoke deferred, English docs deferred, Usage Summary parity deferred, and the M002 `v0.7.x` framing.
3. Convert the proof set into `S01-PLAN.md` tasks.
   - The plan should be file-oriented and deterministic: one task for verbatim decision proof, one task for working-layer truth proof, and one task for final slice acceptance/state sync if needed.
   - This gives downstream planners/executors a clear boundary without re-reading the whole archive.

### Verification Approach

- S01 should use artifact verification only; no runtime build, test, packaging, or browser verification is needed.
- Verify `.gsd/DECISIONS.md` preserves D-024, D-029, D-033, D-037, D-038, and D-039 verbatim from `docs/DECISIONS.md`.
- Verify `.gsd/PROJECT.md` explicitly states:
  - `.gsd/` is the active working layer and `docs/` remains the archive
  - current lane is `v0.6.x (Early Access)`
  - Bedrock is blocked and de-scoped/hidden from first release
  - product boundary remains BYOK + local-only
- Verify `.gsd/REQUIREMENTS.md` encodes:
  - S01 ownership for `R001`, `R002`, and `R023`
  - S01 support for `R003`
  - current-truth notes for Bedrock blocked/de-scoped, perf smoke deferred, English docs deferred, Usage Summary parity deferred
  - D-032 treated as current-scope truth only, not copied verbatim
- Verify `.gsd/STATE.md` is sufficient for a fresh agent to continue by checking that it contains:
  - active milestone/slice/task
  - recent decisions including the current-truth carry-forward set
  - the exact next action to create `S01-PLAN.md`
- Final acceptance should be file-check based: if a fresh agent can start from `.gsd/STATE.md` and proceed with S01 planning without treating `docs/` as the active SSOT, the slice is researched well enough for planning.

## Constraints

- `docs/` is a read-only historical archive; S01 must not modify it.
- M001 is planning-only. No runtime, release, packaging, repo-surface cleanup, or provider implementation work belongs in this slice.
- The selected decision set must remain verbatim. Summary checks are insufficient for `R002`.
- D-032 is intentionally not carried verbatim into `.gsd/DECISIONS.md`; only its current-scope truth should appear in `.gsd/REQUIREMENTS.md`, `.gsd/STATE.md`, and milestone framing.
- `.gsd/` must remain concise working truth, not a second archive dump.

## Common Pitfalls

- **Treating presence as proof** — Seeing the decision headings is not enough; S01 needs exact verbatim preservation for the mandated decisions.
- **Over-copying archive material** — Pull only the active truth set into checks and planning. Do not mirror large `docs/STATUS.md` or `docs/TASKS.md` sections into new working-layer artifacts.
- **Smuggling M002 execution into M001** — The runtime/public-surface hotfix lane, release hygiene closure, packaging, and repo-surface alignment all belong to M002, even if S01 references them as future scope truth.
- **Reintroducing D-032 verbatim** — The milestone explicitly forbids that; planners should verify only its carried-forward implications.

## Open Risks

- The biggest risk is silent drift in `.gsd/DECISIONS.md`: a lightly edited or normalized version of the archived decisions could look correct while failing the verbatim requirement.
- `docs/STATUS.md` contains a lot of historical detail. If planner tasks are not tightly scoped to the milestone’s named truth set, later agents may waste context re-exploring irrelevant phase history.

## Sources

- Milestone contract and slice boundary: `.gsd/milestones/M001/M001-ROADMAP.md`, `.gsd/milestones/M001/M001-CONTEXT.md`
- Working-layer artifacts to prove: `.gsd/DECISIONS.md`, `.gsd/PROJECT.md`, `.gsd/REQUIREMENTS.md`, `.gsd/STATE.md`
- Archive-side comparison anchors: `docs/DECISIONS.md`, `docs/STATUS.md`, `README.md`
- M002 framing cross-check: `.gsd/milestones/M002/M002-CONTEXT.md`
