# Human Silhouette Detector - Setup Script (Windows / Anaconda)
# Usage: Right-click -> "Run with PowerShell"  or  .\setup.ps1

$ErrorActionPreference = "Stop"
$ENV_NAME = "silhouette"

Write-Host ""
Write-Host "=== Human Silhouette Detector - Setup ===" -ForegroundColor Cyan
Write-Host ""

# --- conda check ---
if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] conda not found. Install Anaconda or Miniconda first." -ForegroundColor Red
    Write-Host "  https://www.anaconda.com/download"
    exit 1
}

# --- create env if not exists ---
$envExists = conda env list 2>&1 | Select-String "^\s*$ENV_NAME\s"
if ($envExists) {
    Write-Host "[SKIP] conda env '$ENV_NAME' already exists." -ForegroundColor Yellow
} else {
    Write-Host "[1/2] Creating conda env '$ENV_NAME' (Python 3.11)..." -ForegroundColor Green
    conda create -n $ENV_NAME python=3.11 -y
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create conda env." -ForegroundColor Red
        exit 1
    }
}

# --- install requirements ---
Write-Host "[2/2] Installing packages..." -ForegroundColor Green
$reqPath = Join-Path $PSScriptRoot "requirements.txt"
conda run -n $ENV_NAME pip install -r $reqPath
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] pip install failed." -ForegroundColor Red
    exit 1
}

# --- model reminder ---
Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next: place the model file:" -ForegroundColor White
Write-Host "  models\pose_landmarker_lite.task" -ForegroundColor Yellow
Write-Host "  (see models\README.md for download instructions)"
Write-Host ""
Write-Host "To run:" -ForegroundColor White
Write-Host "  conda activate $ENV_NAME"
Write-Host "  python app.py        # Web server -> http://localhost:5000"
Write-Host "  python main.py       # Local window (dev)"
Write-Host ""
