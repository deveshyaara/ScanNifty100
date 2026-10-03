"""Build comparable annual metrics and explainable company-year scores."""
import json
from pathlib import Path
import pandas as pd
from apps.analytics.features.common import number, ratio
from apps.analytics.features.growth import calculate_revenue_growth, calculate_cagr
from apps.analytics.features.returns import return_on_average
from apps.analytics.scoring.health_score import explain_score
from apps.analytics.scoring.peer_ranking import rank_companies

ROOT = Path(__file__).resolve().parents[2]


def percent(value):
    return value * 100 if value is not None else None


def build_metrics(frames):
    pl, bs, cf = [frames[n].set_index(["company", "year_label"]) for n in ("profitandloss", "balancesheet", "cashflow")]
    companies = frames["companies"].set_index("company")
    rows = []
    for (symbol, label), p in pl.iterrows():
        if bool(p.is_ttm) or bool(p.is_half_year):
            continue
        year = int(p.fiscal_year)
        prev_label = f"{label[:3]} {year - 1}"
        b = bs.loc[(symbol, label)].to_dict() if (symbol, label) in bs.index else {}
        c = cf.loc[(symbol, label)].to_dict() if (symbol, label) in cf.index else {}
        prev = pl.loc[(symbol, prev_label)].to_dict() if (symbol, prev_label) in pl.index else {}
        prev_b = bs.loc[(symbol, prev_label)].to_dict() if (symbol, prev_label) in bs.index else {}
        def growth(col):
            return percent(calculate_revenue_growth(p.get(col), prev.get(col)))
        def cagr(col, years):
            earlier = (symbol, f"{label[:3]} {year - years}")
            return percent(calculate_cagr(pl.loc[earlier, col], p.get(col), years)) if earlier in pl.index else None
        equity = b.get("shareholders_equity")
        ebit = number(p.get("operating_profit"))
        depreciation = number(p.get("depreciation"))
        ebit = ebit - depreciation if ebit is not None and depreciation is not None else None
        row = {"company": symbol, "year_label": label, "fiscal_year": year, "sector": companies.loc[symbol, "sector"], "sales": p.sales, "net_profit": p.net_profit, "eps": p.eps, "operating_profit": p.operating_profit, "ebit": ebit,
            "revenue_growth_pct": growth("sales"), "profit_growth_pct": growth("net_profit"), "eps_growth_pct": growth("eps"),
            "revenue_cagr_3y_pct": cagr("sales", 3), "revenue_cagr_5y_pct": cagr("sales", 5), "profit_cagr_3y_pct": cagr("net_profit", 3), "profit_cagr_5y_pct": cagr("net_profit", 5),
            "net_profit_margin_pct": percent(ratio(p.net_profit, p.sales)), "operating_margin_pct": percent(ratio(p.operating_profit, p.sales)), "ebit_margin_pct": percent(ratio(ebit, p.sales)),
            "roe_pct": percent(return_on_average(p.net_profit, prev_b.get("shareholders_equity"), equity)),
            "roa_pct": percent(return_on_average(p.net_profit, prev_b.get("total_assets"), b.get("total_assets"))),
            "debt_to_equity": ratio(b.get("borrowings"), equity), "equity_ratio": ratio(equity, b.get("total_assets")),
            "asset_turnover": return_on_average(p.sales, prev_b.get("total_assets"), b.get("total_assets")),
            "cash_conversion_ratio": ratio(c.get("operating_activity"), p.net_profit), "cfo_margin_pct": percent(ratio(c.get("operating_activity"), p.sales)),
            "operating_activity": c.get("operating_activity"), "investing_activity": c.get("investing_activity"), "financing_activity": c.get("financing_activity"),
            "total_assets": b.get("total_assets"), "total_liabilities": b.get("total_liabilities"), "shareholders_equity": equity, "borrowings": b.get("borrowings"),
            "equity_growth_pct": percent(calculate_revenue_growth(equity, prev_b.get("shareholders_equity"))), "asset_growth_pct": percent(calculate_revenue_growth(b.get("total_assets"), prev_b.get("total_assets"))),
            "statement_coverage_pct": (1 + bool(b) + bool(c)) / 3 * 100}
        for metric in ("ebitda", "ebitda_margin_pct", "roce_pct", "free_cash_flow", "capex", "cash", "net_debt", "current_ratio", "quick_ratio", "inventory_turnover"):
            row[metric] = None
        for table, col, metric in [(pl, "net_profit", "profit_positive_fraction"), (cf, "operating_activity", "cfo_positive_fraction")]:
            values = [number(table.loc[(symbol, f"{label[:3]} {y}"), col]) if (symbol, f"{label[:3]} {y}") in table.index else None for y in range(year - 2, year + 1)]
            row[metric] = sum(v > 0 for v in values) / 3 if all(v is not None for v in values) else None
        row["identity_status"] = companies.loc[symbol, "identity_status"]
        score = explain_score(row, sector=row["sector"], identity_status=row["identity_status"])
        row.update({k: score[k] for k in ("overall_score", "coverage_pct", "status", "health_label", "model_version")})
        row.update({k + "_score": v for k, v in score["components"].items()})
        row["explanation"] = json.dumps(score, allow_nan=False)
        rows.append(row)
    frame = pd.DataFrame(rows)
    return pd.concat([rank_companies(g) for _, g in frame.groupby("year_label")], ignore_index=True)


def run(clean_dir=None):
    clean_dir = Path(clean_dir or ROOT / "data/clean")
    frames = {n: pd.read_csv(clean_dir / (n + ".csv")) for n in ("companies", "profitandloss", "balancesheet", "cashflow")}
    metrics = build_metrics(frames)
    metrics.to_csv(clean_dir / "metrics.csv", index=False)
    latest = metrics.sort_values(["fiscal_year", "year_label"]).groupby("company", sort=True).tail(1)
    latest = rank_companies(latest)
    latest.to_csv(clean_dir / "rankings.csv", index=False)
    return metrics


if __name__ == "__main__":
    print(f"Generated {len(run())} annual metric rows")
