$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$package = Get-AppxPackage '*PowerBI*' | Sort-Object Version -Descending | Select-Object -First 1
if (-not $package) { throw 'Power BI Desktop is required for native TMDL validation' }
$pbiBin = Join-Path $package.InstallLocation 'bin'
foreach ($assembly in @(
    'Microsoft.AnalysisServices.Server.Core.dll',
    'Microsoft.AnalysisServices.Server.Tabular.dll',
    'Microsoft.AnalysisServices.Server.Tabular.Json.dll',
    'Microsoft.PowerBI.Tabular.dll',
    'Microsoft.PowerBI.Tabular.Json.dll'
)) {
    [Reflection.Assembly]::LoadFrom((Join-Path $pbiBin $assembly)) | Out-Null
}
$modelPath = Join-Path $projectRoot 'powerbi/project/ScanNifty100.SemanticModel/definition'
$database = [Microsoft.AnalysisServices.Tabular.TmdlSerializer]::DeserializeDatabaseFromFolder($modelPath)
Write-Output ('TMDL parsed: {0} tables, {1} relationships, {2} measures' -f $database.Model.Tables.Count, $database.Model.Relationships.Count, ($database.Model.Tables | ForEach-Object { $_.Measures.Count } | Measure-Object -Sum).Sum)
