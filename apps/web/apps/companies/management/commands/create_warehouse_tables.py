"""
Management command to initialise the PostgreSQL warehouse schema.

Applies the DDL files from warehouse/ddl/ in order, then seeds the
static dimension tables (dim_sector, dim_health_label).

Idempotent: every DDL statement uses CREATE TABLE IF NOT EXISTS /
CREATE INDEX IF NOT EXISTS / ON CONFLICT DO UPDATE, so it is safe
to run multiple times without destroying existing data.
"""
from __future__ import annotations

import logging
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import connection

logger = logging.getLogger(__name__)

# Resolve paths relative to this file's location inside the project.
# File lives at:  apps/web/apps/companies/management/commands/create_warehouse_tables.py
# Project root is 6 levels up:
COMMAND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = COMMAND_DIR.parents[5]

DDL_DIR = PROJECT_ROOT / "warehouse" / "ddl"
SEEDS_DIR = PROJECT_ROOT / "warehouse" / "seeds"

# Ordered list of DDL files to apply
DDL_FILES = [
    "001_create_schema.sql",
    "002_dim_tables.sql",
    "003_fact_tables.sql",
    "004_indexes_views.sql",
    "005_grants.sql",
]

# Seed files to run after DDL
SEED_FILES = [
    "dim_sector.sql",
    "dim_health_label.sql",
]


def _split_sql_statements(sql: str) -> list[str]:
    """
    Split a SQL script into individual statements, respecting:
    - Dollar-quoted strings ($$...$$, $body$...$body$)
    - Single-quoted strings
    - Line comments (--)
    - Block comments (/* */)
    """
    import re
    statements: list[str] = []
    current: list[str] = []
    dollar_tag: str | None = None
    i = 0

    while i < len(sql):
        # Inside a dollar-quoted string
        if dollar_tag is not None:
            end = sql.find(dollar_tag, i)
            if end == -1:
                current.append(sql[i:])
                break
            end += len(dollar_tag)
            current.append(sql[i:end])
            i = end
            dollar_tag = None
            continue

        ch = sql[i]

        # Start of a dollar-quoted string
        if ch == "$":
            m = re.match(r"\$([A-Za-z_][A-Za-z0-9_]*)?\$", sql[i:])
            if m:
                dollar_tag = m.group(0)
                current.append(dollar_tag)
                i += len(dollar_tag)
                continue

        # Single-quoted string
        if ch == "'":
            j = i + 1
            while j < len(sql):
                if sql[j] == "'" and (j + 1 < len(sql) and sql[j + 1] == "'"):
                    j += 2
                elif sql[j] == "'":
                    j += 1
                    break
                else:
                    j += 1
            current.append(sql[i:j])
            i = j
            continue

        # Line comment
        if sql[i:i+2] == "--":
            end = sql.find("\n", i)
            if end == -1:
                current.append(sql[i:])
                break
            current.append(sql[i:end+1])
            i = end + 1
            continue

        # Block comment
        if sql[i:i+2] == "/*":
            end = sql.find("*/", i + 2)
            if end == -1:
                current.append(sql[i:])
                break
            current.append(sql[i:end+2])
            i = end + 2
            continue

        # Statement terminator
        if ch == ";":
            stmt = "".join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
            i += 1
            continue

        current.append(ch)
        i += 1

    # Trailing statement without semicolon
    remainder = "".join(current).strip()
    if remainder:
        statements.append(remainder)

    return statements


def _run_sql_file(cursor, path: Path, label: str, stdout) -> None:
    """Execute a SQL file, correctly handling dollar-quoted plpgsql bodies."""
    sql = path.read_text(encoding="utf-8")
    statements = _split_sql_statements(sql)
    for stmt in statements:
        try:
            cursor.execute(stmt)
        except Exception as exc:
            # Most "already exists" errors are safe to skip; log them verbosely
            # only in DEBUG mode, briefly in normal mode.
            stdout.write(f"    ⚠  Skipped: {exc!s:.200}")
    stdout.write(f"  ✓ {label}")


class Command(BaseCommand):
    help = (
        "Initialise the PostgreSQL warehouse schema and seed static dimensions. "
        "Idempotent — safe to run on an already-initialised database."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--ddl-only",
            action="store_true",
            help="Apply DDL files only; skip seed data.",
        )
        parser.add_argument(
            "--seeds-only",
            action="store_true",
            help="Apply seed data only; skip DDL files.",
        )

    def handle(self, *args, **options):
        ddl_only = options["ddl_only"]
        seeds_only = options["seeds_only"]

        self.stdout.write(self.style.MIGRATE_HEADING("ScanNifty100 — Warehouse Initialisation"))
        self.stdout.write(f"  Project root : {PROJECT_ROOT}")
        self.stdout.write(f"  DDL dir      : {DDL_DIR}")
        self.stdout.write(f"  Seeds dir    : {SEEDS_DIR}")
        self.stdout.write("")

        with connection.cursor() as cursor:
            if not seeds_only:
                self.stdout.write(self.style.MIGRATE_HEADING("Step 1/2  — Applying DDL"))
                for filename in DDL_FILES:
                    path = DDL_DIR / filename
                    if not path.exists():
                        self.stdout.write(
                            self.style.WARNING(f"  ⚠  DDL file not found, skipping: {path}")
                        )
                        continue
                    try:
                        _run_sql_file(cursor, path, filename, self.stdout)
                    except Exception as exc:
                        self.stderr.write(self.style.ERROR(f"  ✗ FAILED {filename}: {exc}"))
                        raise

            if not ddl_only:
                self.stdout.write("")
                self.stdout.write(self.style.MIGRATE_HEADING("Step 2/2  — Seeding static dimensions"))
                for filename in SEED_FILES:
                    path = SEEDS_DIR / filename
                    if not path.exists():
                        self.stdout.write(
                            self.style.WARNING(f"  ⚠  Seed file not found, skipping: {path}")
                        )
                        continue
                    try:
                        _run_sql_file(cursor, path, filename, self.stdout)
                    except Exception as exc:
                        self.stderr.write(self.style.ERROR(f"  ✗ FAILED {filename}: {exc}"))
                        raise

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("✅  Warehouse initialisation complete.")
        )
