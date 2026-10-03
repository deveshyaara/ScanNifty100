"""
Fact table loading utilities.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

CLEAN_DIR = Path("data/clean")
ALLOWED_ANALYSIS_PERIODS = {"10Y", "5Y", "3Y", "1Y", "TTM"}


def _read_clean_csv(filename: str, **kwargs) -> pd.DataFrame:
    filepath = CLEAN_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Clean file not found: {filepath}")
    return pd.read_csv(filepath, **kwargs)


def _as_float(value):
    if pd.isna(value) or value == "":
        return None
    return float(value)


def _as_int(value):
    if pd.isna(value) or value == "":
        return None
    return int(float(value))


def _upsert_rows(engine: Engine, sql: str, rows: list[dict]) -> int:
    import math
    count = 0
    with engine.begin() as conn:
        for row in rows:
            clean_row = {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in row.items()}
            conn.execute(text(sql), clean_row)
            count += 1
    return count


def get_year_id_mapping(engine: Engine) -> dict[str, int]:
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT year_id, year_label FROM dim_year")).fetchall()
    return {row[1]: int(row[0]) for row in rows}


def get_valid_symbols(engine: Engine) -> set[str]:
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT symbol FROM dim_company")).fetchall()
    return {row[0] for row in rows}


def prepare_fact_profit_loss_rows(df: pd.DataFrame, year_mapping: dict[str, int]) -> pd.DataFrame:
    frame = df.copy()
    if "company_id" in frame.columns and "company" not in frame.columns:
        frame = frame.rename(columns={"company_id": "company"})

    frame = frame.dropna(subset=["company", "year_label"]).drop_duplicates(subset=["company", "year_label"], keep="first")
    frame["year_id"] = frame["year_label"].map(year_mapping)
    frame = frame[frame["year_id"].notna()]

    column_map = {
        "sales": "sales",
        "expenses": "expenses",
        "operating_profit": "operating_profit",
        "opm_percentage": "opm_pct",
        "other_income": "other_income",
        "interest": "interest",
        "depreciation": "depreciation",
        "profit_before_tax": "profit_before_tax",
        "tax_percentage": "tax_pct",
        "net_profit": "net_profit",
        "eps": "eps",
        "dividend_payout": "dividend_payout_pct",
    }

    output = pd.DataFrame({"symbol": frame["company"], "year_id": frame["year_id"]})
    output["year_id"] = output["year_id"].apply(_as_int)
    for source_column, target_column in column_map.items():
        output[target_column] = frame[source_column].apply(_as_float) if source_column in frame.columns else None
    return output


def load_fact_profit_loss(engine: Engine) -> int:
    df = _read_clean_csv("profitandloss.csv")
    prepared = prepare_fact_profit_loss_rows(df, get_year_id_mapping(engine))
    logger.info("Loaded %s fact_profit_loss rows after normalization", len(prepared))

    sql = """
        INSERT INTO fact_profit_loss (
            symbol, year_id, sales, expenses, operating_profit, opm_pct,
            other_income, interest, depreciation, profit_before_tax,
            tax_pct, net_profit, eps, dividend_payout_pct
        )
        VALUES (
            :symbol, :year_id, :sales, :expenses, :operating_profit, :opm_pct,
            :other_income, :interest, :depreciation, :profit_before_tax,
            :tax_pct, :net_profit, :eps, :dividend_payout_pct
        )
        ON CONFLICT (symbol, year_id) DO UPDATE SET
            sales = EXCLUDED.sales,
            expenses = EXCLUDED.expenses,
            operating_profit = EXCLUDED.operating_profit,
            opm_pct = EXCLUDED.opm_pct,
            other_income = EXCLUDED.other_income,
            interest = EXCLUDED.interest,
            depreciation = EXCLUDED.depreciation,
            profit_before_tax = EXCLUDED.profit_before_tax,
            tax_pct = EXCLUDED.tax_pct,
            net_profit = EXCLUDED.net_profit,
            eps = EXCLUDED.eps,
            dividend_payout_pct = EXCLUDED.dividend_payout_pct,
            loaded_at = NOW()
    """
    valid_symbols = get_valid_symbols(engine)
    prepared = prepared[prepared["symbol"].isin(valid_symbols)]
    return _upsert_rows(engine, sql, prepared.to_dict(orient="records"))


def prepare_fact_balance_sheet_rows(df: pd.DataFrame, year_mapping: dict[str, int]) -> pd.DataFrame:
    frame = df.copy()
    if "company_id" in frame.columns and "company" not in frame.columns:
        frame = frame.rename(columns={"company_id": "company"})

    frame = frame.dropna(subset=["company", "year_label"]).drop_duplicates(subset=["company", "year_label"], keep="first")
    frame["year_id"] = frame["year_label"].map(year_mapping)
    frame = frame[frame["year_id"].notna()]

    column_map = {
        "equity_capital": "equity_capital",
        "reserves": "reserves",
        "borrowings": "borrowings",
        "other_liabilities": "other_liabilities",
        "total_liabilities": "total_liabilities",
        "fixed_assets": "fixed_assets",
        "cwip": "cwip",
        "investments": "investments",
        "other_asset": "other_assets",
        "total_assets": "total_assets",
    }

    output = pd.DataFrame({"symbol": frame["company"], "year_id": frame["year_id"]})
    output["year_id"] = output["year_id"].apply(_as_int)
    for source_column, target_column in column_map.items():
        output[target_column] = frame[source_column].apply(_as_float) if source_column in frame.columns else None
    return output


def load_fact_balance_sheet(engine: Engine) -> int:
    df = _read_clean_csv("balancesheet.csv")
    prepared = prepare_fact_balance_sheet_rows(df, get_year_id_mapping(engine))
    logger.info("Loaded %s fact_balance_sheet rows after normalization", len(prepared))

    sql = """
        INSERT INTO fact_balance_sheet (
            symbol, year_id, equity_capital, reserves, borrowings,
            other_liabilities, total_liabilities, fixed_assets, cwip,
            investments, other_assets, total_assets
        )
        VALUES (
            :symbol, :year_id, :equity_capital, :reserves, :borrowings,
            :other_liabilities, :total_liabilities, :fixed_assets, :cwip,
            :investments, :other_assets, :total_assets
        )
        ON CONFLICT (symbol, year_id) DO UPDATE SET
            equity_capital = EXCLUDED.equity_capital,
            reserves = EXCLUDED.reserves,
            borrowings = EXCLUDED.borrowings,
            other_liabilities = EXCLUDED.other_liabilities,
            total_liabilities = EXCLUDED.total_liabilities,
            fixed_assets = EXCLUDED.fixed_assets,
            cwip = EXCLUDED.cwip,
            investments = EXCLUDED.investments,
            other_assets = EXCLUDED.other_assets,
            total_assets = EXCLUDED.total_assets,
            loaded_at = NOW()
    """
    valid_symbols = get_valid_symbols(engine)
    prepared = prepared[prepared["symbol"].isin(valid_symbols)]
    return _upsert_rows(engine, sql, prepared.to_dict(orient="records"))


def prepare_fact_cash_flow_rows(df: pd.DataFrame, year_mapping: dict[str, int]) -> pd.DataFrame:
    frame = df.copy()
    if "company_id" in frame.columns and "company" not in frame.columns:
        frame = frame.rename(columns={"company_id": "company"})

    frame = frame.dropna(subset=["company", "year_label"]).drop_duplicates(subset=["company", "year_label"], keep="first")
    frame["year_id"] = frame["year_label"].map(year_mapping)
    frame = frame[frame["year_id"].notna()]

    output = pd.DataFrame({"symbol": frame["company"], "year_id": frame["year_id"]})
    for source_column, target_column in [
        ("operating_activity", "operating_activity"),
        ("investing_activity", "investing_activity"),
        ("financing_activity", "financing_activity"),
        ("net_cash_flow", "net_cash_flow"),
        ("cash_conversion_ratio", "cash_conversion_ratio"),
    ]:
        output[target_column] = frame[source_column].apply(_as_float) if source_column in frame.columns else None
    return output


def load_fact_cash_flow(engine: Engine) -> int:
    df = _read_clean_csv("cashflow.csv")
    prepared = prepare_fact_cash_flow_rows(df, get_year_id_mapping(engine))
    logger.info("Loaded %s fact_cash_flow rows after normalization", len(prepared))

    sql = """
        INSERT INTO fact_cash_flow (
            symbol, year_id, operating_activity, investing_activity,
            financing_activity, net_cash_flow, cash_conversion_ratio
        )
        VALUES (
            :symbol, :year_id, :operating_activity, :investing_activity,
            :financing_activity, :net_cash_flow, :cash_conversion_ratio
        )
        ON CONFLICT (symbol, year_id) DO UPDATE SET
            operating_activity = EXCLUDED.operating_activity,
            investing_activity = EXCLUDED.investing_activity,
            financing_activity = EXCLUDED.financing_activity,
            net_cash_flow = EXCLUDED.net_cash_flow,
            cash_conversion_ratio = EXCLUDED.cash_conversion_ratio,
            loaded_at = NOW()
    """
    valid_symbols = get_valid_symbols(engine)
    prepared = prepared[prepared["symbol"].isin(valid_symbols)]
    return _upsert_rows(engine, sql, prepared.to_dict(orient="records"))


def prepare_fact_analysis_rows(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    if "company_id" in frame.columns and "company" not in frame.columns:
        frame = frame.rename(columns={"company_id": "company"})
    if "return_on_equity_pct" not in frame.columns and "roe" in frame.columns:
        frame = frame.rename(columns={"roe": "return_on_equity_pct"})

    frame = frame.dropna(subset=["company", "period_label"]).drop_duplicates(subset=["company", "period_label"], keep="first")
    frame = frame[frame["period_label"].isin(ALLOWED_ANALYSIS_PERIODS)]

    output = pd.DataFrame({"symbol": frame["company"], "period_label": frame["period_label"]})
    for source_column, target_column in [
        ("compounded_sales_growth_pct", "compounded_sales_growth_pct"),
        ("compounded_profit_growth_pct", "compounded_profit_growth_pct"),
        ("stock_price_cagr_pct", "stock_price_cagr_pct"),
        ("return_on_equity_pct", "roe_pct"),
    ]:
        output[target_column] = frame[source_column].apply(_as_float) if source_column in frame.columns else None
    return output


def load_fact_analysis(engine: Engine) -> int:
    df = _read_clean_csv("analysis.csv")
    prepared = prepare_fact_analysis_rows(df)
    skipped = len(df) - len(prepared)
    if skipped:
        logger.warning("Skipped %s analysis rows with unsupported periods", skipped)
    logger.info("Loaded %s fact_analysis rows after normalization", len(prepared))

    sql = """
        INSERT INTO fact_analysis (
            symbol, period_label, compounded_sales_growth_pct,
            compounded_profit_growth_pct, stock_price_cagr_pct, roe_pct
        )
        VALUES (
            :symbol, :period_label, :compounded_sales_growth_pct,
            :compounded_profit_growth_pct, :stock_price_cagr_pct, :roe_pct
        )
        ON CONFLICT (symbol, period_label) DO UPDATE SET
            compounded_sales_growth_pct = EXCLUDED.compounded_sales_growth_pct,
            compounded_profit_growth_pct = EXCLUDED.compounded_profit_growth_pct,
            stock_price_cagr_pct = EXCLUDED.stock_price_cagr_pct,
            roe_pct = EXCLUDED.roe_pct,
            loaded_at = NOW()
    """
    valid_symbols = get_valid_symbols(engine)
    prepared = prepared[prepared["symbol"].isin(valid_symbols)]
    return _upsert_rows(engine, sql, prepared.to_dict(orient="records"))


def prepare_fact_pros_cons_rows(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    if "company_id" in frame.columns and "company" not in frame.columns:
        frame = frame.rename(columns={"company_id": "company"})

    frame["company"] = frame["company"].where(frame["company"].notna(), "")
    frame["company"] = frame["company"].astype(str).str.strip()
    frame = frame[(frame["company"] != "") & (frame["company"].str.lower() != "none")]
    frame = frame[frame["text"].notna() & (frame["text"].astype(str).str.strip() != "")]
    frame = frame.drop_duplicates(subset=["company", "is_pro", "text"], keep="first")
    frame["is_pro"] = frame["is_pro"].apply(lambda value: str(value).strip().lower() in {"1", "true", "t", "yes", "y"})
    frame["source"] = frame["source"].fillna("MANUAL") if "source" in frame.columns else "MANUAL"
    frame["category"] = frame["category"] if "category" in frame.columns else None
    return frame.rename(columns={"company": "symbol"})[["symbol", "is_pro", "category", "text", "source"]]


def load_fact_pros_cons(engine: Engine) -> int:
    df = _read_clean_csv("prosandcons.csv", dtype=str, keep_default_na=False)
    prepared = prepare_fact_pros_cons_rows(df)
    logger.info("Loaded %s fact_pros_cons rows after normalization", len(prepared))

    valid_symbols = get_valid_symbols(engine)
    prepared = prepared[prepared["symbol"].isin(valid_symbols)]
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM fact_pros_cons WHERE source = 'MANUAL'"))
        for row in prepared.to_dict(orient="records"):
            conn.execute(
                text("INSERT INTO fact_pros_cons (symbol, is_pro, category, text, source) VALUES (:symbol, :is_pro, :category, :text, :source)"),
                row,
            )
    return len(prepared)


def prepare_fact_documents_rows(df: pd.DataFrame, year_mapping: dict[str, int]) -> pd.DataFrame:
    frame = df.copy()
    frame = frame[frame["annual_report"].astype(str).str.match(r"https?://")]
    if "company_id" in frame.columns and "company" not in frame.columns:
        frame = frame.rename(columns={"company_id": "company"})

    frame = frame.dropna(subset=["company", "year_label", "annual_report"]).drop_duplicates(
        subset=["company", "year_label", "annual_report"], keep="first"
    )
    frame["year_id"] = frame["year_label"].map(year_mapping)
    frame = frame[frame["year_id"].notna()]
    output = pd.DataFrame({"symbol": frame["company"], "year_id": frame["year_id"], "document_url": frame["annual_report"]})
    output["year_id"] = output["year_id"].apply(_as_int)
    return output


def load_fact_documents(engine: Engine) -> int:
    df = _read_clean_csv("documents.csv", dtype=str, keep_default_na=False)
    prepared = prepare_fact_documents_rows(df, get_year_id_mapping(engine))
    logger.info("Loaded %s fact_documents rows after normalization", len(prepared))

    sql = """
        INSERT INTO fact_documents (symbol, year_id, document_type, document_url)
        VALUES (:symbol, :year_id, 'Annual Report', :document_url)
        ON CONFLICT (symbol, year_id, document_type) DO UPDATE SET
            document_url = EXCLUDED.document_url,
            loaded_at = NOW()
    """
    valid_symbols = get_valid_symbols(engine)
    prepared = prepared[prepared["symbol"].isin(valid_symbols)]
    return _upsert_rows(engine, sql, prepared.to_dict(orient="records"))
import json

def load_fact_metrics(engine: Engine) -> int:
    import pandas as pd
    from sqlalchemy import text
    metrics_path = CLEAN_DIR / "metrics.csv"
    if not metrics_path.exists():
        logger.warning(f"Metrics file not found: {metrics_path}. Did analytics run?")
        return 0
    df = pd.read_csv(metrics_path)
    logger.info("Loaded %s fact_metrics rows after normalization", len(df))
    valid_symbols = get_valid_symbols(engine)
    df = df[df["company"].isin(valid_symbols)]
    
    count = 0
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM fact_metrics"))
        for row in json.loads(df.to_json(orient="records")):
            explanation = row.pop("explanation") if "explanation" in row else None
            # Extract score and coverage safely
            score = row.get("overall_score")
            coverage = row.get("coverage_pct")
            
            sql = """
                INSERT INTO fact_metrics(symbol, year_id, metrics, overall_score, coverage_pct, explanation)
                SELECT :symbol, year_id, CAST(:metrics AS jsonb), :score, :coverage, CAST(:explanation AS jsonb)
                FROM dim_year WHERE year_label=:year
            """
            conn.execute(text(sql), {
                "symbol": row["company"],
                "year": row["year_label"],
                "metrics": json.dumps(row, allow_nan=False),
                "score": score,
                "coverage": coverage,
                "explanation": explanation
            })
            count += 1
    return count


def load_fact_ml_scores(engine: Engine) -> int:
    from sqlalchemy import text
    logger.info("Generating and loading fact_ml_scores from fact_metrics...")
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM fact_ml_scores WHERE model_version='historical-v1'"))
        
        # We need the most recent score per company to be loaded into fact_ml_scores.
        # This correctly calculates it by doing a DISTINCT ON over year sort order.
        sql = """
            INSERT INTO fact_ml_scores(
                symbol, year_id, overall_score, coverage_pct, explanation,
                profitability_score, growth_score, leverage_score,
                cashflow_score, efficiency_score, consistency_score,
                health_label, model_version
            )
            SELECT DISTINCT ON(f.symbol) 
                f.symbol, f.year_id, f.overall_score, f.coverage_pct, f.explanation,
                (metrics->>'profitability_score')::numeric,
                (metrics->>'growth_score')::numeric,
                (metrics->>'balance_sheet_score')::numeric,
                (metrics->>'cash_flow_score')::numeric,
                (metrics->>'efficiency_score')::numeric,
                (metrics->>'consistency_score')::numeric,
                metrics->>'health_label',
                'historical-v1'
            FROM fact_metrics f 
            JOIN dim_year y USING(year_id) 
            ORDER BY f.symbol, y.sort_order DESC
        """
        res = conn.execute(text(sql))
        count = res.rowcount
    logger.info("Loaded %s fact_ml_scores rows", count)
    return count

