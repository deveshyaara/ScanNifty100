"""Validate PBIR against cached Microsoft schemas and model-field references."""
import json
from pathlib import Path
from urllib.parse import urljoin
import jsonschema
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]


def validate():
    schemas = json.loads((ROOT / "powerbi/schemas/microsoft.json").read_text())
    registry = Registry().with_resources((url, Resource.from_contents(value)) for url, value in schemas.items())
    manifest = json.loads((ROOT / "powerbi/model_manifest.json").read_text())
    count = 0
    for path in (ROOT / "powerbi/project").rglob("*"):
        if path.suffix not in (".json", ".pbip", ".pbir", ".pbism"):
            continue
        data = json.loads(path.read_text())
        if "$schema" in data:
            validator = jsonschema.Draft7Validator(schemas[data["$schema"]], registry=registry)
            errors = list(validator.iter_errors(data))
            if errors:
                raise ValueError(f"{path}: {errors[0].json_path}: {errors[0].message}")
            count += 1
        if path.name == "visual.json":
            pos = data["position"]
            if not (0 <= pos["x"] and 0 <= pos["y"] and pos["x"]+pos["width"] <= 1440 and pos["y"]+pos["height"] <= 1040):
                raise ValueError(f"Visual outside page: {path}")
            for role in data.get("visual", {}).get("query", {}).get("queryState", {}).values():
                for projection in role["projections"]:
                    kind, field = next(iter(projection["field"].items()))
                    table = field["Expression"]["SourceRef"]["Entity"]
                    valid = manifest["measures"] if kind == "Measure" else manifest["tables"][table]
                    if field["Property"] not in valid:
                        raise ValueError(f"Unknown model field in {path}: {field}")
    pages = list((ROOT / "powerbi/project/ScanNifty100.Report/definition/pages").glob("*/page.json"))
    if len(pages) != 7:
        raise ValueError(f"Expected seven pages, found {len(pages)}")
    print(f"Validated {count} schema-bound files, seven pages, and all visual field bindings")
    return count


if __name__ == "__main__":
    validate()
