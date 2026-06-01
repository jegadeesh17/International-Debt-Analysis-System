# app.py
# ---------------------------------------------------------
# Purpose : Streamlit dashboard for exploring international
#           debt data stored in a PostgreSQL database.
#
# How to run (from the project root):
#   streamlit run app/app.py
# ---------------------------------------------------------

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(page_title="International Debt Analytics", layout="wide")
st.title("International Debt Analysis Dashboard")
st.markdown("An interactive dashboard exploring global economic debt indicators to support data-driven decision making.")

# ── Database Connection ───────────────────────────────────────────────────────
# @st.cache_resource creates the engine once and reuses it across all sessions.
@st.cache_resource
def get_connection():
    """Create and return a cached SQLAlchemy engine for PostgreSQL."""
    from urllib.parse import quote_plus
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD")
    db_password_encoded = f":{quote_plus(db_password)}" if db_password else ""
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "international_debt")
    return create_engine(f"postgresql+psycopg2://{db_user}{db_password_encoded}@{db_host}:{db_port}/{db_name}")

engine = get_connection()

# ── Cached Data Fetching Functions ────────────────────────────────────────────
# @st.cache_data caches the query result in memory.
# Streamlit only re-runs the query when the function arguments change,
# so switching filters doesn't hit the database every time.

@st.cache_data
def load_regions():
    """Fetch all distinct world regions from the countries table."""
    return pd.read_sql(
        "SELECT DISTINCT region FROM countries WHERE region IS NOT NULL ORDER BY region;",
        engine
    )

@st.cache_data
def load_countries_by_region(region):
    """Fetch distinct countries for a given region."""
    return pd.read_sql(
        f"SELECT DISTINCT country_name FROM countries WHERE region = '{region}' ORDER BY country_name;",
        engine
    )

@st.cache_data
def load_years():
    """Fetch all distinct years available in the debt records."""
    return pd.read_sql(
        "SELECT DISTINCT year FROM debt_records ORDER BY year DESC;",
        engine
    )

@st.cache_data
def load_kpis(region=None, country=None, year=None):
    """Fetch total debt and total number of borrowing countries based on active filters."""
    where_clauses = []
    if region:
        where_clauses.append(f"c.region = '{region}'")
    if country and country != "All Countries":
        where_clauses.append(f"c.country_name = '{country}'")
    if year and year != "All Years":
        where_clauses.append(f"d.year = {year}")
        
    where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    
    query = f"""
        SELECT
            SUM(d.debt_value)              AS total_debt,
            COUNT(DISTINCT d.country_code) AS active_countries
        FROM debt_records d
        JOIN countries c ON d.country_code = c.country_code
        {where_str};
    """
    return pd.read_sql(query, engine)

@st.cache_data
def load_trend(region=None, country=None):
    """Fetch total debt grouped by year for the trend line chart, filtered by region and country."""
    where_clauses = []
    if region:
        where_clauses.append(f"c.region = '{region}'")
    if country and country != "All Countries":
        where_clauses.append(f"c.country_name = '{country}'")
        
    where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    query = f"""
        SELECT d.year, SUM(d.debt_value) AS total_debt_by_year
        FROM debt_records d
        JOIN countries c ON d.country_code = c.country_code
        {where_str}
        GROUP BY d.year
        ORDER BY d.year ASC;
    """
    return pd.read_sql(query, engine)

@st.cache_data
def load_top_indicators(region=None, country=None, year=None):
    """Fetch the top 5 indicators by total debt for the donut chart, filtered by region, country, and year."""
    where_clauses = []
    if region:
        where_clauses.append(f"c.region = '{region}'")
    if country and country != "All Countries":
        where_clauses.append(f"c.country_name = '{country}'")
    if year and year != "All Years":
        where_clauses.append(f"d.year = {year}")
        
    where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    query = f"""
        SELECT i.indicator_name, SUM(d.debt_value) AS total_indicator_debt
        FROM debt_records d
        JOIN indicators i ON d.indicator_code = i.indicator_code
        JOIN countries c ON d.country_code = c.country_code
        {where_str}
        GROUP BY i.indicator_name
        ORDER BY total_indicator_debt DESC
        LIMIT 5;
    """
    return pd.read_sql(query, engine)

