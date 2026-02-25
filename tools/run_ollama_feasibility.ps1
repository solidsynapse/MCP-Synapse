param(
    [Parameter(Mandatory = $false)][string]$BaseUrl = "",
    [Parameter(Mandatory = $false)][string]$Model = "llama3.2",
    [Parameter(Mandatory = $false)][string]$Prompt = "Reply with exactly three words: Ollama is reachable."
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
$evidenceRoot = Join-Path (Join-Path (Join-Path $repoRoot "docs") "evidence") ("G_P3_ollama_feasibility_{0}" -f $timestamp)
New-Item -ItemType Directory -Path $evidenceRoot -Force | Out-Null

$commandsRan = @()
$commandsRan += ("PowerShellVersion={0}" -f $PSVersionTable.PSVersion.ToString())
$commandsRan += ("RepoRoot={0}" -f $repoRoot)
$commandsRan += "python -m pytest -q"
$commandsRan += "python .\\tools\\ollama_probe.py --model <model> --prompt <prompt>"
$commandsRan += "Select-String proof: no streaming key literal and no SSE strings"
$commandsRan += "Get-FileHash -Algorithm SHA256 docs/DECISIONS.md docs/STATUS.md docs/TASKS.md"
_WriteTextFile -Path (Join-Path $evidenceRoot "commands_ran.txt") -Lines $commandsRan

_WriteTextFile -Path (Join-Path $evidenceRoot "changed_files.txt") -Lines @(
    "src/providers/ollama_client.py",
    "src/providers/factory.py",
    "tools/ollama_probe.py",
    "tools/run_ollama_feasibility.ps1"
)
_WriteTextFile -Path (Join-Path $evidenceRoot "rollback.txt") -Lines @(
    "Remove src/providers/ollama_client.py",
    "Revert src/providers/factory.py",
    "Remove tools/ollama_probe.py",
    "Remove tools/run_ollama_feasibility.ps1"
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

$probeOutPath = Join-Path $evidenceRoot "ollama_probe.out.txt"
$probeLines = @()
$argsList = @(".\\tools\\ollama_probe.py", "--model", $Model, "--prompt", $Prompt)
if ($BaseUrl.Trim()) {
    $argsList = @(".\\tools\\ollama_probe.py", "--base-url", $BaseUrl, "--model", $Model, "--prompt", $Prompt)
}
$probeOutput = @()
$probeExit = 127
$prevErrPref = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$probeOutput = & python @argsList 2>&1
$probeExit = $LASTEXITCODE
$ErrorActionPreference = $prevErrPref
$probeLines += ("EXIT_CODE={0}" -f $probeExit)
if ($BaseUrl.Trim()) { $probeLines += ("BASE_URL={0}" -f $BaseUrl) }
$probeLines += ("MODEL={0}" -f $Model)
$probeLines += ("PROMPT={0}" -f $Prompt)
$probeLines += "---"
if ($null -eq $probeOutput) { $probeOutput = @() }
$probeLines += $probeOutput
_WriteTextFile -Path $probeOutPath -Lines $probeLines

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

$probeFiles = @(
    (Join-Path (Join-Path $repoRoot "src") "providers\\ollama_client.py"),
    (Join-Path $repoRoot "tools\\ollama_probe.py")
)
$streamKeyMatches = @(Select-String -Path $probeFiles -Pattern '\"stream\"' -AllMatches -ErrorAction SilentlyContinue | ForEach-Object { $_.ToString() })
$sseMatches = @()
$sseMatches += @(Select-String -Path $probeFiles -SimpleMatch "/sse" -AllMatches -ErrorAction SilentlyContinue | ForEach-Object { $_.ToString() })
$sseMatches += @(Select-String -Path $probeFiles -SimpleMatch "text/event-stream" -AllMatches -ErrorAction SilentlyContinue | ForEach-Object { $_.ToString() })
$sseMatches += @(Select-String -Path $probeFiles -SimpleMatch "EventSource" -AllMatches -ErrorAction SilentlyContinue | ForEach-Object { $_.ToString() })
$grepLines = @()
$grepLines += ("STREAM_KEY_MATCHES={0}" -f $streamKeyMatches.Count)
$grepLines += ("SSE_MATCHES={0}" -f $sseMatches.Count)
_WriteTextFile -Path (Join-Path $evidenceRoot "grep_no_streaming.proof.txt") -Lines $grepLines

exit $pytestExitCode
