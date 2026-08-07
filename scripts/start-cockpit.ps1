# ============================================================================
#  start-cockpit.ps1  —  Launches the offline PowerRay web cockpit
#  Safe to run with no internet connection (everything needed is local).
# ============================================================================

$ErrorActionPreference = 'Stop'

# Resolve paths relative to this script, so it works no matter where the
# repo folder was copied/unzipped on the field laptop.
$RepoRoot  = Split-Path -Parent $PSScriptRoot
$WebUiDir  = Join-Path $RepoRoot 'web-ui'
$ServerPy  = Join-Path $WebUiDir 'server.py'
$StateDir  = Join-Path $RepoRoot '.state'
$PidFile   = Join-Path $StateDir 'cockpit.pid'
$LogFile   = Join-Path $StateDir 'cockpit.log'
$Url       = 'http://localhost:5000'
$VenvPython = Join-Path $RepoRoot 'venv\Scripts\python.exe'

New-Item -ItemType Directory -Force -Path $StateDir | Out-Null

Write-Host ''
Write-Host '=== PowerRay Offline Cockpit — Start ===' -ForegroundColor Magenta
Write-Host ''

# --- 0. Refuse to double-start ---
if (Test-Path $PidFile) {
    $existingId = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($existingId -and (Get-Process -Id $existingId -ErrorAction SilentlyContinue)) {
        Write-Host "[OK] Cockpit is already running (PID $existingId)." -ForegroundColor Green
        Write-Host "Opening browser at $Url ..." -ForegroundColor Yellow
        Start-Process $Url
        exit 0
    } else {
        Remove-Item $PidFile -ErrorAction SilentlyContinue
    }
}

# --- 1. Find the Python interpreter to use — prefer the bundled venv (fully offline) ---
if (Test-Path $VenvPython) {
    $PythonExe = $VenvPython
    Write-Host '[OK] Using bundled virtual environment (venv) — no system Python required.' -ForegroundColor Green
} else {
    $sysPython = Get-Command python -ErrorAction SilentlyContinue
    if (-not $sysPython) {
        Write-Host '[ERROR] No bundled venv found, and Python is not installed on this laptop.' -ForegroundColor Red
        Write-Host 'This laptop needs the one-time setup done BEFORE you go out on the water.' -ForegroundColor Red
        Write-Host 'See INSTRUCTIONS.html — section "Before you leave home".' -ForegroundColor Red
        Read-Host 'Press Enter to close'
        exit 1
    }
    $PythonExe = 'python'
    Write-Host '[WARN] Bundled venv not found — falling back to system Python.' -ForegroundColor Yellow
}

# --- 2. Check the required Python packages are already installed (offline check) ---
# (Written to a temp .py file rather than passed as a -c string — passing a string with
#  embedded double quotes through PowerShell -> external process argv can mangle/strip
#  the quotes, which broke this check.)
$checkScriptPath = Join-Path $StateDir 'check_deps.py'
@'
import importlib.util, sys
mods = ["flask", "flask_socketio", "pymavlink", "cv2"]
missing = [m for m in mods if importlib.util.find_spec(m) is None]
sys.exit(1 if missing else 0)
'@ | Set-Content -Path $checkScriptPath -Encoding utf8
& $PythonExe $checkScriptPath
if ($LASTEXITCODE -ne 0) {
    Write-Host '[ERROR] Required Python packages are not installed.' -ForegroundColor Red
    Write-Host 'This laptop needs internet the FIRST time to run:' -ForegroundColor Red
    Write-Host "    python -m venv venv" -ForegroundColor Yellow
    Write-Host "    venv\Scripts\pip.exe install -r `"$WebUiDir\requirements.txt`"" -ForegroundColor Yellow
    Write-Host 'Do this at home before heading out. Once installed, this works fully offline.' -ForegroundColor Red
    Read-Host 'Press Enter to close'
    exit 1
}
Write-Host '[OK] Python and required packages found.' -ForegroundColor Green

# --- 3. Sanity-check WiFi (informational only — do not block, just warn) ---
$wifi = (netsh wlan show interfaces) -join "`n"
if ($wifi -match 'SSID\s*:\s*(PRA_Station[^\r\n]*)') {
    Write-Host "[OK] Connected to drone WiFi: $($matches[1].Trim())" -ForegroundColor Green
} else {
    Write-Host '[WARN] This laptop does not appear to be connected to the drone WiFi (PRA_Station_xxxxxx).' -ForegroundColor Yellow
    Write-Host '       Make sure the drone + base station are powered on and you have joined its WiFi network.' -ForegroundColor Yellow
    Write-Host '       Continuing anyway — the cockpit will just show "Disconnected" until you do.' -ForegroundColor Yellow
}

# --- 4. Start the server in the background ---
Write-Host ''
Write-Host 'Starting cockpit server...' -ForegroundColor Cyan

$proc = Start-Process -FilePath $PythonExe -ArgumentList '-u', "`"$ServerPy`"" `
    -WorkingDirectory $WebUiDir `
    -WindowStyle Hidden `
    -RedirectStandardOutput $LogFile `
    -RedirectStandardError "$LogFile.err" `
    -PassThru

$proc.Id | Out-File -FilePath $PidFile -Encoding ascii

# --- 5. Wait for the web server to answer, then open the browser ---
Write-Host 'Waiting for cockpit to come up' -NoNewline -ForegroundColor Cyan
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Milliseconds 500
    Write-Host '.' -NoNewline -ForegroundColor Cyan
    try {
        $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($resp.StatusCode -eq 200) { $ready = $true; break }
    } catch { }
    if (-not (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue)) {
        Write-Host ''
        Write-Host '[ERROR] The server process exited unexpectedly. Check the log:' -ForegroundColor Red
        Write-Host "    $LogFile.err" -ForegroundColor Yellow
        Remove-Item $PidFile -ErrorAction SilentlyContinue
        Read-Host 'Press Enter to close'
        exit 1
    }
}
Write-Host ''

if ($ready) {
    Write-Host "[OK] Cockpit is running (PID $($proc.Id))." -ForegroundColor Green
    Write-Host "Opening browser at $Url ..." -ForegroundColor Yellow
    Start-Process $Url
    Write-Host ''
    Write-Host 'Leave this window open (or minimized) while you fly.' -ForegroundColor Cyan
    Write-Host 'To stop the cockpit later, run Stop-Cockpit.cmd.' -ForegroundColor Cyan
} else {
    Write-Host '[WARN] Server did not answer within 15s — it may still be starting.' -ForegroundColor Yellow
    Write-Host "Try opening $Url manually in your browser in a few seconds." -ForegroundColor Yellow
}
