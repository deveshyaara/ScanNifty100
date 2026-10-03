# Power BI Setup Script for ScanNifty100
# This script automates the setup process for Power BI dashboards

param(
    [Parameter(Mandatory=$false)]
    [string]$WorkspacePath = "E:\ScanNifty100",
    
    [Parameter(Mandatory=$false)]
    [switch]$SetupPostgreSQL = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$VerifyConnection = $true,
    
    [Parameter(Mandatory=$false)]
    [switch]$CreateMeasures = $true
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  ScanNifty100 Power BI Setup Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$postgresServer = "localhost"
$postgresPort = "5432"
$postgresDB = "bluestock_dw"
$postgresUser = "bluestock_user"

# Colors for output
$successColor = "Green"
$errorColor = "Red"
$infoColor = "Yellow"

function Write-Success {
    param([string]$Message)
    Write-Host "[✓] $Message" -ForegroundColor $successColor
}

function Write-ErrorMsg {
    param([string]$Message)
    Write-Host "[✗] $Message" -ForegroundColor $errorColor
}

function Write-Info {
    param([string]$Message)
    Write-Host "[i] $Message" -ForegroundColor $infoColor
}

# Step 1: Verify PostgreSQL Connection
Write-Host ""
Write-Host "Step 1: Verifying PostgreSQL Connection" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Cyan

if ($VerifyConnection) {
    try {
        # Check if PostgreSQL is running
        $pgProcess = Get-Process -Name "postgres" -ErrorAction SilentlyContinue
        if ($pgProcess) {
            Write-Success "PostgreSQL is running (PID: $($pgProcess.Id))"
        } else {
            Write-ErrorMsg "PostgreSQL is not running"
            Write-Info "Starting PostgreSQL..."
            
            # Try to start PostgreSQL service
            try {
                Start-Service -Name "postgresql-x64-15" -ErrorAction Stop
                Write-Success "PostgreSQL service started"
                Start-Sleep -Seconds 3
            } catch {
                Write-ErrorMsg "Could not start PostgreSQL service: $_"
                Write-Info "Please start PostgreSQL manually"
            }
        }
        
        # Test connection using psql if available
        $psqlPath = (Get-Command psql -ErrorAction SilentlyContinue).Source
        if ($psqlPath) {
            Write-Info "Testing PostgreSQL connection..."
            $env:PGPASSWORD = "bluestock_password"  # Update with actual password
            $result = & $psqlPath -h $postgresServer -p $postgresPort -U $postgresUser -d $postgresDB -c "SELECT 1;" 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Success "PostgreSQL connection successful"
            } else {
                Write-ErrorMsg "PostgreSQL connection failed: $result"
            }
            Remove-Item Env:PGPASSWORD
        } else {
            Write-Info "psql not found, skipping connection test"
        }
    } catch {
        Write-ErrorMsg "Error checking PostgreSQL: $_"
    }
}

# Step 2: Verify Warehouse Schema
Write-Host ""
Write-Host "Step 2: Verifying Warehouse Schema" -ForegroundColor Cyan
Write-Host "-----------------------------------" -ForegroundColor Cyan

$schemaFiles = @(
    "warehouse\ddl\001_create_schema.sql",
    "warehouse\ddl\002_dim_tables.sql",
    "warehouse\ddl\003_fact_tables.sql",
    "warehouse\ddl\004_indexes_views.sql"
)

foreach ($file in $schemaFiles) {
    $fullPath = Join-Path $WorkspacePath $file
    if (Test-Path $fullPath) {
        Write-Success "Found: $file"
    } else {
        Write-ErrorMsg "Missing: $file"
    }
}

# Step 3: Create Power BI Configuration Directory
Write-Host ""
Write-Host "Step 3: Setting Up Power BI Configuration" -ForegroundColor Cyan
Write-Host "------------------------------------------" -ForegroundColor Cyan

$powerbiDir = Join-Path $WorkspacePath "powerbi"
if (-not (Test-Path $powerbiDir)) {
    New-Item -ItemType Directory -Path $powerbiDir -Force | Out-Null
    Write-Success "Created powerbi directory"
} else {
    Write-Success "PowerBI directory exists"
}

$configDir = Join-Path $powerbiDir "config"
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    Write-Success "Created config directory"
}

$daxDir = Join-Path $powerbiDir "dax"
if (-not (Test-Path $daxDir)) {
    New-Item -ItemType Directory -Path $daxDir -Force | Out-Null
    Write-Success "Created dax directory"
}

$dashboardsDir = Join-Path $powerbiDir "dashboards"
if (-not (Test-Path $dashboardsDir)) {
    New-Item -ItemType Directory -Path $dashboardsDir -Force | Out-Null
    Write-Success "Created dashboards directory"
}

$templatesDir = Join-Path $dashboardsDir "templates"
if (-not (Test-Path $templatesDir)) {
    New-Item -ItemType Directory -Path $templatesDir -Force | Out-Null
    Write-Success "Created templates directory"
}

