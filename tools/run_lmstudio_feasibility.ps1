﻿param(
    [Parameter(Mandatory = $false)][string]$BaseUrl = "http://127.0.0.1:1234/v1",
    [Parameter(Mandatory = $false)][string]$Model = "",
    [Parameter(Mandatory = $false)][string]$Prompt = "Reply with exactly three words: LM Studio is reachable."
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function _WriteTextFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][object]$Lines
    )
    if ($null -eq $Lines) {
        $Lines = @("")
    } elseif ($Lines -is [string]) {
        $s = [string]$Lines
        if ([string]::IsNullOrWhiteSpace($s)) { $Lines = @("") } else { $Lines = @($s) }
    } else {
        $arr = @($Lines)
        $converted = @()
        foreach ($v in $arr) {
            if ($null -eq $v) { $converted += "" } else { $converted += ([string]$v) }
        }
        $nonEmpty = @($converted | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
        if ($nonEmpty.Count -eq 0) { $Lines = @("") } else { $Lines = @($converted) }
    }
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $arr = @($Lines)
    if ($arr.Count -eq 0) { $arr = @("") }
    if ($arr.Count -eq 1 -and [string]::IsNullOrWhiteSpace([string]$arr[0])) { $arr = @("") }
    ($arr -join "`r`n") + "`r`n" | Out-File -FilePath $Path -Encoding utf8
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..") | Select-Object -ExpandProperty Path
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$evidenceRoot = Join-Path (Join-Path (Join-Path $repoRoot "docs") "evidence") ("G_P3_lmstudio_feasibility_{0}" -f $timestamp)
New-Item -ItemType Directory -Path $evidenceRoot -Force | Out-Null

$commandsRan = @()
$commandsRan += ("PowerShellVersion={0}" -f $PSVersionTable.PSVersion.ToString())
$commandsRan += ("RepoRoot={0}" -f $repoRoot)
$commandsRan += "python -m pytest -q"
$commandsRan += "python .\\tools\\lmstudio_probe.py --base-url <url> [--model <id>] --prompt <prompt>"
$commandsRan += "Select-String proof: no streaming key literal and no SSE strings"
$commandsRan += "Get-FileHash -Algorithm SHA256 docs/DECISIONS.md docs/STATUS.md docs/TASKS.md"
_WriteTextFile -Path (Join-Path $evidenceRoot "commands_ran.txt") -Lines $commandsRan

_WriteTextFile -Path (Join-Path $evidenceRoot "changed_files.txt") -Lines @(
    "tools/lmstudio_probe.py",
    "tools/run_lmstudio_feasibility.ps1",
    "tests/test_lmstudio_probe_offline_t17.py"
)
_WriteTextFile -Path (Join-Path $evidenceRoot "rollback.txt") -Lines @(
    "Remove tools/lmstudio_probe.py",
    "Remove tools/run_lmstudio_feasibility.ps1",
    "Remove tests/test_lmstudio_probe_offline_t17.py"
)

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
if ($null -eq $pytestOutput) { $pytestOutput = @() }
$pytestOutput | Out-File -FilePath $pytestOutPath -Encoding utf8
_WriteTextFile -Path $pytestExitPath -Lines @([string]$pytestExitCode)

$probeOutPath = Join-Path $evidenceRoot "lmstudio_probe.out.txt"
$argsList = @(".\\tools\\lmstudio_probe.py", "--base-url", $BaseUrl, "--prompt", $Prompt)
if ($Model.Trim()) {
    $argsList = @(".\\tools\\lmstudio_probe.py", "--base-url", $BaseUrl, "--model", $Model, "--prompt", $Prompt)
}
$prevErrPref = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$probeOutput = & python @argsList 2>&1
$ErrorActionPreference = $prevErrPref
if ($null -eq $probeOutput) { $probeOutput = @() }
_WriteTextFile -Path $probeOutPath -Lines $probeOutput

$probeFiles = @((Join-Path $repoRoot "tools\\lmstudio_probe.py"))
$streamKeyMatches = @(Select-String -Path $probeFiles -Pattern '\"stream\"' -AllMatches -ErrorAction SilentlyContinue | ForEach-Object { $_.ToString() })
$sseMatches = @()
$sseMatches += @(Select-String -Path $probeFiles -SimpleMatch "/sse" -AllMatches -ErrorAction SilentlyContinue | ForEach-Object { $_.ToString() })
$sseMatches += @(Select-String -Path $probeFiles -SimpleMatch "text/event-stream" -AllMatches -ErrorAction SilentlyContinue | ForEach-Object { $_.ToString() })
$sseMatches += @(Select-String -Path $probeFiles -SimpleMatch "EventSource" -AllMatches -ErrorAction SilentlyContinue | ForEach-Object { $_.ToString() })
$grepLines = @()
$grepLines += ("STREAM_KEY_MATCHES={0}" -f $streamKeyMatches.Count)
$grepLines += ("SSE_MATCHES={0}" -f $sseMatches.Count)
if (@($grepLines).Count -eq 0) { $grepLines = @("MATCHES=0") }
_WriteTextFile -Path (Join-Path $evidenceRoot "grep_no_streaming.proof.txt") -Lines $grepLines

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

exit $pytestExitCode
