# Script de démarrage du frontend
# Exécuter: .\start_frontend.ps1

Write-Host "[START] Demarrage du Frontend ERP (Streamlit)..." -ForegroundColor Cyan

# Détecter automatiquement le chemin Python dans .venv
$venvPath = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (Test-Path $venvPath) {
    Write-Host "[OK] Environnement Python trouve" -ForegroundColor Green
    & $venvPath -m streamlit run frontend/app.py
} else {
    Write-Host "[ERROR] Environnement virtuel non trouve" -ForegroundColor Red
    Write-Host "Executez d'abord: python -m venv .venv" -ForegroundColor Yellow
    Write-Host "Puis: .venv\Scripts\Activate.ps1" -ForegroundColor Yellow
}