# Step 4: Create DAX Measures Template
Write-Host ""
Write-Host "Step 4: Creating DAX Measures Template" -ForegroundColor Cyan
Write-Host "---------------------------------------" -ForegroundColor Cyan

$daxTemplate = @"
-- ============================================================================
-- ScanNifty100 Power BI - DAX Measures Template
-- ============================================================================
-- Copy these measures into Power BI Desktop
-- Create a table named '_Measures' and add these measures
-- ============================================================================

-- Basic Aggregations
Total Companies = DISTINCTCOUNT(dim_company[symbol])

Total Sectors = DISTINCTCOUNT(dim_company[sector])

-- Revenue Metrics
Total Sales = SUM(fact_profit_loss[sales])

Total Sales (Latest Year) = 
VAR LatestYear = CALCULATE(MAX(dim_year[sort_order]), ALL(dim_year))
RETURN
    CALCULATE([Total Sales], dim_year[sort_order] = LatestYear)

Avg Sales per Company = DIVIDE([Total Sales], [Total Companies], 0)

-- Profitability Metrics
Total Net Profit = SUM(fact_profit_loss[net_profit])

Avg OPM% = AVERAGE(fact_profit_loss[opm_pct])

Avg Net Profit Margin% = AVERAGE(fact_profit_loss[net_profit_margin_pct])

Avg ROE% = AVERAGE(fact_analysis[roe_pct])

-- Balance Sheet Metrics
Total Assets = SUM(fact_balance_sheet[total_assets])

Total Equity = SUM(fact_balance_sheet[shareholders_equity])

Total Borrowings = SUM(fact_balance_sheet[borrowings])

Avg Debt-to-Equity = AVERAGE(fact_balance_sheet[debt_to_equity])

-- Cash Flow Metrics
Total Free Cash Flow = SUM(fact_cash_flow[free_cash_flow])

Avg Cash Conversion Ratio = AVERAGE(fact_cash_flow[cash_conversion_ratio])

-- Growth Metrics
Avg 10Y Sales CAGR% = 
CALCULATE(
    AVERAGE(fact_analysis[compounded_sales_growth_pct]),
    fact_analysis[period_label] = "10Y"
)

Avg 5Y Sales CAGR% = 
CALCULATE(
    AVERAGE(fact_analysis[compounded_sales_growth_pct]),
    fact_analysis[period_label] = "5Y"
)

Avg 3Y Sales CAGR% = 
CALCULATE(
    AVERAGE(fact_analysis[compounded_sales_growth_pct]),
    fact_analysis[period_label] = "3Y"
)

-- Health Score Metrics
Avg Health Score = AVERAGE(fact_ml_scores[overall_score])

Companies - Excellent = 
CALCULATE(
    [Total Companies],
    fact_ml_scores[health_label] = "EXCELLENT"
)

Companies - Weak or Poor = 
CALCULATE(
    [Total Companies],
    fact_ml_scores[health_label] IN {"WEAK", "POOR"}
)

-- Time Intelligence
YoY Sales Growth% = 
VAR CurrentYearSales = [Total Sales]
VAR PreviousYearSales = 
    CALCULATE(
        [Total Sales],
        DATEADD(dim_year[fiscal_year], -1, YEAR)
    )
RETURN
    DIVIDE(CurrentYearSales - PreviousYearSales, PreviousYearSales, BLANK()) * 100

-- Conditional Formatting Helpers
OPM% Color = 
VAR OPM = [Avg OPM%]
RETURN
    SWITCH(
        TRUE(),
        OPM >= 30, "#217346",
        OPM >= 20, "#70AD47",
        OPM >= 10, "#FFD700",
        OPM >= 5, "#FF8C00",
        "#C0392B"
    )
"@

$daxTemplatePath = Join-Path $daxDir "core_measures_template.dax"
$daxTemplate | Out-File -FilePath $daxTemplatePath -Encoding UTF8
Write-Success "Created DAX measures template: $daxTemplatePath"

# Step 5: Create Connection String Template
Write-Host ""
Write-Host "Step 5: Creating Connection Templates" -ForegroundColor Cyan
Write-Host "--------------------------------------" -ForegroundColor Cyan

$connectionTemplate = @"
# PostgreSQL Connection String for Power BI
# Use this when connecting to the warehouse

Server: $postgresServer
Port: $postgresPort
Database: $postgresDB
Username: $postgresUser
Password: [your_password]

# Connection String Format:
Host=$postgresServer;Port=$postgresPort;Database=$postgresDB;Username=$postgresUser;Password=******;

# In Power BI Desktop:
# 1. Get Data → PostgreSQL database
# 2. Enter Server: $postgresServer
# 3. Enter Database: $postgresDB
# 4. Enter Credentials
# 5. Select tables to load
"@

$connTemplatePath = Join-Path $configDir "connection_template.txt"
$connectionTemplate | Out-File -FilePath $connTemplatePath -Encoding UTF8
Write-Success "Created connection template: $connTemplatePath"

