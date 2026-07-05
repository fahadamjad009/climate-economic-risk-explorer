"""
Fetch annual GDP (current US$) and population for all 25 countries from the
World Bank API (free, no key required). Caches each country as its own
Parquet file so failed/incomplete countries can be retried without
re-fetching everything else.

Usage:
    python src/fetch_worldbank.py
"""

import time
from pathlib import Path

import pandas as pd
import requests

from cities import CITIES

BASE_URL = "https://api.worldbank.org/v2/country/{iso3}/indicator/{indicator}"

INDICATORS = {
    "gdp_current_usd": "NY.GDP.MKTP.CD",
    "population": "SP.POP.TOTL",
}

START_YEAR = 2016
END_YEAR = 2025

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "worldbank_cache"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "worldbank.parquet"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

RETRYABLE_STATUS = {429, 400, 500, 502, 503, 504}

COUNTRY_TO_ISO3 = {
    "USA": "USA", "Mexico": "MEX", "Brazil": "BRA", "Argentina": "ARG",
    "UK": "GBR", "France": "FRA", "Germany": "DEU", "Spain": "ESP",
    "Italy": "ITA", "Russia": "RUS", "Turkey": "TUR", "Egypt": "EGY",
    "Nigeria": "NGA", "Kenya": "KEN", "South Africa": "ZAF", "India": "IND",
    "Bangladesh": "BGD", "Thailand": "THA", "Indonesia": "IDN",
    "Philippines": "PHL", "China": "CHN", "Japan": "JPN",
    "South Korea": "KOR", "Australia": "AUS", "Singapore": "SGP",
}


def fetch_indicator(iso3: str, indicator_code: str) -> pd.DataFrame:
    url = BASE_URL.format(iso3=iso3, indicator=indicator_code)
    params = {"format": "json", "date": f"{START_YEAR}:{END_YEAR}", "per_page": 100}

    max_retries = 5
    backoff = 4  # seconds, doubles each retry -> 4,8,16,32
    payload = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=60)
            if resp.status_code in RETRYABLE_STATUS:
                if attempt == max_retries:
                    resp.raise_for_status()
                print(f"    {iso3}/{indicator_code}: HTTP {resp.status_code}, retrying in {backoff}s (attempt {attempt}/{max_retries})...")
                time.sleep(backoff)
                backoff *= 2
                continue
            resp.raise_for_status()
            payload = resp.json()
            break
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt == max_retries:
                raise
            print(f"    {iso3}/{indicator_code}: {type(e).__name__}, retrying in {backoff}s (attempt {attempt}/{max_retries})...")
            time.sleep(backoff)
            backoff *= 2
    else:
        raise RuntimeError(f"exceeded max retries for {iso3}/{indicator_code}")

    if payload is None or len(payload) < 2 or payload[1] is None:
        return pd.DataFrame(columns=["year", "value"])

    rows = [
        {"year": int(r["date"]), "value": r["value"]}
        for r in payload[1]
        if r["value"] is not None
    ]
    return pd.DataFrame(rows)


def fetch_country(country: str, iso3: str) -> pd.DataFrame:
    merged = None
    for col_name, indicator_code in INDICATORS.items():
        df = fetch_indicator(iso3, indicator_code)
        df = df.rename(columns={"value": col_name})
        merged = df if merged is None else merged.merge(df, on="year", how="outer")
        time.sleep(0.8)
    merged["country"] = country
    merged["iso3"] = iso3
    return merged[["country", "iso3", "year", "gdp_current_usd", "population"]]


def main():
    countries = sorted(set(country for _, country, _, _ in CITIES))
    print(f"Fetching World Bank data for {len(countries)} countries")

    for i, country in enumerate(countries, start=1):
        iso3 = COUNTRY_TO_ISO3.get(country)
        if not iso3:
            print(f"[{i}/{len(countries)}] {country}: NO ISO3 MAPPING, skipping")
            continue

        cache_path = CACHE_DIR / f"{iso3}.parquet"
        if cache_path.exists():
            print(f"[{i}/{len(countries)}] {country} ({iso3}): already cached, skipping")
            continue

        try:
            df = fetch_country(country, iso3)
            df.to_parquet(cache_path, index=False)
            print(f"[{i}/{len(countries)}] {country} ({iso3}): fetched, {len(df)} rows")
        except Exception as e:
            print(f"[{i}/{len(countries)}] {country} ({iso3}): FAILED - {e}")

        time.sleep(0.5)

    # Combine whatever is cached so far
    cached_files = sorted(CACHE_DIR.glob("*.parquet"))
    if not cached_files:
        print("\nNo data cached yet - nothing to combine.")
        return

    combined = pd.concat([pd.read_parquet(f) for f in cached_files], ignore_index=True)
    combined = combined.sort_values(["country", "year"]).reset_index(drop=True)
    combined.to_parquet(OUT_PATH, index=False)

    countries_done = combined["country"].nunique()
    print(f"\nCombined {len(cached_files)} cached countries -> {OUT_PATH}")
    print(f"Countries covered: {countries_done}/{len(countries)}")

    missing_countries = set(countries) - set(combined["country"].unique())
    if missing_countries:
        print(f"Still missing: {sorted(missing_countries)}")
        print("Re-run this script to retry only the missing ones.")
    else:
        print("All countries present.")

    missing_values = combined[combined["gdp_current_usd"].isna() | combined["population"].isna()]
    if len(missing_values) > 0:
        print(f"\nNote: {len(missing_values)} country-year rows have a missing GDP or population value (normal for latest year - not yet published).")


if __name__ == "__main__":
    main()
