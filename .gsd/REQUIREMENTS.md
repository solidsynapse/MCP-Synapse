# Requirements

This file tracks the active working requirement set for `.gsd/`.

## Status Summary

| Status | Count |
|---|---:|
| Delivered | 1 |
| Active | 16 |
| Deferred | 3 |
| Out of scope | 3 |
| Total tracked | 23 |

## Delivered

| ID | Requirement | Class | Delivered in | Notes |
|---|---|---|---|---|
| R015 | Full English documentation pack | launchability | M003/S04 | Delivered through install/download, release-notes, feature reference, root user guide, web user guide, and legal/compliance minimum pack closure. |

## Active

| ID | Requirement | Class | Primary slice | Notes |
|---|---|---|---|---|
| R001 | Working SSOT migration into `.gsd/` | operability | M001/S01 | `.gsd/` becomes the active working SSOT; `docs/` remains archive-only. |
| R002 | Active architectural decisions preserved verbatim | constraint | M001/S01 | Carry forward only D-024, D-029, D-033, D-037, D-038, D-039 verbatim. |
| R003 | Current project state is re-established in `.gsd/` | operability | M001/S01 | `PROJECT.md` and `STATE.md` must describe present truth and immediate next action. |
| R004 | Runtime/public-surface hotfix closure is proven | core-capability | M002/S01 | Covers worker-default and lazy-import release-path truth. |
| R005 | Release hygiene is complete for `v0.7.x` | launchability | M002/S02 | RC-EXT hygiene open set stays visible until closed. |
| R006 | Packaging and install/uninstall readiness are proven | launchability | M002/S03 | Includes packaged first-run behavior and readiness evidence. |
| R007 | Repository and release surface are product-first and aligned | launchability | M002/S04 | Public surface must match actual release state and policy. |
| R008 | Health alerts calibration is closed with evidence | failure-visibility | M002/S02 | Promoted from the RC-EXT open set. |
| R009 | Minimum shortcuts baseline is present and verified | quality-attribute | M002/S02 | Promoted from the RC-EXT open set. |
| R010 | Security hygiene minimum is closed with evidence | compliance/security | M002/S02 | Promoted from the RC-EXT open set. |
| R011 | Debuggability minimum is present and verified | operability | M002/S02 | Promoted from the RC-EXT open set. |
| R012 | Packaging/versioning readiness is closed with evidence | launchability | M002/S03 | Must match archive-defined release progression. |
| R013 | Archive-aligned milestone progression remains authoritative | constraint | M001/S01 | `.gsd/` mirrors the archive milestone model instead of replacing it. |
| R014 | Post-RC performance smoke | quality-attribute | M003/S03 | Promoted from deferred to active because it is confirmed M003 performance baseline scope. |
| R022 | Release integrity and distribution policy is established | launchability | M002/S03 | Tag, SHA256, changelog, unsigned disclosure, and trademark baseline stay explicit. |
| R023 | BYOK + local-only boundary is preserved and verified | compliance/security | M001/S01 | Enforced by decision carry-forward now and release-surface verification later. |

## Deferred

| ID | Requirement | Class | Deferred reason |
|---|---|---|---|
| R016 | Usage Summary filter parity polish | quality-attribute | Deferred polish item, not a current release blocker. |
| R017 | Usage History row-details modal | admin/support | Future enhancement, not part of the current surface. |
| R018 | Bedrock unblock lane | integration | Blocked by external allowlist/quota constraints and removed from first-release scope. |

## Out of Scope

| ID | Requirement | Class | Boundary |
|---|---|---|---|
| R019 | New provider expansion in M001 | anti-feature | M001 is migration/planning only. |
| R020 | Runtime or release implementation work inside M001 | anti-feature | Runtime fixes, packaging, and release closure belong to M002+, not M001. |
| R021 | Replacing the archive milestone model with a new planning model | anti-feature | `.gsd/` must operationalize the archive model, not replace it. |
