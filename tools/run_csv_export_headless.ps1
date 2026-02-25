param(
    [Parameter(Mandatory = $false)][string]$DbPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function _WriteTextFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string[]]$Lines
    )
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    ($Lines -join "`r`n") + "`r`n" | Out-File -FilePath $Path -Encoding utf8
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..") | Select-Object -ExpandProperty Path
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$evidenceRoot = Join-Path (Join-Path (Join-Path $repoRoot "docs") "evidence") ("G_P3_csv_export_headless_{0}" -f $timestamp)
New-Item -ItemType Directory -Path $evidenceRoot -Force | Out-Null

$commandsRan = @()
$commandsRan += ("PowerShellVersion={0}" -f $PSVersionTable.PSVersion.ToString())
$commandsRan += ("RepoRoot={0}" -f $repoRoot)
$commandsRan += "python -m pytest -q"
if ($DbPath.Trim()) {
    $commandsRan += ("python .\\tools\\export_usage_csv.py --db-path `"{0}`" --out `"{1}`"" -f $DbPath, (Join-Path $evidenceRoot "export.csv"))
} else {
    $commandsRan += ("python .\\tools\\export_usage_csv.py --out `"{0}`"" -f (Join-Path $evidenceRoot "export.csv"))
}
$commandsRan += "Get-FileHash -Algorithm SHA256 export.csv"
$commandsRan += "Get-FileHash -Algorithm SHA256 docs/DECISIONS.md docs/STATUS.md docs/TASKS.md"
$commandsRan += "Select-String proof UI does not write export CSV directly"
_WriteTextFile -Path (Join-Path $evidenceRoot "commands_ran.txt") -Lines $commandsRan

$pytestOutPath = Join-Path $evidenceRoot "pytest.txt"
$pytestExitPath = Join-Path $evidenceRoot "pytest_exit_code.txt"
$pytestExitCode = 127
$pytestOutput = @()
try {
    $pytestOutput = & python -m pytest -q 2>&1
    $pytestExitCode = $LASTEXITCODE
} catch {
    $pytestOutput = @(
        "ERROR: failed to run python -m pytest -q",
        ("ExceptionType={0}" -f $_.Exception.GetType().FullName),
        ("Message={0}" -f $_.Exception.Message)
    )
    $pytestExitCode = 127
}
if ($null -eq $pytestOutput) {
    $pytestOutput = @()
}
$pytestOutput | Out-File -FilePath $pytestOutPath -Encoding utf8
_WriteTextFile -Path $pytestExitPath -Lines @([string]$pytestExitCode)

$exportPath = Join-Path $evidenceRoot "export.csv"
if ($DbPath.Trim()) {
    & python .\tools\export_usage_csv.py --db-path $DbPath --out $exportPath 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "export_usage_csv failed" }
} else {
    & python .\tools\export_usage_csv.py --out $exportPath 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "export_usage_csv failed" }
}

$exportHash = (Get-FileHash -Algorithm SHA256 -Path $exportPath).Hash
_WriteTextFile -Path (Join-Path $evidenceRoot "export.sha256.txt") -Lines @("SHA256=$exportHash")

$ssotRel = @("docs\\DECISIONS.md", "docs\\STATUS.md", "docs\\TASKS.md")
$ssotLines = @()
foreach ($rel in $ssotRel) {
    $p = Join-Path $repoRoot $rel
    if (Test-Path -LiteralPath $p) {
        $h = Get-FileHash -Algorithm SHA256 -Path $p
        $ssotLines += ("{0}  {1}" -f $h.Hash, $rel.Replace("\\", "/"))
    } else {
        $ssotLines += ("MISSING  {0}" -f $rel.Replace("\\", "/"))
    }
}
_WriteTextFile -Path (Join-Path $evidenceRoot "ssot_core.sha256.txt") -Lines $ssotLines

$uiPath = Join-Path (Join-Path $repoRoot "src") "ui\\main_window.py"
$matchesPathCwd = @(Select-String -LiteralPath $uiPath -SimpleMatch "Path.cwd(" -AllMatches -ErrorAction SilentlyContinue | ForEach-Object { $_.ToString() })
$matchesOpenWrite = @(Select-String -LiteralPath $uiPath -SimpleMatch '.open("w"' -AllMatches -ErrorAction SilentlyContinue | ForEach-Object { $_.ToString() })
$uiMatches = $matchesPathCwd.Count + $matchesOpenWrite.Count
$proofLines = @()
$proofLines += ("MATCHES={0}" -f $uiMatches)
$proofLines += 'PATTERN=Path.cwd( OR .open("w"'
if ($matchesPathCwd.Count -gt 0) { $proofLines += $matchesPathCwd }
if ($matchesOpenWrite.Count -gt 0) { $proofLines += $matchesOpenWrite }
_WriteTextFile -Path (Join-Path $evidenceRoot "grep_ui_no_export_writes.proof.txt") -Lines $proofLines

exit $pytestExitCode
