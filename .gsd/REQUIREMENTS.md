# Requirements

This file is the explicit capability and coverage contract for the project.

Use it to track what is actively in scope, what has been validated by completed work, what is intentionally deferred, and what is explicitly out of scope.

Guidelines:
- Keep requirements capability-oriented, not a giant feature wishlist.
- Requirements should be atomic, testable, and stated in plain language.
- Every **Active** requirement should be mapped to a slice, deferred, blocked with reason, or moved out of scope.
- Each requirement should have one accountable primary owner and may have supporting slices.
- Research may suggest requirements, but research does not silently make them binding.
- Validation means the requirement was actually proven by completed work and verification, not just discussed.

## Active

### R001 — Working SSOT migration into `.gsd/`
- Class: operability
- Status: active
- Description: `.gsd/` must become the active working SSOT for current and future work while `docs/` remains the read-only historical archive.
- Why it matters: Downstream execution needs one active source of truth instead of reconstructing state from historical documents.
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: M001/S04
- Validation: mapped
- Notes: M001 is migration + planning only; no implementation work belongs here.

### R002 — Active architectural decisions preserved verbatim
- Class: constraint
- Status: active
- Description: The selected active decisions from `docs/DECISIONS.md` must be preserved verbatim in `.gsd/DECISIONS.md`, not summarized or rephrased.
- Why it matters: These decisions are active operating constraints, not historical commentary.
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: none
- Validation: mapped
- Notes: Carry forward D-024, D-029, D-033, D-037, D-038, D-039. D-032 is referenced as current scope truth but not carried verbatim.

### R003 — Current project state is re-established in `.gsd/`
- Class: operability
- Status: active
- Description: `.gsd/STATE.md` and `.gsd/PROJECT.md` must describe the current project truth, current release lane, current blockers, and immediate next action.
- Why it matters: A fresh agent must be able to resume without reconstructing the present from the archive.
- Source: user
- Primary owning slice: M001/S04
- Supporting slices: M001/S01
- Validation: mapped
- Notes: Current truth must explicitly include Bedrock blocked/de-scoped, perf smoke deferred, English docs deferred, Usage Summary parity deferred, and D-032-relevant scope truth.

### R004 — Runtime/public-surface hotfix closure is proven
- Class: core-capability
- Status: active
- Description: The runtime/public-surface hotfix lane must be closed with evidence, including the worker-default and lazy-import truth on the current release path.
- Why it matters: `v0.7.x` execution starts by retiring the highest-risk open runtime/public-surface uncertainty.
- Source: user
- Primary owning slice: M002/S01
- Supporting slices: M002/S02
- Validation: mapped
- Notes: M002 first high-risk slice.

### R005 — Release hygiene is complete for `v0.7.x`
- Class: launchability
- Status: active
- Description: The broader `0.7` release hygiene set must be explicitly visible and driven to closure with evidence.
- Why it matters: Release readiness is not only runtime correctness; it includes hygiene gates that shape public trust.
- Source: user
- Primary owning slice: M002/S02
- Supporting slices: M002/S03, M002/S04
- Validation: mapped
- Notes: RC-EXT release hygiene open set must remain visible under Active until closed.

### R006 — Packaging and install/uninstall readiness are proven
- Class: launchability
- Status: active
- Description: Packaging, installation, uninstallation, and packaged first-run behavior must be proven on the release path.
- Why it matters: `v0.7.x` is defined by RC-EXT closure and packaging/install readiness in the archive progression.
- Source: user
- Primary owning slice: M002/S03
- Supporting slices: M002/S01
- Validation: mapped
- Notes: Includes packaged smoke truth and readiness artifacts.

### R007 — Repository and release surface are product-first and aligned
- Class: launchability
- Status: active
- Description: The public repository and release surface must present a product-first face aligned with the actual release state.
- Why it matters: Public trust depends on the repo/release surface matching current truth and distribution policy.
- Source: user
- Primary owning slice: M002/S04
- Supporting slices: M002/S02, M002/S03
- Validation: mapped
- Notes: README, SECURITY, release package surface, migration notes, and release integrity set all belong here.