@st.cache_data
def load_total_debt_ranking(region, year=None):
    """
    Fetch the highest and lowest countries by raw total debt for a given region and year.
    Both results are returned together.
    """
    year_clause = f"AND d.year = {year}" if (year and year != "All Years") else ""
    query = f"""
        SELECT c.country_name, SUM(d.debt_value) AS metric_value
        FROM debt_records d
        JOIN countries c ON d.country_code = c.country_code
        WHERE c.region = '{region}' {year_clause}
        GROUP BY c.country_name
        ORDER BY metric_value DESC;
    """
    df = pd.read_sql(query, engine)
    return df.head(10), df.tail(10).sort_values('metric_value')

@st.cache_data
def load_indicator_ranking(region, indicator_code, year=None):
    """
    Fetch the highest and lowest countries by a specific indicator for a given region and year.
    """
    if year and year != "All Years":
        query = f"""
            SELECT c.country_name, d.debt_value AS metric_value
            FROM debt_records d
            JOIN countries c ON d.country_code = c.country_code
            WHERE c.region = '{region}'
              AND d.indicator_code = '{indicator_code}'
              AND d.year = {year}
            ORDER BY metric_value DESC;
        """
    else:
        query = f"""
            SELECT c.country_name, d.debt_value AS metric_value
            FROM (
                SELECT DISTINCT ON (country_code) country_code, debt_value
                FROM debt_records
                WHERE indicator_code = '{indicator_code}'
                ORDER BY country_code, year DESC
            ) d
            JOIN countries c ON d.country_code = c.country_code
            WHERE c.region = '{region}'
            ORDER BY metric_value DESC;
        """
    df = pd.read_sql(query, engine)
    return df.head(10), df.tail(10).sort_values('metric_value')

# ── Sidebar Filters ───────────────────────────────────────────────────────────
st.sidebar.header("Filter Options")

regions_df = load_regions()
selected_region = st.sidebar.selectbox("Select a Global Region", regions_df['region'])

countries_df = load_countries_by_region(selected_region)
country_options = ["All Countries"] + sorted(countries_df['country_name'].tolist())
selected_country = st.sidebar.selectbox("Select a Country", country_options)

years_df = load_years()
year_options = ["All Years"] + [int(y) for y in years_df['year']]
selected_year = st.sidebar.selectbox("Select a Year", year_options)

st.sidebar.divider()

st.sidebar.subheader("Ranking Mode")
st.sidebar.caption("Controls how countries are ranked in the Debt Extremes section.")

RANKING_MODES = {
    "Total Debt (USD)":       "total",
    "Debt Per Capita (USD)":  "per_capita",
    "Debt as % of GNI":       "pct_gni",
}
selected_label = st.sidebar.radio("Rank countries by:", options=list(RANKING_MODES.keys()))
ranking_mode   = RANKING_MODES[selected_label]

INDICATOR_CODES = {
    "per_capita": "DT.DOD.DECT.PC.CD",   # Total external debt per capita (current US$)
    "pct_gni":    "DT.DOD.DECT.GN.ZS",   # External debt stocks (% of GNI)
}
AXIS_LABELS = {
    "total":      "Total Debt (USD)",
    "per_capita": "Debt Per Capita (USD)",
    "pct_gni":    "External Debt (% of GNI)",
}
axis_label = AXIS_LABELS[ranking_mode]

st.divider()

# ── Section 1: KPI Summary Cards ─────────────────────────────────────────────
# Dynamic subtitle depending on selection
if selected_country != "All Countries":
    kpi_title = f"Debt Overview for {selected_country}"
elif selected_region:
    kpi_title = f"Debt Overview for {selected_region}"
else:
    kpi_title = "Global Debt Overview"

st.subheader(kpi_title)

kpi_df = load_kpis(selected_region, selected_country, selected_year)
total_debt = kpi_df['total_debt'].iloc[0] if not kpi_df.empty else 0.0
total_countries = kpi_df['active_countries'].iloc[0] if not kpi_df.empty else 0

# Check for NaN and format
if pd.isna(total_debt):
    total_debt = 0.0
