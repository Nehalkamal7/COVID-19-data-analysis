"""
config.py
Central settings for the COVID analytics demo.

Override via environment variables (no code edits needed):

  COVID_SEED              Random seed for synthetic data          (default: 42)
  COVID_START             Time series start date YYYY-MM-DD       (default: 2020-01-01)
  COVID_PERIODS           Number of days for synthetic series     (default: 730)
  COVID_TIME_SERIES_CSV   Absolute or relative path to a CSV.
                          When set and the file exists, it replaces synthetic data.
                          If unset, ./data/time_series.csv is used when present.
  COVID_COUNTRIES         Comma-separated country names to include (overrides built-in list)
  COVID_VACCINES          Comma-separated vaccine names to include (overrides built-in list)
  COVID_PORT              Port for the Flask dev server           (default: 5000)
  COVID_DEBUG             Set to 0 to disable Flask debug mode   (default: 1)
  COVID_ROLLING_WINDOW    Rolling average window (days) for charts (default: 7)
  COVID_TOP_N_COUNTRIES   How many countries to show in line chart (default: 6)
"""

from __future__ import annotations

import os
from pathlib import Path

# ── Project root ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent

# ── Numeric / date settings ───────────────────────────────────────────────────
RANDOM_SEED           = int(os.environ.get("COVID_SEED",           "42"))
TIME_SERIES_START     = os.environ.get("COVID_START",              "2020-01-01")
TIME_SERIES_PERIODS   = int(os.environ.get("COVID_PERIODS",        "730"))
FLASK_PORT            = int(os.environ.get("COVID_PORT",           "5000"))
FLASK_DEBUG           = os.environ.get("COVID_DEBUG", "1").strip() not in ("0", "false", "no")
ROLLING_WINDOW        = int(os.environ.get("COVID_ROLLING_WINDOW", "7"))
TOP_N_COUNTRIES       = int(os.environ.get("COVID_TOP_N_COUNTRIES","6"))

# ── Country list ──────────────────────────────────────────────────────────────
_DEFAULT_COUNTRIES = [
    "USA", "India", "Brazil", "UK", "Germany", "France",
    "Italy", "Spain", "Canada", "Japan", "Mexico", "South Korea",
    "Australia", "Argentina", "Turkey", "Russia", "Indonesia",
    "South Africa", "Egypt", "Nigeria",
]

def _parse_list(env_var: str, default: list[str]) -> list[str]:
    """Return env-var CSV list, or default if env not set / empty."""
    raw = os.environ.get(env_var, "").strip()
    if raw:
        return [s.strip() for s in raw.split(",") if s.strip()]
    return default

COUNTRIES: list[str] = _parse_list("COVID_COUNTRIES", _DEFAULT_COUNTRIES)

# ── Population lookup (extended; unknown countries get a sensible default) ────
_POPULATION_MAP: dict[str, int] = {
    "USA":          331_000_000,
    "India":      1_380_000_000,
    "Brazil":       213_000_000,
    "UK":            67_000_000,
    "Germany":       83_000_000,
    "France":        67_000_000,
    "Italy":         60_000_000,
    "Spain":         47_000_000,
    "Canada":        38_000_000,
    "Japan":        125_000_000,
    "Mexico":       128_000_000,
    "South Korea":   51_000_000,
    "Australia":     26_000_000,
    "Argentina":     45_000_000,
    "Turkey":        84_000_000,
    "Russia":       146_000_000,
    "Indonesia":    273_000_000,
    "South Africa":  60_000_000,
    "Egypt":        102_000_000,
    "Nigeria":      206_000_000,
}
DEFAULT_POPULATION = 50_000_000  # fallback for unknown countries

def get_population(country: str) -> int:
    """Return population for a country; uses DEFAULT_POPULATION if unknown."""
    return _POPULATION_MAP.get(country, DEFAULT_POPULATION)

# ── Vaccine list ──────────────────────────────────────────────────────────────
_DEFAULT_VACCINES = [
    "Pfizer", "Moderna", "AstraZeneca", "J&J", "Sinovac",
    "Novavax", "Sputnik V", "Covaxin",
]
VACCINES: list[str] = _parse_list("COVID_VACCINES", _DEFAULT_VACCINES)

# ── Age groups (not configurable via env — changing breaks severity weights) ──
AGE_GROUPS = ["0-17", "18-34", "35-49", "50-64", "65+"]

# ── CSV path helper ───────────────────────────────────────────────────────────
def time_series_csv_path() -> Path | None:
    """
    Return resolved path to optional user-supplied CSV, or None.

    Search order:
      1. $COVID_TIME_SERIES_CSV  (explicit env override)
      2. <project_root>/data/time_series.csv  (conventional location)
    """
    env = os.environ.get("COVID_TIME_SERIES_CSV", "").strip()
    candidates: list[Path] = []
    if env:
        candidates.append(Path(env))
    candidates.append(PROJECT_ROOT / "data" / "time_series.csv")
    for p in candidates:
        if p.is_file():
            return p.resolve()
    return None


def as_dict() -> dict:
    """Return all config values as a plain dict (for /api/config endpoint)."""
    csv_path = time_series_csv_path()
    return {
        "random_seed":           RANDOM_SEED,
        "time_series_start":     TIME_SERIES_START,
        "time_series_periods":   TIME_SERIES_PERIODS,
        "flask_port":            FLASK_PORT,
        "flask_debug":           FLASK_DEBUG,
        "rolling_window":        ROLLING_WINDOW,
        "top_n_countries":       TOP_N_COUNTRIES,
        "countries":             COUNTRIES,
        "vaccines":              VACCINES,
        "age_groups":            AGE_GROUPS,
        "time_series_csv":       str(csv_path) if csv_path else None,
        "time_series_source":    "csv" if csv_path else "synthetic",
    }
