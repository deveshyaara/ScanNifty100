"""Generate the connected PBIP/TMDL/PBIR project from the deployed warehouse schema."""
import json
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import inspect
from apps.etl.load.db_connection import get_db_engine
from powerbi_schemas import SCHEMAS

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "powerbi/project"
MODEL = PROJECT / "ScanNifty100.SemanticModel"
REPORT = PROJECT / "ScanNifty100.Report"
TABLES = ["dim_company", "dim_sector", "dim_year", "fact_profit_loss", "fact_balance_sheet", "fact_cash_flow", "fact_documents", "fact_analysis", "fact_pros_cons", "vw_metrics", "vw_company_coverage", "vw_score_contributions"]
MEASURES = {}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def latest(expression):
    return 'VAR Period = MAXX(FILTER(dim_year, NOT(dim_year[is_ttm]) && NOT(dim_year[is_half_year])), dim_year[sort_order]) RETURN CALCULATE(' + expression + ', KEEPFILTERS(dim_year[sort_order] = Period))'


def measures():
    sums = {"Revenue (INR Cr)": "sales", "PAT (INR Cr)": "net_profit", "Operating Profit (INR Cr)": "operating_profit", "EBIT (INR Cr)": "ebit", "EBITDA (unavailable)": "ebitda", "Assets (INR Cr)": "total_assets", "Liabilities (INR Cr)": "total_liabilities", "Equity (INR Cr)": "shareholders_equity", "Debt (INR Cr)": "borrowings", "CFO (INR Cr)": "operating_activity", "Investing Cash (INR Cr)": "investing_activity", "Financing Cash (INR Cr)": "financing_activity", "FCF (unavailable)": "free_cash_flow", "Capex (unavailable)": "capex", "Cash (unavailable)": "cash", "Net Debt (unavailable)": "net_debt"}
    averages = {"Health Score": "overall_score", "Coverage %": "coverage_pct", "Revenue Growth %": "revenue_growth_pct", "Profit Growth %": "profit_growth_pct", "EPS Growth %": "eps_growth_pct", "Revenue CAGR 3Y %": "revenue_cagr_3y_pct", "Revenue CAGR 5Y %": "revenue_cagr_5y_pct", "ROE %": "roe_pct", "ROA %": "roa_pct", "ROCE % (unavailable)": "roce_pct", "Debt to Equity": "debt_to_equity", "CFO to PAT": "cash_conversion_ratio", "Current Ratio (unavailable)": "current_ratio", "Asset Turnover": "asset_turnover", "Profitability Score": "profitability_score", "Growth Score": "growth_score", "Balance Sheet Score": "balance_sheet_score", "Cash Flow Score": "cash_flow_score", "Efficiency Score": "efficiency_score", "Consistency Score": "consistency_score", "Cash Consistency": "cfo_positive_fraction", "Growth Consistency": "profit_positive_fraction", "Equity Growth %": "equity_growth_pct", "Asset Growth %": "asset_growth_pct"}
    for name, col in sums.items():
        MEASURES[name] = (latest(f"SUM(vw_metrics[{col}])"), "#,0.0")
    for name, col in averages.items():
        MEASURES[name] = (latest(f"AVERAGE(vw_metrics[{col}])"), '0.0"%"' if "%" in name else "0.00")
    MEASURES.update({
        "Company Count": ("COUNTROWS(dim_company)", "0"),
        "Sector Count": ("DISTINCTCOUNT(dim_company[sector])", "0"),
        "Scored Companies": (latest("COUNT(vw_metrics[overall_score])"), "0"),
        "Complete Statements": (latest("CALCULATE(COUNTROWS(vw_metrics),vw_metrics[statement_coverage_pct]=100)"), "0"),
        "Median Health Score": (latest("MEDIAN(vw_metrics[overall_score])"), "0.00"),
        "Net Margin %": ("DIVIDE([PAT (INR Cr)], [Revenue (INR Cr)]) * 100", '0.0"%"'),
        "Operating Margin %": ("DIVIDE([Operating Profit (INR Cr)], [Revenue (INR Cr)]) * 100", '0.0"%"'),
        "EBIT Margin %": ("DIVIDE([EBIT (INR Cr)], [Revenue (INR Cr)]) * 100", '0.0"%"'),
        "EPS (INR)": ("IF(HASONEVALUE(dim_company[symbol]), " + latest("MAX(vw_metrics[eps])") + ")", "0.00"),
        "Health Rank": ('IF(NOT ISBLANK([Health Score]), RANKX(FILTER(ALLSELECTED(dim_company),NOT ISBLANK([Health Score])),[Health Score],,DESC,Skip))', "0"),
        "Universe Median": ("CALCULATE([Median Health Score],REMOVEFILTERS(dim_company),REMOVEFILTERS(dim_sector))", "0.00"),
        "Sector Median": ("VAR Sector = SELECTEDVALUE(dim_company[sector]) RETURN CALCULATE([Median Health Score],REMOVEFILTERS(dim_company),dim_company[sector]=Sector)", "0.00"),
        "Percentile": ("VAR N=COUNTROWS(FILTER(ALLSELECTED(dim_company),NOT ISBLANK([Health Score]))) RETURN IF(NOT ISBLANK([Health Score]),IF(N=1,100,DIVIDE(N-[Health Rank],N-1)*100))", '0.0"%"'),
        "Screening Note": ('"Historical quantitative screening; not investment advice. Blank values indicate unavailable inputs."', ""),
    })


