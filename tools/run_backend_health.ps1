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
    if ($null -eq $hits) {
        return 0
    }
    return ($hits | Measure-Object).Count
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..") | Select-Object -ExpandProperty Path
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$evidenceRoot = Join-Path (Join-Path (Join-Path $repoRoot "docs") "evidence") ("G_P3_backend_health_runner_{0}" -f $timestamp)
New-Item -ItemType Directory -Path $evidenceRoot -Force | Out-Null

$commandsRan = @()
$commandsRan += ("PowerShellVersion={0}" -f $PSVersionTable.PSVersion.ToString())
$commandsRan += ("RepoRoot={0}" -f $repoRoot)
$commandsRan += "python -m pytest -q"
$commandsRan += "Get-FileHash -Algorithm SHA256 docs/DECISIONS.md docs/STATUS.md docs/TASKS.md"
$commandsRan += "Select-String (UI direct provider-client refs) in src/main.py + src/ui/*.py"
$commandsRan += "Select-String (core provider-specific markers) in src/mcp_server/agent_server.py"

_WriteTextFile -Path (Join-Path $evidenceRoot "commands_ran.txt") -Lines $commandsRan
_WriteTextFile -Path (Join-Path $evidenceRoot "changed_files.txt") -Lines @("none expected")
_WriteTextFile -Path (Join-Path $evidenceRoot "rollback.txt") -Lines @("none; evidence-only run")

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

$uiPattern = "from\s+src\.(providers|vertex)\b|import\s+src\.(providers|vertex)\b|ProviderFactory\b|VertexAIClient\b|azure_openai_client\b|bedrock_client\b|huggingface_client\b|vertex_client\b"
$uiFiles = @()
$uiMain = Join-Path $repoRoot "src\\main.py"
if (Test-Path -LiteralPath $uiMain) {
    $uiFiles += $uiMain
}
$uiDir = Join-Path $repoRoot "src\\ui"
if (Test-Path -LiteralPath $uiDir) {
    $uiFiles += (Get-ChildItem -Path $uiDir -File -Filter "*.py" | Select-Object -ExpandProperty FullName)
}
$uiMatches = _CountMatches -Paths $uiFiles -Pattern $uiPattern
_WriteTextFile -Path (Join-Path $evidenceRoot "grep_ui_provider_refs.count.txt") -Lines @("MATCHES=$uiMatches")

$corePattern = "call_google_vertex_ai|\[VERTEX AI GATEWAY\]|VertexAIClient"
$coreFile = Join-Path $repoRoot "src\\mcp_server\\agent_server.py"
$coreHits = 0
if (Test-Path -LiteralPath $coreFile) {
    $coreHits = _CountMatches -Paths @($coreFile) -Pattern $corePattern
}
_WriteTextFile -Path (Join-Path $evidenceRoot "grep_core_provider_specific.count.txt") -Lines @("HITS=$coreHits")

Write-Host ("PYTEST_EXIT_CODE={0}" -f $pytestExitCode)
Write-Host ("UI_MATCHES={0}" -f $uiMatches)
Write-Host ("CORE_PROVIDER_SPECIFIC_HITS={0}" -f $coreHits)
Write-Host ("EVIDENCE_ROOT={0}" -f $evidenceRoot)

exit $pytestExitCode
