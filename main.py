"""
main.py
COVID-19 Data Analysis & Visualization
========================================
Run:  python main.py

Output PNGs are saved to the ./output/ folder.
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
from data_generator import (
    generate_time_series,
    generate_vaccination_data,
    generate_age_severity_data,
    generate_correlation_data,
)
from visualizations import (
    plot_daily_cases_line,
    plot_vaccination_bar,
    plot_heatmaps,
    plot_scatter_analysis,
)
from analysis import run_statistical_summary


def main():
    print("=" * 55)
    print("  COVID-19 Data Analysis & Visualization Project")
    print("=" * 55)

    # ── 1. Generate data ─────────────────────────────────────
    print("\n[1/3] Generating synthetic COVID datasets...")
    df_ts   = generate_time_series(start="2020-01-01", periods=730)
    df_vax  = generate_vaccination_data()
    df_age  = generate_age_severity_data()
    df_corr = generate_correlation_data()
    print(f"  ✓ Time series:     {len(df_ts):,} rows  "
          f"({df_ts['country'].nunique()} countries, "
          f"{df_ts['date'].nunique()} days)")
    print(f"  ✓ Vaccination:     {len(df_vax)} rows")
    print(f"  ✓ Age/Severity:    {len(df_age)} rows")
    print(f"  ✓ Country metrics: {len(df_corr)} rows")

    # ── 2. Statistical summary ───────────────────────────────
    print("\n[2/3] Running statistical analysis...")
    run_statistical_summary(df_ts, df_vax, df_age, df_corr)

    # ── 3. Generate charts ───────────────────────────────────
    print("\n[3/3] Generating visualizations...")
    plot_daily_cases_line(df_ts, countries=["USA", "India", "Brazil", "UK", "Germany"])
    plot_vaccination_bar(df_vax)
    plot_heatmaps(df_ts, df_age)
    plot_scatter_analysis(df_corr)

    print("\n" + "=" * 55)
    print("  ✅ All done! Check the ./output/ folder for charts.")
    print("=" * 55)


if __name__ == "__main__":
    main()
