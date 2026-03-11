# TRUST AND SECURITY NOTE - v0.6.0-rc.1

MCP Synapse is local-first by design. Your connection setup and routing controls stay on your machine, and runtime safety includes automatic same-request fallback when worker execution fails.

A targeted pre-release security review was completed for this lane, including dispatch boundary checks and release-surface hygiene. No release-blocking findings were identified in that scoped review.

This release remains in Early Access and unsigned temporary mode. Use official release artifacts and verify hashes in `SHA256SUMS.txt`.
