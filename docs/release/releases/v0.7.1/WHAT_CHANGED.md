# WHAT CHANGED - v0.7.1

## Scope summary
- Closed the M003 capability-depth package and carried its user-visible outcomes into the release surface.
- Unified cost normalization under `litellm` and surfaced pricing provenance through `cost_source`.
- Tightened local security behavior around vault reads and error redaction.
- Completed the documentation and compliance baseline for developer-facing release packaging.

## Technical changes
- `src/providers/cost_normalizer.py`
  - switched to a unified `litellm` normalization path,
  - added local manual pricing fallback behavior,
  - kept graceful `UNKNOWN` behavior when pricing cannot be derived.
- `src/data/usage_db.py`
  - persisted nullable `cost_source` on usage rows.
- `src/mcp_server/pipeline_v1.py` and `src/mcp_server/manager.py`
  - passed `cost_source` through execution and logging paths.
- `ui-tauri/src/routes/usage/history/+page.svelte`
  - refined cost display for very small positive values,
  - added cost-source tooltip behavior.
- `ui-tauri/src/routes/usage/summary/+page.svelte`
  - added matching small-cost display behavior,
  - added cost-source tooltip behavior.
- `ui-tauri/src/routes/connections/+page.svelte`
  - added IDE-specific config tabs,
  - replaced the single raw debug-copy path with IDE-targeted copy formats,
  - updated vault behavior to reflect metadata-only reads.
- `src/mcp_server/manager.py` and `tools/headless_dispatch_v1.py`
  - removed raw-secret exposure from dispatch surfaces,
  - added stricter sanitization for paths and public error messages.
- Documentation
  - refreshed `docs/guides/install-download.md`,
  - refreshed `docs/guides/release-notes.md`,
  - added `docs/guides/feature-reference.md`,
  - replaced the stale root `USER_GUIDE.md`,
  - added `docs/legal/privacy-notice.md`,
  - added `docs/legal/retention-deletion-policy.md`,
  - added `docs/legal/disclaimer.md`,
  - added `docs/legal/provider-compliance-matrix.md`.

## Behavior impact
- No provider-network logic moved into the UI.
- No shared-key or proxy behavior was introduced.
- No destructive data migration was required.
- Existing local configuration remains compatible with the current lane.

## Data / migration impact
- Usage rows now carry `cost_source` when available.
- Existing historical rows remain valid with nullable `cost_source`.
- No manual migration step is required for existing local data.
