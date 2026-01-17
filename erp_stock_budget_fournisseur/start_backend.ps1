# Script de démarrage du backend
# Exécuter: .\start_backend.ps1

Write-Host "[START] Demarrage du Backend ERP (MongoDB)..." -ForegroundColor Cyan

# Détecter automatiquement le chemin Python dans .venv
$venvPath = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (Test-Path $venvPath) {
    Write-Host "[OK] Environnement Python trouve" -ForegroundColor Green
    Write-Host "[INFO] Connexion a MongoDB Atlas..." -ForegroundColor Cyan
    & $venvPath -m uvicorn backend.main:app --reload --port 8000
} else {
    Write-Host "[ERROR] Environnement virtuel non trouve" -ForegroundColor Red
    Write-Host "Executez d'abord: python -m venv .venv" -ForegroundColor Yellow
    Write-Host "Puis: .venv\Scripts\Activate.ps1" -ForegroundColor Yellow
}
