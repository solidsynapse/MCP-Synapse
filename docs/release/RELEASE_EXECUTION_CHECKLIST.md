# Release Execution Checklist (v0.6 lane)

Status: Active
Owner: Release Management

## Step A - Tag + notes prep
1. Ensure working tree is clean for release commit.
2. Prepare release notes from `CHANGELOG_TEMPLATE.md`.
3. Set release tag candidate (example: `v0.6.0-rc.1`).

## Step B - Build + integrity
1. Build installer/package artifacts.
2. Generate `SHA256SUMS.txt` for all public artifacts.
3. Verify hashes once on a clean shell session.

## Step C - Unsigned notice (temporary phase)
1. Attach unsigned/SmartScreen notice to release page.
2. Include verification steps (hash + official tag + what changed).

## Step D - Publish bundle contents
Required files in release folder:
- `RELEASE_NOTES.md`
- `WHAT_CHANGED.md`
- `SHA256SUMS.txt`
- `UNSIGNED_NOTICE.md` (while unsigned mode is active)

## Step E - Runtime smoke (packaged)
1. First-run behavior check.
2. Basic navigation/open-modal smoke.
3. Uninstall hygiene check (no zombie process/service left).

## Gate output
Mark `packaging=PASS` only when Steps A-E have evidence.
