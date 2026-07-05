import duckdb

con = duckdb.connect("data/climate.duckdb")
df = con.execute("""
    SELECT city, year, avg_temp_c, days_over_35c, disaster_damage_usd
    FROM city_year_features
    WHERE city IN ('Dhaka', 'Sydney', 'Cairo')
      AND year IN (2016, 2025)
    ORDER BY city, year
""").df()
print(df.to_string(index=False))
con.close()
