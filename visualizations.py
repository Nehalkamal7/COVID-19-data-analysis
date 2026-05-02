"""
visualizations.py
All chart-generating functions for the COVID-19 analytics project.

Dynamic country colors: palette auto-scales to any number of countries
using a HSL-based generator so colours are always visually distinct.
"""

from __future__ import annotations

import colorsys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path

from config import COUNTRIES as DEFAULT_COUNTRY_ORDER, ROLLING_WINDOW

sns.set_theme(style="darkgrid", palette="muted")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Dynamic colour palette ────────────────────────────────────────────────────

def _generate_hsl_palette(n: int) -> list[tuple[float, float, float]]:
    """
    Generate *n* visually distinct RGB colours by evenly spacing hues
    around the HSL colour wheel (golden-angle step for max separation).
    """
    if n == 0:
        return []
    golden_ratio = 0.618033988749895
    colours: list[tuple] = []
    h = 0.0
    for _ in range(n):
        r, g, b = colorsys.hls_to_rgb(h % 1.0, 0.52, 0.72)
        colours.append((r, g, b))
        h += golden_ratio
    return colours


def country_colors(countries: list[str]) -> dict[str, tuple]:
    """
    Return a stable {country: RGB-tuple} mapping.

    Strategy:
      • ≤ 10 countries  → seaborn tab10 (hand-tuned, looks great)
      • 11-20 countries → tab20 extended palette
      • > 20 countries  → HSL golden-angle generator (always distinct)
    """
    n = len(countries)
    if n == 0:
        return {}
    if n <= 10:
        palette = sns.color_palette("tab10", n)
    elif n <= 20:
        palette = sns.color_palette("tab20", n)
    else:
        palette = _generate_hsl_palette(n)
    return {c: palette[i] for i, c in enumerate(countries)}


# ── Chart 1: Line chart ───────────────────────────────────────────────────────

def plot_daily_cases_line(
    df_ts: pd.DataFrame,
    countries: list[str] | None = None,
    rolling_window: int | None = None,
) -> Figure:
    """
    Line chart: rolling-average new daily cases & deaths for selected countries.

    Parameters
    ----------
    df_ts          : Time-series DataFrame (from data_generator)
    countries      : Countries to plot; defaults to first TOP_N from DEFAULT_COUNTRY_ORDER
    rolling_window : Window size in days; defaults to config.ROLLING_WINDOW
    """
    from config import TOP_N_COUNTRIES
    rolling_window = rolling_window if rolling_window is not None else ROLLING_WINDOW

    if countries is None:
        # Use countries present in df that are in the default order list
        available = [c for c in DEFAULT_COUNTRY_ORDER if c in df_ts["country"].unique()]
        countries = available[:TOP_N_COUNTRIES] or list(df_ts["country"].unique())[:TOP_N_COUNTRIES]

    cmap = country_colors(countries)

    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    fig.suptitle(
        f"COVID-19 Daily Trends ({rolling_window}-day Rolling Average)",
        fontsize=16, fontweight="bold", y=0.98,
    )

    for country in countries:
        sub = df_ts[df_ts["country"] == country].copy().sort_values("date")
        sub["rolling_cases"]  = sub["new_cases"].rolling(rolling_window).mean()
        sub["rolling_deaths"] = sub["new_deaths"].rolling(rolling_window).mean()
        color = cmap.get(country, "gray")
        axes[0].plot(sub["date"], sub["rolling_cases"],  label=country,
                     color=color, linewidth=2, alpha=0.9)
        axes[1].plot(sub["date"], sub["rolling_deaths"], label=country,
                     color=color, linewidth=2, alpha=0.9)

    axes[0].set_ylabel("New Cases",  fontsize=12)
    axes[0].legend(loc="upper right", fontsize=9, ncol=max(1, len(countries) // 5))
    axes[0].yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))

    axes[1].set_ylabel("New Deaths", fontsize=12)
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    axes[1].xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(axes[1].xaxis.get_majorticklabels(), rotation=45, ha="right")

    for ax in axes:
        ax.grid(True, alpha=0.4)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    fig.tight_layout()
    out = OUTPUT_DIR / "1_line_daily_trends.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"  Saved: {out}")
    return fig


# ── Chart 2: Vaccination bar ──────────────────────────────────────────────────

def plot_vaccination_bar(df_vax: pd.DataFrame) -> Figure:
    """
    Stacked bar chart: vaccination share by vaccine type per country.
    Side-by-side with a horizontal bar of total rate per country.
    """
    countries_in_data = list(df_vax["country"].unique())
    cmap = country_colors(countries_in_data)

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle("COVID-19 Vaccination Analysis by Country",
                 fontsize=16, fontweight="bold")

    pivot = df_vax.pivot_table(
        index="country", columns="vaccine",
        values="vaccinated_pct", aggfunc="sum",
    )
    pivot.plot(kind="bar", stacked=True, ax=axes[0],
               colormap="Set2", edgecolor="white", linewidth=0.5)
    axes[0].set_title("Vaccination % by Vaccine Type", fontsize=13)
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Population Vaccinated (%)", fontsize=11)
    axes[0].tick_params(axis="x", rotation=35)
    axes[0].legend(title="Vaccine", fontsize=9, title_fontsize=10)
    axes[0].spines["top"].set_visible(False)
    axes[0].spines["right"].set_visible(False)

    total_vax      = df_vax.groupby("country")["vaccinated_pct"].sum().sort_values()
    colors_sorted  = [cmap.get(c, "gray") for c in total_vax.index]
    bars           = axes[1].barh(
        total_vax.index, total_vax.values,
        color=colors_sorted, edgecolor="white", height=0.65,
    )
    for bar, val in zip(bars, total_vax.values):
        axes[1].text(
            bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}%", va="center", fontsize=9, fontweight="bold",
        )
    axes[1].set_title("Total Vaccination Rate per Country", fontsize=13)
    axes[1].set_xlabel("Population Vaccinated (%)", fontsize=11)
    axes[1].set_xlim(0, max(total_vax.values) * 1.15)
    axes[1].spines["top"].set_visible(False)
    axes[1].spines["right"].set_visible(False)

    fig.tight_layout()
    out = OUTPUT_DIR / "2_bar_vaccination.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"  Saved: {out}")
    return fig


