"""
data_generator.py
Generates realistic synthetic COVID-19 data for analysis.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

COUNTRIES = ["USA", "India", "Brazil", "UK", "Germany", "France", "Italy", "Spain"]
COUNTRY_POP = {
    "USA": 331_000_000, "India": 1_380_000_000, "Brazil": 213_000_000,
    "UK": 67_000_000, "Germany": 83_000_000, "France": 67_000_000,
    "Italy": 60_000_000, "Spain": 47_000_000,
}
VACCINES = ["Pfizer", "Moderna", "AstraZeneca", "J&J", "Sinovac"]
AGE_GROUPS = ["0-17", "18-34", "35-49", "50-64", "65+"]


def generate_time_series(start="2020-01-01", periods=730) -> pd.DataFrame:
    """Daily cases/deaths/recoveries per country over ~2 years."""
    dates = pd.date_range(start=start, periods=periods)
    records = []

    for country in COUNTRIES:
        pop = COUNTRY_POP[country]
        # Simulate 3 waves with gaussian peaks
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