### R008 — Health alerts calibration is closed with evidence
- Class: failure-visibility
- Status: active
- Description: Health alerts calibration must be explicitly tracked and closed with evidence.
- Why it matters: Failure visibility must be trustworthy before release closure.
- Source: user
- Primary owning slice: M002/S02
- Supporting slices: none
- Validation: mapped
- Notes: Promoted from the RC-EXT open set.

### R009 — Minimum shortcuts baseline is present and verified
- Class: quality-attribute
- Status: active
- Description: A minimum shortcuts baseline must exist and be verified as part of release hygiene.
- Why it matters: Baseline desktop usability is part of the release-closure surface.
- Source: user
- Primary owning slice: M002/S02
- Supporting slices: none
- Validation: mapped
- Notes: Promoted from the RC-EXT open set.

### R010 — Security hygiene minimum is closed with evidence
- Class: compliance/security
- Status: active
- Description: Security hygiene minimum must be explicitly tracked and evidenced on the release path.
- Why it matters: Release closure needs a clear minimum security posture, not just ad-hoc fixes.
- Source: user
- Primary owning slice: M002/S02
- Supporting slices: M002/S04
- Validation: mapped
- Notes: Promoted from the RC-EXT open set.

### R011 — Debuggability minimum is present and verified
- Class: operability
- Status: active
- Description: The product must expose enough durable debugging surface to support release-quality operation and troubleshooting.
- Why it matters: Evidence-first work requires durable diagnostic surfaces, not only passing checks.
- Source: user
- Primary owning slice: M002/S02
- Supporting slices: none
- Validation: mapped
- Notes: Promoted from the RC-EXT open set.

### R012 — Packaging/versioning readiness is closed with evidence
- Class: launchability
- Status: active
- Description: Packaging and versioning readiness must be closed in a way that matches the archive-defined release progression.
- Why it matters: The public release lane depends on integrity between artifact identity, version policy, and release messaging.
- Source: user
- Primary owning slice: M002/S03
- Supporting slices: M002/S04
- Validation: mapped
- Notes: Promoted from the RC-EXT open set.

### R013 — Archive-aligned milestone progression remains authoritative
- Class: constraint
- Status: active
- Description: The `0.7 / 0.8 / 0.9 / 1.0` progression from the archive remains authoritative and `.gsd/` must mirror it rather than replace it.
- Why it matters: Planning continuity matters; the new working layer must not invent a competing milestone model.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: M001/S03
- Validation: mapped
- Notes: `.gsd/` operationalizes the existing progression.

### R022 — Release integrity and distribution policy is established
- Class: launchability
- Status: active
- Description: Official release-channel integrity requirements must be explicit and owned: tag, SHA256, changelog, unsigned disclosure, and trademark baseline.
- Why it matters: The product is in an unsigned Early Access lane and needs explicit trust/distribution controls.
- Source: user
- Primary owning slice: M002/S03
- Supporting slices: M002/S04
- Validation: mapped
- Notes: Mirrors the archive’s release integrity and distribution policy truth.

### R023 — BYOK + local-only boundary is preserved and verified
- Class: compliance/security
- Status: active
- Description: The product must preserve and verify the BYOK + local-only operating boundary, including no shared-key pattern and no proxy-as-a-service pattern.
- Why it matters: This is a core product boundary, not a later policy nicety.
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: M002/S04
- Validation: mapped
- Notes: Preserved by verbatim decision carry-forward and later release-surface verification.

## Deferred

### R014 — Post-RC performance smoke
- Class: quality-attribute
- Status: deferred
- Description: A post-RC performance smoke pass should run after the current technical freeze lane.
- Why it matters: It helps confirm the release behaves as expected after closure.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Explicitly deferred in current truth.