# ── Chart 3: Heatmaps ─────────────────────────────────────────────────────────

def plot_heatmaps(df_ts: pd.DataFrame, df_age: pd.DataFrame) -> Figure:
    """
    Two heatmaps:
      (a) Monthly new cases per country (intensity calendar)
      (b) Case severity (%) by age group
    """
    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    fig.suptitle("COVID-19 Heatmap Analysis", fontsize=16, fontweight="bold")

    # (a) Monthly cases heatmap
    df_monthly = df_ts.copy()
    df_monthly["month"] = df_monthly["date"].dt.to_period("M").astype(str)
    monthly = (
        df_monthly
        .groupby(["country", "month"])["new_cases"]
        .sum()
        .unstack("month")
        .fillna(0)
    )
    # Show every 3rd x-label to avoid crowding
    col_labels = [c if i % 3 == 0 else "" for i, c in enumerate(monthly.columns)]
    sns.heatmap(
        monthly / 1_000, ax=axes[0], cmap="YlOrRd",
        linewidths=0.3, linecolor="white",
        cbar_kws={"label": "New Cases (thousands)"},
        xticklabels=col_labels, yticklabels=True,
    )
    axes[0].set_title("Monthly New Cases by Country", fontsize=13)
    axes[0].set_xlabel("Month", fontsize=11)
    axes[0].set_ylabel("Country", fontsize=11)
    axes[0].tick_params(axis="x", rotation=60, labelsize=8)

    # (b) Severity heatmap
    severity_matrix = df_age.set_index("age_group")[["mild", "severe", "critical"]]
    severity_pct    = severity_matrix.div(severity_matrix.sum(axis=1), axis=0) * 100
    sns.heatmap(
        severity_pct, ax=axes[1], cmap="RdYlGn_r",
        annot=True, fmt=".1f", linewidths=0.5,
        cbar_kws={"label": "% of Cases"},
        annot_kws={"size": 12, "weight": "bold"},
    )
    axes[1].set_title("Case Severity Distribution by Age Group (%)", fontsize=13)
    axes[1].set_xlabel("Severity Level", fontsize=11)
    axes[1].set_ylabel("Age Group", fontsize=11)
    axes[1].tick_params(axis="x", rotation=0)

    fig.tight_layout()
    out = OUTPUT_DIR / "3_heatmap.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"  Saved: {out}")
    return fig


# ── Chart 4: Scatter / correlation grid ──────────────────────────────────────

def plot_scatter_analysis(df_corr: pd.DataFrame) -> Figure:
    """
    2×2 scatter grid exploring correlations between health/economic metrics.
    Bubble size = population; colour = country (dynamic palette).
    """
    countries_in_data = list(df_corr["country"])
    cmap   = country_colors(countries_in_data)
    colors = [cmap.get(c, "gray") for c in df_corr["country"]]
    bubble = (df_corr["population"] / df_corr["population"].max()) * 800 + 80

    plots = [
        ("vaccination_rate",  "deaths_per_million",
         "Vaccination Rate (%)",  "Deaths per Million",
         "Vaccination vs. Deaths per Million"),
        ("gdp_per_capita",    "vaccination_rate",
         "GDP per Capita (USD)",  "Vaccination Rate (%)",
         "GDP per Capita vs. Vaccination Rate"),
        ("healthcare_index",  "cases_per_million",
         "Healthcare Index",      "Cases per Million",
         "Healthcare Index vs. Cases per Million"),
        ("gdp_per_capita",    "deaths_per_million",
         "GDP per Capita (USD)",  "Deaths per Million",
         "GDP per Capita vs. Deaths per Million"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle("COVID-19 Country-Level Correlation Analysis",
                 fontsize=16, fontweight="bold")

    for ax, (x, y, xlabel, ylabel, title) in zip(axes.flat, plots):
        ax.scatter(
            df_corr[x], df_corr[y],
            s=bubble, c=colors, alpha=0.82,
            edgecolors="white", linewidths=1.5, zorder=3,
        )
        # Regression line
        m, b   = np.polyfit(df_corr[x], df_corr[y], 1)
        xline  = np.linspace(df_corr[x].min(), df_corr[x].max(), 100)
        ax.plot(xline, m * xline + b, color="gray", linewidth=1.5,
                linestyle="--", alpha=0.7, zorder=2)

        # Country labels (skip if too many countries)
        if len(df_corr) <= 20:
            for _, row in df_corr.iterrows():
                ax.annotate(
                    row["country"], (row[x], row[y]),
                    textcoords="offset points", xytext=(6, 4),
                    fontsize=7, color="#333333", alpha=0.90,
                )

        # Pearson r badge
        corr = df_corr[[x, y]].corr().iloc[0, 1]
        ax.text(
            0.05, 0.95, f"r = {corr:.2f}", transform=ax.transAxes,
            fontsize=10, verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.75),
        )

        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, alpha=0.3)

    fig.tight_layout()
    out = OUTPUT_DIR / "4_scatter_correlations.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"  Saved: {out}")
    return fig
