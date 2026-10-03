param()

$ErrorActionPreference = 'Stop'

Write-Host '=== ScanNifty100 Bootstrap ==='

if (-not (Test-Path '.env')) {
    Copy-Item '.env.example' '.env'
    Write-Host 'Created .env from .env.example'
}

if (-not (Test-Path 'venv')) {
    python -m venv venv
    Write-Host 'Created virtual environment'
}

& .\venv\Scripts\python.exe -m pip install --upgrade pip
& .\venv\Scripts\python.exe -m pip install -r requirements\dev.txt

New-Item -ItemType Directory -Force -Path data\raw, data\staging, data\clean, data\reference, data\samples, data\logs, logs | Out-Null

Write-Host '=== Bootstrap Complete ==='
Write-Host 'Activate: .\\venv\\Scripts\\Activate.ps1'
Write-Host 'Verify:   python scripts/verify_setup.py'
Write-Host 'Start:    docker compose up -d'