# WHAT CHANGED - v0.6.0-rc.1

## Scope summary
- Release package artifacts were rebuilt from a single fresh source and indexed with SHA256 manifest.
- Single-runtime release stance is locked: worker-primary is the default runtime behavior; legacy subprocess path is internal fallback safety only.
- Wave-1 read-state worker expansion is active for:
  - `settings.get_state`
  - `policies.persona.get_state`
  - `policies.optimizations.get_state`
  - `resilience.budget.get_state`
  - `resilience.interceptors.get_state`
- Persona write-path route-leave coalescing was applied to reduce duplicate `policies.persona.set_state` during Persona -> Optimizations transition.
- Lifecycle mini-slice, desktop shell branding, and desktop UX hardening were applied in narrow, release-focused slices.
- Settings + Help release-facing targets were finalized:
  - Docs -> `https://mcpsynapse.dev/docs`
  - Feedback -> `https://mcpsynapse.dev/feedback`
  - About -> `https://mcpsynapse.dev`
  - Check for updates -> `https://mcpsynapse.dev/download`

## Behavior impact
- No broad architecture rewrite.
- No runtime model split in user-facing behavior.
- Worker/fallback core logic remains fail-open at same-request boundary.
- Security lane includes narrow semantic hardening and generic vault error hygiene.

## Non-breaking / Breaking
- Breaking changes: none for data format or public API.
- Non-breaking updates:
  - UI polish and shell identity updates,
  - lifecycle responsiveness hardening,
  - single-instance behavior and browser-like print/context suppression.

## Data / migration impact
- No schema migration.
- No mandatory user data migration.
- Existing local state and connection configuration remain compatible in this lane.

## Evidence links
- `docs/evidence/V57_RELEASE_PACKAGE_PREP_20260310-022825/`
- `docs/evidence/V58_STEP2A_UI_MINI_POLISH_2SURFACES_20260311-063054/`
- `docs/evidence/V59_STEP2A_DASHBOARD_FINAL_POLISH_20260311-064604/`
- `docs/evidence/V60_STEP2B_UI_POLISH_CONNECTIONS_USAGE_METADATA_20260311-070451/`
- `docs/evidence/V61_STEP2C_SETTINGS_HELP_FINALIZE_20260311-074026/`
- `docs/evidence/V62_STEP2C_HELP_LINK_HOTFIX_20260311-074647/`
- `docs/evidence/V65_STEP2D_CLOSURE_INSTALL_ROOT_ICON_20260311-090522/`
- `docs/evidence/V66_STEP2E_DESKTOP_UX_HARDENING_20260311-093444/`
