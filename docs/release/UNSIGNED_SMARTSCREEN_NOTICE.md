# Unsigned Build / SmartScreen Notice (Temporary)

Status: Temporary (first 3-5 months)
Owner: Release Management

## User notice text (default)
This build is currently unsigned. Windows SmartScreen may show a warning before first run.

To verify authenticity:
1) Download only from the official release channel.
2) Verify SHA256 against `SHA256SUMS.txt`.
3) Check release tag and "What Changed" notes.

## Rules
- This notice must be present on every unsigned release page.
- Remove only after code-signing rollout is active (`0.9.x -> 1.0.0`).
