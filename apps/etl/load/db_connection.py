"""
Database connection utilities for the warehouse loader.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL

logger = logging.getLogger(__name__)

load_dotenv(Path(__file__).resolve().parents[3] / '.env')


def get_db_url() -> str:
    """Return the PostgreSQL URL from `DATABASE_URL` or the component env vars."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    db_name = os.getenv("DB_NAME", "scannifty100")
    db_user = os.getenv("DB_USER", "scannifty100")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5433")

    if not db_password:
        raise ValueError("DATABASE_URL or DB_PASSWORD environment variable not set")

    return URL.create('postgresql', username=db_user, password=db_password, host=db_host, port=int(db_port), database=db_name).render_as_string(hide_password=False)


def get_db_engine(echo: bool = False) -> Engine:
    """Create a SQLAlchemy engine."""
    return create_engine(get_db_url(), echo=echo, future=True)


def get_db_connection():
    """Create a psycopg2 connection using the same environment settings."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg2.connect(database_url)

    db_name = os.getenv("DB_NAME", "scannifty100")
    db_user = os.getenv("DB_USER", "scannifty100")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5433")

    if not db_password:
        raise ValueError("DATABASE_URL or DB_PASSWORD environment variable not set")

    return psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
    )


def test_connection() -> bool:
    """Check whether the warehouse database is reachable."""
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            return conn.execute(text("SELECT 1")).scalar() == 1
    except Exception as exc:
        logger.error("Database connection failed: %s", exc)
        return False


def execute_sql_file(filepath: Path, conn) -> None:
    """Execute a SQL file against a psycopg2 connection."""
    with open(filepath, "r", encoding="utf-8") as handle:
        sql = handle.read()

    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()
    cursor.close()
