# KNOWN ISSUES - v0.7.1

## Carry-forward items
1. Bedrock remains blocked and is not runtime-proven in the public provider surface because the current account has a model-support mismatch and quota gap.
2. Commercial code signing remains deferred to the post-revenue phase; unsigned-distribution guidance is still required.
3. Worker memory optimization below the currently accepted band remains deferred to a future optimization slice.

## New or newly visible notes in this package
4. Claude Code CLI compatibility was skipped during the IDE matrix closure because of environment and budget constraints; the tested PASS set is VS Code, Cursor, and TRAE.
5. The local workspace bundle artifacts currently available for hashing are still labeled `v0.6.1`; rebuild versioned bundle outputs before publishing a final `v0.7.1` package.
6. Small-cost display now shows `<$0.0001` for positive values below that threshold; exact zero still renders as `$0.0000` for truly free local paths such as Ollama.

## Notes
- These items are documented as non-blocking for the release-document package itself.
- Do not mark Bedrock as supported until runtime proof exists.
- Keep SmartScreen and unsigned-package guidance visible while unsigned mode remains active.
