# KNOWN ISSUES - v0.6.1

## Deferred (non-blocking in this release lane)
1. Bedrock remains blocked and hidden from the first-release provider surface until external quota and allowlist constraints are resolved.
2. Worker steady-state memory optimization remains deferred to a later dedicated optimization slice.
3. Full code-signing rollout remains deferred to the `0.9.x -> 1.0.0` phase.

## Notes
- These items are tracked as deferred and are not release-blocking for `v0.6.1`.
- Runtime safety remains explicit: worker-primary on the packaged path, with same-request fallback safety retained internally.
- `v0.7.x` remains the next broader milestone for release-closure work beyond this patch lane.
