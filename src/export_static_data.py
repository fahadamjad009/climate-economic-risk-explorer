"""
Export all data + model outputs needed by the React/JSX version of the app
into a single static JSON file. Run this once (or whenever the underlying
data/models change) - the JSX app reads this file directly, no backend needed.

Usage:
    python src/export_static_data.py
"""

import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import xgboost as xgb

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "climate.duckdb"
HEAT_MODEL_PATH = Path(__file__).resolve().parent.parent / "data" / "heat_anomaly_model.json"
RISK_MODEL_PATH = Path(__file__).resolve().parent.parent / "data" / "high_risk_model.json"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "static_export.json"


def score_heat_anomaly_risk(city, weather, locations, model):
    city_weather = weather[weather["city"] == city].copy()
    city_weather["date"] = pd.to_datetime(city_weather["date"])
    city_weather = city_weather.sort_values("date")

    last_date = city_weather["date"].max()
    next_day_of_year = (last_date + pd.Timedelta(days=1)).dayofyear

    lag1 = city_weather.iloc[-1]["temperature_2m_max"]
    lag2 = city_weather.iloc[-2]["temperature_2m_max"]
    trailing_3day = city_weather["temperature_2m_max"].tail(3).mean()
    trailing_7day_temp = city_weather["temperature_2m_max"].tail(7).mean()
    trailing_7day_precip = city_weather["precipitation_sum"].tail(7).mean()

    city_weather["day_of_year"] = city_weather["date"].dt.dayofyear
    climo_mean = city_weather[city_weather["day_of_year"] == next_day_of_year]["temperature_2m_max"].mean()

    loc_row = locations[locations["city"] == city].iloc[0]

    features = pd.DataFrame([{
        "lat": loc_row["lat"], "lon": loc_row["lon"],
        "day_of_year_sin": np.sin(2 * np.pi * next_day_of_year / 365.25),
        "day_of_year_cos": np.cos(2 * np.pi * next_day_of_year / 365.25),
        "lag1_temp_max": lag1, "lag2_temp_max": lag2,
        "trailing_3day_avg_temp": trailing_3day,
        "trailing_7day_avg_temp": trailing_7day_temp,
        "trailing_7day_avg_precip": trailing_7day_precip,
        "climo_mean": climo_mean,
    }])
    return float(model.predict_proba(features)[0, 1])


def score_high_risk_year(city, features_df, model):
    city_latest = features_df[features_df["city"] == city].sort_values("year").iloc[-1]
    feature_cols = [
        "avg_temp_c", "max_temp_c", "min_temp_c",
        "total_precip_mm", "max_daily_precip_mm",
        "days_over_35c", "heavy_rain_days", "avg_max_windspeed",
        "population",
    ]
    X = pd.DataFrame([city_latest[feature_cols]])
    return float(model.predict_proba(X)[0, 1])


