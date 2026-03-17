# INSTALL AND RUN NOTES - v0.6.1

## Install
1. Download one official installer artifact from the release page:
   - `MCP Synapse_0.6.1_x64-setup.exe` (NSIS installer)
   - `MCP Synapse_0.6.1_x64_en-US.msi` (MSI installer)
2. Keep the default destination unless your environment requires a custom path.
3. Complete setup and launch MCP Synapse from the Start Menu shortcut.
4. `mcp-synapse.exe` is a packaged app binary and is not a standalone public download artifact.

## Verified Windows readiness
- Silent install on Windows completed with exit code `0`.
- Installed executable resolved to `%LOCALAPPDATA%\MCP Synapse\mcp-synapse.exe`.
- Start Menu shortcut target and DisplayIcon matched the installed executable.
- Silent uninstall on Windows completed with exit code `0` and removed install directory, Start Menu shortcut, and HKCU uninstall entry.

## Run behavior
- Runtime profile is single and fast by default (worker-primary behavior).
- Legacy subprocess path is internal same-request fallback safety only; there is no user-facing runtime mode split.

## Help and product links
- Docs: `https://mcpsynapse.dev/docs`
- Feedback: `https://mcpsynapse.dev/feedback`
- About: `https://mcpsynapse.dev`
- Check for updates: `https://mcpsynapse.dev/download`

## Unsigned temporary notice
- This lane remains temporarily unsigned.
- Verify package integrity with `SHA256SUMS.txt` before first run.

## Windows shell notes
- The installer normalizes temporary probe paths before file copy and shortcut writes.
- Start Menu shortcut cleanup/recreate is part of install and uninstall hooks.
- If icon cache refresh lags after upgrade, the effective shortcut target should still resolve to the installed app location.
