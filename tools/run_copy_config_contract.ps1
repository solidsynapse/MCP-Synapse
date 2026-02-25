param(
    [Parameter(Mandatory = $false)][string]$AgentId = ""
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

function _CountMatchesInText {
    param(
        [Parameter(Mandatory = $true)][string]$Text,
        [Parameter(Mandatory = $true)][string]$Pattern
    )
    $hits = $Text | Select-String -Pattern $Pattern -AllMatches -ErrorAction SilentlyContinue
    if ($null -eq $hits) {
        return 0
    }
    return ($hits | Measure-Object).Count
}

function _PickAgentIdFromConfig {
    param(
        [Parameter(Mandatory = $true)][string]$ConfigPath
    )
    if (-not (Test-Path -LiteralPath $ConfigPath)) {
        return ""
    }
    $raw = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8
    $obj = $raw | ConvertFrom-Json
    if ($null -eq $obj) {
        return ""
    }
    $agents = $obj.agents
    if ($null -eq $agents) {
        return ""
    }
    $ids = @()
    foreach ($a in $agents) {
        if ($null -ne $a.id -and [string]$a.id) {
            $ids += [string]$a.id
        }
    }
    if ($ids.Count -eq 0) {
        return ""
    }
    $sorted = @($ids | Sort-Object)
    return [string]$sorted[0]
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..") | Select-Object -ExpandProperty Path
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$evidenceRoot = Join-Path (Join-Path (Join-Path $repoRoot "docs") "evidence") ("G_P3_copy_config_contract_{0}" -f $timestamp)
New-Item -ItemType Directory -Path $evidenceRoot -Force | Out-Null

$configPath = Join-Path (Join-Path $repoRoot "data") "config.json"
if (-not $AgentId.Trim()) {
    $AgentId = _PickAgentIdFromConfig -ConfigPath $configPath
}
if (-not $AgentId.Trim()) {
    throw "No agent_id provided and none found in data/config.json"
}

$commandsRan = @()
$commandsRan += ("PowerShellVersion={0}" -f $PSVersionTable.PSVersion.ToString())
$commandsRan += ("RepoRoot={0}" -f $repoRoot)
$commandsRan += ("AgentId={0}" -f $AgentId)
$commandsRan += "python -m pytest -q"
$commandsRan += ("python .\\tools\\copy_mcp_config.py --agent-id {0}" -f $AgentId)
$commandsRan += ("python .\\tools\\copy_mcp_config.py --agent-id {0}" -f $AgentId)
$commandsRan += "Get-FileHash -Algorithm SHA256 docs/DECISIONS.md docs/STATUS.md docs/TASKS.md"
$commandsRan += "Select-String (no secrets) over copy_config.out.txt"
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

$out1 = & python .\tools\copy_mcp_config.py --agent-id $AgentId 2>&1
$ec1 = $LASTEXITCODE
if ($ec1 -ne 0) {
    throw ("copy_mcp_config first run failed exit_code={0}`n{1}" -f $ec1, ($out1 -join "`n"))
}
$bytes1 = [System.Text.Encoding]::UTF8.GetBytes(($out1 -join "`r`n") + "`r`n")
_WriteBytesFile -Path (Join-Path $evidenceRoot "copy_config.out.txt") -Bytes $bytes1

$out2 = & python .\tools\copy_mcp_config.py --agent-id $AgentId 2>&1
$ec2 = $LASTEXITCODE
if ($ec2 -ne 0) {
    throw ("copy_mcp_config second run failed exit_code={0}`n{1}" -f $ec2, ($out2 -join "`n"))
}
$bytes2 = [System.Text.Encoding]::UTF8.GetBytes(($out2 -join "`r`n") + "`r`n")

$sha1 = (Get-FileHash -Algorithm SHA256 -Path (Join-Path $evidenceRoot "copy_config.out.txt")).Hash
$tmp2 = Join-Path $evidenceRoot "copy_config._run2.tmp"
_WriteBytesFile -Path $tmp2 -Bytes $bytes2
$sha2 = (Get-FileHash -Algorithm SHA256 -Path $tmp2).Hash
Remove-Item -LiteralPath $tmp2 -Force

$identical = 0
if ($sha1 -eq $sha2) {
    $identical = 1
}
_WriteTextFile -Path (Join-Path $evidenceRoot "copy_config.sha256.txt") -Lines @(
    ("RUN1_SHA256={0}" -f $sha1),
    ("RUN2_SHA256={0}" -f $sha2),
    ("IDENTICAL={0}" -f $identical)
)

$copyText = [System.Text.Encoding]::UTF8.GetString($bytes1)
$secretPattern = "Bearer|api_key|apikey|token=|authorization"
$secretMatches = _CountMatchesInText -Text $copyText -Pattern $secretPattern
_WriteTextFile -Path (Join-Path $evidenceRoot "copy_config.no_secrets_grep.txt") -Lines @("MATCHES=$secretMatches")

exit $pytestExitCode
