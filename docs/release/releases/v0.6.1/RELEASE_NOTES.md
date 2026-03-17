# RELEASE NOTES - v0.6.1

Date: 2026-03-17
Channel: Official (Early Access)
Signing status: Unsigned (temporary)

## Highlights
- Runtime hotfix verification is closed on the packaged path:
  - worker-default ON behavior revalidated,
  - worker ON/OFF/fallback smoke revalidated,
  - packaged clean first-run revalidated,
  - no-dispatch-regression smoke revalidated.
- RC-EXT hygiene closure is complete:
  - health alerts calibration,
  - minimum shortcuts baseline,
  - security hygiene minimum,
  - debuggability minimum.
- Packaging readiness is revalidated for `0.6.1`:
  - current NSIS/MSI artifact set captured,
  - clean Windows install verified,
  - clean Windows uninstall verified.
- Public release surface is synchronized to `v0.6.1`.

## Fixed in this patch lane
- Packaged runtime verification gaps from the 2026-03-15 runtime hotfix window are closed with current evidence.
- Start Menu, install-root, and uninstall-path behavior is revalidated on the current `0.6.1` installer.
- Public release references now point to `v0.6.1` instead of the prior RC package.

## Deferred (non-blocking in this lane)
- Bedrock remains blocked and hidden from the first-release provider surface due to external quota/allowlist constraints.
- Broader `v0.7.x` milestone work remains separate from this `0.6.1` patch lane.
- Code signing remains deferred to the `0.9.x -> 1.0.0` phase.

## Included release files
- `WHAT_CHANGED.md`
- `SHA256SUMS.txt`
- `UNSIGNED_NOTICE.md`
- `KNOWN_ISSUES.md`
- `INSTALL_RUN_NOTES.md`
- `TRUST_SECURITY.md`

## Evidence anchors
- Runtime hotfix verification: `docs/evidence/S01_20260317-005332/`
- RC-EXT hygiene pack: `docs/evidence/S02_20260317-010639/`, `docs/evidence/S02_20260317-010719/`, `docs/evidence/S02_20260317-011057/`, `docs/evidence/S02_20260317-011224/`
- Packaging/install/uninstall readiness: `docs/evidence/S03_20260317-011725/`, `docs/evidence/S03_20260317-011757/`, `docs/evidence/S03_20260317-011837/`
