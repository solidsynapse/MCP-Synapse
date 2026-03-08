# Release Tag Policy

Status: Active
Owner: Release Management

## Version lane
- Current public lane: `v0.6.x (Early Access)`.
- Do not use `v1.0.0` before domain-agnostic execution-fabric completion (D-037).

## Tag format
- Release candidate: `v0.6.0-rc.N`
- Stable patch in lane: `v0.6.P`
- Next milestones:
  - `v0.7.x`: RC-EXT + packaging closure
  - `v0.8.x`: hardening/security/perf baseline/docs
  - `v0.9.x`: migration-readiness + code-signing start

## Rules
- Every public binary maps to exactly one git tag.
- Tags are immutable after release.
- Hotfixes require new patch tag; no retagging.
