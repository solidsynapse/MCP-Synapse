$ErrorActionPreference = "Stop"

Write-Host "[SMOKE] pytest"
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "pytest failed with exit code $LASTEXITCODE" }

Write-Host "[SMOKE] MCP probe (headless)"
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$outDir = "docs/evidence/MVP1_smoke_run_$ts/mcp_probe"
New-Item -ItemType Directory -Force $outDir | Out-Null

# Run via cmd to avoid PowerShell NativeCommandError on stderr INFO logs
cmd /c "py -3.11 -m src.tests.mcp_sse_probe --start-local-server --port 5055 --out-dir `"$outDir`" 1> `"$outDir\probe.out.txt`" 2> `"$outDir\probe.err.txt`""
if ($LASTEXITCODE -ne 0) { throw "MCP probe failed with exit code $LASTEXITCODE" }

Write-Host "[SMOKE] done"
