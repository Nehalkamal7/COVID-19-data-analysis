import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path

sns.set_theme(style="darkgrid", palette="muted")
PALETTE = sns.color_palette("tab10")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

COUNTRY_COLORS = {
    c: PALETTE[i] for i, c in enumerate(
        ["USA", "India", "Brazil", "UK", "Germany", "France", "Italy", "Spain"]
    )
}


def plot_daily_cases_line(df_ts: pd.DataFrame, countries: list[str] | None = None,
                          rolling_window: int = 7) -> Figure:
    """
    Line chart: 7-day rolling average of new daily cases for selected countries.
    """
    if countries is None:
        countries = ["USA", "India", "Brazil", "UK", "Germany"]

    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    fig.suptitle("COVID-19 Daily Trends (7-day Rolling Average)",
                 fontsize=16, fontweight="bold", y=0.98)

    for country in countries:
        sub = df_ts[df_ts["country"] == country].copy()
        sub["rolling_cases"] = sub["new_cases"].rolling(rolling_window).mean()
        sub["rolling_deaths"] = sub["new_deaths"].rolling(rolling_window).mean()
        color = COUNTRY_COLORS.get(country, "gray")
        axes[0].plot(sub["date"], sub["rolling_cases"], label=country,
                     color=color, linewidth=2)
        axes[1].plot(sub["date"], sub["rolling_deaths"], label=country,
                     color=color, linewidth=2)

    axes[0].set_ylabel("New Cases", fontsize=12)
    axes[0].legend(loc="upper right", fontsize=10)
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
    fig.savefig(OUTPUT_DIR / "1_line_daily_trends.png", dpi=150, bbox_inches="tight")
    print("  ✓ Saved: output/1_line_daily_trends.png")
    return fig


