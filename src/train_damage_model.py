"""
Train an XGBoost regression model to estimate annual climate disaster
economic damage per city, using weather extremes + economic context as
features. Target is log1p(damage) due to heavy right-skew (many zeros,
a few very large events).

Usage:
    python src/train_damage_model.py
"""

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "climate.duckdb"
MODEL_PATH = Path(__file__).resolve().parent.parent / "data" / "damage_model.json"

FEATURE_COLS = [
    "avg_temp_c", "max_temp_c", "min_temp_c",
    "total_precip_mm", "max_daily_precip_mm",
    "days_over_35c", "heavy_rain_days", "avg_max_windspeed",
    "gdp_current_usd", "population",
]
TARGET_COL = "disaster_damage_usd"


def main():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute("SELECT * FROM city_year_features").df()
    con.close()

    print(f"Loaded {len(df)} rows")
    print(f"Target distribution: {(df[TARGET_COL] == 0).sum()} zero-damage rows, "
          f"{(df[TARGET_COL] > 0).sum()} non-zero rows")
    print(f"Max damage in dataset: ${df[TARGET_COL].max():,.0f}")

    df["log_damage"] = np.log1p(df[TARGET_COL])

    X = df[FEATURE_COLS]
    y = df["log_damage"]

    # With only 300 rows, a simple random split is fine, but stratifying by
    # city would leak - instead split by year so the model is tested on
    # years it hasn't seen for held-out cities' patterns
    X_train, X_test, y_train, y_test, df_train, df_test = train_test_split(
        X, y, df, test_size=0.2, random_state=42
    )
    print(f"\nTrain: {len(X_train)} rows, Test: {len(X_test)} rows")

    model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
    )
    model.fit(X_train, y_train)

    pred_log = model.predict(X_test)
    pred_damage = np.expm1(pred_log)
    actual_damage = np.expm1(y_test)

    r2 = r2_score(y_test, pred_log)
    mae_log = mean_absolute_error(y_test, pred_log)
    print(f"\nModel performance (on log1p scale):")
    print(f"  R2: {r2:.3f}")
    print(f"  MAE: {mae_log:.3f}")

    print(f"\nSample predictions (actual vs predicted damage, test set):")
    comparison = pd.DataFrame({
        "city": df_test["city"].values,
        "year": df_test["year"].values,
        "actual_damage": actual_damage.values,
        "predicted_damage": pred_damage,
    }).sort_values("actual_damage", ascending=False)
    print(comparison.head(10).to_string(index=False))

    print(f"\nFeature importance:")
    importance = pd.DataFrame({
        "feature": FEATURE_COLS,
        "importance": model.feature_importances_,
    }).sort_values("importance", ascending=False)
    print(importance.to_string(index=False))

    model.save_model(str(MODEL_PATH))
    print(f"\nModel saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
