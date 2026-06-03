# 🎯 International Debt Analysis System

An end-to-end data analytics and visualization platform designed to ingest, structure, and explore World Bank International Debt Statistics for low- and middle-income nations.

## 📖 Project Overview
Global institutions produce massive amounts of multi-year debt statistics. However, the raw data is often in a complex wide format (years as individual columns), contains missing values and encoding issues, and is inefficient for direct analytical querying.

This project implements a Python-based ETL pipeline to clean and normalize the data into a PostgreSQL Star Schema database. An interactive Streamlit dashboard provides high-performance data exploration and insights into global debt trends.

## 🏗️ Architecture & Pipeline

1. **Data Preprocessing & ETL**: A Python pipeline using Pandas to load raw World Bank CSVs, clean missing values, handle Latin-1 encoding, strip trailing whitespaces, and unpivot (melt) the multi-year wide data format into a normalized long format.
2. **Relational Database Design**: A PostgreSQL database modeled in a Star Schema format. It features standardized column names and establishes primary-foreign key relationships across a fact table (`debt_records`) and dimension tables (`countries` and `indicators`).
3. **High-Performance Ingestion**: Optimized batch ingestion using Psycopg2's `execute_values` to stream hundreds of thousands of data points into the database rapidly.
4. **Interactive Dashboard**: A Streamlit application featuring Plotly line charts, pie charts, and unified horizontal bar charts. Advanced caching (`st.cache_data` and `st.cache_resource`) minimizes database queries for a seamless user experience.

## 🚀 How to Run

1. **Verify Database**: Ensure your local PostgreSQL is running and has the `international_debt` database configured.
2. **Execute Ingestion**: 
   ```bash
   python -m src.load_data
   ```
3. **Run the Streamlit Dashboard**:
   ```bash
   streamlit run app/app.py
   ```