def model():
    inspector = inspect(get_db_engine())
    columns = {table: inspector.get_columns(table) for table in TABLES}
    definition = MODEL / "definition"
    (definition / "tables").mkdir(parents=True, exist_ok=True)
    write_json(MODEL / "definition.pbism", {"$schema": SCHEMAS["semantic_properties"], "version": "4.0", "settings": {}})
    (definition / "database.tmdl").write_text("database\n\tcompatibilityLevel: 1601\n", encoding="utf-8")
    (definition / "model.tmdl").write_text("model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tsourceQueryCulture: en-US\n\tdataAccessOptions\n\t\tlegacyRedirects\n\t\treturnErrorValuesAsNull\n\n" + "\n".join(f"ref table {table}" for table in TABLES) + "\n", encoding="utf-8")
    server = os.environ.get("POWERBI_SERVER", os.environ.get("DB_HOST", "localhost") + ":" + os.environ.get("DB_PORT", "5433"))
    database = os.environ.get("DB_NAME", "scannifty100")
    expressions = f'expression WarehouseServer = "{server}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n\nexpression WarehouseDatabase = "{database}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
    (definition / "expressions.tmdl").write_text(expressions, encoding="utf-8")
    relationships = []
    for table, fields in columns.items():
        lines = [f"table {table}"]
        for field in fields:
            name = field["name"]
            dbtype = str(field["type"]).lower()
            datatype = "int64" if "int" in dbtype else "double" if "numeric" in dbtype or "float" in dbtype else "boolean" if "bool" in dbtype else "dateTime" if "timestamp" in dbtype or dbtype == "date" else "string"
            lines += [f"\tcolumn {name}", f"\t\tdataType: {datatype}", f"\t\tsourceColumn: {name}", "\t\tsummarizeBy: none"]
            if name in ("id", "year_id", "source", "source_file", "model_version"):
                lines.append("\t\tisHidden")
            if name == "year_label":
                lines.append("\t\tsortByColumn: sort_order")
            lines.append("")
        if table == "vw_metrics":
            for name, (expression, fmt) in MEASURES.items():
                lines += [f"\tmeasure '{name}' = {expression}", f"\t\tformatString: {fmt}" if fmt else "\t\tdisplayFolder: Screening", ""]
        lines += [f"\tpartition {table} = m", "\t\tmode: import", "\t\tsource =", "\t\t\tlet", "\t\t\t    Source = PostgreSQL.Database(WarehouseServer, WarehouseDatabase, [CreateNavigationProperties=false]),", f'\t\t\t    Data = Source{{[Schema="public", Item="{table}"]}}[Data]', "\t\t\tin", "\t\t\t    Data", ""]
        (definition / "tables" / (table + ".tmdl")).write_text("\n".join(lines), encoding="utf-8")
        names = {f["name"] for f in fields}
        for col, target, targetcol in [("symbol", "dim_company", "symbol"), ("year_id", "dim_year", "year_id"), ("sector", "dim_sector", "sector_name")]:
            if col in names and table != target and (col != "sector" or table == "dim_company"):
                relationships += [f"relationship {uuid.uuid5(uuid.NAMESPACE_URL, table + col)}", f"\tfromColumn: {table}.{col}", f"\ttoColumn: {target}.{targetcol}", "\tcrossFilteringBehavior: oneDirection", ""]
    (definition / "relationships.tmdl").write_text("\n".join(relationships), encoding="utf-8")
    write_json(ROOT / "powerbi/model_manifest.json", {"tables": {t: [f["name"] for f in fs] for t, fs in columns.items()}, "measures": list(MEASURES), "server": server, "database": database})
    (ROOT / "powerbi/dax/core_measures.dax").write_text("\n\n".join(f"{name} = {expr}" for name, (expr, _) in MEASURES.items()), encoding="utf-8")


