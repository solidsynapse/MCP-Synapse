# TRUST AND SECURITY NOTE - v0.6.1

MCP Synapse is local-first by design. Connection setup, routing controls, and policy surfaces remain user-owned and local, while provider execution stays behind explicit backend boundaries.

This `v0.6.1` lane includes current-surface security and debuggability revalidation:
- dispatch boundary fail-closed behavior,
- explicit network-gate enforcement,
- canonical error envelopes with request IDs on runtime-path debug proofs,
- packaged install/uninstall hygiene on Windows.

No release-blocking findings were identified in the scoped `v0.6.1` security and hygiene review package.

This release remains in Early Access and temporary unsigned mode. Use official release artifacts and verify hashes in `SHA256SUMS.txt` before first run.
