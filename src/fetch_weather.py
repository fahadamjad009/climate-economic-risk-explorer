"""
Fetch 10 years of daily historical weather for all 30 cities from Open-Meteo
(free, no API key required) and cache each city as a Parquet file.

Usage:
    python src/fetch_weather.py
"""

import time
from pathlib import Path

import pandas as pd
import requests

from cities import CITIES

# Open-Meteo historical archive endpoint (free, no key)
BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

START_DATE = "2016-01-01"
END_DATE = "2025-12-31"

DAILY_VARS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "windspeed_10m_max",
]

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw_weather"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def fetch_city(name: str, country: str, lat: float, lon: float) -> pd.DataFrame:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": ",".join(DAILY_VARS),
        "timezone": "auto",
    }

    max_retries = 5
    backoff = 5  # seconds, doubles each retry
    for attempt in range(1, max_retries + 1):
        resp = requests.get(BASE_URL, params=params, timeout=60)
        if resp.status_code == 429:
            print(f"    rate limited, waiting {backoff}s (attempt {attempt}/{max_retries})...")
            time.sleep(backoff)
            backoff *= 2
            continue
        resp.raise_for_status()
        payload = resp.json()
        break
    else:
        raise RuntimeError("exceeded max retries on 429")

    df = pd.DataFrame(payload["daily"])
    df["date"] = pd.to_datetime(df["time"])
    df = df.drop(columns=["time"])
    df["city"] = name
    df["country"] = country
    df["lat"] = lat
    df["lon"] = lon
    return df


def main():
    total = len(CITIES)
    for i, (name, country, lat, lon) in enumerate(CITIES, start=1):
        safe_name = name.lower().replace(" ", "_")
        out_path = OUT_DIR / f"{safe_name}.parquet"

        if out_path.exists():
            print(f"[{i}/{total}] {name}: already cached, skipping")
            continue

        print(f"[{i}/{total}] {name}: fetching...")
        try:
            df = fetch_city(name, country, lat, lon)
            df.to_parquet(out_path, index=False)
            print(f"[{i}/{total}] {name}: saved {len(df)} rows -> {out_path.name}")
        except Exception as e:
            print(f"[{i}/{total}] {name}: FAILED - {e}")

        # Be polite to the free API - avoid rate limiting
        time.sleep(3)

    print("\nDone. Cached files in:", OUT_DIR)


if __name__ == "__main__":
    main()
