"""
analysis.py
Statistical summaries and insights printed to the console.
"""

import pandas as pd
import numpy as np


def run_statistical_summary(df_ts, df_vax, df_age, df_corr):
    """Print key statistics and insights from each dataset."""

    print("\n  ── Time Series Summary ──────────────────────────────")
    total = df_ts.groupby("country")[["new_cases", "new_deaths"]].sum()
    total["CFR_%"] = (total["new_deaths"] / total["new_cases"] * 100).round(2)
    total["new_cases"] = total["new_cases"].apply(lambda x: f"{x:,}")
    total["new_deaths"] = total["new_deaths"].apply(lambda x: f"{x:,}")
    print(total.to_string())

    print("\n  ── Peak Daily Cases per Country ─────────────────────")
    peaks = (df_ts.groupby("country")["new_cases"].max()
               .sort_values(ascending=False)
               .apply(lambda x: f"{x:,}"))
    for country, peak in peaks.items():
        print(f"    {country:<12} {peak}")

    print("\n  ── Vaccination Rate Summary ─────────────────────────")
    total_vax = df_vax.groupby("country")["vaccinated_pct"].sum().round(1)
    for country, rate in total_vax.sort_values(ascending=False).items():
        bar = "█" * int(rate / 5) + "░" * (20 - int(rate / 5))
        print(f"    {country:<12} {bar}  {rate}%")

    print("\n  ── Age Group — Case Fatality Rate ───────────────────")
    for _, row in df_age.iterrows():
        cfr = row["case_fatality_rate"]
        risk = "🔴 HIGH" if cfr > 8 else ("🟡 MED" if cfr > 3 else "🟢 LOW")
        print(f"    {row['age_group']:<6}  CFR: {cfr:5.2f}%  {risk}")

    print("\n  ── Correlation Matrix (country metrics) ─────────────")
    cols = ["vaccination_rate", "healthcare_index",
            "gdp_per_capita", "deaths_per_million"]
    corr_mat = df_corr[cols].corr().round(2)
    print(corr_mat.to_string())

    print("\n  ── Key Insights ─────────────────────────────────────")
    r_vax_death = df_corr[["vaccination_rate", "deaths_per_million"]].corr().iloc[0, 1]
    r_gdp_vax   = df_corr[["gdp_per_capita", "vaccination_rate"]].corr().iloc[0, 1]
    r_hci_cases = df_corr[["healthcare_index", "cases_per_million"]].corr().iloc[0, 1]

    def strength(r):
        a = abs(r)
        d = "negative" if r < 0 else "positive"
        if a > 0.7:   return f"strong {d}"
        elif a > 0.4: return f"moderate {d}"
        else:         return f"weak {d}"

    print(f"    • Vaccination ↔ Deaths/M:   r={r_vax_death:.2f}  ({strength(r_vax_death)})")
    print(f"    • GDP/capita  ↔ Vaccination: r={r_gdp_vax:.2f}  ({strength(r_gdp_vax)})")
    print(f"    • Healthcare  ↔ Cases/M:    r={r_hci_cases:.2f}  ({strength(r_hci_cases)})")
    print()
