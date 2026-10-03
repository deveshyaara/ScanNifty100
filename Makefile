.PHONY: help setup install-dev install-prod test lint format clean docker-up docker-down etl check-source run worker beat migrate shell verify-setup deploy-warehouse validate-warehouse load-warehouse etl-full refresh-mvs validate-clean

help:
	@echo "ScanNifty100 Commands"
	@echo "==================="
	@echo "make setup         - Create venv and install dev dependencies"
	@echo "make install-dev   - Install development dependencies"
	@echo "make install-prod  - Install production dependencies"
	@echo "make docker-up     - Start Docker services (dev, with override)"
	@echo "make docker-prod   - Start Docker services (production, no override)"
	@echo "make docker-down   - Stop Docker services"
	@echo "make verify-setup  - Run environment verification"
	@echo "make check-source  - Check if all source Excel files are present"
	@echo "make etl           - Run ETL pipeline (extract + transform)"
	@echo "make load-warehouse - Load clean CSVs to PostgreSQL warehouse"
	@echo "make etl-full      - Run extract, transform, and load"
	@echo "make refresh-mvs   - Refresh warehouse materialized views"
	@echo "make validate-clean - Run phase 6 validation tests"
	@echo "make run           - Start Django development server"
	@echo "make worker        - Start Celery worker"
	@echo "make beat          - Start Celery beat"
	@echo "make migrate       - Run Django migrations"
	@echo "make deploy-warehouse - Deploy PostgreSQL warehouse DDL"
	@echo "make validate-warehouse - Run warehouse validation queries"
	@echo "make shell         - Open Django shell"
	@echo "make test          - Run tests"
	@echo "make lint          - Run linters"
	@echo "make format        - Format code"
	@echo "make clean         - Remove cache files"

setup:
	python -m venv venv
	venv\\Scripts\\python.exe -m pip install --upgrade pip
	venv\\Scripts\\pip.exe install -r requirements/dev.txt

install-dev:
	pip install -r requirements/dev.txt

install-prod:
	pip install -r requirements/prod.txt

docker-up:
	docker compose up -d

docker-prod:
	@echo "Starting production stack (no docker-compose.override.yml)..."
	docker compose -f docker-compose.yml up -d

docker-down:
	docker compose down

verify-setup:
	python scripts/verify_setup.py

test:
	pytest apps/ tests/ --cov=apps --cov-report=html --cov-report=term

lint:
	flake8 apps/ tests/
	black --check apps/ tests/
	isort --check apps/ tests/

format:
	black apps/ tests/
	isort apps/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache htmlcov dist build

run:
	cd apps/web && python manage.py runserver

worker:
	cd apps/web && celery -A config worker --loglevel=info

beat:
	cd apps/web && celery -A config beat --loglevel=info

migrate:
	cd apps/web && python manage.py makemigrations
	cd apps/web && python manage.py migrate

shell:
	cd apps/web && python manage.py shell

check-source:
	python scripts/check_source_files.py

etl: check-source
	python apps/etl/pipelines/01_extract_n100.py
	python apps/etl/pipelines/02_clean_transform.py

load-warehouse:
	python apps/etl/pipelines/03_load_warehouse.py
	@echo "✅ Warehouse loading complete"

etl-full:
	@echo "Running full ETL pipeline (01 → 02 → 03)..."
	python apps/etl/pipelines/01_extract_n100.py
	python apps/etl/pipelines/02_clean_transform.py
	python apps/etl/pipelines/03_load_warehouse.py
	@echo "✅ Full ETL pipeline completed"

refresh-mvs:
	psql $(DB_URL) -c "SELECT refresh_all_materialized_views();"
	@echo "✅ Materialized views refreshed"

validate-clean:
	pytest tests/integration/test_02_clean.py -v

deploy-warehouse:
	powershell -ExecutionPolicy Bypass -File scripts/deploy_warehouse.ps1

validate-warehouse:
	psql -U bluestock_user -d bluestock_dw -h localhost -p 5432 -f warehouse/checks/validation_queries.sql
