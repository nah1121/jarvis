#!/usr/bin/env pwsh
# JARVIS Launcher Script for Windows 11
# Checks dependencies and starts all required services

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  JARVIS Windows 11 Launcher" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if a URL is reachable
function Test-ServiceRunning {
    param(
        [string]$Url,
        [string]$ServiceName
    )

    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 404) {
            Write-Host "[OK] $ServiceName is running at $Url" -ForegroundColor Green
            return $true
        }
    } catch {
        Write-Host "[WARN] $ServiceName is NOT running at $Url" -ForegroundColor Yellow
        return $false
    }
    return $false
}

# Check Python
Write-Host "Checking Python installation..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found. Please install Python 3.10+" -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Check Node.js
Write-Host "Checking Node.js installation..." -ForegroundColor Cyan
try {
    $nodeVersion = node --version 2>&1
    Write-Host "[OK] Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Node.js not found. Please install Node.js" -ForegroundColor Red
    Write-Host "Download from: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# Check Copilot CLI
Write-Host "Checking GitHub Copilot CLI..." -ForegroundColor Cyan
try {
    $copilotVersion = copilot --version 2>&1
    Write-Host "[OK] Copilot CLI found: $copilotVersion" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Copilot CLI not found. Install with: npm install -g @github/copilot" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Checking required services..." -ForegroundColor Cyan
Write-Host ""

# Check Fish Speech TTS server
$ttsRunning = Test-ServiceRunning -Url "http://localhost:8080/v1/voices" -ServiceName "Fish Speech TTS"
if (-not $ttsRunning) {
    Write-Host "  -> Start Fish Speech: cd C:\fish-speech && python -m fish_speech.api_server" -ForegroundColor Yellow
    Write-Host "  -> Or update TTS_BASE_URL in .env to your TTS server URL" -ForegroundColor Yellow
}

Write-Host ""

# Check .env file
if (-not (Test-Path ".env")) {
    Write-Host "[WARN] .env file not found. Copying from .env.example..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "[OK] Created .env file. Please edit it with your settings." -ForegroundColor Green
        Write-Host "  -> Confirm COPILOT_CLI_ENABLED=true" -ForegroundColor Cyan
        Write-Host "  -> Set COPILOT_MODEL_FAST / COPILOT_MODEL_SMART as needed" -ForegroundColor Cyan
        Write-Host "  -> Set TTS_BASE_URL=http://localhost:8080" -ForegroundColor Cyan
    } else {
        Write-Host "[ERROR] .env.example not found" -ForegroundColor Red
        exit 1
    }
}

# Check if Python dependencies are installed
Write-Host "Checking Python dependencies..." -ForegroundColor Cyan
$pipList = pip list 2>&1
if ($pipList -notmatch "fastapi") {
    Write-Host "[WARN] Some Python packages may be missing. Installing..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Check if frontend dependencies are installed
Write-Host "Checking frontend dependencies..." -ForegroundColor Cyan
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "[WARN] Frontend dependencies not installed. Installing..." -ForegroundColor Yellow
    Push-Location frontend
    npm install
    Pop-Location
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting JARVIS..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start backend in a new window
Write-Host "Starting JARVIS backend server..." -ForegroundColor Green
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    python server.py
}

Write-Host "[OK] Backend started (Job ID: $($backendJob.Id))" -ForegroundColor Green
Write-Host "  -> Backend will run on https://0.0.0.0:8443" -ForegroundColor Cyan

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start frontend in a new window
Write-Host "Starting JARVIS frontend..." -ForegroundColor Green
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    Set-Location frontend
    npm run dev
}

Write-Host "[OK] Frontend started (Job ID: $($frontendJob.Id))" -ForegroundColor Green
Write-Host "  -> Frontend will run on http://localhost:5173" -ForegroundColor Cyan

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  JARVIS is starting up!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend logs:" -ForegroundColor Yellow
Write-Host "  View with: Receive-Job -Id $($backendJob.Id) -Keep" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend logs:" -ForegroundColor Yellow
Write-Host "  View with: Receive-Job -Id $($frontendJob.Id) -Keep" -ForegroundColor Cyan
Write-Host ""
Write-Host "Open your browser to: http://localhost:5173" -ForegroundColor Green
Write-Host ""
Write-Host "To stop JARVIS:" -ForegroundColor Yellow
Write-Host "  Stop-Job -Id $($backendJob.Id),$($frontendJob.Id)" -ForegroundColor Cyan
Write-Host "  Remove-Job -Id $($backendJob.Id),$($frontendJob.Id)" -ForegroundColor Cyan
Write-Host ""

# Optional: Open browser automatically after a delay
Start-Sleep -Seconds 5
Write-Host "Opening browser..." -ForegroundColor Green
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "Press Ctrl+C to stop monitoring, or close this window." -ForegroundColor Yellow
Write-Host "The jobs will continue running in the background." -ForegroundColor Yellow
Write-Host ""

# Monitor both jobs and show output
try {
    while ($true) {
        # Show backend output
        $backendOutput = Receive-Job -Id $backendJob.Id
        if ($backendOutput) {
            Write-Host "[BACKEND] $backendOutput" -ForegroundColor Blue
        }

        # Show frontend output
        $frontendOutput = Receive-Job -Id $frontendJob.Id
        if ($frontendOutput) {
            Write-Host "[FRONTEND] $frontendOutput" -ForegroundColor Magenta
        }

        # Check if jobs are still running
        $backendState = (Get-Job -Id $backendJob.Id).State
        $frontendState = (Get-Job -Id $frontendJob.Id).State

        if ($backendState -eq "Failed" -or $backendState -eq "Stopped") {
            Write-Host "[ERROR] Backend job stopped or failed!" -ForegroundColor Red
            break
        }

        if ($frontendState -eq "Failed" -or $frontendState -eq "Stopped") {
            Write-Host "[ERROR] Frontend job stopped or failed!" -ForegroundColor Red
            break
        }

        Start-Sleep -Milliseconds 500
    }
} finally {
    Write-Host ""
    Write-Host "Cleaning up..." -ForegroundColor Yellow
    Stop-Job -Id $backendJob.Id,$frontendJob.Id -ErrorAction SilentlyContinue
    Remove-Job -Id $backendJob.Id,$frontendJob.Id -ErrorAction SilentlyContinue
    Write-Host "Jobs stopped." -ForegroundColor Green
}
