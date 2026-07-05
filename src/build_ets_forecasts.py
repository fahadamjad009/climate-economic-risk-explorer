"""
Fit an ETS (Holt-Winters) model per city on monthly mean temperature,
forecast 24 months ahead, and store results in a new 'city_temp_forecasts'
table in climate.duckdb.

Usage:
    python src/build_ets_forecasts.py
"""

from pathlib import Path

import duckdb
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "climate.duckdb"
FORECAST_MONTHS = 24


def fit_city(monthly_series: pd.Series) -> dict:
    model = ExponentialSmoothing(
        monthly_series,
        trend="add",
        seasonal="add",
        seasonal_periods=12,
        damped_trend=True,
    )
    fitted = model.fit(optimized=True)
    forecast = fitted.forecast(FORECAST_MONTHS)

    level = fitted.level
    trend_start = level.iloc[0]
    trend_end = level.iloc[-1]
    years_span = (level.index[-1] - level.index[0]).days / 365.25
    warming_trend_c = trend_end - trend_start

    hist_min, hist_max = monthly_series.min(), monthly_series.max()
    forecast_min, forecast_max = forecast.min(), forecast.max()
    is_plausible = not (forecast_min < hist_min - 2 or forecast_max > hist_max + 2)

    return {
        "avg_temp_forecast_year1": forecast.iloc[:12].mean(),
        "avg_temp_forecast_year2": forecast.iloc[12:24].mean(),
        "warming_trend_c_per_decade": warming_trend_c / years_span * 10,
        "alpha_level": fitted.params["smoothing_level"],
        "beta_trend": fitted.params["smoothing_trend"],
        "gamma_seasonal": fitted.params["smoothing_seasonal"],
        "phi_damping": fitted.params["damping_trend"],
        "is_plausible": is_plausible,
    }


def main():
    con = duckdb.connect(str(DB_PATH))
    cities = con.execute("SELECT DISTINCT city FROM weather_daily ORDER BY city").fetchall()
    cities = [c[0] for c in cities]
    print(f"Fitting ETS models for {len(cities)} cities...")

    results = []
    for i, city in enumerate(cities, start=1):
        df = con.execute("""
            SELECT date, temperature_2m_mean
            FROM weather_daily
            WHERE city = ?
            ORDER BY date
        """, [city]).df()

        df = df.set_index("date")
        df.index = pd.DatetimeIndex(df.index)
        monthly = df["temperature_2m_mean"].resample("MS").mean()

        try:
            metrics = fit_city(monthly)
            metrics["city"] = city
            results.append(metrics)
            flag = "OK" if metrics["is_plausible"] else "WARNING - implausible forecast"
            print(f"[{i}/{len(cities)}] {city}: trend {metrics['warming_trend_c_per_decade']:+.2f}C/decade ({flag})")
        except Exception as e:
            print(f"[{i}/{len(cities)}] {city}: FAILED - {e}")

    results_df = pd.DataFrame(results)
    con.execute("DROP TABLE IF EXISTS city_temp_forecasts")
    con.register("results_df", results_df)
    con.execute("CREATE TABLE city_temp_forecasts AS SELECT * FROM results_df")

    n_implausible = (~results_df["is_plausible"]).sum()
    print(f"\ncity_temp_forecasts created: {len(results_df)} cities")
    print(f"Implausible forecasts flagged: {n_implausible}")
    if n_implausible > 0:
        print("Cities needing review:")
        print(results_df[~results_df["is_plausible"]][["city", "warming_trend_c_per_decade"]].to_string(index=False))

    print(f"\nWarming trend summary across all cities (C/decade):")
    print(results_df["warming_trend_c_per_decade"].describe().to_string())

    con.close()


if __name__ == "__main__":
    main()
