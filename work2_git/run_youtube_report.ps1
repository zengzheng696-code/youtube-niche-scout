$ErrorActionPreference = "Stop"

$Workspace = "D:\codex\work2"
$LogDir = Join-Path $Workspace "logs"
$LogFile = Join-Path $LogDir "youtube_report.log"

if (!(Test-Path $LogDir)) {
  New-Item -ItemType Directory -Path $LogDir | Out-Null
}

Set-Location $Workspace

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"[$timestamp] Starting YouTube pet product report" | Tee-Object -FilePath $LogFile -Append

try {
  python scripts/generate_weekly_report.py 2>&1 | Tee-Object -FilePath $LogFile -Append
  $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  "[$timestamp] Finished successfully" | Tee-Object -FilePath $LogFile -Append
} catch {
  $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  "[$timestamp] Failed: $($_.Exception.Message)" | Tee-Object -FilePath $LogFile -Append
  exit 1
}
