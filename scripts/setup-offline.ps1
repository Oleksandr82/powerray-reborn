# ============================================================================
#  setup-offline.ps1  —  ONE-TIME setup (needs internet).
#  Run this once at home, while you still have internet, to create the
#  bundled virtual environment and install all required packages locally.
#  After this completes successfully, Start-Cockpit.cmd works with NO
#  internet connection at all (fully offline in the field).
# ============================================================================

$ErrorActionPreference = 'Stop'

$RepoRoot  = Split-Path -Parent $PSScriptRoot
$WebUiDir  = Join-Path $RepoRoot 'web-ui'
$VenvDir   = Join-Path $RepoRoot 'venv'
$VenvPython = Join-Path $VenvDir 'Scripts\python.exe'

Write-Host ''
Write-Host '=== PowerRay Cockpit — One-time offline setup (needs internet) ===' -ForegroundColor Magenta
Write-Host ''

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host '[ERROR] Python was not found on this computer.' -ForegroundColor Red
    Write-Host 'Install Python 3 from python.org or the Microsoft Store, then run this script again.' -ForegroundColor Red
    Read-Host 'Press Enter to close'
    exit 1
}

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating virtual environment at `"$VenvDir`" ..." -ForegroundColor Cyan
    & python -m venv $VenvDir
} else {
    Write-Host '[OK] Virtual environment already exists.' -ForegroundColor Green
}

Write-Host 'Installing/updating required packages (needs internet)...' -ForegroundColor Cyan
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r (Join-Path $WebUiDir 'requirements.txt')

if ($LASTEXITCODE -ne 0) {
    Write-Host '[ERROR] Package installation failed. Check your internet connection and try again.' -ForegroundColor Red
    Read-Host 'Press Enter to close'
    exit 1
}

Write-Host ''
Write-Host '[OK] Setup complete!' -ForegroundColor Green
Write-Host 'You can now use Start-Cockpit.cmd / Stop-Cockpit.cmd with NO internet connection.' -ForegroundColor Green
Read-Host 'Press Enter to close'