def field(name, table=None):
    kind = "Column" if table else "Measure"
    table = table or "vw_metrics"
    return {kind: {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}


def literal(value):
    return {"expr": {"Literal": {"Value": "'" + value.replace("'", "''") + "'"}}}


def visual(page, index, title, visual_type, roles, position):
    name = uuid.uuid5(uuid.NAMESPACE_URL, page + str(index)).hex[:20]
    query = {role: {"projections": [{"field": field(n, t), "queryRef": f"{t or 'vw_metrics'}.{n}"} for n, t in fields]} for role, fields in roles.items()}
    value = {"$schema": SCHEMAS["visual"], "name": name, "position": {"x": position[0], "y": position[1], "width": position[2], "height": position[3], "z": index, "tabOrder": index}, "visual": {"visualType": visual_type, "query": {"queryState": query}, "visualContainerObjects": {"title": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "text": literal(title), "fontSize": {"expr": {"Literal": {"Value": "11D"}}}, "fontFamily": literal("Segoe UI")}}]}, "drillFilterOtherVisuals": True}}
    if visual_type == "slicer":
        value["visual"]["objects"] = {"data": [{"properties": {"mode": literal("Dropdown")}}]}
        if title in ("Company", "Sector", "Year"):
            value["visual"]["syncGroup"] = {"groupName": title, "fieldChanges": True, "filterChanges": True}
    write_json(REPORT / "definition/pages" / page / "visuals" / name / "visual.json", value)


