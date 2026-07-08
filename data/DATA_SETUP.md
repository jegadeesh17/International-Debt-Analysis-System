# Data Setup

## Included in Git

| File | Purpose |
|------|---------|
| `IDS_ALLCountries_Data_sample.csv` | Subset of country debt records for EDA and dashboard demos |
| `IDS_CountryMetaData.csv` | Country dimension (full metadata) |
| `IDS_SeriesMetaData.csv` | Indicator dimension (full metadata) |
| `IDS_FootNoteMetaData.csv` | Footnote reference |
| `Country-Series - Metadata.csv` | Series-country mapping |

## Full dataset (local only)

| File | Purpose |
|------|---------|
| `IDS_ALLCountries_Data.csv` | Full World Bank IDS export for complete ETL |

**How to obtain:** [World Bank International Debt Statistics](https://datacatalog.worldbank.org/search/dataset/0038015) — download `IDS_ALLCountries_Data.csv` into `data/`.

**Resolution order:** `src/load_data.py` uses the full file when present; otherwise the sample.

**Load database:** `python -m src.load_data` (requires PostgreSQL; see `.env` / `DB_*` vars in `src/load_data.py`).
