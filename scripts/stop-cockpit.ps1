# ============================================================================
#  stop-cockpit.ps1  —  Stops the offline PowerRay web cockpit
# ============================================================================

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$StateDir = Join-Path $RepoRoot '.state'
$PidFile  = Join-Path $StateDir 'cockpit.pid'

Write-Host ''
Write-Host '=== PowerRay Offline Cockpit — Stop ===' -ForegroundColor Magenta
Write-Host ''

if (-not (Test-Path $PidFile)) {
    Write-Host '[INFO] No running cockpit found (no PID file).' -ForegroundColor Yellow
    Read-Host 'Press Enter to close'
    exit 0
}

$processId = Get-Content $PidFile -ErrorAction SilentlyContinue
$proc = if ($processId) { Get-Process -Id $processId -ErrorAction SilentlyContinue } else { $null }

if ($proc) {
    Write-Host "Stopping cockpit server (PID $processId)..." -ForegroundColor Cyan
    Stop-Process -Id $processId -Force
    Start-Sleep -Milliseconds 500
    if (Get-Process -Id $processId -ErrorAction SilentlyContinue) {
        Write-Host '[WARN] Process did not stop immediately — it may take a moment.' -ForegroundColor Yellow
    } else {
        Write-Host '[OK] Cockpit stopped.' -ForegroundColor Green
    }
} else {
    Write-Host '[INFO] Cockpit process was not running (already stopped).' -ForegroundColor Yellow
}

Remove-Item $PidFile -ErrorAction SilentlyContinue
Read-Host 'Press Enter to close'
