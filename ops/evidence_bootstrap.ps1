param(
  [string]$IdPrefix = "SSOT_BOOTSTRAP"
)

$ErrorActionPreference = "Stop"
$repo = (Get-Location).Path
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$evidenceRoot = Join-Path $repo ("docs\evidence\{0}_{1}" -f $IdPrefix,$ts)

New-Item -ItemType Directory -Force -Path $evidenceRoot | Out-Null

function Write-Text($path, $text) {
  $text | Out-File -FilePath $path -Encoding utf8
}

function Hash-File($path) {
  if (!(Test-Path $path)) { return "MISSING: $path" }
  $h = Get-FileHash -Algorithm SHA256 -Path $path
  return "{0}  {1}" -f $h.Hash, $h.Path
}

# Canonical SSOT paths (adjust if needed)
$ssot = @(
  "docs\DECISIONS.md",
  "docs\STATUS.md",
  "docs\TASKS.md",
  "docs\UI_STYLE_GUIDE.md",
  "ui-tauri\src\app.css"
)

$beforePath = Join-Path $evidenceRoot "ssot_core.sha256.before.txt"
$afterPath  = Join-Path $evidenceRoot "ssot_core.sha256.after.txt"
$cmdPath    = Join-Path $evidenceRoot "commands_ran.txt"
$anchorPath = Join-Path $evidenceRoot "anchor_proofs.txt"
$summary    = Join-Path $evidenceRoot "summary.txt"

Write-Text $cmdPath ("# commands_ran.txt`n# repo: {0}`n# ts: {1}`n" -f $repo,$ts)

# BEFORE hashes
$hashLines = @()
foreach ($p in $ssot) { $hashLines += (Hash-File (Join-Path $repo $p)) }
Write-Text $beforePath ($hashLines -join "`n")

# Anchor helper: show file:line + 3-8 lines around match
function Anchor-Proof($relPath, $pattern, $context=3) {
  $full = Join-Path $repo $relPath
  if (!(Test-Path $full)) { return @("MISSING: $relPath") }
  $content = Get-Content $full
  $matches = Select-String -Path $full -Pattern $pattern
  if (!$matches) { return @("NOT_FOUND: $relPath :: $pattern") }
  $out = New-Object System.Collections.Generic.List[string]
  foreach ($m in $matches) {
    $line = $m.LineNumber
    $start = [Math]::Max(1, $line-$context)
    $end   = [Math]::Min($content.Count, $line+$context)
    $out.Add(("FILE: {0}  LINE: {1}  PATTERN: {2}" -f $relPath,$line,$pattern))
    for ($i=$start; $i -le $end; $i++) {
      $out.Add(("{0,6}: {1}" -f $i, $content[$i-1]))
    }
    $out.Add("")
  }
  return $out
}

$anchors = @()
$anchors += (Anchor-Proof "docs\UI_STYLE_GUIDE.md" "UI_STYLE_GUIDE|Design language|Dashboard" 4)
$anchors += (Anchor-Proof "ui-tauri\src\app.css" "UI Primitives \(Dashboard Design Language\)" 4)
$anchors += (Anchor-Proof "docs\DECISIONS.md" "thin[- ]shell|single[- ]entrypoint|D-024|D-029" 4)
Write-Text $anchorPath ($anchors -join "`n")

# AFTER hashes (same as before for bootstrap; kept for later phases too)
$hashLines2 = @()
foreach ($p in $ssot) { $hashLines2 += (Hash-File (Join-Path $repo $p)) }
Write-Text $afterPath ($hashLines2 -join "`n")

# Summary flags (simple presence checks)
function Flag($line) { if ($line -like "MISSING:*" -or $line -like "NOT_FOUND:*") { "FAIL" } else { "PASS" } }
$flags = @()
$flags += "SSOT_HASHES_BEFORE=" + (Flag ($hashLines -join " "))
$flags += "UI_STYLE_GUIDE_ANCHOR=" + (Flag ($anchors -join " "))

Write-Text $summary ($flags -join "`n")

Write-Output ("EVIDENCE_ROOT={0}" -f $evidenceRoot)
