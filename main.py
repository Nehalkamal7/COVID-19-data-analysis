"""
main.py
COVID-19 Data Analysis & Visualization
========================================
Run:  python main.py

Output PNGs are saved to the ./output/ folder.
Set environment variables (see config.py) to customise the run without
editing any source files.
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
from config import (
    RANDOM_SEED,
    TIME_SERIES_START,
    TIME_SERIES_PERIODS,
    COUNTRIES,
    VACCINES,
    ROLLING_WINDOW,
    TOP_N_COUNTRIES,
    time_series_csv_path,
    as_dict as config_as_dict,
)
from data_generator import (
    set_random_seed,
    resolve_time_series,
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


def _print_config() -> None:
    cfg = config_as_dict()
    print(f"  Seed        : {cfg['random_seed']}")
    print(f"  Start date  : {cfg['time_series_start']}")
    print(f"  Periods     : {cfg['time_series_periods']} days")
    print(f"  Countries   : {len(cfg['countries'])}  ({', '.join(cfg['countries'][:5])}{'...' if len(cfg['countries']) > 5 else ''})")
    print(f"  Vaccines    : {len(cfg['vaccines'])}")
    print(f"  Rolling win : {cfg['rolling_window']} days")
    print(f"  CSV source  : {cfg['time_series_csv'] or 'none (synthetic)'}")


def main() -> None:
    print("=" * 60)
    print("  COVID-19 Data Analysis & Visualization Project")
    print("=" * 60)

    # ── 0. Show active config ────────────────────────────────
    print("\n[0/3] Active configuration:")
    _print_config()

    # ── 1. Generate / load data ──────────────────────────────
    print("\n[1/3] Loading datasets...")
    set_random_seed()

    df_ts, ts_src = resolve_time_series()
    df_vax        = generate_vaccination_data()
    df_age        = generate_age_severity_data()
    df_corr       = generate_correlation_data()

    print(f"  + Time series  [{ts_src}]: "
          f"{len(df_ts):,} rows | "
          f"{df_ts['country'].nunique()} countries | "
          f"{df_ts['date'].nunique()} days "
          f"({df_ts['date'].min().date()} → {df_ts['date'].max().date()})")
    print(f"  + Vaccination  : {len(df_vax):,} rows  ({df_vax['vaccine'].nunique()} vaccines)")
    print(f"  + Age/Severity : {len(df_age)} rows")
    print(f"  + Correlations : {len(df_corr)} rows")

    # ── 2. Statistical summary ───────────────────────────────
    print("\n[2/3] Running statistical analysis...")
    run_statistical_summary(df_ts, df_vax, df_age, df_corr)

    # ── 3. Generate charts ───────────────────────────────────
    print("\n[3/3] Generating visualizations...")

    # Use top-N from the countries actually present in the data
    available = [c for c in COUNTRIES if c in df_ts["country"].unique()]
    chart_countries = available[:TOP_N_COUNTRIES] or list(df_ts["country"].unique())[:TOP_N_COUNTRIES]

    plot_daily_cases_line(df_ts, countries=chart_countries, rolling_window=ROLLING_WINDOW)
    plot_vaccination_bar(df_vax)
    plot_heatmaps(df_ts, df_age)
    plot_scatter_analysis(df_corr)

    print("\n" + "=" * 60)
    print("  Done. Charts saved to ./output/")
    print("=" * 60)


if __name__ == "__main__":
    main()
