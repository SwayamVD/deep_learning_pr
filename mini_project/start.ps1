# ============================================================
# Devanagari Classifier — Quick Start Script
# Run from the "Mini project" folder:  .\start.ps1
# ============================================================

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Devanagari Classifier — Quick Start" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python not found. Install Python 3.9+ first." -ForegroundColor Red
    exit 1
}

# Install deps if not present
Write-Host "`nInstalling backend dependencies..." -ForegroundColor Yellow
pip install -r backend\requirements.txt --quiet

# Check for model file
$modelPath = "backend\devanagari_resnet18.h5"
if (-not (Test-Path $modelPath)) {
    Write-Host ""
    Write-Host "WARNING: Model file not found at '$modelPath'" -ForegroundColor Yellow
    Write-Host "  The backend will start but predictions won't work until the model is saved." -ForegroundColor Yellow
    Write-Host "  Add this cell at the end of your Colab notebook after training:" -ForegroundColor Cyan
    Write-Host '    model.save("devanagari_resnet18.h5")' -ForegroundColor White
    Write-Host "  Then download the .h5 file from Colab and place it in the backend/ folder." -ForegroundColor Cyan
    Write-Host ""
}

# Start Flask server
Write-Host "`nStarting Flask server..." -ForegroundColor Green
Write-Host "  Frontend: http://localhost:5000" -ForegroundColor White
Write-Host "  API:      http://localhost:5000/api" -ForegroundColor White
Write-Host ""

Set-Location backend
python run.py
