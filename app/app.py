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
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "international_debt")
    return create_engine(f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")

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
def load_kpis():
    """Fetch total global debt and total number of borrowing countries."""
    return pd.read_sql("""
        SELECT
            SUM(debt_value)              AS total_global_debt,
            COUNT(DISTINCT country_code) AS active_countries
        FROM debt_records;
    """, engine)

@st.cache_data
def load_trend():
    """Fetch total global debt grouped by year for the trend line chart."""
    return pd.read_sql("""
        SELECT year, SUM(debt_value) AS total_debt_by_year
        FROM debt_records
        GROUP BY year
        ORDER BY year ASC;
    """, engine)

@st.cache_data
def load_top_indicators():
    """Fetch the top 5 indicators by total global debt for the donut chart."""
    return pd.read_sql("""
        SELECT i.indicator_name, SUM(d.debt_value) AS total_indicator_debt
        FROM debt_records d
        JOIN indicators i ON d.indicator_code = i.indicator_code
        GROUP BY i.indicator_name
        ORDER BY total_indicator_debt DESC
        LIMIT 5;
    """, engine)

@st.cache_data
def load_total_debt_ranking(region):
    """
    Fetch the highest and lowest countries by raw total debt for a given region.
    Both results are returned together to avoid two separate DB round-trips.
    """
    query = f"""
        SELECT c.country_name, SUM(d.debt_value) AS metric_value
        FROM debt_records d
        JOIN countries c ON d.country_code = c.country_code
        WHERE c.region = '{region}'
        GROUP BY c.country_name
        ORDER BY metric_value DESC;
    """
    df = pd.read_sql(query, engine)
    return df.head(10), df.tail(10).sort_values('metric_value')

@st.cache_data
def load_indicator_ranking(region, indicator_code):
    """
    Fetch the highest and lowest countries by a specific indicator (most recent year).

    Uses DISTINCT ON to efficiently pick just the latest year per country
    without a slow correlated subquery.
    """
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

# ── Section 1: Global KPI Summary Cards ──────────────────────────────────────
st.subheader("Global Debt Overview")

kpi_df          = load_kpis()
total_debt      = kpi_df['total_global_debt'].iloc[0]
total_countries = kpi_df['active_countries'].iloc[0]

col1, col2 = st.columns(2)
col1.metric(label="Total Logged Global Debt",  value=f"${total_debt:,.2f} USD")
col2.metric(label="Total Borrowing Countries", value=int(total_countries))

st.divider()

# ── Section 2: Debt Trend Over Time + Indicator Breakdown ────────────────────
st.subheader("Trends and Indicator Analysis")

col_trend, col_pie = st.columns(2)

with col_trend:
    st.markdown("### Total Debt Trend Over Years")
    df_trend = load_trend()
    fig_trend = px.line(
        df_trend,
        x='year',
        y='total_debt_by_year',
        labels={'year': 'Year', 'total_debt_by_year': 'Total Debt (USD)'},
        title="Global Debt Trajectory"
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with col_pie:
    st.markdown("### Top 5 Debt-Contributing Indicators Globally")
    df_chart2 = load_top_indicators()
    fig2 = px.pie(
        df_chart2,
        values='total_indicator_debt',
        names='indicator_name',
        hole=0.4,
        title="Global Indicator Breakdown"
    )
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── Section 3: Highest vs Lowest Debt Countries (unified chart) ───────────────
# A single full-width chart shows both groups together:
#   Top half    → Top 10 highest debt countries (highest at the very top, red)
#   Bottom half → Top 10 lowest debt countries  (lowest at the very bottom, green)
# The RdYlGn colorscale makes the contrast intuitive at a glance.
st.subheader(f"Country-Wise Debt Extremes — Ranked by {selected_label}")

if ranking_mode == "total":
    df_highest, df_lowest = load_total_debt_ranking(selected_region)
else:
    indicator_code = INDICATOR_CODES[ranking_mode]
    df_highest, df_lowest = load_indicator_ranking(selected_region, indicator_code)

if df_highest.empty and df_lowest.empty:
    st.info(f"No data available for '{selected_label}' in this region.")
else:
    # Plotly horizontal bar charts render the FIRST row of the dataframe at the
    # BOTTOM of the chart and the LAST row at the TOP.
    #
    # To get:  [highest at top] → [lowest at bottom]
    # We stack: [lowest ascending] + [highest ascending]
    # so the very lowest country is row 0 (bottom) and the very highest is
    # the last row (top).

    df_lowest_display  = df_lowest.sort_values('metric_value', ascending=True)
    df_highest_display = df_highest.sort_values('metric_value', ascending=True)
    df_combined        = pd.concat([df_lowest_display, df_highest_display], ignore_index=True)

    # RdYlGn_r colorscale:  high value → red (top),  low value → green (bottom)
    # This matches the intuition: red = heavy debt burden, green = light burden.
    fig_combined = px.bar(
        df_combined,
        x='metric_value',
        y='country_name',
        orientation='h',
        labels={'metric_value': axis_label, 'country_name': 'Country'},
        color='metric_value',
        color_continuous_scale='RdYlGn_r',
    )

    # Lock the y-axis order so it exactly matches our stacked dataframe.
    fig_combined.update_layout(
        yaxis={
            'categoryorder': 'array',
            'categoryarray': df_combined['country_name'].tolist(),
        },
        height=560,
        coloraxis_colorbar=dict(title=axis_label),
    )

    # Dotted divider line between the two groups so the boundary is obvious.
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
def load_raw_data(region):
    """Fetch a sample of 100 debt records for the selected region."""
    return pd.read_sql(f"""
        SELECT c.country_name, i.indicator_name, d.year, d.debt_value
        FROM debt_records d
        JOIN countries c ON d.country_code = c.country_code
        JOIN indicators i ON d.indicator_code = i.indicator_code
        WHERE c.region = '{region}'
        LIMIT 100;
    """, engine)

df_raw = load_raw_data(selected_region)
st.dataframe(df_raw, use_container_width=True)