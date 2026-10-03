"""Extract the authoritative workbooks, retaining source-row provenance."""
from pathlib import Path
import hashlib
import json
import logging
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DATASETS = ("companies", "profitandloss", "balancesheet", "cashflow", "documents", "analysis", "prosandcons")


def detect_title_row(path):
    path = Path(path)
    if not path.exists():
        return 0
    first = pd.read_excel(path, header=None, nrows=1)
    return int(not first.empty and any(word in str(first.iloc[0, 0]) for word in ("Bluestock", "Nifty", "Fintech")))


def standardize_column_names(frame):
    frame = frame.copy()
    frame.columns = frame.columns.astype(str).str.strip().str.lower().str.replace(" ", "_").str.replace("%", "percent").str.replace("&", "and").str.replace(r"[^a-z0-9_]", "", regex=True)
    return frame


def replace_null_variants(frame):
    return frame.replace(r"^\s*(?:NULL|Null|null|None|none|N/A|NA|n/a|--?|\u2014)?\s*$", float("nan"), regex=True)


def extract(source=None, output=None):
    source, output = Path(source or ROOT / "n100"), Path(output or ROOT / "data/raw")
    output.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name in DATASETS:
        matches = sorted(source.rglob(name + ".xlsx"))
        if len(matches) != 1:
            raise ValueError(f"Expected one {name}.xlsx in {source}; found {len(matches)}")
        path = matches[0]
        book = pd.ExcelFile(path)
        if len(book.sheet_names) != 1:
            raise ValueError(f"Unexpected additional sheets in {path}; review before extraction")
        header = detect_title_row(path)
        frame = replace_null_variants(standardize_column_names(pd.read_excel(path, header=header)))
        if name == "companies":
            frame = frame.rename(columns={"id": "company"})
        frame["source_row"] = range(header + 2, len(frame) + header + 2)
        frame["source_file"] = path.relative_to(source).as_posix()
        frame.to_csv(output / (name + ".csv"), index=False)
        mirror = ROOT / "data/source" / path.name
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest[name] = {"rows": len(frame), "columns": list(frame.columns), "sheets": book.sheet_names, "sha256": digest, "legacy_source_identical": mirror.exists() and hashlib.sha256(mirror.read_bytes()).hexdigest() == digest}
        logging.info("Extracted %s: %s rows", name, len(frame))
    (output / "source_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main():
    logging.basicConfig(level=logging.INFO)
    extract()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
