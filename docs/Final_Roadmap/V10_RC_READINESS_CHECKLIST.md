# V1.0 RC Readiness Checklist

Status: PASS baseline checklist for release-candidate transition.

Scope: Current V1.0 surfaces only. No feature expansion.

## 1) Checkpoint Readiness

- Working checkpoint branch exists: `pre-release-checkpoint`
- Historical recovery branches/refs remain available:
  - `checkpoint/pre-dashboard-head-20260302-094944`
  - `refs/checkpoints/pre-dashboard-snapshot-20260302-094944`

Operational rule:
- Any post-RC blocker fix must start from `pre-release-checkpoint` and be re-verified against SSOT gates.

## 2) Known Issues Coverage

Known issues are explicitly documented in:
- `docs/Final_Roadmap/DOCS_MIN_01_User_Guide_Known_Issues_Feature_Wiki.md`

Covered release-facing items:
- Manual refresh may be needed in some UI sections.
- Export/save dialogs can fail under restricted OS permissions.
- External credential changes can invalidate previously working connections.

## 3) Support Boundaries Coverage

Support and responsibility boundaries are documented in:
- `docs/Final_Roadmap/LC_MIN_01_Legal_Compliance_Minimum_Pack.md`
- `docs/Final_Roadmap/LC_V10_Comprehensive_Legal_Compliance_Pack.md`

Current contact map:
- Security: `security@solidsynapse.com`
- Support: `support@solidsynapse.com`
- Legal/Privacy: `legal@solidsynapse.com`
- Product/Technical: `mcp@solidsynapse.com`
- General: `info@solidsynapse.com`

Boundary rules:
- Budget semantics remain monitor-only for V1.0 (no enforced blocking/throttling claims).
- Provider-side processing remains under configured provider terms/policies.

## 4) RC Gate Decision

`GATE-V10-RC-READINESS` is PASS when:
1) checkpoint exists and is referenceable,
2) known issues are documented and user-visible,
3) support boundaries and contact routes are explicit.

This checklist confirms all three conditions in current truth.
