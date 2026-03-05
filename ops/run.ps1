param(
  [ValidateSet("smoke","build","test")]
  [string]$Task = "smoke"
)
$ErrorActionPreference = "Stop"

Write-Host "NOTE: ops\run.ps1 is a placeholder. Customize it for your repo."
Write-Host ("TASK={0}" -f $Task)

# Example placeholders (replace):
# if ($Task -eq "smoke") { python -m pytest -q }
# if ($Task -eq "build") { ... }
# if ($Task -eq "test")  { ... }
