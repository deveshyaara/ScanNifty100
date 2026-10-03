"""Explicit source reconciliation. Conflicting values are never chosen arbitrarily."""
import json
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
PROVENANCE = {"id", "source_row", "source_file"}


def normalize_symbols(frame, dataset, report):
    frame = frame.rename(columns={"company_id": "company"}).copy()
    if "company" not in frame:
        raise ValueError(f"{dataset}: missing company identifier")
    frame["company"] = frame.company.astype("string").str.strip().str.upper()
    mappings = json.loads((ROOT / "data/reference/symbol_normalization.json").read_text())
    for original, rule in mappings.items():
        if dataset in rule["datasets"]:
            mask = frame.company.eq(original)
            if mask.any():
                report["symbol_corrections"].append({"dataset": dataset, "from": original, "to": rule["symbol"], "rows": int(mask.sum()), "reason": rule["reason"]})
                frame.loc[mask, "company"] = rule["symbol"]
    valid = frame.company.str.fullmatch(r"[A-Z0-9&-]+", na=False) & ~frame.company.isin(["COMPANY", "COMPANY_ID"])
    reject(frame.loc[~valid], dataset, "invalid identifier", report)
    return frame.loc[valid].copy()


def reject(frame, dataset, reason, report):
    for row in frame.to_dict("records"):
        report["rejected_rows"].append({"dataset": dataset, "reason": reason, "record": row})


def reconcile_duplicates(frame, keys, dataset, report):
    """Merge identical/complementary rows; quarantine every conflicting group."""
    values = [c for c in frame if c not in PROVENANCE and c not in keys]
    rows = []
    for key, group in frame.groupby(keys, dropna=False, sort=True):
        if len(group) > 1:
            conflicts = [c for c in values if group[c].nunique(dropna=True) > 1]
            report["duplicates"].append({"dataset": dataset, "key": str(key), "extra_rows": len(group) - 1, "conflicts": conflicts, "resolution": "quarantined" if conflicts else "merged equal/complementary values; earliest source row provenance"})
            if conflicts:
                reject(group, dataset, "conflicting duplicate: " + ", ".join(conflicts), report)
                continue
        rows.append(group.iloc[0].combine_first(group.bfill().iloc[0]))
    return pd.DataFrame(rows, columns=frame.columns).reset_index(drop=True)


def canonical_sectors(path, report):
    frame = pd.read_csv(path, dtype=str)
    frame = frame[frame.company.str.lower() != "company"].copy()
    frame["company"] = frame.company.str.strip().str.upper()
    # ATGL's source profile explicitly says city gas distribution.
    wrong = frame.company.eq("ATGL") & ~frame.sector.eq("Energy")
    report["sector_resolution"] = {"ATGL": "Energy / Gas Distribution; n100/companies.xlsx about_company describes city gas distribution", "discarded_conflicting_rows": int(wrong.sum())}
    frame = frame.loc[~wrong]
    before = len(frame)
    frame = reconcile_duplicates(frame, ["company"], "sector_mapping", report)
    report["sector_resolution"]["duplicate_rows_collapsed"] = before - len(frame)
    return frame


def numeric_columns(frame, columns, dataset, report):
    frame = frame.copy()
    for col in columns:
        if col not in frame:
            raise ValueError(f"{dataset}: missing required column {col}")
        original = frame[col]
        parsed = pd.to_numeric(original.astype("string").str.replace(",", "", regex=False).str.rstrip("%"), errors="coerce")
        bad = original.notna() & (parsed.isna() | parsed.isin([float("inf"), -float("inf")]))
        for idx in frame.index[bad]:
            report["invalid_values"].append({"dataset": dataset, "source_row": int(frame.loc[idx, "source_row"]), "column": col, "value": str(original.loc[idx])})
        frame[col] = parsed.mask(bad).astype(float)
    return frame
