🦠 COVID-19 Analytics Dashboard
A full-stack Python project that generates realistic COVID-19 epidemiological datasets, runs statistical analysis, renders publication-quality charts, and serves an interactive Flask web dashboard — all configurable via environment variables with zero code changes.

✨ Features
Feature	Description
📊 4 Chart Types	Line trends, stacked bar (vaccination), dual heatmaps, scatter correlation grid
🌍 20 Countries	USA, India, Brazil, UK, Germany, France, Italy, Spain, Canada, Japan + 10 more
💉 8 Vaccines	Pfizer, Moderna, AstraZeneca, J&J, Sinovac, Novavax, Sputnik V, Covaxin
📁 CSV Support	Drop your own data/time_series.csv — the app auto-detects and uses it
🎨 Dynamic Colors	Auto-scaling palette: tab10 → tab20 → HSL golden-angle (works for any N countries)
⚙️ Env-var config	Change every setting without touching source code
🌐 REST API	7 JSON endpoints powering the dashboard
🖥️ One-click launch	START_DASHBOARD.bat opens everything automatically (Windows)
📁 Project Structure
covid_project/
│
├── app.py               # Flask web server + all /api/* routes
├── main.py              # CLI pipeline (generate → analyse → charts)
├── config.py            # Central settings (env vars, helpers)
├── data_generator.py    # Synthetic + CSV data generators
├── visualizations.py    # All 4 Matplotlib/Seaborn chart functions
├── analysis.py          # Console statistical summaries
│
├── data/
│   ├── time_series.csv          # 14,600-row sample (20 countries × 730 days)
│   └── time_series.example.csv  # Minimal CSV format example
│
├── templates/
│   └── index.html       # Dark-themed dashboard UI
│
├── output/              # Auto-generated PNG charts land here
│   ├── 1_line_daily_trends.png
│   ├── 2_bar_vaccination.png
│   ├── 3_heatmap.png
│   └── 4_scatter_correlations.png
│
├── requirements.txt
└── START_DASHBOARD.bat  # Windows one-click launcher
🚀 Quick Start
Option A — Windows (One Click)
Double-click START_DASHBOARD.bat

It will:

Detect your Python installation
Install dependencies silently
Start the Flask server in a separate window
Open http://127.0.0.1:5000 in your browser automatically
Option B — Manual (any OS)
bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/covid_project.git
cd covid_project
# 2. Create & activate a virtual environment (recommended)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate
# 3. Install dependencies
pip install -r requirements.txt
# 4a. Run the web dashboard
python app.py
# → open http://localhost:5000
# 4b. OR run the CLI pipeline (saves charts to ./output/)
python main.py
🌐 API Endpoints
Endpoint	Method	Description
/	GET	Interactive web dashboard
/api/summary	GET	KPI hero cards (total cases, deaths, peak day, best vaccination)
/api/stats	GET	Country-level totals + Case Fatality Rate
/api/vaccination	GET	Total vaccination rate per country (sorted)
/api/age	GET	Case severity breakdown by age group
/api/timeline	GET	7-day rolling average sparkline data
/api/countries	GET	List of all loaded countries
/api/config	GET	Full runtime config + dataset statistics
/api/config example response
json
{
  "random_seed": 42,
  "time_series_start": "2020-01-01",
  "time_series_periods": 730,
  "rolling_window": 7,
  "top_n_countries": 6,
  "countries": ["USA", "India", "Brazil", "..."],
  "vaccines": ["Pfizer", "Moderna", "..."],
  "time_series_source": "csv",
  "dataset_stats": {
    "total_rows": 14600,
    "countries_loaded": 20,
    "days_loaded": 730,
    "date_range": { "start": "2020-01-01", "end": "2021-12-31" }
  }
}
⚙️ Configuration via Environment Variables
No code edits needed — just set env vars before running:

Variable	Default	Description
COVID_SEED	42	Random seed for reproducible synthetic data
COVID_START	2020-01-01	Time series start date (YYYY-MM-DD)
COVID_PERIODS	730	Number of days in synthetic series
COVID_TIME_SERIES_CSV	(auto-detect)	Explicit path to your CSV file
COVID_COUNTRIES	(20 built-in)	Comma-separated list to override countries
COVID_VACCINES	(8 built-in)	Comma-separated list to override vaccines
COVID_PORT	5000	Flask server port
COVID_DEBUG	1	Set to 0 to disable Flask debug mode
COVID_ROLLING_WINDOW	7	Rolling average window (days) for charts
COVID_TOP_N_COUNTRIES	6	Countries shown in the line trend chart
Examples:

bash
# Windows PowerShell
$env:COVID_COUNTRIES = "Egypt,Nigeria,South Africa,Kenya"
$env:COVID_ROLLING_WINDOW = "14"
python app.py
bash
# macOS / Linux
COVID_SEED=123 COVID_ROLLING_WINDOW=14 python app.py
📂 Bring Your Own Data (CSV)
Place a CSV at data/time_series.csv (or set $COVID_TIME_SERIES_CSV).

Required columns:

Column	Type	Example
date	YYYY-MM-DD	2020-03-15
country	string	Egypt
new_cases	integer	1250
new_deaths	integer	35
Optional columns (auto-computed if missing):

Column	Auto-computed as
new_recoveries	new_cases × 0.90
cumulative_cases	running sum per country
cumulative_deaths	running sum per country
See data/time_series.example.csv for a minimal working example.

📊 Charts Generated
#	File	Description
1	1_line_daily_trends.png	7-day rolling average of cases & deaths per country
2	2_bar_vaccination.png	Stacked vaccination % by type + total rate horizontal bar
3	3_heatmap.png	Monthly case intensity × country + severity by age group
4	4_scatter_correlations.png	2×2 correlation grid (GDP, healthcare, vaccination vs outcomes)
🛠️ Tech Stack
Library	Version	Use
Python	3.10+	Core language
Flask	≥ 3.0	Web server & REST API
pandas	≥ 2.0	Data wrangling
NumPy	≥ 1.24	Numerical generation
Matplotlib	≥ 3.7	Chart rendering
Seaborn	≥ 0.12	Heatmaps & theming
