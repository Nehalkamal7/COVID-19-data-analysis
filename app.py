"""
app.py
COVID-19 Dashboard — Flask Web Server
Run: python app.py  →  open http://localhost:5000
"""

import warnings
warnings.filterwarnings("ignore")

import os
import io
import base64
from pathlib import Path
from flask import Flask, render_template, jsonify, send_from_directory

import config
from config import (
    RANDOM_SEED,
    TIME_SERIES_START,
    TIME_SERIES_PERIODS,
    FLASK_PORT,
    FLASK_DEBUG,
    ROLLING_WINDOW,
    TOP_N_COUNTRIES,
    COUNTRIES,
    VACCINES,
    AGE_GROUPS,
    time_series_csv_path,
    as_dict as config_as_dict,
)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

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

app = Flask(__name__)
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Generate all data once on startup ────────────────────────────────────────
print("Generating datasets...")
set_random_seed()
DF_TS, TIME_SERIES_SOURCE = resolve_time_series()
DF_VAX  = generate_vaccination_data()
DF_AGE  = generate_age_severity_data()
DF_CORR = generate_correlation_data()

csv_path = time_series_csv_path()
print(f"   Time series : {TIME_SERIES_SOURCE}"
      + (f" ({csv_path})" if csv_path else ""))
print(f"   Countries   : {DF_TS['country'].nunique()}")
print(f"   Days tracked: {DF_TS['date'].nunique()}")

# ── Pre-render charts to disk ─────────────────────────────────────────────────
print("Rendering charts...")
for fig_fn, kwargs in [
    (plot_daily_cases_line, {"df_ts": DF_TS}),
    (plot_vaccination_bar,  {"df_vax": DF_VAX}),
    (plot_heatmaps,         {"df_ts": DF_TS, "df_age": DF_AGE}),
    (plot_scatter_analysis, {"df_corr": DF_CORR}),
]:
    fig = fig_fn(**kwargs)
    plt.close(fig)
print("Ready.\n")


# ── Helpers ───────────────────────────────────────────────────────────────────
def fig_to_b64(fig) -> str:
    """Convert a matplotlib figure to a base64-encoded PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/output/<path:filename>")
def serve_chart(filename):
    return send_from_directory(OUTPUT_DIR, filename)


# ---------- data endpoints ----------

@app.route("/api/stats")
def api_stats():
    """Country-level totals for the stats table."""
    total = DF_TS.groupby("country")[["new_cases", "new_deaths"]].sum().reset_index()
    total["cfr"]        = (total["new_deaths"] / total["new_cases"].replace(0, 1) * 100).round(2)
    total["new_cases"]  = total["new_cases"].astype(int)
    total["new_deaths"] = total["new_deaths"].astype(int)
    return jsonify(total.to_dict(orient="records"))


@app.route("/api/vaccination")
def api_vaccination():
    """Total vaccination rate per country (sorted descending)."""
    vax = (
        DF_VAX.groupby("country")["vaccinated_pct"]
        .sum()
        .round(1)
        .reset_index()
        .rename(columns={"vaccinated_pct": "rate"})
        .sort_values("rate", ascending=False)
    )
    return jsonify(vax.to_dict(orient="records"))


@app.route("/api/age")
def api_age():
    """Age-group severity breakdown."""
    return jsonify(DF_AGE.to_dict(orient="records"))


@app.route("/api/timeline")
def api_timeline():
    """
    Weekly rolling average for sparklines (USA first, then first available country).
    Keeps payload small by returning a single country.
    """
    target = "USA" if "USA" in DF_TS["country"].unique() else DF_TS["country"].iloc[0]
    sub = DF_TS[DF_TS["country"] == target].copy().sort_values("date")
    sub["rolling"] = sub["new_cases"].rolling(ROLLING_WINDOW).mean().fillna(0).astype(int)
    data = sub[["date", "rolling"]].copy()
    data["date"] = data["date"].dt.strftime("%Y-%m-%d")
    return jsonify({"country": target, "data": data.to_dict(orient="records")})


@app.route("/api/summary")
def api_summary():
    """High-level KPIs for the hero cards."""
    total_cases   = int(DF_TS["new_cases"].sum())
    total_deaths  = int(DF_TS["new_deaths"].sum())
    peak_day      = int(DF_TS.groupby("date")["new_cases"].sum().max())
    vax_by_country = DF_VAX.groupby("country")["vaccinated_pct"].sum()
    best_vax       = vax_by_country.idxmax() if not vax_by_country.empty else "N/A"
    return jsonify({
        "total_cases":   total_cases,
        "total_deaths":  total_deaths,
        "peak_day":      peak_day,
        "best_vax":      best_vax,
        "countries":     int(DF_TS["country"].nunique()),
        "days_tracked":  int(DF_TS["date"].nunique()),
    })


@app.route("/api/config")
def api_config():
    """
    Expose all runtime configuration values so the frontend (or any API client)
    can understand exactly how the current dataset was generated.

    Returns a JSON object with keys:
      random_seed, time_series_start, time_series_periods,
      flask_port, flask_debug, rolling_window, top_n_countries,
      countries, vaccines, age_groups,
      time_series_csv, time_series_source
    """
    cfg = config_as_dict()
    # Augment with live dataset stats
    cfg["dataset_stats"] = {
        "total_rows":      len(DF_TS),
        "countries_loaded": int(DF_TS["country"].nunique()),
        "days_loaded":      int(DF_TS["date"].nunique()),
        "date_range": {
            "start": str(DF_TS["date"].min().date()),
            "end":   str(DF_TS["date"].max().date()),
        },
        "vaccination_rows": len(DF_VAX),
        "time_series_source": TIME_SERIES_SOURCE,
    }
    return jsonify(cfg)


@app.route("/api/countries")
def api_countries():
    """List of countries present in the loaded dataset."""
    countries = sorted(DF_TS["country"].unique().tolist())
    return jsonify({"countries": countries, "count": len(countries)})


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Dashboard: http://localhost:{FLASK_PORT}\n")
    app.run(debug=FLASK_DEBUG, port=FLASK_PORT)
