"""One deterministic cleaning pipeline with auditable reconciliation."""
import json
import logging
from pathlib import Path
import pandas as pd

from apps.etl.pipelines.extract_n100 import ROOT, DATASETS
from apps.etl.transform.reconcile import (
    normalize_symbols, numeric_columns, canonical_sectors, reconcile_duplicates, reject,
)
from apps.etl.transform.standardize_years import create_year_dimension, extract_unique_years
from apps.etl.transform.clean_analysis import explode_analysis_metrics
from apps.etl.transform.derive_metrics import (
    compute_profit_loss_metrics, compute_balance_sheet_metrics,
    compute_cash_flow_metrics, compute_cross_table_metrics,
)

NUMERIC = {
    "profitandloss": "sales expenses operating_profit opm_percentage other_income interest depreciation profit_before_tax tax_percentage net_profit eps dividend_payout".split(),
    "balancesheet": "equity_capital reserves borrowings other_liabilities total_liabilities fixed_assets cwip investments other_asset total_assets".split(),
    "cashflow": "operating_activity investing_activity financing_activity net_cash_flow".split(),
    "companies": "face_value book_value roce_percentage roe_percentage".split(),
}


def clean(raw=None, output=None, reports=None):
    raw, output, reports = Path(raw or ROOT / "data/raw"), Path(output or ROOT / "data/clean"), Path(reports or ROOT / "reports")
    output.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    report = {"source": "n100", "symbol_corrections": [], "duplicates": [], "rejected_rows": [], "invalid_values": [], "warnings": [], "errors": [], "datasets": {}}
    frames = {}
    for name in DATASETS:
        frame = pd.read_csv(raw / (name + ".csv"))
        report["datasets"][name] = {"raw_rows": len(frame)}
        frame = normalize_symbols(frame, name, report)
        if name in NUMERIC:
            frame = numeric_columns(frame, NUMERIC[name], name, report)
        if "year" in frame:
            frame = create_year_dimension(frame, "year")
            invalid = frame.sort_order.isna() | (~frame.is_ttm & ~frame.fiscal_year.between(1900, 2100))
            reject(frame.loc[invalid], name, "invalid reporting period", report)
            frame = frame.loc[~invalid]
            frame = reconcile_duplicates(frame, ["company", "year_label"], name, report)
        frames[name] = frame

    sectors = canonical_sectors(ROOT / "data/reference/sector_mapping.csv", report)
    sectors.to_csv(output / "sector_mapping.csv", index=False)
    universe = sorted(set().union(*(set(f.company) for f in frames.values())))
    profiles = reconcile_duplicates(frames["companies"], ["company"], "companies", report)
    companies = pd.DataFrame({"company": universe}).merge(profiles, on="company", how="left", validate="one_to_one")
    companies = companies.merge(sectors, on="company", how="left", validate="one_to_one")
    companies["profile_available"] = companies.company_name.notna()
    companies["identity_status"] = "source_identifier"
    companies.loc[companies.company.eq("ABB"), "identity_status"] = "conflicting_profile"
    companies["source"] = "n100"
    companies["is_active"] = pd.NA  # No dated membership/active-status evidence.
    companies["company_name"] = companies.company_name.astype("string").str.strip()
    # Preserve the supplied profile in raw; do not publish Abbott metadata as ABB.
    ambiguous = companies.company.eq("ABB")
    for column in list(profiles.columns):
        if column not in {"company", "source_row", "source_file"}:
            companies.loc[ambiguous, column] = pd.NA
    companies.loc[ambiguous, ["sector", "sub_sector"]] = pd.NA
    report["warnings"].extend([
        "ABB identity is unresolved: source profile says Abbott India/ABBOTINDIA; identifier and sector say ABB. Profile withheld; scores excluded.",
        "Universe is the supplied historical dataset, not verified current Nifty 100 membership.",
        "Units follow the existing source contract (INR crore except per-share INR); workbooks do not independently specify units.",
        "Capex, cash balances, liquidity detail and inventory are absent: FCF, net debt, current/quick ratio and inventory metrics are unavailable.",
    ])
    frames["companies"] = companies
    frames["profitandloss"] = compute_profit_loss_metrics(frames["profitandloss"])
    frames["balancesheet"] = compute_balance_sheet_metrics(frames["balancesheet"])
    frames["cashflow"] = compute_cross_table_metrics(frames["profitandloss"], frames["balancesheet"], compute_cash_flow_metrics(frames["cashflow"]))
    analysis = explode_analysis_metrics(frames["analysis"])
    frames["analysis"] = reconcile_duplicates(analysis, ["company", "period_label"], "analysis", report)
    insights = []
    for row in frames["prosandcons"].itertuples():
        for column, is_pro in [("pros", True), ("cons", False)]:
            value = getattr(row, column)
            if pd.notna(value) and str(value).strip():
                insights.append({"company": row.company, "is_pro": is_pro, "text": str(value).strip(), "source": "MANUAL"})
    frames["prosandcons"] = reconcile_duplicates(pd.DataFrame(insights), ["company", "is_pro", "text"], "prosandcons", report)
    years = extract_unique_years(list(frames.values()))
    years.to_csv(output / "dim_year.csv", index=False)
    coverage = pd.DataFrame({"company": universe})
    for name, frame in frames.items():
        frame.to_csv(output / (name + ".csv"), index=False)
        available = frame
        if name == "documents":
            available = frame[frame.annual_report.notna() & frame.annual_report.astype(str).str.match(r"https?://")]
        symbols = set(available.company)
        report["datasets"][name].update({"clean_rows": len(frame), "companies": len(symbols), "missing_companies": sorted(set(universe) - symbols), "missing_values": {k: int(v) for k, v in frame.isna().sum().items()}, "years": sorted(frame.year_label.unique().tolist()) if "year_label" in frame else []})
        coverage[name] = coverage.company.isin(symbols)
    coverage["complete_statements"] = coverage[["profitandloss", "balancesheet", "cashflow"]].all(axis=1)
    coverage.to_csv(reports / "data_quality.csv", index=False)
    report["canonical_company_count"] = len(universe)
    report["financial_year_range"] = [int(years.fiscal_year.min()), int(years.fiscal_year.max())]
    report["missing_profiles"] = companies.loc[~companies.profile_available, "company"].tolist()
    # pandas' JSON encoder normalizes NaN/NA to JSON null, including rejected rows.
    encoded = pd.Series([report]).to_json(orient="values", force_ascii=True)
    (reports / "data_quality.json").write_text(json.dumps(json.loads(encoded)[0], indent=2), encoding="utf-8")
    logging.info("Canonical universe: %s; report: %s", len(universe), reports)
    return frames, report


def main():
    logging.basicConfig(level=logging.INFO)
    clean()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
