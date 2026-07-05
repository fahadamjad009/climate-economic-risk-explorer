"""
Prototype: fit a Prophet model on one city's daily mean temperature and
forecast forward, to validate the approach before scaling to all 30 cities.

Usage:
    python src/prophet_prototype.py
"""

from pathlib import Path

import duckdb
import pandas as pd
from prophet import Prophet

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "climate.duckdb"
CITY = "Sydney"
FORECAST_DAYS = 365 * 2  # forecast 2 years ahead


def main():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute("""
        SELECT date, temperature_2m_mean
        FROM weather_daily
        WHERE city = ?
        ORDER BY date
    """, [CITY]).df()
    con.close()

    print(f"Loaded {len(df)} rows for {CITY}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Missing values: {df['temperature_2m_mean'].isna().sum()}")

    # Prophet requires columns named exactly 'ds' and 'y'
    prophet_df = df.rename(columns={"date": "ds", "temperature_2m_mean": "y"})

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,  # no weekly pattern expected in temperature
        daily_seasonality=False,
        changepoint_prior_scale=0.05,  # default; controls trend flexibility
    )
    print("\nFitting Prophet model...")
    model.fit(prophet_df)

    future = model.make_future_dataframe(periods=FORECAST_DAYS)
    forecast = model.predict(future)

    print(f"\nForecast generated: {len(forecast)} rows (history + {FORECAST_DAYS} days ahead)")

    # Sanity checks: compare historical yearly averages to see if trend is picking up warming
    historical = df.copy()
    historical["year"] = pd.to_datetime(historical["date"]).dt.year
    yearly_avg = historical.groupby("year")["temperature_2m_mean"].mean()
    print("\nActual yearly average temps (Sydney):")
    print(yearly_avg.to_string())

    # Show forecasted values for the last historical year vs 2 years into the future
    forecast["year"] = pd.to_datetime(forecast["ds"]).dt.year
    forecast_yearly = forecast.groupby("year")["yhat"].mean()
    print("\nProphet's fitted+forecasted yearly average temps:")
    print(forecast_yearly.to_string())

    # Save the trend component specifically - this isolates long-term warming
    # signal from seasonal noise, which is what we actually care about
    trend_start = forecast["trend"].iloc[0]
    trend_end = forecast["trend"].iloc[-1]
    print(f"\nTrend component: {trend_start:.2f}C at start -> {trend_end:.2f}C at end of forecast")
    print(f"Implied warming trend over {(forecast['ds'].iloc[-1] - forecast['ds'].iloc[0]).days / 365.25:.1f} years: {trend_end - trend_start:+.2f}C")


if __name__ == "__main__":
    main()
