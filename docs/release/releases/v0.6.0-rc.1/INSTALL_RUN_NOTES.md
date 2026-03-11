# INSTALL AND RUN NOTES - v0.6.0-rc.1

## Install
1. Launch the official installer package from the release artifacts.
2. Keep the default destination unless your environment requires a custom path.
3. Complete setup and launch MCP Synapse from Start Menu shortcut.

## Run behavior
- Runtime profile is single and fast by default (worker-primary behavior).
- Legacy subprocess path is internal fallback safety only; there is no user-facing runtime mode switch.

## Help and product links
- Docs: `https://mcpsynapse.dev/docs`
- Feedback: `https://mcpsynapse.dev/feedback`
- About: `https://mcpsynapse.dev`
- Check for updates: `https://mcpsynapse.dev/download`

## Unsigned temporary notice
- This lane is unsigned temporary mode.
- Verify package integrity with `SHA256SUMS.txt` before use.

## Windows shell notes
- If a shortcut icon appears stale after upgrade, Windows icon cache refresh may lag temporarily.
- The effective shortcut target and installed executable path should still resolve to the installed app location.
