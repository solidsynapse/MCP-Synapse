---
depends_on: [M001]
---

# M002: v0.7.x release closure and readiness — Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

## Project Description

M002 is the broader `v0.7.x` execution milestone for MCP Synapse. It is not a narrow hotfix milestone. It closes the runtime/public-surface hotfix lane first, then drives the full `0.7` release-closure set: release hygiene, packaging, install/uninstall readiness, repo/release surface sync, and the explicit trust/distribution boundary required for the Early Access lane.

## Why This Milestone

The archive defines `v0.7.x` as the RC-EXT closure and packaging/install readiness milestone. Current truth shows an open release-hygiene set, a narrow runtime hotfix in progress, and public-surface alignment work still to close. M002 exists to turn those open truths into a coherent evidence-backed release-closure package.

## User-Visible Outcome

### When this milestone is complete, the user can:

- run the packaged app on the intended release profile with the current runtime truth validated
- inspect a product-first repository and release surface that matches the shipped lane and trust posture
- verify release integrity/distribution artifacts for the `v0.7.x` lane

### Entry point / environment

- Entry point: packaged app + repository release surface + release artifacts
- Environment: local packaged runtime / public repo surface / release package surface
- Live dependencies involved: packaged app runtime, provider integrations already in first-release scope, release artifacts

## Completion Class

- Contract complete means: all `v0.7.x` release-closure requirements are explicitly mapped and proven.
- Integration complete means: runtime truth, packaging/install behavior, repo surface, and release artifacts agree with one another.
- Operational complete means: packaged first-run/readiness and fallback/runtime stance are validated on the real release path.

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- the runtime/public-surface hotfix lane is closed with evidence on the current packaged path
- the RC-EXT release hygiene open set is closed or explicitly reclassified with rationale
- packaging/install/uninstall readiness and release integrity artifacts match the product’s public-facing release surface
- the repo/release surface presents MCP Synapse as a product-first Early Access release without violating BYOK + local-only boundaries

## Risks and Unknowns

- Runtime hotfix truth may diverge between code-level expectation and packaged behavior.
- Public repo/release surface may still leak internal-orchestration shape or stale wording.
- Packaging/install readiness may expose edge conditions not visible in earlier evidence packs.

## Existing Codebase / Prior Art

- `docs/STATUS.md` — current release-open set, deferrals, and runtime hotfix snapshot
- `docs/DECISIONS.md` — release/versioning/distribution/public-surface decisions
- `README.md` — current product-first surface baseline
- `docs/release/releases/v0.6.0-rc.1/` — current release artifact/document surface
- `ui-tauri/src-tauri/` and backend runtime surfaces — current packaging/runtime implementation base

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R004 — runtime/public-surface hotfix closure is proven
- R005 — release hygiene is complete for `v0.7.x`
- R006 — packaging and install/uninstall readiness are proven
- R007 — repository and release surface are product-first and aligned
- R008 — health alerts calibration is closed with evidence
- R009 — minimum shortcuts baseline is present and verified
- R010 — security hygiene minimum is closed with evidence
- R011 — debuggability minimum is present and verified
- R012 — packaging/versioning readiness is closed with evidence
- R022 — release integrity and distribution policy is established
- R023 — BYOK + local-only boundary is preserved and verified

## Scope

### In Scope

- runtime/public-surface hotfix closure as first high-risk slice
- broader RC-EXT release hygiene closeout
- packaging/install/uninstall readiness
- repo/release surface sync and product-first public surface
- release integrity/distribution surface alignment

### Out of Scope / Non-Goals

- changing the archive milestone progression
- Bedrock unblock/enablement as part of first-release closure
- deferred polish/future enhancements already classified in REQUIREMENTS

## Technical Constraints

- Thin-shell UI and backend-owned provider logic remain binding
- BYOK + local-only boundary remains binding
- no silent fallback/retry/backoff without explicit authorization
- evidence-first verification is mandatory for each closure claim

## Integration Points

- packaged runtime profile and fallback path
- README / SECURITY / release package surface
- release artifact integrity set (tag, SHA256, changelog, unsigned disclosure, trademark baseline)
- current first-release provider surface (excluding Bedrock)

## Open Questions

- exact slice decomposition for M002 remains to be planned under the new `.gsd/` working layer
