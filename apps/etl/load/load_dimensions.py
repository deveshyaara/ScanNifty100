"""
Dimension table loading utilities.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

CLEAN_DIR = Path("data/clean")


def _read_clean_csv(filename: str, **kwargs) -> pd.DataFrame:
    filepath = CLEAN_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Clean file not found: {filepath}")
    return pd.read_csv(filepath, **kwargs)


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y"}


def _as_int(value):
    if pd.isna(value) or value == "":
        return None
    return int(float(value))


def _as_float(value):
    if pd.isna(value) or value == "":
        return None
    return float(value)


def _upsert_rows(engine: Engine, sql: str, rows: Iterable[dict]) -> int:
    import math
    count = 0
    with engine.begin() as conn:
        for row in rows:
            clean_row = {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in row.items()}
            conn.execute(text(sql), clean_row)
            count += 1
    return count


def load_dim_sector(engine: Engine) -> int:
    """Validate that the seeded sector dimension exists."""
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM dim_sector")).scalar() or 0
    if count == 0:
        logger.warning("dim_sector is empty. Seed `warehouse/seeds/dim_sector.sql` first.")
    else:
        logger.info("dim_sector: %s rows", count)
    return int(count)


def load_dim_health_label(engine: Engine) -> int:
    """Validate that the seeded health-label dimension exists."""
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM dim_health_label")).scalar() or 0
    if count == 0:
        logger.warning("dim_health_label is empty. Seed `warehouse/seeds/dim_health_label.sql` first.")
    else:
        logger.info("dim_health_label: %s rows", count)
    return int(count)


def prepare_dim_year_rows(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    if "year_id" not in frame.columns:
        frame["year_id"] = range(1, len(frame) + 1)
    if "quarter" not in frame.columns:
        frame["quarter"] = None

    for column in ["year_id", "fiscal_year", "sort_order"]:
        if column in frame.columns:
            frame[column] = frame[column].apply(_as_int)

    frame["is_ttm"] = frame["is_ttm"].apply(_as_bool)
    frame["is_half_year"] = frame["is_half_year"].apply(_as_bool)
    frame = frame.drop_duplicates(subset=["year_label"], keep="first")
    frame = frame.where(pd.notnull(frame), None)
    return frame[["year_id", "year_label", "fiscal_year", "quarter", "is_ttm", "is_half_year", "sort_order"]]


def load_dim_year(engine: Engine) -> int:
    """Load the standardized year dimension."""
    df = _read_clean_csv("dim_year.csv")
    df = prepare_dim_year_rows(df)
    logger.info("Loaded %s dim_year rows from CSV", len(df))

    sql = """
        INSERT INTO dim_year (year_label, fiscal_year, quarter, is_ttm, is_half_year, sort_order)
        VALUES (:year_label, :fiscal_year, :quarter, :is_ttm, :is_half_year, :sort_order)
        ON CONFLICT (year_label) DO UPDATE SET
            fiscal_year = EXCLUDED.fiscal_year,
            quarter = EXCLUDED.quarter,
            is_ttm = EXCLUDED.is_ttm,
            is_half_year = EXCLUDED.is_half_year,
            sort_order = EXCLUDED.sort_order
    """

    return _upsert_rows(engine, sql, df.to_dict(orient="records"))


def prepare_dim_company_rows(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    if "company_id" in frame.columns and "company" not in frame.columns:
        frame = frame.rename(columns={"company_id": "company"})

    frame = frame.replace({"": None})
    frame = frame.dropna(subset=["company"]).drop_duplicates(subset=["company"], keep="first")
    frame = frame.rename(
        columns={
            "company": "symbol",
            "nse_profile": "nse_url",
            "bse_profile": "bse_url",
            "roce_percentage": "roce_pct",
            "roe_percentage": "roe_pct",
        }
    )
    return frame[[
        "symbol",
        "company_name",
        "sector",
        "sub_sector",
        "company_logo",
        "website",
        "nse_url",
        "bse_url",
        "chart_link",
        "about_company",
        "face_value",
        "book_value",
        "roce_pct",
        "roe_pct",
    ]]


def load_dim_company(engine: Engine) -> int:
    """Load the company dimension with sector classification."""
    df = _read_clean_csv("companies.csv", dtype=str, keep_default_na=False)
    df = prepare_dim_company_rows(df)
    logger.info("Loaded %s candidate company rows from CSV", len(df))

    for column in ["face_value", "book_value", "roce_pct", "roe_pct"]:
        df[column] = df[column].apply(_as_float)

    sql = """
        INSERT INTO dim_company (
            symbol, company_name, sector, sub_sector, company_logo, website,
            nse_url, bse_url, chart_link, about_company, face_value, book_value,
            roce_pct, roe_pct
        )
        VALUES (
            :symbol, :company_name, :sector, :sub_sector, :company_logo, :website,
            :nse_url, :bse_url, :chart_link, :about_company, :face_value, :book_value,
            :roce_pct, :roe_pct
        )
        ON CONFLICT (symbol) DO UPDATE SET
            company_name = EXCLUDED.company_name,
            sector = EXCLUDED.sector,
            sub_sector = EXCLUDED.sub_sector,
            company_logo = EXCLUDED.company_logo,
            website = EXCLUDED.website,
            nse_url = EXCLUDED.nse_url,
            bse_url = EXCLUDED.bse_url,
            chart_link = EXCLUDED.chart_link,
            about_company = EXCLUDED.about_company,
            face_value = EXCLUDED.face_value,
            book_value = EXCLUDED.book_value,
            roce_pct = EXCLUDED.roce_pct,
            roe_pct = EXCLUDED.roe_pct,
            updated_at = NOW()
    """

    return _upsert_rows(engine, sql, df.to_dict(orient="records"))
"""
Placeholder files for ETL load modules
"""
