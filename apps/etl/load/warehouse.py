"""Idempotent DDL deployment and atomic publication of validated clean datasets."""
from contextlib import contextmanager
import json
from pathlib import Path
import pandas as pd
from sqlalchemy import text
from apps.etl.load.db_connection import get_db_engine
from apps.etl.load.load_dimensions import load_dim_company, load_dim_year
from apps.etl.load.load_facts import (
    load_fact_profit_loss, load_fact_balance_sheet, load_fact_cash_flow,
    load_fact_analysis, load_fact_documents, load_fact_pros_cons,
)

ROOT = Path(__file__).resolve().parents[3]


class Transaction:
    """Adapt existing loader helpers to one shared transaction without early commits."""
    def __init__(self, connection):
        self.connection = connection

    @contextmanager
    def begin(self):
        yield self.connection

    connect = begin


def deploy(engine=None):
    engine = engine or get_db_engine()
    with engine.begin() as conn:
        for path in sorted((ROOT / "warehouse/ddl").glob("*.sql")):
            if path.name == "005_grants.sql":
                continue  # Owner already has access; roles are deployment-specific.
            with conn.connection.cursor() as cursor:
                cursor.execute(path.read_text(encoding="utf-8"))
        for path in sorted((ROOT / "warehouse/seeds").glob("*.sql")):
            with conn.connection.cursor() as cursor:
                cursor.execute(path.read_text(encoding="utf-8"))


def load(engine=None):
    engine = engine or get_db_engine()
    report = json.loads((ROOT / "reports/data_quality.json").read_text())
    if report["errors"]:
        raise ValueError("Data quality report contains blocking errors")
    companies = pd.read_csv(ROOT / "data/clean/companies.csv")
    metrics = pd.read_csv(ROOT / "data/clean/metrics.csv")
    with engine.begin() as conn:
        conn.execute(text("SELECT pg_advisory_xact_lock(731009)"))
        tx = Transaction(conn)
        for sector in sorted(companies.sector.dropna().unique()):
            import hashlib
            code = hashlib.sha256(sector.encode()).hexdigest()[:10]
            conn.execute(text("INSERT INTO dim_sector(sector_name,sector_code) VALUES (:name,:code) ON CONFLICT(sector_name) DO NOTHING"), {"name": sector, "code": code})
        load_dim_year(tx)
        load_dim_company(tx)
        for row in companies.to_dict("records"):
            conn.execute(text("UPDATE dim_company SET source=:source, identity_status=:identity_status, profile_available=:profile_available, is_active=NULL WHERE symbol=:company"), {k: row[k] for k in ["source", "identity_status", "profile_available", "company"]})
        conn.execute(text("INSERT INTO dim_industry(sector,industry_name) SELECT DISTINCT sector,sub_sector FROM dim_company WHERE sector IS NOT NULL AND sub_sector IS NOT NULL ON CONFLICT DO NOTHING"))
        conn.execute(text("INSERT INTO dim_date SELECT d::date,extract(year FROM d)::int,extract(month FROM d)::int FROM generate_series(make_date((SELECT min(fiscal_year) FROM dim_year),1,1), make_date((SELECT max(fiscal_year) FROM dim_year),12,31),interval '1 day') d ON CONFLICT DO NOTHING"))
        # These tables are a published snapshot of the authoritative source. Clearing
        # them inside the transaction prevents stale/rejected records surviving reruns.
        for table in ("fact_metrics", "fact_profit_loss", "fact_balance_sheet", "fact_cash_flow", "fact_analysis", "fact_documents"):
            conn.execute(text(f"DELETE FROM {table}"))
        for loader in (load_fact_profit_loss, load_fact_balance_sheet, load_fact_cash_flow, load_fact_analysis, load_fact_documents, load_fact_pros_cons):
            loader(tx)
        for row in json.loads(metrics.to_json(orient="records")):
            explanation = row.pop("explanation")
            conn.execute(text("INSERT INTO fact_metrics(symbol,year_id,metrics,overall_score,coverage_pct,explanation) SELECT :symbol,year_id,CAST(:metrics AS jsonb),:score,:coverage,CAST(:explanation AS jsonb) FROM dim_year WHERE year_label=:year"), {"symbol": row["company"], "year": row["year_label"], "metrics": json.dumps(row, allow_nan=False), "score": row["overall_score"], "coverage": row["coverage_pct"], "explanation": explanation})
        conn.execute(text("DELETE FROM fact_ml_scores WHERE model_version='historical-v1'"))
        conn.execute(text("""INSERT INTO fact_ml_scores(symbol,year_id,overall_score,coverage_pct,explanation,profitability_score,growth_score,leverage_score,cashflow_score,efficiency_score,consistency_score,health_label,model_version)
            SELECT DISTINCT ON(f.symbol) f.symbol,f.year_id,f.overall_score,f.coverage_pct,f.explanation,
            (metrics->>'profitability_score')::numeric,(metrics->>'growth_score')::numeric,
            (metrics->>'balance_sheet_score')::numeric,(metrics->>'cash_flow_score')::numeric,
            (metrics->>'efficiency_score')::numeric,(metrics->>'consistency_score')::numeric,
            metrics->>'health_label','historical-v1'
            FROM fact_metrics f JOIN dim_year y USING(year_id) ORDER BY f.symbol,y.sort_order DESC"""))
        conn.execute(text("INSERT INTO data_quality_report(report_id,report) VALUES(1,CAST(:report AS jsonb)) ON CONFLICT(report_id) DO UPDATE SET report=EXCLUDED.report,loaded_at=NOW()"), {"report": json.dumps(report)})
        conn.execute(text("SELECT refresh_all_materialized_views()"))
        count = conn.execute(text("SELECT count(*) FROM fact_metrics")).scalar_one()
        if count != len(metrics):
            raise ValueError("Warehouse metrics count differs from clean source")
        conn.exec_driver_sql((ROOT / "warehouse/checks/assertions.sql").read_text())
    return {"companies": len(companies), "metrics": count}
