$ErrorActionPreference = "Stop"

$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$evidenceDir = "docs/evidence/G_P3_backend_health_runner_$ts"
New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null

@(
  "python -m pytest -q"
  "python -m pytest -q src/tests/test_core_provider_agnostic_strings.py"
  "FORBIDDEN_STRINGS: call_google_vertex_ai, [VERTEX AI GATEWAY]"
) -join "`n" | Out-File -FilePath (Join-Path $evidenceDir "commands_ran.txt") -Encoding utf8

@(
  "Repo is not a git repository in this environment; changed files listed manually."
  ""
  "docs/TASKS.md"
  "p3_be3_headless_health_runner.ps1"
  ""
  "Notes:"
  "- Core forbidden-string checks are enforced by src/tests/test_core_provider_agnostic_strings.py (dependency; not modified by this runner)."
) -join "`n" | Out-File -FilePath (Join-Path $evidenceDir "changed_files.txt") -Encoding utf8

@(
  "Rollback plan:"
  "- Revert docs\\TASKS.md edits under P3.BE3"
  "- Remove p3_be3_headless_health_runner.ps1"
  "- Re-run: python -m pytest -q"
) -join "`n" | Out-File -FilePath (Join-Path $evidenceDir "rollback.txt") -Encoding utf8

$anchors = @(
  (Select-String -Path "docs\TASKS.md" -Pattern "^### P3\.BE3" | ForEach-Object { "$($_.Path):$($_.LineNumber):$($_.Line.TrimEnd())" }),
  (Select-String -Path "docs\STATUS.md" -Pattern "^## P3\.BE3" | ForEach-Object { "$($_.Path):$($_.LineNumber):$($_.Line.TrimEnd())" })
)
($anchors | Where-Object { $_ -and $_.Length -gt 0 }) -join "`n" | Out-File -FilePath (Join-Path $evidenceDir "anchor_proofs.txt") -Encoding utf8

$forbidden = @("call_google_vertex_ai", "[VERTEX AI GATEWAY]")
$coreFiles = Get-ChildItem -Path "src\mcp_server" -Filter "*.py" -Recurse | Sort-Object FullName

$grepLines = @("GREP_PROOFS:")
foreach ($needle in $forbidden) {
  $matches = Select-String -Path $coreFiles.FullName -Pattern $needle -SimpleMatch -AllMatches -ErrorAction SilentlyContinue
  $hitCount = 0
  if ($matches) {
    $hitCount = @($matches).Count
  }
  $grepLines += "NEEDLE: $needle"
  $grepLines += "MATCH_COUNT=$hitCount"
  if ($matches) {
    $sorted = @($matches) | Sort-Object Path, LineNumber
    foreach ($m in $sorted) {
      $grepLines += "HIT: $($m.Path):$($m.LineNumber):$($m.Line.TrimEnd())"
    }
  }
}

$grepLines -join "`n" | Out-File -FilePath (Join-Path $evidenceDir "grep_proofs.txt") -Encoding utf8

Write-Host "[BE3] pytest (full suite)"
$pytestOut = python -m pytest -q 2>&1
$pytestOut | Out-File -FilePath (Join-Path $evidenceDir "pytest.txt") -Encoding utf8
$pytestExit = $LASTEXITCODE
"$pytestExit" | Out-File -FilePath (Join-Path $evidenceDir "pytest_exit_code.txt") -Encoding utf8

Write-Host "[BE3] core forbidden-string test (core-only)"
python -m pytest -q src/tests/test_core_provider_agnostic_strings.py | Out-Null
if ($LASTEXITCODE -ne 0) {
  throw "core forbidden-string test failed with exit code $LASTEXITCODE"
}

$required = @(
  "commands_ran.txt",
  "changed_files.txt",
  "rollback.txt",
  "pytest.txt",
  "pytest_exit_code.txt",
  "anchor_proofs.txt",
  "grep_proofs.txt"
)
foreach ($f in $required) {
  $fp = Join-Path $evidenceDir $f
  if (-not (Test-Path $fp)) {
    throw "missing required evidence file: $fp"
  }
}

if ($pytestExit -ne 0) {
  throw "pytest failed with exit code $pytestExit"
}

Write-Host "[BE3] PASS evidence_dir=$evidenceDir"
