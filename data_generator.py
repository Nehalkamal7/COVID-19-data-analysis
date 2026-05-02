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
    time_series_csv_path,
)

COUNTRIES = [
    "USA", "India", "Brazil", "UK", "Germany", "France", "Italy", "Spain",
    "Canada", "Japan", "Mexico", "South Korea", "Australia",
]
COUNTRY_POP = {
    "USA": 331_000_000,
    "India": 1_380_000_000,
    "Brazil": 213_000_000,
    "UK": 67_000_000,
    "Germany": 83_000_000,
    "France": 67_000_000,
    "Italy": 60_000_000,
    "Spain": 47_000_000,
    "Canada": 38_000_000,
    "Japan": 125_000_000,
    "Mexico": 128_000_000,
    "South Korea": 51_000_000,
    "Australia": 26_000_000,
}
VACCINES = [
    "Pfizer", "Moderna", "AstraZeneca", "J&J", "Sinovac",
    "Novavax", "Sputnik V",
]
AGE_GROUPS = ["0-17", "18-34", "35-49", "50-64", "65+"]


def set_random_seed(seed: int | None = None) -> None:
    """Set NumPy RNG for reproducible synthetic data."""
    np.random.seed(RANDOM_SEED if seed is None else seed)


def load_time_series_from_csv(path: str | Path) -> pd.DataFrame:
    """
    Load daily time series from CSV.

    Required columns: date, country, new_cases, new_deaths
    Optional: new_recoveries (defaults computed), cumulative_* (computed if missing)
    """
    path = Path(path)
    df = pd.read_csv(path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    required = {"date", "country", "new_cases", "new_deaths"}
    if not required.issubset(df.columns):
        raise ValueError(
            f"CSV {path} must include columns {sorted(required)}; got {sorted(df.columns)}"
        )
    df["date"] = pd.to_datetime(df["date"])
    df["country"] = df["country"].astype(str).str.strip()
    df["new_cases"] = pd.to_numeric(df["new_cases"], errors="coerce").fillna(0).astype(int)
    df["new_deaths"] = pd.to_numeric(df["new_deaths"], errors="coerce").fillna(0).astype(int)

    if "new_recoveries" not in df.columns:
        df["new_recoveries"] = (df["new_cases"].astype(float) * 0.9).clip(lower=0).round().astype(int)
    else:
        df["new_recoveries"] = pd.to_numeric(df["new_recoveries"], errors="coerce").fillna(0).astype(int)

    df = df.sort_values(["country", "date"]).reset_index(drop=True)

    parts: list[pd.DataFrame] = []
    for _, g in df.groupby("country", sort=False):
        g = g.sort_values("date").copy()
        if "cumulative_cases" not in g.columns:
            g["cumulative_cases"] = g["new_cases"].cumsum()
        else:
            g["cumulative_cases"] = pd.to_numeric(g["cumulative_cases"], errors="coerce").fillna(0).astype(int)
        if "cumulative_deaths" not in g.columns:
            g["cumulative_deaths"] = g["new_deaths"].cumsum()
        else:
            g["cumulative_deaths"] = pd.to_numeric(g["cumulative_deaths"], errors="coerce").fillna(0).astype(int)
        parts.append(g)
    return pd.concat(parts, ignore_index=True)


def resolve_time_series(
    start: str | None = None,
    periods: int | None = None,
) -> tuple[pd.DataFrame, str]:
    """
    Return time-series DataFrame and source label: 'csv' or 'synthetic'.
    When a CSV is configured and exists, synthetic wave parameters are skipped.
    """
    csv_path = time_series_csv_path()
    if csv_path is not None:
        return load_time_series_from_csv(csv_path), "csv"
    return (
        generate_time_series(
            start=start or TIME_SERIES_START,
            periods=periods if periods is not None else TIME_SERIES_PERIODS,
        ),
        "synthetic",
    )


def generate_time_series(start: str | None = None, periods: int | None = None) -> pd.DataFrame:
    """Daily cases/deaths/recoveries per country."""
    start = start or TIME_SERIES_START
    periods = periods if periods is not None else TIME_SERIES_PERIODS
    dates = pd.date_range(start=start, periods=periods)
    records = []

    for country in COUNTRIES:
        pop = COUNTRY_POP[country]
        wave_centers = [60, 240, 480]
        wave_heights = np.random.uniform(0.6, 1.4, 3)

        cases = np.zeros(periods)
        for wc, wh in zip(wave_centers, wave_heights):
            peak = int(pop * np.random.uniform(0.0005, 0.002) * wh)
            cases += peak * np.exp(-((np.arange(periods) - wc) ** 2) / (2 * 60 ** 2))

        cases = np.clip(cases + np.random.normal(0, cases * 0.05 + 1), 0, None).astype(int)
        deaths = (cases * np.random.uniform(0.01, 0.025) + np.random.normal(0, 2, periods)).clip(0).astype(int)
        recoveries = (cases * np.random.uniform(0.85, 0.95)).astype(int)

        for i, date in enumerate(dates):
            records.append({
                "date": date,
                "country": country,
                "new_cases": cases[i],
                "new_deaths": deaths[i],
                "new_recoveries": recoveries[i],
                "cumulative_cases": int(cases[:i+1].sum()),
                "cumulative_deaths": int(deaths[:i+1].sum()),
            })

    return pd.DataFrame(records)


def generate_vaccination_data() -> pd.DataFrame:
    """Vaccination rates by country and vaccine type."""
    records = []
    for country in COUNTRIES:
        total_vax = np.random.uniform(0.45, 0.92)
        shares = np.random.dirichlet(np.ones(len(VACCINES)))
        for vaccine, share in zip(VACCINES, shares):
            records.append({
                "country": country,
                "vaccine": vaccine,
                "vaccinated_pct": round(total_vax * share * 100, 2),
                "total_vaccinated": int(COUNTRY_POP[country] * total_vax * share),
            })
    return pd.DataFrame(records)


def generate_age_severity_data() -> pd.DataFrame:
    """Case severity (mild/severe/critical) by age group."""
    severity_weights = {
        "0-17":  [0.97, 0.025, 0.005],
        "18-34": [0.93, 0.055, 0.015],
        "35-49": [0.85, 0.11,  0.04],
        "50-64": [0.72, 0.20,  0.08],
        "65+":   [0.55, 0.28,  0.17],
    }
    records = []
    for age in AGE_GROUPS:
        base_cases = np.random.randint(50_000, 500_000)
        mild, severe, critical = severity_weights[age]
        records.append({
            "age_group": age,
            "total_cases": base_cases,
            "mild": int(base_cases * mild),
            "severe": int(base_cases * severe),
            "critical": int(base_cases * critical),
            "case_fatality_rate": round(critical * 0.6 * 100, 2),
        })
    return pd.DataFrame(records)


def generate_correlation_data() -> pd.DataFrame:
    """Country-level stats for correlation/scatter analysis."""
    records = []
    for country in COUNTRIES:
        pop = COUNTRY_POP[country]
        gdp_per_capita = np.random.uniform(10_000, 65_000)
        healthcare_index = np.random.uniform(55, 95)
        vax_rate = np.random.uniform(45, 92)
        cases_per_million = np.random.uniform(30_000, 180_000) * (1 - vax_rate / 200)
        deaths_per_million = cases_per_million * np.random.uniform(0.005, 0.025) * (100 / healthcare_index)

        records.append({
            "country": country,
            "population": pop,
            "gdp_per_capita": round(gdp_per_capita, 0),
            "healthcare_index": round(healthcare_index, 1),
            "vaccination_rate": round(vax_rate, 1),
            "cases_per_million": round(cases_per_million, 0),
            "deaths_per_million": round(deaths_per_million, 1),
        })
    return pd.DataFrame(records)