def report():
    write_json(PROJECT / "ScanNifty100.pbip", {"$schema": SCHEMAS["project"], "version": "1.0", "artifacts": [{"report": {"path": "ScanNifty100.Report"}}], "settings": {"enableAutoRecovery": True}})
    write_json(REPORT / "definition.pbir", {"$schema": SCHEMAS["report_properties"], "version": "4.0", "datasetReference": {"byPath": {"path": "../ScanNifty100.SemanticModel"}}})
    write_json(REPORT / "definition/version.json", {"$schema": SCHEMAS["version"], "version": "2.0.0"})
    theme = {"name": "ScanNifty100", "dataColors": ["#137C72", "#3477A5", "#AE5260", "#7C8341", "#6F7175"], "background": "#FFFFFF", "foreground": "#202529", "tableAccent": "#137C72", "textClasses": {"title": {"fontFace": "Segoe UI", "fontSize": 12}, "label": {"fontFace": "Segoe UI", "fontSize": 10}, "callout": {"fontFace": "Segoe UI", "fontSize": 24}}}
    write_json(REPORT / "StaticResources/RegisteredResources/ScanNifty100.json", theme)
    write_json(REPORT / "definition/report.json", {"$schema": SCHEMAS["report"], "themeCollection": {"customTheme": {"name": "ScanNifty100", "reportVersionAtImport": "2.0.0", "type": "RegisteredResources"}}, "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources", "items": [{"name": "ScanNifty100", "path": "ScanNifty100.json", "type": "CustomTheme"}]}]})
    pages = [
        ("Executive Overview", ["Company Count", "Complete Statements", "Health Score", "Median Health Score", "Sector Count"], ["Revenue Growth %", "Net Margin %"], ["Revenue (INR Cr)", "PAT (INR Cr)"], ["Health Rank", "Health Score", "Coverage %", "Revenue Growth %", "Profit Growth %"]),
        ("Fundamentals & Profitability", ["Revenue (INR Cr)", "Operating Profit (INR Cr)", "EBIT (INR Cr)", "PAT (INR Cr)", "EPS (INR)"], ["ROE %", "ROA %"], ["Net Margin %", "Operating Margin %", "EBIT Margin %"], ["ROE %", "ROA %", "Net Margin %", "ROCE % (unavailable)", "EBITDA (unavailable)"]),
        ("Growth & Earnings", ["Revenue Growth %", "Profit Growth %", "EPS Growth %", "Revenue CAGR 3Y %", "Revenue CAGR 5Y %"], ["Revenue Growth %", "Net Margin %"], ["Revenue Growth %", "Profit Growth %"], ["Revenue Growth %", "Profit Growth %", "Revenue CAGR 3Y %", "Revenue CAGR 5Y %", "Growth Consistency"]),
        ("Balance Sheet & Financial Strength", ["Assets (INR Cr)", "Liabilities (INR Cr)", "Equity (INR Cr)", "Debt (INR Cr)", "Debt to Equity"], ["Debt to Equity", "ROE %"], ["Debt (INR Cr)", "Equity (INR Cr)"], ["Debt to Equity", "Equity Growth %", "Asset Growth %", "Current Ratio (unavailable)", "Cash (unavailable)", "Net Debt (unavailable)"]),
        ("Cash Flow Quality", ["CFO (INR Cr)", "Investing Cash (INR Cr)", "Financing Cash (INR Cr)", "CFO to PAT", "Cash Consistency"], ["PAT (INR Cr)", "CFO (INR Cr)"], ["CFO (INR Cr)", "PAT (INR Cr)"], ["CFO to PAT", "Cash Flow Score", "Cash Consistency", "FCF (unavailable)", "Capex (unavailable)"]),
        ("Financial Health Scanner", ["Scored Companies", "Health Score", "Coverage %", "Median Health Score", "Complete Statements"], ["Growth Score", "Profitability Score"], ["Health Score", "Coverage %"], ["Health Rank", "Health Score", "Coverage %", "Revenue Growth %", "Profit Growth %", "ROE %", "Debt to Equity", "CFO to PAT", "Percentile"]),
        ("Company Deep Dive", ["Health Score", "Coverage %", "Health Rank", "Sector Median", "Universe Median"], ["Revenue Growth %", "Net Margin %"], ["Revenue (INR Cr)", "PAT (INR Cr)", "CFO (INR Cr)"], ["Profitability Score", "Growth Score", "Balance Sheet Score", "Cash Flow Score", "Efficiency Score", "Consistency Score", "Percentile"]),
    ]
    order = []
    for i, (title, cards, scatter, trend, table) in enumerate(pages):
        page = uuid.uuid5(uuid.NAMESPACE_URL, title).hex[:20]
        order.append(page)
        write_json(REPORT / "definition/pages" / page / "page.json", {"$schema": SCHEMAS["page"], "name": page, "displayName": f"{i+1}. {title}", "displayOption": "FitToPage", "width": 1440, "height": 1040})
        index = 0
        def add(label, kind, roles, rect):
            nonlocal index
            visual(page, index, label, kind, roles, rect)
            index += 1
        for j, (label, column, table_name) in enumerate([("Company", "symbol", "dim_company"), ("Sector", "sector_name", "dim_sector"), ("Year", "year_label", "dim_year")]):
            add(label, "slicer", {"Values": [(column, table_name)]}, (24+j*464, 20, 440, 64))
        for j, name in enumerate(cards):
            add(name, "card", {"Values": [(name, None)]}, (24+j*280, 100, 264, 100))
        tooltips = [(n, None) for n in ["Health Score", "Coverage %", "Profitability Score", "Growth Score", "Balance Sheet Score", "Cash Flow Score", "Efficiency Score", "Consistency Score"]]
        add(title + " | history", "lineChart", {"Category": [("year_label", "dim_year")], "Y": [(n, None) for n in trend]}, (24, 224, 684, 280))
        add(scatter[0] + " vs " + scatter[1], "scatterChart", {"Category": [("symbol", "dim_company")], "X": [(scatter[0], None)], "Y": [(scatter[1], None)], "Tooltips": tooltips}, (732, 224, 684, 280))
        add("Sector comparison", "clusteredBarChart", {"Category": [("sector_name", "dim_sector")], "Y": [(table[1], None)], "Tooltips": [("Coverage %", None)]}, (24, 528, 430, 300))
        add("Company comparison", "tableEx", {"Values": [("symbol", "dim_company"), ("company_name", "dim_company"), ("sector", "dim_company")] + [(n, None) for n in table]}, (478, 528, 938, 300))
        if i == 5:
            for j, (label, col) in enumerate([("Score", "overall_score"), ("Revenue growth", "revenue_growth_pct"), ("ROE", "roe_pct"), ("Debt / equity", "debt_to_equity"), ("Cash conversion", "cash_conversion_ratio")]):
                add(label, "slicer", {"Values": [(col, "vw_metrics")]}, (24+j*280, 850, 264, 105))
        elif i == 6:
            add("Metric contributions and missing inputs", "tableEx", {"Values": [(n, "vw_score_contributions") for n in ["component", "metric_name", "metric_value", "metric_score", "metric_weight", "availability"]]}, (24, 850, 1392, 130))
        else:
            add("Source coverage", "tableEx", {"Values": [(n, "vw_company_coverage") for n in ["symbol", "profile_available", "has_profit_loss", "has_balance_sheet", "has_cash_flow", "has_documents", "has_source_analysis", "has_source_insights", "identity_status"]]}, (24, 850, 1392, 130))
        add("Historical screening", "card", {"Values": [("Screening Note", None)]}, (24, 992, 1392, 36))
    write_json(REPORT / "definition/pages/pages.json", {"$schema": SCHEMAS["pages"], "pageOrder": order, "activePageName": order[0]})


if __name__ == "__main__":
    measures()
    model()
    report()
    print(f"Built {len(TABLES)} model tables, {len(MEASURES)} measures and seven report pages")
