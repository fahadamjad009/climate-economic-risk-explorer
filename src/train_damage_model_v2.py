"""
Two improved framings of the disaster damage model, both addressing the
weaknesses found in the raw-dollar regression (R2=0.25, badly underestimated
the largest events):

1. REGRESSION: predict damage as a % of GDP instead of raw dollars. This
   normalizes scale across small vs large economies (a $1B loss means very
   different things to Singapore vs the USA) and is the standard framing
   used in climate-economics literature.

2. CLASSIFICATION: predict whether a city-year is a "high-risk" year
   (top quartile of damage-to-GDP ratio) rather than the exact dollar figure.
   This is more robust with only 300 rows, since catastrophic single events
   make exact-dollar regression inherently noisy, but "was this a bad year"
   is a more learnable, more useful signal for a risk-screening tool.

Usage:
    python src/train_damage_model_v2.py
"""

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score, classification_report, mean_absolute_error,
    r2_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "climate.duckdb"
REG_MODEL_PATH = Path(__file__).resolve().parent.parent / "data" / "damage_ratio_model.json"
CLF_MODEL_PATH = Path(__file__).resolve().parent.parent / "data" / "high_risk_model.json"

FEATURE_COLS = [
    "avg_temp_c", "max_temp_c", "min_temp_c",
    "total_precip_mm", "max_daily_precip_mm",
    "days_over_35c", "heavy_rain_days", "avg_max_windspeed",
    "population",  # GDP dropped from features since it's now baked into the target
]
HIGH_RISK_PERCENTILE = 0.75


def main():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute("SELECT * FROM city_year_features").df()
    con.close()

    df["damage_to_gdp_pct"] = df["disaster_damage_usd"] / df["gdp_current_usd"] * 100
    df["log_damage_ratio"] = np.log1p(df["damage_to_gdp_pct"])

    threshold = df["damage_to_gdp_pct"].quantile(HIGH_RISK_PERCENTILE)
    df["is_high_risk_year"] = (df["damage_to_gdp_pct"] >= threshold).astype(int)

    print(f"Loaded {len(df)} rows")
    print(f"Damage-to-GDP ratio: median={df['damage_to_gdp_pct'].median():.4f}%, "
          f"75th pct threshold={threshold:.4f}%")
    print(f"High-risk years: {df['is_high_risk_year'].sum()} / {len(df)} "
          f"({df['is_high_risk_year'].mean()*100:.1f}%)")

    X = df[FEATURE_COLS]

    # --- Model 1: GDP-normalized regression ---
    print("\n" + "=" * 60)
    print("MODEL 1: Damage-to-GDP ratio regression")
    print("=" * 60)

    y_reg = df["log_damage_ratio"]
    X_train, X_test, y_train, y_test, df_train, df_test = train_test_split(
        X, y_reg, df, test_size=0.2, random_state=42
    )

    reg_model = xgb.XGBRegressor(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, random_state=42,
    )
    reg_model.fit(X_train, y_train)
    pred_log = reg_model.predict(X_test)

    r2 = r2_score(y_test, pred_log)
    mae = mean_absolute_error(y_test, pred_log)
    print(f"R2: {r2:.3f}  |  MAE (log scale): {mae:.3f}")

    comparison = pd.DataFrame({
        "city": df_test["city"].values,
        "year": df_test["year"].values,
        "actual_ratio_pct": np.expm1(y_test).values,
        "predicted_ratio_pct": np.expm1(pred_log),
    }).sort_values("actual_ratio_pct", ascending=False)
    print("\nTop actual vs predicted damage-to-GDP ratio (test set):")
    print(comparison.head(10).to_string(index=False))

    reg_model.save_model(str(REG_MODEL_PATH))

    # --- Model 2: High-risk year classification ---
    print("\n" + "=" * 60)
    print("MODEL 2: High-risk year classification")
    print("=" * 60)

    y_clf = df["is_high_risk_year"]
    X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(
        X, y_clf, test_size=0.2, random_state=42, stratify=y_clf
    )

    clf_model = xgb.XGBClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, random_state=42,
        eval_metric="logloss",
    )
    clf_model.fit(X_train_c, y_train_c)
    pred_class = clf_model.predict(X_test_c)
    pred_proba = clf_model.predict_proba(X_test_c)[:, 1]

    acc = accuracy_score(y_test_c, pred_class)
    auc = roc_auc_score(y_test_c, pred_proba)
    print(f"Accuracy: {acc:.3f}  |  ROC-AUC: {auc:.3f}")
    print(f"\nClassification report:")
    print(classification_report(y_test_c, pred_class, target_names=["Normal year", "High-risk year"]))

    clf_model.save_model(str(CLF_MODEL_PATH))

    print("\nFeature importance (classification model):")
    importance = pd.DataFrame({
        "feature": FEATURE_COLS,
        "importance": clf_model.feature_importances_,
    }).sort_values("importance", ascending=False)
    print(importance.to_string(index=False))

    print(f"\nModels saved:\n  {REG_MODEL_PATH}\n  {CLF_MODEL_PATH}")


if __name__ == "__main__":
    main()
