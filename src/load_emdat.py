"""
Clean the raw EM-DAT Country Profiles export, filter to our 25 countries and
2016-2025 climate-relevant disasters, and load into climate.duckdb.

Usage:
    python src/load_emdat.py
"""

from pathlib import Path

import duckdb
import pandas as pd

from cities import CITIES

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "emdat_raw.xlsx"
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "climate.duckdb"

START_YEAR = 2016
END_YEAR = 2025

# Climate-relevant disaster groups only - excludes Geophysical (earthquakes,
# volcanic activity) and Biological (epidemics, insect infestation)
CLIMATE_RELEVANT_GROUPS = {"Climatological", "Meteorological", "Hydrological"}

COUNTRY_TO_ISO3 = {
    "USA": "USA", "Mexico": "MEX", "Brazil": "BRA", "Argentina": "ARG",
    "UK": "GBR", "France": "FRA", "Germany": "DEU", "Spain": "ESP",
    "Italy": "ITA", "Russia": "RUS", "Turkey": "TUR", "Egypt": "EGY",
    "Nigeria": "NGA", "Kenya": "KEN", "South Africa": "ZAF", "India": "IND",
    "Bangladesh": "BGD", "Thailand": "THA", "Indonesia": "IDN",
    "Philippines": "PHL", "China": "CHN", "Japan": "JPN",
    "South Korea": "KOR", "Australia": "AUS", "Singapore": "SGP",
}


def main():
    print(f"Reading {RAW_PATH}...")
    df = pd.read_excel(RAW_PATH)
    print(f"Raw shape (before HXL row removal): {df.shape}")

    # HDX exports include an HXL hashtag row right after the header
    # (e.g. '#cause+group', '#country+name') meant for machine tagging, not data.
    # Detect and drop it: it's the row where 'Year' isn't a valid number.
    hxl_mask = pd.to_numeric(df["Year"], errors="coerce").isna()
    if hxl_mask.any():
        print(f"Dropping {hxl_mask.sum()} HXL hashtag row(s): {df.loc[hxl_mask, 'Year'].tolist()}")
        df = df[~hxl_mask].copy()

    df["Year"] = df["Year"].astype(int)
    print(f"Shape after HXL row removal: {df.shape}")

    our_iso3_codes = set(COUNTRY_TO_ISO3.values())

    print(f"\nUnique Disaster Group values found: {sorted(df['Disaster Group'].unique())}")
    print(f"Unique Disaster Subroup values found: {sorted(df['Disaster Subroup'].dropna().unique())}")

    filtered = df[
        (df["ISO"].isin(our_iso3_codes))
        & (df["Year"] >= START_YEAR)
        & (df["Year"] <= END_YEAR)
        & (df["Disaster Subroup"].isin(CLIMATE_RELEVANT_GROUPS))
    ].copy()

    # Standardize column names to snake_case for consistency with our other tables
    filtered = filtered.rename(columns={
        "Year": "year",
        "Country": "country",
        "ISO": "iso3",
        "Disaster Group": "disaster_group",
        "Disaster Subroup": "disaster_subgroup",
        "Disaster Type": "disaster_type",
        "Disaster Subtype": "disaster_subtype",
        "Total Events": "total_events",
        "Total Affected": "total_affected",
        "Total Deaths": "total_deaths",
        "Total Damage (USD, original)": "total_damage_usd_original",
        "Total Damage (USD, adjusted)": "total_damage_usd_adjusted",
        "CPI": "cpi",
    })

    print(f"\nFiltered to our 25 countries, {START_YEAR}-{END_YEAR}, climate-relevant groups:")
    print(f"Filtered shape: {filtered.shape}")
    print(f"Countries present: {sorted(filtered['iso3'].unique())}")

    missing_countries = our_iso3_codes - set(filtered["iso3"].unique())
    if missing_countries:
        print(f"\nNote: no climate disasters recorded in this window for: {sorted(missing_countries)}")
        print("(This can be legitimate - e.g. Singapore rarely has major climate disaster events.)")

    # Load into DuckDB alongside weather_daily
    con = duckdb.connect(str(DB_PATH))
    con.execute("DROP TABLE IF EXISTS emdat_disasters")
    con.register("filtered_df", filtered)
    con.execute("CREATE TABLE emdat_disasters AS SELECT * FROM filtered_df")

    row_count = con.execute("SELECT COUNT(*) FROM emdat_disasters").fetchone()[0]
    print(f"\nemdat_disasters table created in climate.duckdb: {row_count} rows")

    total_damage = con.execute(
        "SELECT SUM(total_damage_usd_adjusted) FROM emdat_disasters"
    ).fetchone()[0]
    if total_damage is not None:
        print(f"Total adjusted damage across all filtered events: ${total_damage:,.0f} USD")
    else:
        print("Total adjusted damage: N/A (no rows matched filter)")

    con.close()


if __name__ == "__main__":
    main()
