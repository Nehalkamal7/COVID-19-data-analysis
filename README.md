# COVID-19 Analytics Dashboard

A small Python project that generates **synthetic** COVID-style epidemiological data, runs statistical summaries, renders Matplotlib charts, and serves an interactive **Flask** dashboard in the browser.

> **Note:** All figures and metrics are based on simulated data for learning and visualization—not real outbreak statistics.

## Features

- **Synthetic datasets** — Multi-country daily cases/deaths, vaccination uptake by vaccine type, age vs. severity, and correlation-style country metrics (`data_generator.py`).
- **CLI pipeline** — Run `main.py` to print summaries and save PNG charts under `./output/`.
- **Web dashboard** — Run `app.py` for a dark-themed UI with KPI cards, charts, tables, and sparklines fed by JSON APIs.
- **Analysis** — Console summaries (totals, peaks, vaccination bars, etc.) via `analysis.py`.

## Tech stack

Python **3.10+** recommended · **Flask** · **pandas** · **NumPy** · **Matplotlib** · **Seaborn**

## Setup

1. **Clone the repository** (or download the project folder).

2. **Create a virtual environment** (optional but recommended):

   ```bash
   python -m venv .venv
