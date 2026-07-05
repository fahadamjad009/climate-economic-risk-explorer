"""
Consolidate all per-city Parquet weather files into a single DuckDB database.

Usage:
    python src/build_duckdb.py
"""

from pathlib import Path

import duckdb

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw_weather"
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "climate.duckdb"


def main():
    parquet_files = sorted(RAW_DIR.glob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No parquet files found in {RAW_DIR}")

    print(f"Found {len(parquet_files)} city files")

    con = duckdb.connect(str(DB_PATH))

    con.execute("DROP TABLE IF EXISTS weather_daily")
    con.execute(f"""
        CREATE TABLE weather_daily AS
        SELECT * FROM read_parquet('{RAW_DIR}/*.parquet')
    """)

    row_count = con.execute("SELECT COUNT(*) FROM weather_daily").fetchone()[0]
    city_count = con.execute("SELECT COUNT(DISTINCT city) FROM weather_daily").fetchone()[0]
    date_range = con.execute(
        "SELECT MIN(date), MAX(date) FROM weather_daily"
    ).fetchone()

    print(f"weather_daily table created: {row_count} rows, {city_count} cities")
    print(f"Date range: {date_range[0]} to {date_range[1]}")

    # Sanity check: every city should have the same row count
    per_city = con.execute("""
        SELECT city, COUNT(*) as n
        FROM weather_daily
        GROUP BY city
        ORDER BY n
    """).fetchall()

    min_rows = per_city[0][1]
    max_rows = per_city[-1][1]
    if min_rows != max_rows:
        print(f"\nWARNING: row count mismatch across cities (min={min_rows}, max={max_rows})")
        for city, n in per_city:
            if n != max_rows:
                print(f"  {city}: {n} rows")
    else:
        print(f"All {city_count} cities have exactly {max_rows} rows - consistent")

    con.close()
    print(f"\nDatabase written to: {DB_PATH}")


if __name__ == "__main__":
    main()