### R015 — Full English documentation pack
- Class: launchability
- Status: deferred
- Description: A full English documentation pack should be completed after the current technical-first lane.
- Why it matters: It improves adoption and clarity, but is not part of the immediate bootstrap or current release closure gate.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Explicitly deferred in current truth.

### R016 — Usage Summary filter parity polish
- Class: quality-attribute
- Status: deferred
- Description: Usage Summary filter parity polish remains a later polish item rather than a current release blocker.
- Why it matters: It affects polish and parity, but current truth says it is deferred.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Explicitly deferred in current truth.

### R017 — Usage History row-details modal
- Class: admin/support
- Status: deferred
- Description: A row-details modal for Usage History is a future enhancement and not part of the current surface.
- Why it matters: It may improve diagnostics later without blocking current release closure.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Explicitly tracked as future enhancement.

### R018 — Bedrock unblock lane
- Class: integration
- Status: deferred
- Description: Bedrock enablement remains deferred until the external allowlist/quota blocker is removed and the first-release scope is revisited.
- Why it matters: It is an active external dependency, but not part of the current first-release surface.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Current truth is Bedrock blocked and de-scoped/hidden from first release.

## Out of Scope

### R019 — New provider expansion in M001
- Class: anti-feature
- Status: out-of-scope
- Description: M001 must not expand provider scope or introduce new runtime/provider implementation work.
- Why it matters: Keeps the migration bootstrap clean and prevents scope confusion.
- Source: inferred
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: M001 is planning-only.

### R020 — Runtime or release implementation work inside M001
- Class: anti-feature
- Status: out-of-scope
- Description: Runtime fixes, release docs closure, packaging work, and public-surface implementation do not belong inside M001.
- Why it matters: The user explicitly separated migration/planning from execution work.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Execution begins in M002.

### R021 — Replacing the archive milestone model with a new planning model
- Class: anti-feature
- Status: out-of-scope
- Description: `.gsd/` must not invent a competing milestone model that replaces the archive’s normative progression.
- Why it matters: Prevents governance drift and loss of continuity.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: `.gsd/` mirrors and operationalizes the archive progression.

## Traceability

| ID | Class | Status | Primary owner | Supporting | Proof |
|---|---|---|---|---|---|
| R001 | operability | active | M001/S01 | M001/S04 | mapped |
| R002 | constraint | active | M001/S01 | none | mapped |
| R003 | operability | active | M001/S04 | M001/S01 | mapped |
| R004 | core-capability | active | M002/S01 | M002/S02 | mapped |
| R005 | launchability | active | M002/S02 | M002/S03, M002/S04 | mapped |
| R006 | launchability | active | M002/S03 | M002/S01 | mapped |
| R007 | launchability | active | M002/S04 | M002/S02, M002/S03 | mapped |
| R008 | failure-visibility | active | M002/S02 | none | mapped |
| R009 | quality-attribute | active | M002/S02 | none | mapped |
| R010 | compliance/security | active | M002/S02 | M002/S04 | mapped |
| R011 | operability | active | M002/S02 | none | mapped |
| R012 | launchability | active | M002/S03 | M002/S04 | mapped |
| R013 | constraint | active | M001/S02 | M001/S03 | mapped |
| R014 | quality-attribute | deferred | none | none | unmapped |
| R015 | launchability | deferred | none | none | unmapped |
| R016 | quality-attribute | deferred | none | none | unmapped |
| R017 | admin/support | deferred | none | none | unmapped |
| R018 | integration | deferred | none | none | unmapped |
| R019 | anti-feature | out-of-scope | none | none | n/a |
| R020 | anti-feature | out-of-scope | none | none | n/a |
| R021 | anti-feature | out-of-scope | none | none | n/a |
| R022 | launchability | active | M002/S03 | M002/S04 | mapped |
| R023 | compliance/security | active | M001/S01 | M002/S04 | mapped |

## Coverage Summary

- Active requirements: 15
- Mapped to slices: 15
- Validated: 0
- Unmapped active requirements: 0
