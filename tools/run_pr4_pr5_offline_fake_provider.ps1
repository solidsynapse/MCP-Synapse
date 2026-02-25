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
        [Parameter(Mandatory = $true)][string[]]$Paths,
        [Parameter(Mandatory = $true)][string]$Pattern
    )
    $hits = Select-String -Path $Paths -Pattern $Pattern -AllMatches -ErrorAction SilentlyContinue
    if ($null -eq $hits) { return 0 }
    return ($hits | Measure-Object).Count
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..") | Select-Object -ExpandProperty Path
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$evidenceRoot = Join-Path (Join-Path (Join-Path $repoRoot "docs") "evidence") ("G_P3_pr4_pr5_offline_fake_provider_{0}" -f $timestamp)
New-Item -ItemType Directory -Path $evidenceRoot -Force | Out-Null

$testPr4 = Join-Path $repoRoot "tests\\test_pr4_i0_offline_fake_provider_anthropic.py"
$testPr5 = Join-Path $repoRoot "tests\\test_pr5_i0_offline_fake_provider_groq.py"

$commandsRan = @()
$commandsRan += ("PowerShellVersion={0}" -f $PSVersionTable.PSVersion.ToString())
$commandsRan += ("RepoRoot={0}" -f $repoRoot)
$commandsRan += "python -m pytest -q tests/test_pr4_i0_offline_fake_provider_anthropic.py tests/test_pr5_i0_offline_fake_provider_groq.py"
$commandsRan += "python -c (compute determinism hashes twice)"
$commandsRan += "Select-String grep proof: no urllib/requests/httpx imports in PR4/PR5 fake provider tests"
$commandsRan += "Get-FileHash -Algorithm SHA256 docs/DECISIONS.md docs/STATUS.md docs/TASKS.md"
_WriteTextFile -Path (Join-Path $evidenceRoot "commands_ran.txt") -Lines $commandsRan

_WriteTextFile -Path (Join-Path $evidenceRoot "changed_files.txt") -Lines @(
    "tests/test_pr4_i0_offline_fake_provider_anthropic.py",
    "tests/test_pr5_i0_offline_fake_provider_groq.py",
    "tools/run_pr4_pr5_offline_fake_provider.ps1"
)
_WriteTextFile -Path (Join-Path $evidenceRoot "rollback.txt") -Lines @(
    "Remove tests/test_pr4_i0_offline_fake_provider_anthropic.py",
    "Remove tests/test_pr5_i0_offline_fake_provider_groq.py",
    "Remove tools/run_pr4_pr5_offline_fake_provider.ps1"
)

$pytestOutPath = Join-Path $evidenceRoot "pytest.txt"
$pytestExitPath = Join-Path $evidenceRoot "pytest_exit_code.txt"
$pytestExitCode = 127
$pytestOutput1 = @()
$pytestOutput2 = @()
try {
    $pytestOutput1 = & python -m pytest -q $testPr4 $testPr5 2>&1
    $pytestExitCode = $LASTEXITCODE
    $pytestOutput2 = & python -m pytest -q $testPr4 $testPr5 2>&1
} catch {
    $pytestOutput1 = @(
        "ERROR: failed to run python -m pytest -q",
        ("ExceptionType={0}" -f $_.Exception.GetType().FullName),
        ("Message={0}" -f $_.Exception.Message)
    )
    $pytestExitCode = 127
}
if ($null -eq $pytestOutput1) { $pytestOutput1 = @() }
if ($null -eq $pytestOutput2) { $pytestOutput2 = @() }
$joined = @()
$joined += "=== PYTEST_RUN_1 ==="
$joined += $pytestOutput1
$joined += "=== PYTEST_RUN_2 ==="
$joined += $pytestOutput2
$joined | Out-File -FilePath $pytestOutPath -Encoding utf8
_WriteTextFile -Path $pytestExitPath -Lines @([string]$pytestExitCode)

function _ComputeHashes {
    $py = @"
import importlib.util
import pathlib

root = pathlib.Path(r'$repoRoot')

def _load(name: str, rel: str):
    p = root / rel
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(m)
    return m

m4 = _load('pr4', 'tests/test_pr4_i0_offline_fake_provider_anthropic.py')
m5 = _load('pr5', 'tests/test_pr5_i0_offline_fake_provider_groq.py')
print('PR4=' + m4.compute_pr4_determinism_hash())
print('PR5=' + m5.compute_pr5_determinism_hash())
"@
    $prevErrPref = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $out = & python -c $py 2>&1
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prevErrPref
    return ,@($code, $out)
}

$h1 = _ComputeHashes
$h2 = _ComputeHashes
$detLines = @()
$detLines += ("RUN1_EXIT_CODE={0}" -f $h1[0])
$detLines += ("RUN2_EXIT_CODE={0}" -f $h2[0])
$detLines += "=== RUN1 ==="
if ($null -ne $h1[1]) { $detLines += $h1[1] }
$detLines += "=== RUN2 ==="
if ($null -ne $h2[1]) { $detLines += $h2[1] }
$identical = (($h1[1] -join "`n") -eq ($h2[1] -join "`n"))
$detLines += ("IDENTICAL={0}" -f $(if ($identical) { 1 } else { 0 }))
_WriteTextFile -Path (Join-Path $evidenceRoot "determinism.sha256.txt") -Lines $detLines

$urllibHits = _CountMatches -Paths @($testPr4, $testPr5) -Pattern "\burllib\b"
$requestsHits = _CountMatches -Paths @($testPr4, $testPr5) -Pattern "\brequests\b"
$httpxHits = _CountMatches -Paths @($testPr4, $testPr5) -Pattern "\bhttpx\b"
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
