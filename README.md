# Climate-Economic Risk Explorer

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-ML-orange)
![License](https://img.shields.io/badge/License-MIT-green)

An interactive risk-analytics platform combining 10 years of weather data, GDP/population figures, and climate disaster records across 30 global cities — with machine learning models for heat-anomaly detection, disaster damage risk classification, and temperature trend forecasting.

**[Live app - Streamlit](https://climate-economic-risk-explorer.streamlit.app)** &nbsp;|&nbsp; **[Live app - React](https://fahadamjad009.github.io/climate-economic-risk-explorer/)** &nbsp;|&nbsp; Built with Python, DuckDB, XGBoost, statsmodels, Streamlit, pydeck, React, Vite

---

## Architecture

```
                    ┌─────────────────┐   ┌──────────────────┐   ┌─────────────────┐
                    │   Open-Meteo    │   │   World Bank     │   │  EM-DAT (HDX)   │
                    │  Weather API    │   │      API         │   │  Disaster Data  │
                    │  30 cities      │   │  25 countries    │   │  XLSX export    │
                    │  2016-2025      │   │  GDP, population │   │  6,509 events    │
                    └────────┬────────┘   └────────┬─────────┘   └────────┬────────┘
                             │                     │                      │
                             ▼                     ▼                      ▼
                    ┌─────────────────────────────────────────────────────────────┐
                    │                    INGESTION LAYER (src/)                  │
                    │  fetch_weather.py · fetch_worldbank.py · load_emdat.py     │
                    │  retry/backoff, idempotent caching, HXL-row stripping,     │
                    │  leave-one-year-out climatology                            │
                    └──────────────────────────┬──────────────────────────────────┘
                                                ▼
                    ┌─────────────────────────────────────────────────────────────┐
                    │                  climate.duckdb (3 MB)                     │
                    │  weather_daily (109,590 rows) · worldbank · emdat_disasters │
                    │  city_year_features (300 rows: 30 cities x 10 years)       │
                    └──────────────────────────┬──────────────────────────────────┘
                                                ▼
                    ┌─────────────────────────────────────────────────────────────┐
                    │                     ML LAYER (src/)                         │
                    │  ┌───────────────┐  ┌────────────────┐  ┌─────────────────┐ │
                    │  │ ETS/Holt-     │  │ XGBoost         │  │ XGBoost         │ │
                    │  │ Winters       │  │ High-Risk-Year  │  │ Heat-Anomaly    │ │
                    │  │ (statsmodels) │  │ Classifier      │  │ Classifier      │ │
                    │  │ per-city      │  │ ROC-AUC 0.754   │  │ ROC-AUC 0.898   │ │
                    │  │ temp forecast │  │                 │  │                 │ │
                    │  └───────────────┘  └────────────────┘  └─────────────────┘ │
                    └──────────────────────────┬──────────────────────────────────┘
                                                ▼
                    ┌─────────────────────────────────────────────────────────────┐
                    │              Streamlit App (app/app.py)                    │
                    │  pydeck globe · live model scoring · EDA · risk matrix     │
                    │  humanitarian view · dynamically-generated policy findings  │
                    └─────────────────────────────────────────────────────────────┘
```

## Repository structure

```
climate-economic-risk-explorer/
├── app/
│   └── app.py                      Streamlit app - single scrolling page, dark theme
├── src/
│   ├── cities.py                   30-city reference list (name, country, lat, lon)
│   ├── fetch_weather.py            Open-Meteo ingestion, retry/backoff, per-city cache
│   ├── fetch_worldbank.py          World Bank GDP/population, per-country cache
│   ├── load_emdat.py               EM-DAT cleaning: HXL-row strip, country/year filter
│   ├── build_duckdb.py             Consolidates weather parquet -> climate.duckdb
│   ├── build_features.py           Joins weather + GDP + disasters -> city_year_features
│   ├── build_ets_forecasts.py      Fits ETS model per city, stores forecasts
│   ├── train_damage_model_v2.py    XGBoost: damage-to-GDP regression + risk classifier
│   └── train_heat_anomaly_model.py XGBoost: day-level extreme heat classifier
├── data/
│   ├── climate.duckdb               Consolidated database (weather, econ, disasters, features)
│   ├── *.json                       Trained model artifacts (4 models)
│   └── worldbank.parquet            Cached World Bank data
├── requirements.txt
├── LICENSE                          MIT
└── README.md
```

## What it does

| Section | Visualization | Business/policy purpose |
|---|---|---|
| Global Overview | pydeck (deck.gl) interactive globe | Spot which cities combine high heat exposure with high dollar damage at a glance |
| Temperature Trend & Forecast | Line chart + ETS 2-year forecast | Shows whether a city's warming is accelerating, flat, or reversing |
| Live Risk Score | Real-time XGBoost inference | Answers "is this city at elevated risk right now" - not a cached number |
| Disaster Damage: Top 10 | Horizontal bar chart | Identifies where absolute dollar exposure concentrates |
| Climate Distributions | Boxplots per city | Compares climate volatility/spread, not just averages, across cities |
| What Drives Disaster Damage | Correlation heatmap | Surfaces which factors (heat days, rainfall, GDP, population) actually associate with losses |
| Where the Damage Concentrates | Treemap (country -> city) | Visualizes exposure concentration for portfolio/reinsurance-style thinking |
| Climate Risk Matrix | Quadrant scatter (probability x impact) | Classic risk-management framing: prioritizes where adaptation investment has the highest marginal value |
| Humanitarian Exposure | Log-scale scatter (affected vs. deaths) | Prioritizes disaster-response and early-warning funding by human cost, not just dollars |
| Key Findings | Dynamically-generated text | Turns the charts above into a stated recommendation, computed live from the data |

## Data sources

| Source | What | Coverage |
|---|---|---|
| [Open-Meteo](https://open-meteo.com/) | Daily weather (temp, precipitation, wind) | 30 cities, 2016-2025 |
| [World Bank API](https://data.worldbank.org/) | GDP, population | 25 countries, 2016-2025 |
| [EM-DAT](https://www.emdat.be/) (via [HDX](https://data.humdata.org/)) | Disaster events, deaths, damage | Climatological/meteorological/hydrological events only |

## Model performance summary

| Model | Type | Target | Result | Notes |
|---|---|---|---|---|
| ETS / Holt-Winters | Time series (statsmodels) | Monthly avg temp, 2yr forecast | Validated on all 30 cities, 0 flagged implausible | Damped trend; monthly aggregation (daily/365-period was numerically unstable) |
| Damage regression (raw $) | XGBoost Regressor | log1p(disaster damage USD) | R² = 0.25 | Badly underestimates largest events - catastrophic losses are event-driven, not trend-driven |
| Damage regression (%GDP) | XGBoost Regressor | log1p(damage / GDP) | R² = 0.12 | Worse than raw-$ - ratio amplifies noise for small economies |
| **High-risk-year classifier** | XGBoost Classifier | Top-quartile damage/GDP year | **ROC-AUC = 0.754**, 82% accuracy | The model actually used in the app - reframing as classification is more robust than regression here |
| **Heat-anomaly classifier** | XGBoost Classifier | Extreme heat day (z >= 2, leave-one-year-out climatology) | **ROC-AUC = 0.898**, recall = 0.83 | Tuned for high recall over precision - a heat-warning tool should over-flag, not miss dangerous days |

## Modeling approach and honest limitations

**Temperature forecasting (ETS / Holt-Winters):** fit on monthly-aggregated data with damped trend, validated across all 30 cities with an automatic sanity check against historical range. Originally built with Prophet, but abandoned after an unresolved Windows-specific binary crash (CmdStan/TBB compatibility issue) - statsmodels' ETS is the more classically rigorous choice for this kind of seasonal-decomposition problem anyway.

**Disaster damage modeling:** this is the part worth being upfront about. Two regression attempts - raw-dollar damage (R² = 0.25) and damage-as-%-of-GDP (R² = 0.12) - both performed weakly and badly underestimated the largest loss events (e.g. a $250B actual year predicted at $2.6B). This isn't a bug: catastrophic disaster losses are driven by **discrete events** (a hurricane landfall, a specific flood), not smooth yearly climate trends, so yearly aggregate features have limited power to predict exact dollar figures - a well-known limitation in catastrophe modeling generally.

Reframing the problem as **binary high-risk-year classification** (top-quartile damage-to-GDP years) produced a far more robust and actionable result: **ROC-AUC 0.754**, 82% accuracy. This is the model actually used in the app, framed as a risk-screening tool rather than a precise forecaster - consistent with how real catastrophe risk models are used in practice.

**Extreme heat anomaly detection:** day-level XGBoost classifier (109K+ rows) predicting whether a day will exceed 2 standard deviations above that city's leave-one-year-out climatological normal, using only lagged/trailing features (no same-day leakage). **ROC-AUC 0.898**, recall 0.83 for the extreme-heat class - tuned deliberately for high recall over precision, since a heat-warning tool should over-flag rather than miss dangerous days.

## Tech stack

Python, DuckDB, pandas, XGBoost, statsmodels, Streamlit, Plotly, pydeck (deck.gl), Open-Meteo API, World Bank API, EM-DAT/HDX

## Running locally

```bash
python -m venv venv
venv\Scripts\Activate.ps1        # Windows
pip install -r requirements.txt
streamlit run app/app.py
```

Data pipeline (run once, in order, if rebuilding from scratch):

```bash
python src/fetch_weather.py
python src/fetch_worldbank.py
python src/load_emdat.py
python src/build_duckdb.py
python src/build_features.py
python src/build_ets_forecasts.py
python src/train_damage_model_v2.py
python src/train_heat_anomaly_model.py
```

## License

MIT - see [LICENSE](LICENSE).
