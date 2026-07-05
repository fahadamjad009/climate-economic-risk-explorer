# Climate-Economic Risk Explorer

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-ML-orange)
![License](https://img.shields.io/badge/License-MIT-green)

An interactive risk-analytics platform combining 10 years of weather data, GDP/population figures, and climate disaster records across 30 global cities — with machine learning models for heat-anomaly detection, disaster damage risk classification, and temperature trend forecasting.

**[Live app](#)** &nbsp;|&nbsp; Built with Python, DuckDB, XGBoost, statsmodels, Streamlit, pydeck

---

## What it does

- **Global risk map** — 30 cities, bubble-sized by disaster damage, colored by average temperature, rendered with pydeck/deck.gl for smooth zoom and pan
- **Temperature forecasting** — ETS (Holt-Winters) models per city, forecasting 2 years ahead with automatic plausibility checks
- **Live ML risk scoring** — two XGBoost classifiers scored in real time (not pre-cached) for the selected city: extreme-heat-day risk and high-damage-year probability
- **EDA suite** — climate distribution boxplots, correlation heatmap, damage treemap by country/city
- **Policy risk matrix** — probability (heat frequency) x impact (damage-to-GDP) quadrant chart identifying where climate-adaptation investment has the highest marginal value
- **Humanitarian exposure view** — people affected vs. deaths per city, for disaster-response prioritization
- **Dynamically generated findings** — the closing policy narrative is computed from the live data, not hand-written, so it stays accurate if the underlying data changes

## Data sources

| Source | What | Coverage |
|---|---|---|
| [Open-Meteo](https://open-meteo.com/) | Daily weather (temp, precipitation, wind) | 30 cities, 2016-2025 |
| [World Bank API](https://data.worldbank.org/) | GDP, population | 25 countries, 2016-2025 |
| [EM-DAT](https://www.emdat.be/) (via [HDX](https://data.humdata.org/)) | Disaster events, deaths, damage | Climatological/meteorological/hydrological events only |

## Modeling approach and honest limitations

**Temperature forecasting (ETS / Holt-Winters):** fit on monthly-aggregated data with damped trend, validated across all 30 cities with an automatic sanity check against historical range. Originally built with Prophet, but abandoned after an unresolved Windows-specific binary crash (CmdStan/TBB compatibility issue) - statsmodels' ETS is the more classically rigorous choice for this kind of seasonal-decomposition problem anyway.

**Disaster damage modeling:** this is the part worth being upfront about. Two regression attempts - raw-dollar damage (R2 = 0.25) and damage-as-%-of-GDP (R2 = 0.12) - both performed weakly and badly underestimated the largest loss events (e.g. a $250B actual year predicted at $2.6B). This isn't a bug: catastrophic disaster losses are driven by **discrete events** (a hurricane landfall, a specific flood), not smooth yearly climate trends, so yearly aggregate features have limited power to predict exact dollar figures - a well-known limitation in catastrophe modeling generally.

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