if pd.isna(total_countries):
    total_countries = 0

col1, col2 = st.columns(2)
col1.metric(label="Total Logged Debt (USD)",  value=f"${total_debt:,.2f} USD")
col2.metric(label="Total Borrowing Countries", value=int(total_countries))

st.divider()

# ── Section 2: Debt Trend Over Time + Indicator Breakdown ────────────────────
st.subheader("Trends and Indicator Analysis")

col_trend, col_pie = st.columns(2)

with col_trend:
    st.markdown("### Total Debt Trend Over Years")
    df_trend = load_trend(selected_region, selected_country)
    if not df_trend.empty:
        fig_trend = px.line(
            df_trend,
            x='year',
            y='total_debt_by_year',
            labels={'year': 'Year', 'total_debt_by_year': 'Total Debt (USD)'},
            title="Debt Trajectory Over Time"
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No trend data available for current selection.")

with col_pie:
    st.markdown("### Top 5 Debt-Contributing Indicators")
    df_chart2 = load_top_indicators(selected_region, selected_country, selected_year)
    if not df_chart2.empty:
        fig2 = px.pie(
            df_chart2,
            values='total_indicator_debt',
            names='indicator_name',
            hole=0.4,
            title="Indicator Breakdown"
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No indicator breakdown available for current selection.")

st.divider()

# ── Section 3: Highest vs Lowest Debt Countries (unified chart) ───────────────
st.subheader(f"Country-Wise Debt Extremes — Ranked by {selected_label}")

if selected_country != "All Countries":
    st.info("Extremes ranking is shown at the region level. To view rankings, select 'All Countries' in the sidebar.")
else:
    if ranking_mode == "total":
        df_highest, df_lowest = load_total_debt_ranking(selected_region, selected_year)
    else:
        indicator_code = INDICATOR_CODES[ranking_mode]
        df_highest, df_lowest = load_indicator_ranking(selected_region, indicator_code, selected_year)

    if df_highest.empty and df_lowest.empty:
        st.info(f"No ranking data available for '{selected_label}' in this region/year.")
    else:
        df_lowest_display  = df_lowest.sort_values('metric_value', ascending=True)
        df_highest_display = df_highest.sort_values('metric_value', ascending=True)
        df_combined        = pd.concat([df_lowest_display, df_highest_display], ignore_index=True)

        fig_combined = px.bar(
            df_combined,
            x='metric_value',
            y='country_name',
            orientation='h',
            labels={'metric_value': axis_label, 'country_name': 'Country'},
            color='metric_value',
            color_continuous_scale='RdYlGn_r',
        )

        fig_combined.update_layout(
            yaxis={
                'categoryorder': 'array',
                'categoryarray': df_combined['country_name'].tolist(),
            },
            height=560,
            coloraxis_colorbar=dict(title=axis_label),
        )

        midpoint = len(df_lowest_display) - 0.5
        fig_combined.add_hline(
            y=midpoint,
            line_dash="dot",
            line_color="gray",
            annotation_text="  Lowest 10  ↕  Highest 10",
            annotation_position="right",
            annotation_font_size=11,
        )

        st.plotly_chart(fig_combined, use_container_width=True)

st.divider()

# ── Section 4: Raw Data Explorer ─────────────────────────────────────────────
st.subheader("Data Explorer")

@st.cache_data
def load_raw_data(region, country=None, year=None):
    """Fetch a sample of 100 debt records for the selected region, country, and year."""
    where_clauses = [f"c.region = '{region}'"]
    if country and country != "All Countries":
        where_clauses.append(f"c.country_name = '{country}'")
    if year and year != "All Years":
        where_clauses.append(f"d.year = {year}")
        
    query = f"""
        SELECT c.country_name, i.indicator_name, d.year, d.debt_value
        FROM debt_records d
        JOIN countries c ON d.country_code = c.country_code
        JOIN indicators i ON d.indicator_code = i.indicator_code
        WHERE {' AND '.join(where_clauses)}
        LIMIT 100;
    """
    return pd.read_sql(query, engine)

df_raw = load_raw_data(selected_region, selected_country, selected_year)
st.dataframe(df_raw, use_container_width=True)