# Step 6: Create README
Write-Host ""
Write-Host "Step 6: Creating Setup Documentation" -ForegroundColor Cyan
Write-Host "-------------------------------------" -ForegroundColor Cyan

$setupReadme = @"
# Power BI Setup Guide

## Prerequisites

1. Power BI Desktop installed
2. PostgreSQL warehouse running
3. Data loaded into warehouse

## Quick Start

### 1. Open Power BI Desktop

### 2. Connect to PostgreSQL

1. Click **Get Data**
2. Search for **PostgreSQL**
3. Select **PostgreSQL database**
4. Click **Connect**

### 3. Enter Connection Details

```
Server: localhost
Database: bluestock_dw
Authentication: Database
Username: bluestock_user
Password: [your_password]
```

### 4. Select Tables

**Dimensions:**
- ✅ dim_company
- ✅ dim_year
- ✅ dim_sector
- ✅ dim_health_label

**Facts:**
- ✅ fact_profit_loss
- ✅ fact_balance_sheet
- ✅ fact_cash_flow
- ✅ fact_analysis
- ✅ fact_ml_scores
- ✅ fact_pros_cons

**Materialized Views:**
- ✅ mv_latest_financials
- ✅ mv_company_timeseries

Click **Load**

### 5. Configure Data Model

1. Switch to **Model** view (Ctrl+1)
2. Verify relationships are created
3. Hide technical columns
4. Set data categories

### 6. Create Measures

1. Create table named `_Measures`
2. Copy measures from `dax/core_measures_template.dax`
3. Paste into Power BI

### 7. Build Visuals

Follow specifications in:
- `dashboards/01_executive_overview_spec.md`

## Files in This Directory

- `README.md` - Main documentation
- `data_model.md` - Star schema documentation
- `config/powerbi_config.json` - Configuration settings
- `dax/core_measures_template.dax` - DAX measures
- `dashboards/` - Dashboard specifications
- `dashboards/templates/` - Additional dashboard templates

## Troubleshooting

### Connection Issues

```powershell
# Test PostgreSQL
Test-NetConnection -ComputerName localhost -Port 5432

# Check PostgreSQL service
Get-Service postgresql*
```

### Performance Issues

- Use Import mode (not DirectQuery)
- Filter to recent years
- Check indexes on fact tables

## Support

For issues, check:
1. PostgreSQL is running
2. Credentials are correct
3. Tables exist in database
4. Network connectivity

---
**Last Updated**: April 2026
"@

$setupReadmePath = Join-Path $powerbiDir "SETUP.md"
$setupReadme | Out-File -FilePath $setupReadmePath -Encoding UTF8
Write-Success "Created setup guide: $setupReadmePath"

# Step 7: Create Sample PBIX Template (Placeholder)
Write-Host ""
Write-Host "Step 7: Creating Dashboard Templates" -ForegroundColor Cyan
Write-Host "-------------------------------------" -ForegroundColor Cyan

# Create placeholder files for dashboards
$placeholders = @(
    "01_executive_overview.pbix",
    "02_company_deep_dive.pbix",
    "03_sector_comparison.pbix",
    "04_health_scorecard.pbix",
    "05_growth_analytics.pbix",
    "06_debt_leverage.pbix",
    "07_dividend_returns.pbix"
)

foreach ($placeholder in $placeholders) {
    $placeholderPath = Join-Path $dashboardsDir $placeholder
    if (-not (Test-Path $placeholderPath)) {
        # Create a marker file instead of actual PBIX
        $markerPath = [System.IO.Path]::ChangeExtension($placeholderPath, ".placeholder")
        "Power BI Dashboard: $placeholder`nCreated: $(Get-Date)" | Out-File -FilePath $markerPath -Encoding UTF8
        Write-Info "Placeholder: $placeholder (create in Power BI Desktop)"
    }
}

# Summary
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Success "Power BI configuration files created"
Write-Success "DAX measures template ready"
Write-Success "Connection templates configured"
Write-Success "Dashboard specifications documented"
Write-Host ""
Write-Info "Next Steps:"
Write-Host "  1. Open Power BI Desktop"
Write-Host "  2. Connect to PostgreSQL warehouse"
Write-Host "  3. Load tables as specified"
Write-Host "  4. Create measures from template"
Write-Host "  5. Build dashboards per specifications"
Write-Host ""
Write-Info "Documentation:"
Write-Host "  - Setup Guide: powerbi\SETUP.md"
Write-Host "  - Data Model: powerbi\data_model.md"
Write-Host "  - DAX Measures: powerbi\dax\core_measures.md"
Write-Host "  - Config: powerbi\config\powerbi_config.json"
Write-Host ""

# Optional: Open Power BI directory
$openDir = Read-Host "Open Power BI directory in Explorer? (Y/N)"
if ($openDir -eq "Y" -or $openDir -eq "y") {
    Invoke-Item $powerbiDir
}
