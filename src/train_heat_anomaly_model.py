"""
Extreme heat anomaly detection: label each day as anomalous if its max temp
exceeds that city's day-of-year climatological normal by 2+ standard
deviations, then train XGBoost to predict this from lagged/trailing
features (not the same-day temp itself, to avoid leakage).

Usage:
    python src/train_heat_anomaly_model.py
"""

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score, classification_report, roc_auc_score,
)
from sklearn.model_selection import train_test_split

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "climate.duckdb"
MODEL_PATH = Path(__file__).resolve().parent.parent / "data" / "heat_anomaly_model.json"

ANOMALY_ZSCORE_THRESHOLD = 2.0


def main():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute("""
        SELECT city, lat, lon, date, temperature_2m_max, precipitation_sum, windspeed_10m_max
        FROM weather_daily
        ORDER BY city, date
    """).df()
    con.close()

    df["date"] = pd.to_datetime(df["date"])
    df["day_of_year"] = df["date"].dt.dayofyear
    df["year"] = df["date"].dt.year
    print(f"Loaded {len(df)} day-level rows across {df['city'].nunique()} cities")

    # Climatological normal per city per day-of-year, using LEAVE-ONE-YEAR-OUT:
    # each day's baseline excludes that day's own year, so the label isn't
    # partly derived from itself (a subtle leakage that a straight groupby
    # mean/std across all years would introduce).
    grp_stats = df.groupby(["city", "day_of_year"])["temperature_2m_max"].agg(
        n="count", total_sum="sum", total_sq_sum=lambda s: (s ** 2).sum()
    ).reset_index()
    df = df.merge(grp_stats, on=["city", "day_of_year"], how="left")

    n_loo = df["n"] - 1
    sum_loo = df["total_sum"] - df["temperature_2m_max"]
    sq_sum_loo = df["total_sq_sum"] - df["temperature_2m_max"] ** 2

    df["climo_mean"] = sum_loo / n_loo
    loo_var = (sq_sum_loo / n_loo) - (df["climo_mean"] ** 2)
    df["climo_std"] = np.sqrt(loo_var.clip(lower=0))

    df["zscore"] = (df["temperature_2m_max"] - df["climo_mean"]) / df["climo_std"]
    df["is_extreme_heat_day"] = (df["zscore"] >= ANOMALY_ZSCORE_THRESHOLD).astype(int)

    print(f"\nExtreme heat days (z >= {ANOMALY_ZSCORE_THRESHOLD}): "
          f"{df['is_extreme_heat_day'].sum()} / {len(df)} "
          f"({df['is_extreme_heat_day'].mean()*100:.1f}%)")

    # Lag/trailing features - all computed from PRIOR days only, no same-day leakage
    df = df.sort_values(["city", "date"])
    grp = df.groupby("city")
    df["lag1_temp_max"] = grp["temperature_2m_max"].shift(1)
    df["lag2_temp_max"] = grp["temperature_2m_max"].shift(2)
    df["trailing_3day_avg_temp"] = grp["temperature_2m_max"].shift(1).rolling(3).mean().reset_index(drop=True)
    df["trailing_7day_avg_temp"] = grp["temperature_2m_max"].shift(1).rolling(7).mean().reset_index(drop=True)
    df["trailing_7day_avg_precip"] = grp["precipitation_sum"].shift(1).rolling(7).mean().reset_index(drop=True)
    df["day_of_year_sin"] = np.sin(2 * np.pi * df["day_of_year"] / 365.25)
    df["day_of_year_cos"] = np.cos(2 * np.pi * df["day_of_year"] / 365.25)

    df = df.dropna(subset=[
        "lag1_temp_max", "lag2_temp_max", "trailing_3day_avg_temp",
        "trailing_7day_avg_temp", "trailing_7day_avg_precip", "climo_std",
    ])
    print(f"Rows after dropping warm-up/missing rows: {len(df)}")

    feature_cols = [
        "lat", "lon", "day_of_year_sin", "day_of_year_cos",
        "lag1_temp_max", "lag2_temp_max",
        "trailing_3day_avg_temp", "trailing_7day_avg_temp", "trailing_7day_avg_precip",
        "climo_mean",  # legitimate: known seasonal norm for this city/date, not the outcome
    ]
    X = df[feature_cols]
    y = df["is_extreme_heat_day"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\nTrain: {len(X_train)} rows, Test: {len(X_test)} rows")

    model = xgb.XGBClassifier(
        n_estimators=300, max_depth=5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, random_state=42,
        eval_metric="logloss",
        scale_pos_weight=(y_train == 0).sum() / (y_train == 1).sum(),  # handle class imbalance
    )
    model.fit(X_train, y_train)

    pred_class = model.predict(X_test)
    pred_proba = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, pred_class)
    auc = roc_auc_score(y_test, pred_proba)
    print(f"\nAccuracy: {acc:.3f}  |  ROC-AUC: {auc:.3f}")
    print(f"\nClassification report:")
    print(classification_report(y_test, pred_class, target_names=["Normal day", "Extreme heat day"]))

    print(f"\nFeature importance:")
    importance = pd.DataFrame({
        "feature": feature_cols,
        "importance": model.feature_importances_,
    }).sort_values("importance", ascending=False)
    print(importance.to_string(index=False))

    model.save_model(str(MODEL_PATH))
    print(f"\nModel saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
