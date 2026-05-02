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
import json
from pathlib import Path
from flask import Flask, render_template, jsonify, send_from_directory

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Import your existing modules
from data_generator import (
    generate_time_series, generate_vaccination_data,
    generate_age_severity_data, generate_correlation_data,
)
from visualizations import (
    plot_daily_cases_line, plot_vaccination_bar,
    plot_heatmaps, plot_scatter_analysis,
)

app = Flask(__name__)
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Generate all data once on startup ────────────────────────────────────────
print("⚙  Generating datasets...")
DF_TS   = generate_time_series(start="2020-01-01", periods=730)
DF_VAX  = generate_vaccination_data()
DF_AGE  = generate_age_severity_data()
DF_CORR = generate_correlation_data()

# ── Pre-render charts to disk ─────────────────────────────────────────────────
print("🎨 Rendering charts...")
for fig_fn, kwargs in [
    (plot_daily_cases_line, {"df_ts": DF_TS}),
    (plot_vaccination_bar,  {"df_vax": DF_VAX}),
    (plot_heatmaps,         {"df_ts": DF_TS, "df_age": DF_AGE}),
    (plot_scatter_analysis, {"df_corr": DF_CORR}),
]:
    fig = fig_fn(**kwargs)
    plt.close(fig)
print("✅ Ready!\n")


def fig_to_b64(fig):
    """Convert a matplotlib figure to a base64 PNG string."""
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


@app.route("/api/stats")
def api_stats():
    """Country-level totals for the stats table."""
    total = DF_TS.groupby("country")[["new_cases", "new_deaths"]].sum().reset_index()
    total["cfr"] = (total["new_deaths"] / total["new_cases"] * 100).round(2)
    total["new_cases"] = total["new_cases"].astype(int)
    total["new_deaths"] = total["new_deaths"].astype(int)
    return jsonify(total.to_dict(orient="records"))


@app.route("/api/vaccination")
def api_vaccination():
    vax = DF_VAX.groupby("country")["vaccinated_pct"].sum().round(1).reset_index()
    vax.columns = ["country", "rate"]
    return jsonify(vax.sort_values("rate", ascending=False).to_dict(orient="records"))


@app.route("/api/age")
def api_age():
    return jsonify(DF_AGE.to_dict(orient="records"))


@app.route("/api/timeline")
def api_timeline():
    """Weekly rolling average for sparklines (USA only, keep payload small)."""
    sub = DF_TS[DF_TS["country"] == "USA"].copy()
    sub["rolling"] = sub["new_cases"].rolling(7).mean().fillna(0).astype(int)
    data = sub[["date", "rolling"]].copy()
    data["date"] = data["date"].dt.strftime("%Y-%m-%d")
    return jsonify(data.to_dict(orient="records"))


@app.route("/api/summary")
def api_summary():
    total_cases  = int(DF_TS["new_cases"].sum())
    total_deaths = int(DF_TS["new_deaths"].sum())
    peak_day     = int(DF_TS.groupby("date")["new_cases"].sum().max())
    best_vax     = DF_VAX.groupby("country")["vaccinated_pct"].sum().idxmax()
    return jsonify({
        "total_cases":  total_cases,
        "total_deaths": total_deaths,
        "peak_day":     peak_day,
        "best_vax":     best_vax,
        "countries":    int(DF_TS["country"].nunique()),
        "days_tracked": int(DF_TS["date"].nunique()),
    })


if __name__ == "__main__":
    print("🌐  Dashboard → http://localhost:5000\n")
    app.run(debug=True, port=5000)
