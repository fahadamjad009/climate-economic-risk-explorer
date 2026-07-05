"""
Prototype: fit a statsmodels Exponential Smoothing (ETS / Holt-Winters) model
on one city's daily mean temperature and forecast forward. Replaces the
Prophet approach, which hit an unresolved Windows binary compatibility issue.

ETS with additive trend + additive yearly seasonality is a standard,
well-established approach for series with a clear seasonal cycle and a
slow-moving trend - exactly what city temperature data looks like.

Usage:
    python src/ets_prototype.py
"""

from pathlib import Path

import duckdb
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

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

    print(f"\nAggregating to monthly means (daily data with seasonal_periods=365 is numerically unstable for Holt-Winters)...")
    df = df.set_index("date")
    df.index = pd.DatetimeIndex(df.index)
    monthly = df["temperature_2m_mean"].resample("MS").mean()
    print(f"Monthly series: {len(monthly)} months")

    print("\nFitting ETS model (additive trend + additive yearly seasonality, monthly)...")
    model = ExponentialSmoothing(
        monthly,
        trend="add",
        seasonal="add",
        seasonal_periods=12,
        damped_trend=True,  # prevents unrealistic runaway trend extrapolation
    )
    fitted = model.fit(optimized=True)

    print(f"Model fitted. Smoothing params:")
    print(f"  alpha (level): {fitted.params['smoothing_level']:.4f}")
    print(f"  beta (trend):  {fitted.params['smoothing_trend']:.4f}")
    print(f"  gamma (season): {fitted.params['smoothing_seasonal']:.4f}")
    print(f"  phi (damping): {fitted.params['damping_trend']:.4f}")

    FORECAST_MONTHS = 24
    forecast = fitted.forecast(FORECAST_MONTHS)
    print(f"\nForecast generated: {len(forecast)} months ahead")

    # Sanity checks: compare historical yearly averages to the model's fitted values
    historical = df.copy()
    historical["year"] = historical.index.year
    yearly_avg = historical.groupby("year")["temperature_2m_mean"].mean()
    print("\nActual yearly average temps (Sydney):")
    print(yearly_avg.to_string())

    fitted_values = fitted.fittedvalues
    fitted_df = pd.DataFrame({"fitted": fitted_values})
    fitted_df["year"] = fitted_df.index.year
    fitted_yearly = fitted_df.groupby("year")["fitted"].mean()
    print("\nModel's fitted yearly average temps:")
    print(fitted_yearly.to_string())

    forecast_df = pd.DataFrame({"forecast": forecast})
    forecast_df["year"] = forecast_df.index.year
    forecast_yearly = forecast_df.groupby("year")["forecast"].mean()
    print("\nForecasted yearly average temps (next 2 years):")
    print(forecast_yearly.to_string())

    # Isolate the trend/level component the same way we did for Prophet:
    # look at the underlying level series (not the seasonal swings) to get
    # the actual warming signal
    level = fitted.level
    trend_start = level.iloc[0]
    trend_end = level.iloc[-1]
    years_span = (level.index[-1] - level.index[0]).days / 365.25
    print(f"\nLevel component: {trend_start:.2f}C at start -> {trend_end:.2f}C at end of history")
    print(f"Implied warming trend over {years_span:.1f} years: {trend_end - trend_start:+.2f}C")

    # Cross-check: does the forecast fall within a plausible range of
    # historical yearly averages? If not, something is still wrong.
    hist_min, hist_max = yearly_avg.min(), yearly_avg.max()
    forecast_min, forecast_max = forecast_yearly.min(), forecast_yearly.max()
    print(f"\nSanity range check: historical yearly avgs span [{hist_min:.2f}, {hist_max:.2f}]C")
    print(f"                     forecast yearly avgs span [{forecast_min:.2f}, {forecast_max:.2f}]C")
    if forecast_min < hist_min - 2 or forecast_max > hist_max + 2:
        print("WARNING: forecast falls well outside historical range - likely still unstable.")
    else:
        print("Forecast falls within a plausible range of historical values.")


if __name__ == "__main__":
    main()
