# inspect_and_clean.py
# ---------------------------------------------------------
# Purpose : Load the three raw CSV files from the data folder,
#           quickly inspect their shapes and column names,
#           and standardize column names for PostgreSQL.
#
# Run this script first before load_data.py to understand
# the structure of the raw data files.
#
# How to run (from the project root):
#   python -m src.inspect_and_clean
# ---------------------------------------------------------

import pandas as pd
from pathlib import Path

# Build the path to the data folder relative to this script file.
# Using Path(__file__) means this works no matter where you run it from.
DATA_DIR = Path(__file__).resolve().parent.parent / 'data'

# ── Step 1: Load all three CSV files ──────────────────────────────────────────
# The files use latin-1 encoding (common in World Bank datasets).
# Without this, pandas throws a UnicodeDecodeError on special characters.
print("Loading datasets into Pandas DataFrames...")

df_data        = pd.read_csv(DATA_DIR / 'IDS_ALLCountries_Data.csv',  encoding='latin-1')
df_country_meta = pd.read_csv(DATA_DIR / 'IDS_CountryMetaData.csv',   encoding='latin-1')
df_series_meta  = pd.read_csv(DATA_DIR / 'IDS_SeriesMetaData.csv',    encoding='latin-1')

# Print how many rows and columns each file has
print(f"  Main Data shape    : {df_data.shape}")
print(f"  Country Meta shape : {df_country_meta.shape}")
print(f"  Series Meta shape  : {df_series_meta.shape}")


# ── Step 2: Standardize column names for PostgreSQL ───────────────────────────
# PostgreSQL column names work best in lowercase with underscores (snake_case).
# This helper function strips spaces, lowercases everything, and removes
# any special characters that PostgreSQL would reject.
def clean_column_names(df):
    """Convert all column names to lowercase snake_case for PostgreSQL."""
    df.columns = (
        df.columns
        .str.strip()                              # remove leading/trailing spaces
        .str.lower()                              # make all lowercase
        .str.replace(' ', '_')                    # replace spaces with underscores
        .str.replace('[^a-zA-Z0-9_]', '', regex=True)  # remove special characters
    )
    return df

print("\nStandardizing column names to snake_case...")
df_data         = clean_column_names(df_data)
df_country_meta = clean_column_names(df_country_meta)
df_series_meta  = clean_column_names(df_series_meta)

# Drop any fully duplicate rows in the main dataset
df_data.drop_duplicates(inplace=True)


# ── Step 3: Preview the first few column names ────────────────────────────────
# This helps us identify which columns will become our Primary and Foreign Keys.
print("\nProcessed column names (first few):")
print("  Main Data    :", list(df_data.columns[:5]), "... plus year columns")
print("  Country Meta :", list(df_country_meta.columns[:4]))
print("  Series Meta  :", list(df_series_meta.columns[:4]))