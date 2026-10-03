#!/usr/bin/env python3
"""Compatibility entrypoint for the canonical end-to-end refresh."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from apps.etl.pipelines.refresh_all import main


if __name__ == "__main__":
    raise SystemExit(main())
