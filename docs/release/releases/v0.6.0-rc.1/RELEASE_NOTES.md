# RELEASE NOTES - v0.6.0-rc.1

Date: 2026-03-11
Channel: Official (Early Access)
Signing status: Unsigned (temporary)

## Highlights
- Single fast runtime profile for installed app behavior (worker-primary path by default; no user-facing runtime mode split).
- Main navigation read-state responsiveness uplift across Dashboard, Connections, Usage Summary, Settings, Persona Lite, Optimizations, Budget Guards, and Interceptors.
- Persona Lite -> Optimizations transition write-path coalescing to reduce transition stutter.
- Lifecycle responsiveness hardening:
  - startup ready marker around ~1.0-1.1s in release-path evidence,
  - bounded close path with fail-open budget around ~1.5s class evidence.
- Desktop shell release polish:
  - installer destination normalization against repo tmp paths,
  - branded icon propagation for packaged surfaces,
  - Help links and Settings "Check for updates" wired to production URLs,
  - single-instance + browser-like context-menu/print hardening.

## Fixed in this candidate lane
- No-console runtime execution path (visible CMD flash removed on packaged flow).
- Installer/shortcut target normalization for tmp probe path carryover.
- Packaging identity consistency through release icon asset chain.
- Narrow security polish:
  - unknown-op / invalid-request semantic hardening,
  - vault plaintext-read generic error hygiene.

## Deferred (non-blocking for this candidate lane)
- Connections detail interaction rough edge (Wave-2A residual).
- Worker-ON steady RAM optimization target (<250 MB) future slice.
- `MCP_SYNAPSE_PYTHON` boundary tightening (security deferred item).

## Included release files
- `WHAT_CHANGED.md`
- `SHA256SUMS.txt`
- `UNSIGNED_NOTICE.md`
- `KNOWN_ISSUES.md`
- `INSTALL_RUN_NOTES.md`
- `TRUST_SECURITY.md`

## Evidence anchors
- Release package prep: `docs/evidence/V57_RELEASE_PACKAGE_PREP_20260310-022825/`
- Desktop shell/icon closure patch: `docs/evidence/V65_STEP2D_CLOSURE_INSTALL_ROOT_ICON_20260311-090522/`
- Desktop UX hardening patch: `docs/evidence/V66_STEP2E_DESKTOP_UX_HARDENING_20260311-093444/`
- Security lane: `docs/evidence/V50_RELEASE_SECURITY_MINI_GATE_20260309-234645/`, `docs/evidence/V52_NARROW_SECURITY_POLISH_PATCH_20260310-000816/`
