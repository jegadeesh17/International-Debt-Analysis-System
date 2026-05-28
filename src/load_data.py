# load_data.py
# ---------------------------------------------------------
# Purpose : Read the three raw CSV files, clean and transform
#           the data, create the PostgreSQL schema, and load
#           everything into the database.
#
# This is the main ETL (Extract, Transform, Load) script.
# Run it once to populate the database from scratch.
#
# How to run (from the project root):
#   python -m src.load_data
# ---------------------------------------------------------

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_CONFIG = dict(
    host=os.getenv("DB_HOST", "localhost"),
    database=os.getenv("DB_NAME", "international_debt"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT", "5432")
)

# Build the path to the data folder relative to this script file.
# This works no matter which directory you run the script from.
DATA_DIR = Path(__file__).resolve().parent.parent / 'data'

# ── Step 1: Connect to PostgreSQL ─────────────────────────────────────────────
# We use psycopg2 to execute all commands and insert data.

pg_conn = psycopg2.connect(**DB_CONFIG)
pg_conn.autocommit = True   # each DDL statement commits immediately
print("Connected to PostgreSQL successfully!")


# ── Step 2: Load the raw CSV files into DataFrames ────────────────────────────
# The CSV files use latin-1 encoding (a common encoding in World Bank datasets).
# Without specifying this, pandas will throw a UnicodeDecodeError.
print("Loading CSV files...")

df_data_raw    = pd.read_csv(DATA_DIR / 'IDS_ALLCountries_Data.csv',  encoding='latin-1')
df_country_raw = pd.read_csv(DATA_DIR / 'IDS_CountryMetaData.csv',    encoding='latin-1')
df_series_raw  = pd.read_csv(DATA_DIR / 'IDS_SeriesMetaData.csv',     encoding='latin-1')

print("CSV files loaded successfully.")


# ── Step 3: Clean the Country Metadata table ──────────────────────────────────
# Note: The country metadata file uses 'Code' as the column name,
#       not 'Country Code' like the main data file does.
print("Cleaning Country Metadata...")

df_country = df_country_raw[['Code', 'Long Name', 'Region', 'Income Group']].copy()
df_country.columns = ['country_code', 'country_name', 'region', 'income_group']
df_country = df_country.dropna(subset=['country_code'])   # remove rows with no country code
df_country = df_country.drop_duplicates()


# ── Step 4: Clean the Indicator / Series Metadata table ───────────────────────
# Note: The series file uses 'Code' and 'Indicator Name' as column names.
print("Cleaning Series Metadata...")

df_series = df_series_raw[['Code', 'Indicator Name']].copy()
df_series.columns = ['indicator_code', 'indicator_name']
df_series = df_series.dropna(subset=['indicator_code'])
df_series = df_series.drop_duplicates()


# ── Step 5: Transform the Main Debt Data (Fact Table) ─────────────────────────
# The raw data is in "wide" format: one row per country+indicator, with a
# separate column for each year (2000, 2001, ..., 2023).
# We need to convert it to "long" format: one row per country+indicator+year.
# This process is called "melting" or "unpivoting".
print("Transforming main debt data (this may take a moment)...")

# Rename the key columns to match our database schema
df_data_raw = df_data_raw.rename(columns={
    'Country Code': 'country_code',
    'Series Code':  'indicator_code'
})

# Strip trailing whitespace from key columns.
# The CSV file stores country codes with trailing spaces (e.g. 'AFG       ')
# which would cause the filter step below to miss matches.
df_data_raw['country_code']   = df_data_raw['country_code'].str.strip()
df_data_raw['indicator_code'] = df_data_raw['indicator_code'].str.strip()

# Identify all year columns by excluding the text/identifier columns.
# Note: the counterpart columns use hyphens in their names ('Counterpart-Area Name').
NON_YEAR_COLUMNS = [
    'Country Name', 'country_code',
    'Counterpart-Area Name', 'Counterpart-Area Code',
    'Series Name', 'indicator_code'
]
year_columns = [col for col in df_data_raw.columns if col not in NON_YEAR_COLUMNS]

# Melt: converts all year columns into two columns — 'year' and 'debt_value'
df_melted = pd.melt(
    df_data_raw,
    id_vars=['country_code', 'indicator_code'],
    value_vars=year_columns,
    var_name='year',
    value_name='debt_value'
)


# ── Step 6: Clean the melted fact table ───────────────────────────────────────
print("Cleaning melted data values...")

# Extract just the numeric year from the column name (e.g. '2000 [YR2000]' → 2000)
df_melted['year'] = df_melted['year'].str.extract(r'(\d+)').astype(int)

# Convert debt values to numbers; any non-numeric strings become NaN
df_melted['debt_value'] = pd.to_numeric(df_melted['debt_value'], errors='coerce')

# Drop rows with missing or zero debt values — they add no analytical value
df_melted = df_melted.dropna(subset=['debt_value'])
df_melted = df_melted[df_melted['debt_value'] > 0]

# Only keep rows whose country and indicator codes exist in our metadata tables.
# This ensures referential integrity when we load into PostgreSQL.
df_melted = df_melted[df_melted['country_code'].isin(df_country['country_code'])]
df_melted = df_melted[df_melted['indicator_code'].isin(df_series['indicator_code'])]

print(f"Fact table ready: {len(df_melted):,} rows after filtering.")


# ── Step 7: Create the database tables ────────────────────────────────────────
# We drop and recreate all tables each time this script runs (fresh load).
# Tables are dropped in reverse dependency order to avoid foreign key errors.
print("Creating database tables in PostgreSQL...")

with pg_conn.cursor() as cur:
    # Drop tables in reverse order of relationships
    cur.execute("DROP TABLE IF EXISTS debt_records CASCADE;")
    cur.execute("DROP TABLE IF EXISTS countries CASCADE;")
    cur.execute("DROP TABLE IF EXISTS indicators CASCADE;")

    # Create the countries dimension table
    cur.execute("""
        CREATE TABLE countries (
            country_code  VARCHAR(50)  PRIMARY KEY,
            country_name  VARCHAR(255),
            region        VARCHAR(255),
            income_group  VARCHAR(255)
        );
    """)

    # Create the indicators dimension table
    cur.execute("""
        CREATE TABLE indicators (
            indicator_code VARCHAR(50) PRIMARY KEY,
            indicator_name TEXT
        );
    """)

    # Create the debt_records fact table with foreign key relationships
    cur.execute("""
        CREATE TABLE debt_records (
            id             SERIAL       PRIMARY KEY,
            country_code   VARCHAR(50)  REFERENCES countries(country_code),
            indicator_code VARCHAR(50)  REFERENCES indicators(indicator_code),
            year           INT,
            debt_value     NUMERIC
        );
    """)

print("Tables created.")


# ── Step 8: Load data into PostgreSQL ─────────────────────────────────────────
# We use psycopg2's execute_values to insert data efficiently.
print("Exporting DataFrames to PostgreSQL tables...")

# Clean NaN/None values from the DataFrames
df_country_clean = df_country.where(pd.notnull(df_country), None)
df_series_clean = df_series.where(pd.notnull(df_series), None)
df_melted_clean = df_melted.where(pd.notnull(df_melted), None)

# Convert DataFrames to list of tuples for insertion
country_values = list(df_country_clean.itertuples(index=False, name=None))
series_values = list(df_series_clean.itertuples(index=False, name=None))
melted_values = list(df_melted_clean.itertuples(index=False, name=None))

try:
    with pg_conn.cursor() as cur:
        # Load country metadata
        insert_countries = "INSERT INTO countries (country_code, country_name, region, income_group) VALUES %s"
        execute_values(cur, insert_countries, country_values)
        print("Loaded country metadata.")

        # Load indicators metadata
        insert_indicators = "INSERT INTO indicators (indicator_code, indicator_name) VALUES %s"
        execute_values(cur, insert_indicators, series_values)
        print("Loaded indicators metadata.")

        # Load main debt data
        insert_debt = "INSERT INTO debt_records (country_code, indicator_code, year, debt_value) VALUES %s"
        execute_values(cur, insert_debt, melted_values)
        print("Loaded main debt records.")
        
    print("All data loaded successfully into PostgreSQL!")
except Exception as e:
    print(f"An error occurred while loading data: {e}")
finally:
    pg_conn.close()