def plot_vaccination_bar(df_vax: pd.DataFrame) -> Figure:
    """
    Stacked bar chart: Vaccination share by vaccine type per country.
    Side-by-side comparison of total vaccination rates.
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle("COVID-19 Vaccination Analysis by Country",
                 fontsize=16, fontweight="bold")

    pivot = df_vax.pivot_table(index="country", columns="vaccine",
                               values="vaccinated_pct", aggfunc="sum")
    pivot.plot(kind="bar", stacked=True, ax=axes[0],
               colormap="Set2", edgecolor="white", linewidth=0.5)
    axes[0].set_title("Vaccination % by Vaccine Type", fontsize=13)
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Population Vaccinated (%)", fontsize=11)
    axes[0].tick_params(axis="x", rotation=30)
    axes[0].legend(title="Vaccine", fontsize=9, title_fontsize=10)
    axes[0].spines["top"].set_visible(False)
    axes[0].spines["right"].set_visible(False)

    total_vax = df_vax.groupby("country")["vaccinated_pct"].sum().sort_values()
    colors_sorted = [COUNTRY_COLORS[c] for c in total_vax.index]
    bars = axes[1].barh(total_vax.index, total_vax.values,
                        color=colors_sorted, edgecolor="white", height=0.6)
    for bar, val in zip(bars, total_vax.values):
        axes[1].text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                     f"{val:.1f}%", va="center", fontsize=10, fontweight="bold")
    axes[1].set_title("Total Vaccination Rate per Country", fontsize=13)
    axes[1].set_xlabel("Population Vaccinated (%)", fontsize=11)
    axes[1].set_xlim(0, max(total_vax.values) * 1.12)
    axes[1].spines["top"].set_visible(False)
    axes[1].spines["right"].set_visible(False)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "2_bar_vaccination.png", dpi=150, bbox_inches="tight")
    print("  ✓ Saved: output/2_bar_vaccination.png")
    return fig


def plot_heatmaps(df_ts: pd.DataFrame, df_age: pd.DataFrame) -> Figure:
    """
    Two heatmaps:
      (a) Monthly new cases per country (intensity calendar)
      (b) Case severity by age group
    """
    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    fig.suptitle("COVID-19 Heatmap Analysis", fontsize=16, fontweight="bold")

    df_monthly = df_ts.copy()
    df_monthly["month"] = df_monthly["date"].dt.to_period("M").astype(str)
    monthly = (df_monthly.groupby(["country", "month"])["new_cases"]
               .sum()
               .unstack("month")
               .fillna(0))

    col_labels = [c if i % 3 == 0 else "" for i, c in enumerate(monthly.columns)]

    sns.heatmap(monthly / 1_000, ax=axes[0], cmap="YlOrRd",
                linewidths=0.3, linecolor="white",
                cbar_kws={"label": "New Cases (thousands)"},
                xticklabels=col_labels, yticklabels=True)
    axes[0].set_title("Monthly New Cases by Country", fontsize=13)
    axes[0].set_xlabel("Month", fontsize=11)
    axes[0].set_ylabel("Country", fontsize=11)
    axes[0].tick_params(axis="x", rotation=60, labelsize=8)

    severity_matrix = df_age.set_index("age_group")[["mild", "severe", "critical"]]
    severity_pct = severity_matrix.div(severity_matrix.sum(axis=1), axis=0) * 100

    sns.heatmap(severity_pct, ax=axes[1], cmap="RdYlGn_r",
                annot=True, fmt=".1f", linewidths=0.5,
                cbar_kws={"label": "% of Cases"},
                annot_kws={"size": 12, "weight": "bold"})
    axes[1].set_title("Case Severity Distribution by Age Group (%)", fontsize=13)
    axes[1].set_xlabel("Severity Level", fontsize=11)
    axes[1].set_ylabel("Age Group", fontsize=11)
    axes[1].tick_params(axis="x", rotation=0)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "3_heatmap.png", dpi=150, bbox_inches="tight")
    print("  ✓ Saved: output/3_heatmap.png")
    return fig


def plot_scatter_analysis(df_corr: pd.DataFrame) -> Figure:
    """
    2×2 scatter grid exploring correlations between health/economic metrics.
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle("COVID-19 Country-Level Correlation Analysis",
                 fontsize=16, fontweight="bold")


    bubble = (df_corr["population"] / df_corr["population"].max()) * 800 + 100
    colors = [COUNTRY_COLORS[c] for c in df_corr["country"]]

    plots = [
        ("vaccination_rate", "deaths_per_million",
         "Vaccination Rate (%)", "Deaths per Million",
         "Vaccination vs. Deaths per Million"),
        ("gdp_per_capita", "vaccination_rate",
         "GDP per Capita (USD)", "Vaccination Rate (%)",
         "GDP per Capita vs. Vaccination Rate"),
        ("healthcare_index", "cases_per_million",
         "Healthcare Index", "Cases per Million",
         "Healthcare Index vs. Cases per Million"),
        ("gdp_per_capita", "deaths_per_million",
         "GDP per Capita (USD)", "Deaths per Million",
         "GDP per Capita vs. Deaths per Million"),
    ]

    for ax, (x, y, xlabel, ylabel, title) in zip(axes.flat, plots):
        sc = ax.scatter(df_corr[x], df_corr[y],
                        s=bubble, c=colors, alpha=0.80, edgecolors="white",
                        linewidths=1.5, zorder=3)
        # Regression line
        m, b = np.polyfit(df_corr[x], df_corr[y], 1)
        xline = np.linspace(df_corr[x].min(), df_corr[x].max(), 100)
        ax.plot(xline, m * xline + b, color="gray", linewidth=1.5,
                linestyle="--", alpha=0.7, zorder=2)

        # Country labels
        for _, row in df_corr.iterrows():
            ax.annotate(row["country"], (row[x], row[y]),
                        textcoords="offset points", xytext=(6, 4),
                        fontsize=8, color="black", alpha=0.85)

        # Correlation coefficient
        corr = df_corr[[x, y]].corr().iloc[0, 1]
        ax.text(0.05, 0.95, f"r = {corr:.2f}", transform=ax.transAxes,
                fontsize=10, verticalalignment="top",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))

        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "4_scatter_correlations.png", dpi=150, bbox_inches="tight")
    print("  ✓ Saved: output/4_scatter_correlations.png")
    return fig