def main():
    print("Loading data from climate.duckdb...")
    con = duckdb.connect(str(DB_PATH), read_only=True)
    features = con.execute("SELECT * FROM city_year_features").df()
    weather = con.execute("SELECT * FROM weather_daily").df()
    forecasts = con.execute("SELECT * FROM city_temp_forecasts").df()
    locations = con.execute("""
        SELECT DISTINCT city, country, lat, lon FROM weather_daily ORDER BY city
    """).df()
    con.close()

    print("Loading trained models...")
    heat_model = xgb.XGBClassifier()
    heat_model.load_model(str(HEAT_MODEL_PATH))
    risk_model = xgb.XGBClassifier()
    risk_model.load_model(str(RISK_MODEL_PATH))

    city_list = sorted(locations["city"].unique())
    print(f"Scoring live risk models for {len(city_list)} cities...")

    cities_data = []
    for i, city in enumerate(city_list, start=1):
        loc_row = locations[locations["city"] == city].iloc[0]
        city_features = features[features["city"] == city].sort_values("year")
        city_forecast = forecasts[forecasts["city"] == city]

        heat_risk = score_heat_anomaly_risk(city, weather, locations, heat_model)
        year_risk = score_high_risk_year(city, features, risk_model)

        city_weather = weather[weather["city"] == city].copy()
        city_weather["date"] = pd.to_datetime(city_weather["date"])
        city_weather["year"] = city_weather["date"].dt.year
        yearly_temp = city_weather.groupby("year")["temperature_2m_mean"].mean().reset_index()

        cities_data.append({
            "name": city,
            "country": loc_row["country"],
            "lat": float(loc_row["lat"]),
            "lon": float(loc_row["lon"]),
            "yearlyFeatures": city_features.drop(columns=["city", "country"]).to_dict(orient="records"),
            "yearlyAvgTemp": yearly_temp.to_dict(orient="records"),
            "forecast": {
                "avgTempForecastYear1": float(city_forecast["avg_temp_forecast_year1"].iloc[0]),
                "avgTempForecastYear2": float(city_forecast["avg_temp_forecast_year2"].iloc[0]),
                "warmingTrendCPerDecade": float(city_forecast["warming_trend_c_per_decade"].iloc[0]),
            } if not city_forecast.empty else None,
            "riskScores": {
                "heatAnomalyRisk": heat_risk,
                "highDamageYearProbability": year_risk,
            },
            "totalDisasterDamage": float(city_features["disaster_damage_usd"].sum()),
            "avgTempOverall": float(city_features["avg_temp_c"].mean()),
        })
        print(f"  [{i}/{len(city_list)}] {city}: heat_risk={heat_risk:.2f}, year_risk={year_risk:.2f}")

    # Global aggregates (same as the KPI cards in the Streamlit app)
    global_stats = {
        "citiesTracked": int(features["city"].nunique()),
        "globalAvgTemp": float(features["avg_temp_c"].mean()),
        "totalDisasterEvents": int(features["disaster_event_count"].sum()),
        "totalDamageUsd": float(features["disaster_damage_usd"].sum()),
    }

    # Correlation matrix
    corr_cols = [
        "avg_temp_c", "max_temp_c", "days_over_35c", "total_precip_mm",
        "heavy_rain_days", "avg_max_windspeed", "gdp_current_usd",
        "population", "disaster_damage_usd", "disaster_deaths",
    ]
    corr_matrix = features[corr_cols].corr().round(3)
    correlation = {
        "labels": corr_cols,
        "matrix": corr_matrix.values.tolist(),
    }

    # Risk matrix data (probability x impact quadrant)
    risk_data = features.groupby(["city", "country"]).agg(
        avgHeatDays=("days_over_35c", "mean"),
        totalDamage=("disaster_damage_usd", "sum"),
        avgGdp=("gdp_current_usd", "mean"),
        population=("population", "mean"),
    ).reset_index()
    risk_data["damageToGdpPct"] = risk_data["totalDamage"] / (risk_data["avgGdp"] * 10) * 100
    heat_median = float(risk_data["avgHeatDays"].median())
    damage_median = float(risk_data["damageToGdpPct"].median())

    # Humanitarian data
    humanitarian = features.groupby(["city", "country"]).agg(
        totalAffected=("disaster_affected", "sum"),
        totalDeaths=("disaster_deaths", "sum"),
        population=("population", "mean"),
    ).reset_index()
    humanitarian = humanitarian[(humanitarian["totalAffected"] > 0) | (humanitarian["totalDeaths"] > 0)]

    # Key findings (same dynamic logic as the Streamlit app)
    priority_cities = risk_data[
        (risk_data["avgHeatDays"] >= heat_median) & (risk_data["damageToGdpPct"] >= damage_median)
    ].sort_values("damageToGdpPct", ascending=False)
    top_humanitarian = humanitarian.sort_values("totalDeaths", ascending=False).head(3)
    fastest_warming = forecasts.sort_values("warming_trend_c_per_decade", ascending=False).head(3)

    key_findings = {
        "priorityCities": priority_cities["city"].head(5).tolist(),
        "humanitarianPriorityCities": top_humanitarian["city"].tolist(),
        "fastestWarmingCities": [
            {"city": row["city"], "trend": round(float(row["warming_trend_c_per_decade"]), 1)}
            for _, row in fastest_warming.iterrows()
        ],
    }

    export = {
        "generatedAt": pd.Timestamp.now().isoformat(),
        "globalStats": global_stats,
        "cities": cities_data,
        "correlation": correlation,
        "riskMatrix": {
            "cities": risk_data.rename(columns={
                "avgHeatDays": "avgHeatDays", "damageToGdpPct": "damageToGdpPct",
            })[["city", "country", "avgHeatDays", "damageToGdpPct", "population"]].to_dict(orient="records"),
            "heatMedian": heat_median,
            "damageMedian": damage_median,
        },
        "humanitarian": humanitarian.to_dict(orient="records"),
        "keyFindings": key_findings,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(export, f, indent=2, default=str)

    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"\nExport complete: {OUT_PATH} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
