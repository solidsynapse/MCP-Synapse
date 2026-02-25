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

function _CountMatches {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Pattern
    )
    $hits = Select-String -Path $Path -Pattern $Pattern -AllMatches -ErrorAction SilentlyContinue
    if ($null -eq $hits) {
        return 0
    }
    return ($hits | Measure-Object).Count
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..") | Select-Object -ExpandProperty Path
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$evidenceRoot = Join-Path (Join-Path (Join-Path $repoRoot "docs") "evidence") ("G_P3_openai_offline_fake_provider_{0}" -f $timestamp)
New-Item -ItemType Directory -Path $evidenceRoot -Force | Out-Null

$commandsRan = @()
$commandsRan += ("PowerShellVersion={0}" -f $PSVersionTable.PSVersion.ToString())
$commandsRan += ("RepoRoot={0}" -f $repoRoot)
$commandsRan += "python -m pytest -q"
$commandsRan += "Select-String grep proof: no urllib/requests/httpx imports in fake provider test"
$commandsRan += "Get-FileHash -Algorithm SHA256 docs/DECISIONS.md docs/STATUS.md docs/TASKS.md"
_WriteTextFile -Path (Join-Path $evidenceRoot "commands_ran.txt") -Lines $commandsRan

_WriteTextFile -Path (Join-Path $evidenceRoot "changed_files.txt") -Lines @(
    "tests/test_pr3_i0_offline_fake_provider.py",
    "tools/run_openai_offline_fake_provider.ps1"
)
_WriteTextFile -Path (Join-Path $evidenceRoot "rollback.txt") -Lines @(
    "Remove tests/test_pr3_i0_offline_fake_provider.py",
    "Remove tools/run_openai_offline_fake_provider.ps1"
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

$testFile = Join-Path $repoRoot "tests\\test_pr3_i0_offline_fake_provider.py"
$urllibHits = _CountMatches -Path $testFile -Pattern "\burllib\b"
$requestsHits = _CountMatches -Path $testFile -Pattern "\brequests\b"
$httpxHits = _CountMatches -Path $testFile -Pattern "\bhttpx\b"
$grepLines = @()
$grepLines += ("URLLIB_MATCHES={0}" -f $urllibHits)
$grepLines += ("REQUESTS_MATCHES={0}" -f $requestsHits)
$grepLines += ("HTTPX_MATCHES={0}" -f $httpxHits)
_WriteTextFile -Path (Join-Path $evidenceRoot "grep_no_network.proof.txt") -Lines $grepLines

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
