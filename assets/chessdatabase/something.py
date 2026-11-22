import duckdb

# Connect to DuckDB (creates a database file if needed)
con = duckdb.connect("lichess_openings.duckdb")

# Convert Parquet to CSV directly
con.execute("""
    COPY (
        SELECT *
        FROM '0000.parquet'
    )
    TO '0000.csv'
    WITH (HEADER TRUE)
""")

print("Conversion complete: '0000.csv' created successfully!")
