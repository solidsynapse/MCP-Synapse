# RELEASE NOTES - v0.7.1

Date: 2026-03-18
Channel: Early Access
Signing status: Unsigned (temporary)

## Highlights
- Cost transparency is now explicit across the shipped usage surfaces:
  - `litellm` is the unified cost-normalization layer under D-040,
  - usage rows persist `cost_source` as `ACTUAL`, `ESTIMATED`, or `UNKNOWN`,
  - very small positive costs now render as `<$0.0001` instead of misleading `$0.0000`.
- IDE-oriented copy-config UX is improved in the Connections details modal:
  - `Cursor / Windsurf`,
  - `VS Code`,
  - `Other / Raw`.
- Security hardening is tightened on the local-only path:
  - vault reads are metadata-only,
  - raw secret autofill is disabled,
  - error-path sanitization now redacts filesystem paths more aggressively.
- The documentation and compliance pack is now part of the public release surface:
  - refreshed `guides/`,
  - legal baseline under `docs/legal/`,
  - updated user-facing release notes and install guidance.
- Performance work from the release-hardening lane remains visible:
  - lazy import behavior stays in place,
  - startup memory guidance is documented with a 140 MB startup reference and a higher steady-state worker band accepted for the current lane.

## Included in this release
- Cost normalization through `litellm` with local fallback behavior.
- Persisted `cost_source` data through pipeline, database, and usage views.
- Usage cost display refinement for very small positive values.
- IDE-specific config tabs in the Connections details modal.
- Cost-source hover details in the Usage surfaces.
- Vault metadata-only behavior and safer error redaction.
- Documentation pack completion across `guides/`, `USER_GUIDE.md`, and `docs/legal/`.

## Security and trust notes
- Distribution remains unsigned in the current lane.
- SHA256 hashes are included in `SHA256SUMS.txt`.
- SmartScreen and unsigned-package guidance must remain visible while unsigned mode is active.

## Artifact note
- The current local workspace still contains bundle artifacts named `v0.6.1`.
- The hashes in `SHA256SUMS.txt` are the real hashes of the currently available local artifacts and the release executable.
- Rebuild versioned bundle artifacts before publishing a final `v0.7.1` public package.

## Deferred / known carry-forward items
- Bedrock remains coded but not runtime-proven because of the model-support mismatch and quota gap.
- Commercial code signing remains deferred to the post-revenue phase per D-038.
- Further memory optimization below the current accepted worker band remains a future slice.
- Claude Code CLI compatibility was not completed in M003/S05 due environment and budget constraints.
