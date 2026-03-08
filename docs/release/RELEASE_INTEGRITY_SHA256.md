# Release Integrity (SHA256)

Status: Active
Owner: Release Engineering

## Required artifacts per release
- Installer/package file(s)
- `SHA256SUMS.txt`
- `WHAT_CHANGED.md`
- changelog entry

## Generation (PowerShell)
Use in release output directory:

```powershell
Get-FileHash -Algorithm SHA256 .\MCP-Synapse-Setup.exe | ForEach-Object { "$($_.Hash.ToLower())  $($_.Path | Split-Path -Leaf)" } | Set-Content -Encoding UTF8 .\SHA256SUMS.txt
```

## Verification (user-facing)

```powershell
Get-FileHash -Algorithm SHA256 .\MCP-Synapse-Setup.exe
# Compare with SHA256SUMS.txt
```

## Rules
- Hash file is mandatory for every public release.
- If hash mismatches, release is invalid.
