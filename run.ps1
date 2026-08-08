# run.ps1 - sobe backend (FastAPI :8000) e frontend (Vite :5173) numa execução.
# Uso:  ./run.ps1        (Ctrl+C encerra os dois)
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

# Instala deps do frontend no primeiro uso.
if (-not (Test-Path "$root\frontend\node_modules")) {
    Write-Host "Instalando dependências do frontend..." -ForegroundColor Cyan
    Push-Location "$root\frontend"; npm install; Pop-Location
}

Write-Host "Backend  -> http://localhost:8000" -ForegroundColor Green
Write-Host "Frontend -> http://localhost:5173" -ForegroundColor Green

# Backend em processo separado (uvicorn com reload).
$backend = Start-Process -PassThru -NoNewWindow -WorkingDirectory "$root\backend" `
    -FilePath "python" `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"

try {
    # Frontend em primeiro plano; o proxy do Vite encaminha /convert, /themes, /health.
    Push-Location "$root\frontend"
    npm run dev
}
finally {
    Pop-Location
    if ($backend -and -not $backend.HasExited) {
        # /T mata a árvore (uvicorn --reload cria processo filho).
        taskkill /PID $backend.Id /T /F 2>$null | Out-Null
    }
}
