"""Cache Microsoft's public Power BI schemas and recursively referenced schemas."""
import json
from pathlib import Path
from urllib.parse import urljoin, urldefrag
import requests

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://developer.microsoft.com/json-schemas/fabric/item/"
SCHEMAS = {
    "project": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
    "report_properties": BASE + "report/definitionProperties/2.0.0/schema.json",
    "semantic_properties": BASE + "semanticModel/definitionProperties/1.0.0/schema.json",
    "report": BASE + "report/definition/report/2.0.0/schema.json",
    "page": BASE + "report/definition/page/1.0.0/schema.json",
    "pages": BASE + "report/definition/pagesMetadata/1.0.0/schema.json",
    "version": BASE + "report/definition/versionMetadata/1.0.0/schema.json",
    "visual": BASE + "report/definition/visualContainer/2.0.0/schema.json",
}


def refs(value):
    if isinstance(value, dict):
        if "$ref" in value:
            yield value["$ref"]
        for child in value.values():
            yield from refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from refs(child)


def main():
    cache = ROOT / "powerbi/schemas"
    cache.mkdir(parents=True, exist_ok=True)
    pending, schemas = list(SCHEMAS.values()), {}
    while pending:
        url = pending.pop()
        if url in schemas:
            continue
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        schema = response.json()
        schemas[url] = schema
        for ref in refs(schema):
            target = urldefrag(urljoin(url, ref))[0]
            if target not in schemas:
                pending.append(target)
    (cache / "microsoft.json").write_text(json.dumps(schemas, indent=2), encoding="utf-8")
    print(f"Cached {len(schemas)} official schemas")


if __name__ == "__main__":
    main()
