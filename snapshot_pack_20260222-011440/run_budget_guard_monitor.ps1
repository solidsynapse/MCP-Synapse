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

function _WriteBytesFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][byte[]]$Bytes
    )
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    [System.IO.File]::WriteAllBytes($Path, $Bytes)
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..") | Select-Object -ExpandProperty Path
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$evidenceRoot = Join-Path (Join-Path (Join-Path $repoRoot "docs") "evidence") ("G_P3_budget_guard_monitor_{0}" -f $timestamp)
New-Item -ItemType Directory -Path $evidenceRoot -Force | Out-Null

$commandsRan = @()
$commandsRan += ("PowerShellVersion={0}" -f $PSVersionTable.PSVersion.ToString())
$commandsRan += ("RepoRoot={0}" -f $repoRoot)
$commandsRan += "python -m pytest -q"
$commandsRan += "python .\\tools\\budget_guard_report.py --date <auto-picked-utc-day> --max-tokens-in 0 --max-tokens-out 0"
$commandsRan += "python .\\tools\\budget_guard_report.py --date <auto-picked-utc-day> --max-tokens-in 0 --max-tokens-out 0"
$commandsRan += "Get-FileHash -Algorithm SHA256 budget_report.out.txt"
$commandsRan += "Get-FileHash -Algorithm SHA256 docs/DECISIONS.md docs/STATUS.md docs/TASKS.md"
$commandsRan += "Select-String (monitor-only grep) for 'raise' in budget guard files"
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

$dateCmd = @(
    "import sys",
    "from src.data.usage_db import UsageDatabase",
    "db=UsageDatabase()",
    "rows=db.list_usage(limit=1, most_recent=True)",
    "ts=(rows[0].get('timestamp') if rows else '')",
    "s=str(ts or '').replace('Z','+00:00')",
    "d=(s.split('T')[0] if 'T' in s else '')",
    "sys.stdout.write(d if d else '1970-01-01')"
) -join ";"

$utcDay = (& python -c $dateCmd 2>$null).Trim()
if (-not $utcDay) { $utcDay = "1970-01-01" }

$out1 = @()
if ($DbPath.Trim()) {
    $out1 = & python .\tools\budget_guard_report.py --db-path $DbPath --date $utcDay --max-tokens-in 0 --max-tokens-out 0 2>&1
} else {
    $out1 = & python .\tools\budget_guard_report.py --date $utcDay --max-tokens-in 0 --max-tokens-out 0 2>&1
}
if ($LASTEXITCODE -ne 0) { throw "budget_guard_report run1 failed" }
$bytes1 = [System.Text.Encoding]::UTF8.GetBytes(($out1 -join "`r`n") + "`r`n")
_WriteBytesFile -Path (Join-Path $evidenceRoot "budget_report.out.txt") -Bytes $bytes1

$out2 = @()
if ($DbPath.Trim()) {
    $out2 = & python .\tools\budget_guard_report.py --db-path $DbPath --date $utcDay --max-tokens-in 0 --max-tokens-out 0 2>&1
} else {
    $out2 = & python .\tools\budget_guard_report.py --date $utcDay --max-tokens-in 0 --max-tokens-out 0 2>&1
}
if ($LASTEXITCODE -ne 0) { throw "budget_guard_report run2 failed" }
$bytes2 = [System.Text.Encoding]::UTF8.GetBytes(($out2 -join "`r`n") + "`r`n")
$tmp2 = Join-Path $evidenceRoot "budget_report._run2.tmp"
_WriteBytesFile -Path $tmp2 -Bytes $bytes2

$sha1 = (Get-FileHash -Algorithm SHA256 -Path (Join-Path $evidenceRoot "budget_report.out.txt")).Hash
$sha2 = (Get-FileHash -Algorithm SHA256 -Path $tmp2).Hash
Remove-Item -LiteralPath $tmp2 -Force

$identical = 0
if ($sha1 -eq $sha2) { $identical = 1 }
_WriteTextFile -Path (Join-Path $evidenceRoot "budget_report.sha256.txt") -Lines @(
    ("RUN1_SHA256={0}" -f $sha1),
    ("RUN2_SHA256={0}" -f $sha2),
    ("IDENTICAL={0}" -f $identical),
    ("UTC_DAY={0}" -f $utcDay)
)

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

$guardFiles = @(
    (Join-Path (Join-Path $repoRoot "src") "data\\budget_guard_report.py"),
    (Join-Path $repoRoot "tools\\budget_guard_report.py")
)
$raiseMatches = @(Select-String -Path $guardFiles -Pattern "raise" -AllMatches -ErrorAction SilentlyContinue | ForEach-Object { $_.ToString() })
$enforceLines = @()
$enforceLines += ("RAISE_MATCHES={0}" -f $raiseMatches.Count)
if ($raiseMatches.Count -gt 0) { $enforceLines += $raiseMatches }
_WriteTextFile -Path (Join-Path $evidenceRoot "grep_monitor_only.proof.txt") -Lines $enforceLines

exit $pytestExitCode
