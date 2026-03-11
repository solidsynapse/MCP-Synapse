# KNOWN ISSUES - v0.6.0-rc.1

## Deferred (non-blocking in this release lane)
1. Connections detail interaction rough edge remains in narrow Wave-2A residual paths.
2. Worker-ON memory optimization target (<250 MB steady RAM) is deferred to a dedicated future optimization slice.
3. `MCP_SYNAPSE_PYTHON` boundary tightening is deferred as a narrow security follow-up.

## Notes
- These items are tracked as deferred and are not release-blocking in this candidate lane.
- Runtime safety behavior remains fail-open with same-request fallback on worker error/timeout/invalid-response paths.
