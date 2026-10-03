#!/usr/bin/env python3
"""Compatibility entrypoint for the canonical warehouse deploy/load pipeline."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from apps.etl.load.warehouse import deploy, load


def main() -> int:
    deploy()
    result = load()
    print(f"Warehouse published: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
