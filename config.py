"""
Central settings for the COVID analytics demo.

Override via environment variables (no code edits needed):

  COVID_SEED              Random seed for synthetic data (default: 42)
  COVID_START             Time series start date YYYY-MM-DD (default: 2020-01-01)
  COVID_PERIODS           Number of days for synthetic series (default: 730)
  COVID_TIME_SERIES_CSV   Absolute or relative path to a CSV file. When set and
                          the file exists, it replaces the synthetic time series.
                          If unset, ./data/time_series.csv is used when present.
"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

RANDOM_SEED = int(os.environ.get("COVID_SEED", "42"))
TIME_SERIES_START = os.environ.get("COVID_START", "2020-01-01")
TIME_SERIES_PERIODS = int(os.environ.get("COVID_PERIODS", "730"))


def time_series_csv_path() -> Path | None:
    """Return path to optional user CSV, or None to use synthetic series."""
    env = os.environ.get("COVID_TIME_SERIES_CSV", "").strip()
    candidates: list[Path] = []
    if env:
        candidates.append(Path(env))
    candidates.append(PROJECT_ROOT / "data" / "time_series.csv")
    for p in candidates:
        if p.is_file():
            return p.resolve()
    return None
