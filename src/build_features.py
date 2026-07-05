"""
Build a single yearly city-level feature table joining:
  - weather_daily (aggregated to yearly stats per city)
  - worldbank.parquet (GDP, population per country-year)
  - emdat_disasters (aggregated to yearly stats per country)

Output: a new 'city_year_features' table in climate.duckdb, ready for
ML modeling and the Streamlit app.

Usage:
    python src/build_features.py
"""

from pathlib import Path

import duckdb

from cities import CITIES

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "climate.duckdb"
WORLDBANK_PATH = Path(__file__).resolve().parent.parent / "data" / "worldbank.parquet"

# Map city -> country, needed to join country-level economic/disaster data
CITY_TO_COUNTRY = {name: country for name, country, _, _ in CITIES}

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
    con = duckdb.connect(str(DB_PATH))

    # Register worldbank parquet as a view so we can query it with SQL directly
    con.execute(f"CREATE OR REPLACE VIEW worldbank AS SELECT * FROM read_parquet('{WORLDBANK_PATH}')")

    print("Aggregating weather_daily to yearly city-level stats...")
    con.execute("""
        CREATE OR REPLACE TABLE city_year_weather AS
        SELECT
            city,
            country,
            lat,
            lon,
            EXTRACT(YEAR FROM date) AS year,
            AVG(temperature_2m_mean) AS avg_temp_c,
            MAX(temperature_2m_max) AS max_temp_c,
            MIN(temperature_2m_min) AS min_temp_c,
            SUM(precipitation_sum) AS total_precip_mm,
            MAX(precipitation_sum) AS max_daily_precip_mm,
            SUM(CASE WHEN temperature_2m_max >= 35 THEN 1 ELSE 0 END) AS days_over_35c,
            SUM(CASE WHEN precipitation_sum >= 50 THEN 1 ELSE 0 END) AS heavy_rain_days,
            AVG(windspeed_10m_max) AS avg_max_windspeed
        FROM weather_daily
        GROUP BY city, country, lat, lon, EXTRACT(YEAR FROM date)
    """)

    row_count = con.execute("SELECT COUNT(*) FROM city_year_weather").fetchone()[0]
    print(f"city_year_weather: {row_count} rows ({row_count // 30 if row_count else 0} years x 30 cities expected)")

    print("\nAggregating emdat_disasters to yearly country-level stats...")
    con.execute("""
        CREATE OR REPLACE TABLE country_year_disasters AS
        SELECT
            iso3,
            year,
            SUM(total_events) AS disaster_event_count,
            SUM(total_deaths) AS disaster_deaths,
            SUM(total_affected) AS disaster_affected,
            SUM(total_damage_usd_adjusted) AS disaster_damage_usd
        FROM emdat_disasters
        GROUP BY iso3, year
    """)

    print("\nJoining weather + worldbank (GDP/population) + disasters into final feature table...")
    con.execute("""
        CREATE OR REPLACE TABLE city_year_features AS
        SELECT
            w.city,
            w.country,
            w.lat,
            w.lon,
            w.year,
            w.avg_temp_c,
            w.max_temp_c,
            w.min_temp_c,
            w.total_precip_mm,
            w.max_daily_precip_mm,
            w.days_over_35c,
            w.heavy_rain_days,
            w.avg_max_windspeed,
            wb.gdp_current_usd,
            wb.population,
            COALESCE(d.disaster_event_count, 0) AS disaster_event_count,
            COALESCE(d.disaster_deaths, 0) AS disaster_deaths,
            COALESCE(d.disaster_affected, 0) AS disaster_affected,
            COALESCE(d.disaster_damage_usd, 0) AS disaster_damage_usd
        FROM city_year_weather w
        LEFT JOIN worldbank wb
            ON w.country = wb.country AND w.year = wb.year
        LEFT JOIN country_year_disasters d
            ON wb.iso3 = d.iso3 AND w.year = d.year
        ORDER BY w.city, w.year
    """)

    final_count = con.execute("SELECT COUNT(*) FROM city_year_features").fetchone()[0]
    print(f"\ncity_year_features created: {final_count} rows")

    # Sanity checks
    missing_gdp = con.execute(
        "SELECT COUNT(*) FROM city_year_features WHERE gdp_current_usd IS NULL"
    ).fetchone()[0]
    missing_pop = con.execute(
        "SELECT COUNT(*) FROM city_year_features WHERE population IS NULL"
    ).fetchone()[0]
    print(f"Rows missing GDP: {missing_gdp} ({missing_gdp/final_count*100:.1f}%)")
    print(f"Rows missing population: {missing_pop} ({missing_pop/final_count*100:.1f}%)")

    year_range = con.execute("SELECT MIN(year), MAX(year) FROM city_year_features").fetchone()
    city_count = con.execute("SELECT COUNT(DISTINCT city) FROM city_year_features").fetchone()[0]
    print(f"Year range: {year_range[0]}-{year_range[1]}, {city_count} cities")

    con.close()
    print(f"\nDone. Feature table ready in {DB_PATH}")


if __name__ == "__main__":
    main()
