#!/usr/bin/env python3
"""Verify the Phase 3 environment setup."""

from __future__ import annotations

import importlib.metadata as metadata
import os
import subprocess
import sys
from pathlib import Path


REQUIRED_PACKAGES = {
    "pandas": "pandas",
    "numpy": "numpy",
    "openpyxl": "openpyxl",
    "Django": "django",
    "djangorestframework": "rest_framework",
    "celery": "celery",
    "redis": "redis",
    "psycopg2-binary": "psycopg2",
    "SQLAlchemy": "sqlalchemy",
}


def check_command(command: list[str], label: str) -> bool:
    try:
        subprocess.run(command, capture_output=True, check=True)
        print(f"✅ {label}")
        return True
    except Exception:
        print(f"❌ {label}")
        return False


def check_package(dist_name: str, import_name: str) -> bool:
    try:
        version = metadata.version(dist_name)
        __import__(import_name)
        print(f"✅ {dist_name} {version}")
        return True
    except Exception:
        print(f"❌ {dist_name}")
        return False


def check_path(path: str) -> bool:
    if Path(path).exists():
        print(f"✅ {path}")
        return True
    print(f"❌ {path}")
    return False


def main() -> int:
    print("ScanNifty100 Phase 3 Environment Verification")
    print("=" * 48)

    ok = True

    print("\nSystem commands:")
    ok &= check_command(["python", "--version"], "Python installed")
    ok &= check_command(["git", "--version"], "Git installed")
    ok &= check_command(["docker", "--version"], "Docker installed")
    ok &= check_command(["psql", "--version"], "PostgreSQL client installed")
    ok &= check_command(["redis-cli", "ping"], "Redis CLI reachable")

    print("\nPython packages:")
    for dist_name, import_name in REQUIRED_PACKAGES.items():
        ok &= check_package(dist_name, import_name)

    print("\nProject files:")
    for path in [
        ".env",
        "docker-compose.yml",
        "Makefile",
        "requirements/base.txt",
        "requirements/dev.txt",
        "requirements/prod.txt",
        "scripts/bootstrap.sh",
        "scripts/run_etl.sh",
    ]:
        ok &= check_path(path)

    print("\nProject directories:")
    for path in [
        "apps/web",
        "apps/etl",
        "apps/analytics",
        "data/source",
        "data/raw",
        "data/clean",
        "warehouse/ddl",
        "infra/docker",
    ]:
        ok &= check_path(path)

    print("\nEnvironment variables:")
    for key in ["DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "REDIS_URL"]:
        value = os.environ.get(key)
        print(f"{'✅' if value else '⚠️'} {key}{' set' if value else ' missing'}")

    print("\n" + "=" * 48)
    print("✅ Environment looks ready" if ok else "❌ Environment needs attention")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())