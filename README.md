# ScanNifty100

Financial analytics platform for the local Nifty 100 workbook set. The project ingests the seven authoritative `n100/*.xlsx` workbooks, reconciles symbol/data-quality issues, publishes a PostgreSQL warehouse, serves Django/DRF endpoints, and generates a Power BI Project with seven connected report pages.

## Current Status

Verified on 2026-10-03:

- Extract, clean, analytics, warehouse deploy, and warehouse load complete successfully.
- PostgreSQL row counts after load: 100 companies, 1,149 annual metric rows, 1,260 P&L rows, 1,225 balance-sheet rows, 1,141 cash-flow rows.
- Django `check` and `check --deploy` pass with no warnings when production environment variables are supplied.
- Test suite: 42 integration tests passing.
- Power BI JSON validation: 115 schema-bound files, seven pages, all visual field bindings valid.
- Native Power BI TMDL parse: 12 tables, 16 relationships, 54 measures.

Known source limitations are preserved in the data-quality report instead of being guessed:

- `balancesheet.xlsx` is missing `SBIN` and `VBL`.
- `documents.xlsx` is missing `DIVISLAB`.
- `cashflow.xlsx` uses `AGTL`, normalized to `ATGL` with an audit entry.
- The `ABB` profile conflicts with source identity evidence and is withheld from scoring.
- Capex/cash/current-asset detail is absent, so metrics such as free cash flow, net debt, current ratio, and quick ratio remain unavailable instead of being fabricated.

## Project Structure

```text
apps/etl/             Workbook extraction, cleaning, reconciliation, warehouse loading
apps/analytics/       Metric generation, scoring, ranking, explanation logic
apps/web/             Django web app, DRF API, unmanaged warehouse models
apps/api_client/      Small Python client for the local API
warehouse/            PostgreSQL DDL, seeds, checks
powerbi/              PBIP/PBIR/TMDL project, schemas, generated DAX
data/                 raw/clean/reference generated artifacts
n100/                 authoritative workbook inputs
reports/              reconciliation and data-quality reports
scripts/              validation, Power BI generation, deployment helpers
tests/                integration tests for extract/clean/load behavior
```

## Environment

Copy `.env.example` to `.env` and set real secrets locally. Do not commit `.env`.

Important variables:

```env
DJANGO_SETTINGS_MODULE=config.settings.dev
DJANGO_SECRET_KEY=<long-random-secret>
DB_NAME=scannifty100
DB_USER=scannifty100
DB_PASSWORD=<strong-password>
DB_HOST=localhost
DB_PORT=5433
REDIS_URL=redis://localhost:6379/0
```

For production, use:

```env
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_ALLOWED_HOSTS=your-domain.example
CSRF_TRUSTED_ORIGINS=https://your-domain.example
CORS_ALLOWED_ORIGINS=https://your-frontend.example
```

## Local Run

Start PostgreSQL:

```powershell
docker compose up -d db
```

Run the full pipeline:

```powershell
venv\Scripts\python.exe -m apps.etl.pipelines.refresh_all --deploy --load
```

Run Django locally:

```powershell
venv\Scripts\python.exe apps\web\manage.py runserver 0.0.0.0:8000
```

Useful URLs:

- Web app: `http://localhost:8000/`
- API root: `http://localhost:8000/api/v1/`
- OpenAPI schema: `http://localhost:8000/api/schema/`
- Swagger UI: `http://localhost:8000/api/swagger-ui/`

## API Highlights

```text
GET /api/v1/companies/
GET /api/v1/companies/<SYMBOL>/
GET /api/v1/companies/<SYMBOL>/score/
GET /api/v1/companies/<SYMBOL>/financials/
GET /api/v1/companies/compare/?symbols=RELIANCE,TCS
GET /api/v1/sectors/
GET /api/v1/metrics/
GET /api/v1/rankings/
GET /api/v1/data-quality/
```

## Power BI

Regenerate the project after warehouse/schema changes:

```powershell
venv\Scripts\python.exe scripts\build_powerbi.py
venv\Scripts\python.exe scripts\validate_powerbi.py
powershell -NoProfile -File scripts\validate_tmdl.ps1
```

Open `powerbi/project/ScanNifty100.pbip` in Power BI Desktop. The generated model uses PostgreSQL import partitions with server/database parameters; credentials are intentionally not stored in the project.

## Verification

Run the main checks before deployment:

```powershell
venv\Scripts\python.exe apps\web\manage.py check
venv\Scripts\python.exe apps\web\manage.py check --deploy
venv\Scripts\python.exe -m pytest tests -q --tb=short
venv\Scripts\python.exe scripts\validate_powerbi.py
powershell -NoProfile -File scripts\validate_tmdl.ps1
venv\Scripts\python.exe apps\web\manage.py collectstatic --noinput
```

Warehouse assertions:

```powershell
venv\Scripts\python.exe -c "from apps.etl.load.db_connection import get_db_engine; from pathlib import Path; engine=get_db_engine(); sql=Path('warehouse/checks/assertions.sql').read_text(encoding='utf-8'); conn=engine.raw_connection(); cur=conn.cursor(); cur.execute(sql); conn.commit(); cur.close(); conn.close()"
```

## Deployment Notes

- `infra/docker/django.Dockerfile` installs production requirements and defaults to Gunicorn.
- `docker-compose.yml` still keeps a development `web` override using `runserver`; use a production Compose override or orchestrator command for Gunicorn behind HTTPS.
- `config.settings.prod` enables HSTS, secure cookies, SSL redirect, and proxy SSL header support. Set the host/origin variables correctly before public deployment.
- The source workbooks are proprietary/local data inputs; licensing for redistributed data must be handled separately.
