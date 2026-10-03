param()

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $root '.env'

if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^[\s]*([^#=]+)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim())
        }
    }
}

$dbName = $env:DB_NAME
if (-not $dbName) { $dbName = 'scannifty100' }

$dbUser = $env:DB_USER
if (-not $dbUser) { $dbUser = 'scannifty100' }

$dbPassword = $env:DB_PASSWORD
if (-not $dbPassword) { $dbPassword = 'change-me' }

$dbHost = $env:DB_HOST
if (-not $dbHost) { $dbHost = 'localhost' }

$dbPort = $env:DB_PORT
if (-not $dbPort) { $dbPort = '5433' }

$conn = "postgresql://$dbUser`:$dbPassword@$dbHost`:$dbPort/$dbName"

Write-Host "ScanNifty100 Warehouse Deployment"
Write-Host "Target: $dbName on $dbHost`:$dbPort"

& python -m apps.etl.pipelines.refresh_all --deploy

Write-Host 'Warehouse deployment complete'
Write-Host "Validation: psql `"$conn`" -f warehouse/checks/validation_queries.sql"
