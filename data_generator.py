"""
data_generator.py
Generates realistic synthetic COVID-19 data for analysis.
Optional: load daily time series from CSV (see config / data/time_series.csv).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path

from config import (
    RANDOM_SEED,
    TIME_SERIES_START,
    TIME_SERIES_PERIODS,
    COUNTRIES,
    VACCINES,
    AGE_GROUPS,
    get_population,
    time_series_csv_path,
)

# Re-export so callers can do: from data_generator import COUNTRIES
__all__ = [
    "COUNTRIES", "VACCINES", "AGE_GROUPS",
    "set_random_seed",
    "load_time_series_from_csv",
    "resolve_time_series",
    "generate_time_series",
    "generate_vaccination_data",
    "generate_age_severity_data",
    "generate_correlation_data",
]


def set_random_seed(seed: int | None = None) -> None:
    """Set NumPy RNG for reproducible synthetic data."""
    np.random.seed(RANDOM_SEED if seed is None else seed)


# ── CSV loader ────────────────────────────────────────────────────────────────

def load_time_series_from_csv(path: str | Path) -> pd.DataFrame:
    """
    Load daily time series from a CSV file.

    Required columns : date, country, new_cases, new_deaths
    Optional columns : new_recoveries  (auto-computed if missing)
                       cumulative_cases / cumulative_deaths  (auto-computed)

    Raises ValueError when required columns are absent.
    """
    path = Path(path)
    df = pd.read_csv(path)
    df.columns = [str(c).strip().lower() for c in df.columns]

    required = {"date", "country", "new_cases", "new_deaths"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"CSV {path.name} is missing required columns: {sorted(missing)}. "
            f"Got: {sorted(df.columns)}"
        )

    df["date"]       = pd.to_datetime(df["date"])
    df["country"]    = df["country"].astype(str).str.strip()
    df["new_cases"]  = pd.to_numeric(df["new_cases"],  errors="coerce").fillna(0).astype(int)
    df["new_deaths"] = pd.to_numeric(df["new_deaths"], errors="coerce").fillna(0).astype(int)

    if "new_recoveries" in df.columns:
        df["new_recoveries"] = (
            pd.to_numeric(df["new_recoveries"], errors="coerce").fillna(0).astype(int)
        )
    else:
        df["new_recoveries"] = (df["new_cases"] * 0.90).clip(lower=0).round().astype(int)

    # Compute cumulative columns per-country if absent
    parts: list[pd.DataFrame] = []
    for _, g in df.groupby("country", sort=False):
        g = g.sort_values("date").copy()
        if "cumulative_cases" not in g.columns:
            g["cumulative_cases"] = g["new_cases"].cumsum()
        else:
            g["cumulative_cases"] = (
                pd.to_numeric(g["cumulative_cases"], errors="coerce").fillna(0).astype(int)
            )
        if "cumulative_deaths" not in g.columns:
            g["cumulative_deaths"] = g["new_deaths"].cumsum()
        else:
            g["cumulative_deaths"] = (
                pd.to_numeric(g["cumulative_deaths"], errors="coerce").fillna(0).astype(int)
            )
        parts.append(g)

    return pd.concat(parts, ignore_index=True).sort_values(["country", "date"]).reset_index(drop=True)


# ── Time series resolver ──────────────────────────────────────────────────────

def resolve_time_series(
    start: str | None = None,
    periods: int | None = None,
) -> tuple[pd.DataFrame, str]:
    """
    Return (DataFrame, source_label) where source_label is 'csv' or 'synthetic'.

    Priority:
      1. CSV configured via $COVID_TIME_SERIES_CSV env var
      2. ./data/time_series.csv  (if it exists)
      3. Fully synthetic generated data
    """
    csv_path = time_series_csv_path()
    if csv_path is not None:
        try:
            df = load_time_series_from_csv(csv_path)
            return df, "csv"
        except Exception as exc:
            print(f"  [WARN] Could not load CSV ({csv_path.name}): {exc}. Falling back to synthetic.")

    return (
        generate_time_series(
            start=start or TIME_SERIES_START,
            periods=periods if periods is not None else TIME_SERIES_PERIODS,
        ),
        "synthetic",
    )


# ── Synthetic generators ──────────────────────────────────────────────────────

def generate_time_series(
    start: str | None = None,
    periods: int | None = None,
    countries: list[str] | None = None,
) -> pd.DataFrame:
    """
    Daily new cases / deaths / recoveries per country.

    Parameters
    ----------
    start     : ISO date string, defaults to config.TIME_SERIES_START
    periods   : number of days, defaults to config.TIME_SERIES_PERIODS
    countries : list of country names, defaults to config.COUNTRIES
    """
    start    = start   or TIME_SERIES_START
    periods  = periods if periods is not None else TIME_SERIES_PERIODS
    countries = countries or COUNTRIES

    dates   = pd.date_range(start=start, periods=periods)
    records = []

    for country in countries:
        pop = get_population(country)

        # 3 epidemic waves at different centres
        wave_centers = [60, 240, 480]
        wave_heights = np.random.uniform(0.5, 1.5, 3)

        cases = np.zeros(periods)
        for wc, wh in zip(wave_centers, wave_heights):
            peak   = int(pop * np.random.uniform(0.0004, 0.0022) * wh)
            sigma  = np.random.uniform(45, 75)          # wave width varies
            cases += peak * np.exp(-((np.arange(periods) - wc) ** 2) / (2 * sigma ** 2))

        # add noise and weekend dip (~15 % dip on day 6–0)
        noise  = np.random.normal(0, cases * 0.06 + 1)
        dow    = np.array([(dates[i].weekday() >= 5) * -0.15 for i in range(periods)])
        cases  = np.clip(cases + noise + cases * dow, 0, None).astype(int)

        cfr        = np.random.uniform(0.008, 0.028)
        deaths     = (cases * cfr + np.random.normal(0, 2, periods)).clip(0).astype(int)
        recoveries = (cases * np.random.uniform(0.84, 0.95)).astype(int)

        cum_cases  = np.cumsum(cases)
        cum_deaths = np.cumsum(deaths)

        for i, date in enumerate(dates):
            records.append({
                "date":              date,
                "country":           country,
                "new_cases":         int(cases[i]),
                "new_deaths":        int(deaths[i]),
                "new_recoveries":    int(recoveries[i]),
                "cumulative_cases":  int(cum_cases[i]),
                "cumulative_deaths": int(cum_deaths[i]),
            })

    return pd.DataFrame(records)


def generate_vaccination_data(countries: list[str] | None = None,
                               vaccines: list[str] | None = None) -> pd.DataFrame:
    """
    Vaccination rates by country and vaccine type.

    Returns a DataFrame with columns:
      country, vaccine, vaccinated_pct, total_vaccinated
    """
    countries = countries or COUNTRIES
    vaccines  = vaccines  or VACCINES
    records   = []

    for country in countries:
        pop          = get_population(country)
        total_vax    = np.random.uniform(0.40, 0.94)           # total population fraction
        shares       = np.random.dirichlet(np.ones(len(vaccines)))  # vaccine market share

        for vaccine, share in zip(vaccines, shares):
            records.append({
                "country":          country,
                "vaccine":          vaccine,
                "vaccinated_pct":   round(total_vax * share * 100, 2),
                "total_vaccinated": int(pop * total_vax * share),
            })

    return pd.DataFrame(records)


def generate_age_severity_data() -> pd.DataFrame:
    """
    Case severity (mild / severe / critical) by age group.

    Severity weights are evidence-based approximations and are fixed
    (not configurable) since changing them breaks chart interpretation.
    """
    severity_weights = {
        "0-17":  [0.970, 0.024, 0.006],
        "18-34": [0.930, 0.055, 0.015],
        "35-49": [0.850, 0.110, 0.040],
        "50-64": [0.720, 0.200, 0.080],
        "65+":   [0.550, 0.280, 0.170],
    }
    records = []
    for age in AGE_GROUPS:
        base    = np.random.randint(50_000, 500_000)
        m, s, c = severity_weights[age]
        records.append({
            "age_group":          age,
            "total_cases":        base,
            "mild":               int(base * m),
            "severe":             int(base * s),
            "critical":           int(base * c),
            "case_fatality_rate": round(c * 0.60 * 100, 2),
        })
    return pd.DataFrame(records)


def generate_correlation_data(countries: list[str] | None = None) -> pd.DataFrame:
    """
    Country-level macro stats for correlation / scatter analysis.

    Columns: country, population, gdp_per_capita, healthcare_index,
             vaccination_rate, cases_per_million, deaths_per_million
    """
    countries = countries or COUNTRIES
    records   = []

    for country in countries:
        pop              = get_population(country)
        gdp_per_capita   = np.random.uniform(5_000, 70_000)
        healthcare_index = np.random.uniform(40, 96)
        vax_rate         = np.random.uniform(30, 94)

        # Higher vaccination and healthcare → fewer deaths per million
        cases_per_million  = (
            np.random.uniform(20_000, 200_000) * (1 - vax_rate / 250)
        )
        deaths_per_million = (
            cases_per_million
            * np.random.uniform(0.004, 0.028)
            * (100 / max(healthcare_index, 1))
        )

        records.append({
            "country":           country,
            "population":        pop,
            "gdp_per_capita":    round(gdp_per_capita, 0),
            "healthcare_index":  round(healthcare_index, 1),
            "vaccination_rate":  round(vax_rate, 1),
            "cases_per_million": round(cases_per_million, 0),
            "deaths_per_million":round(deaths_per_million, 1),
        })

    return pd.DataFrame(records)
