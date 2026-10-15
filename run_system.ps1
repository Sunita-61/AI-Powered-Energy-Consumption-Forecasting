<#
.SYNOPSIS
    All-India Electricity Grid Demand Forecasting System - Unified Service Launcher
.DESCRIPTION
    Starts the FastAPI backend (port 8000), Streamlit dashboard (port 8502),
    and Caddy reverse proxy on port 8501.
    Provides single-origin unified entrypoint at http://localhost:8501.
    Cleanly shuts down all child processes on exit.
#>

$ErrorActionPreference = "Stop"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   AI-Powered Energy Consumption Forecasting - India Grid" -ForegroundColor Cyan
Write-Host "               Unified Service Launcher (Port 8501)" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Resolve Python Executable
$PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PythonExe) {
    Write-Error "Python executable not found in PATH."
    exit 1
}
Write-Host "[1/5] Using Python: $PythonExe" -ForegroundColor Green

# 2. Locate Caddy Executable
$CaddyExe = (Get-Command caddy -ErrorAction SilentlyContinue).Source
if (-not $CaddyExe) {
    # Check winget standard install location
    $CaddySearch = Get-ChildItem -Path "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\*caddy*" -Recurse -Filter "caddy.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($CaddySearch) {
        $CaddyExe = $CaddySearch.FullName
    }
}

if (-not $CaddyExe) {
    Write-Error "Caddy executable could not be located. Please install Caddy via 'winget install CaddyServer.Caddy'."
    exit 1
}
Write-Host "[2/5] Located Caddy: $CaddyExe" -ForegroundColor Green

# 3. Clean stale port listeners on 8501, 8502, 8000 if any
$TargetPorts = @(8501, 8502, 8000)
foreach ($Port in $TargetPorts) {
    $StalePID = (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue).OwningProcess
    if ($StalePID -and $StalePID -ne $PID) {
        Write-Host "  Freeing occupied port $Port (Process ID: $StalePID)..." -ForegroundColor Yellow
        try { Stop-Process -Id $StalePID -Force -ErrorAction SilentlyContinue } catch {}
    }
}

# 4. Start Internal Services as background processes
Write-Host "[3/5] Starting FastAPI REST service on 127.0.0.1:8000..." -ForegroundColor Cyan
$FastApiProcess = Start-Process -FilePath $PythonExe -ArgumentList "-m uvicorn api.main:app --host 127.0.0.1 --port 8000" -PassThru -NoNewWindow

Write-Host "[4/5] Starting Streamlit dashboard on 127.0.0.1:8502..." -ForegroundColor Cyan
$StreamlitProcess = Start-Process -FilePath $PythonExe -ArgumentList "-m streamlit run app/dashboard.py --server.headless true --server.port 8502" -PassThru -NoNewWindow

# Wait 3 seconds for internal sockets
Start-Sleep -Seconds 3

# 5. Start Caddy Reverse Proxy
Write-Host "[5/5] Starting Caddy reverse proxy on port 8501..." -ForegroundColor Cyan
$CaddyProcess = Start-Process -FilePath $CaddyExe -ArgumentList "run --config Caddyfile" -PassThru -NoNewWindow

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "  ALL SERVICES OPERATIONAL - UNIFIED LOCAL ENTRYPOINT:           " -ForegroundColor Green
Write-Host "  👉 Primary URL:       http://localhost:8501                     " -ForegroundColor Yellow
Write-Host "  👉 Interactive UI:    http://localhost:8501/                    " -ForegroundColor Yellow
Write-Host "  👉 Live Data Status:  http://localhost:8501/api/data-status     " -ForegroundColor Yellow
Write-Host "  👉 API Forecast:      http://localhost:8501/api/forecast        " -ForegroundColor Yellow
Write-Host "  👉 API Metrics:       http://localhost:8501/api/metrics         " -ForegroundColor Yellow
Write-Host "  👉 Swagger API Docs:  http://localhost:8501/api/docs            " -ForegroundColor Yellow
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "Press Ctrl+C to cleanly stop all services." -ForegroundColor Gray
Write-Host ""

try {
    # Keep script alive and monitor child processes
    while ($true) {
        if ($FastApiProcess.HasExited -or $StreamlitProcess.HasExited -or $CaddyProcess.HasExited) {
            Write-Warning "One of the services terminated unexpectedly."
            break
        }
        Start-Sleep -Seconds 2
    }
}
finally {
    Write-Host "`nStopping all background services cleanly..." -ForegroundColor Yellow
    if ($CaddyProcess -and -not $CaddyProcess.HasExited) { Stop-Process -Id $CaddyProcess.Id -Force -ErrorAction SilentlyContinue }
    if ($FastApiProcess -and -not $FastApiProcess.HasExited) { Stop-Process -Id $FastApiProcess.Id -Force -ErrorAction SilentlyContinue }
    if ($StreamlitProcess -and -not $StreamlitProcess.HasExited) { Stop-Process -Id $StreamlitProcess.Id -Force -ErrorAction SilentlyContinue }
    Write-Host "Shutdown complete." -ForegroundColor Green
}
