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
st.markdown("""
<div style="text-align: center; background: linear-gradient(120deg, #fdfbfb 0%, #ebedee 100%); padding: 2rem; border-radius: 10px; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
    <h1 style="margin-bottom: 0.5rem; color: #2c3e50; font-weight: 700;">International Debt Analysis Dashboard</h1>
    <p style="color: #596a7b; font-size: 1.1rem; margin-top: 0;">An interactive dashboard exploring global economic debt indicators to support data-driven decision making.</p>
</div>
<style>
    /* Center align the tabs */
    div[data-baseweb="tab-list"] {
        justify-content: center;
    }
</style>
""", unsafe_allow_html=True)

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

@st.cache_data
def load_map_data(year=None, ranking_mode="total", indicator_code=None):
    """Fetch debt by country code for the map."""
    where_clauses = []
    if year and year != "All Years":
        where_clauses.append(f"d.year = {year}")
        
    if ranking_mode != "total":
        where_clauses.append(f"d.indicator_code = '{indicator_code}'")

    where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    if ranking_mode == "total":
        query = f"""
            SELECT c.country_code, c.country_name, c.region, SUM(d.debt_value) AS metric_value
            FROM debt_records d
            JOIN countries c ON d.country_code = c.country_code
            {where_str}
            GROUP BY c.country_code, c.country_name, c.region;
        """
    else:
        if year and year != "All Years":
            query = f"""
                SELECT c.country_code, c.country_name, c.region, d.debt_value AS metric_value
                FROM debt_records d
                JOIN countries c ON d.country_code = c.country_code
                {where_str}
            """
        else:
            query = f"""
                SELECT c.country_code, c.country_name, c.region, d.debt_value AS metric_value
                FROM (
                    SELECT DISTINCT ON (country_code) country_code, debt_value
                    FROM debt_records
                    WHERE indicator_code = '{indicator_code}'
                    ORDER BY country_code, year DESC
                ) d
                JOIN countries c ON d.country_code = c.country_code
            """
    return pd.read_sql(query, engine)

@st.cache_data
def load_sunburst_data(year=None):
    """Fetch debt aggregated by Region, Income Group, and Country."""
    where_clause = f"WHERE d.year = {year}" if year and year != "All Years" else ""
    query = f"""
        SELECT c.region, c.income_group, c.country_name, SUM(d.debt_value) AS total_debt
        FROM debt_records d
        JOIN countries c ON d.country_code = c.country_code
        {where_clause}
        GROUP BY c.region, c.income_group, c.country_name;
    """
    return pd.read_sql(query, engine)

@st.cache_data
def load_scatter_data(year=None):
    """Fetch Total Debt and Debt Per Capita for the scatter plot."""
    where_clause = f"AND year = {year}" if year and year != "All Years" else ""
    query = f"""
        WITH total AS (
            SELECT country_code, SUM(debt_value) as total_debt
            FROM debt_records
            WHERE 1=1 {where_clause}
            GROUP BY country_code
        ),
        per_capita AS (
            SELECT country_code, SUM(debt_value) as debt_per_capita
            FROM debt_records
            WHERE indicator_code = 'DT.DOD.DECT.PC.CD' {where_clause}
            GROUP BY country_code
        )
        SELECT c.country_name, c.region, c.income_group, t.total_debt, p.debt_per_capita
        FROM countries c
        JOIN total t ON c.country_code = t.country_code
        JOIN per_capita p ON c.country_code = p.country_code;
    """
    return pd.read_sql(query, engine)

@st.cache_data
def load_heatmap_data(region=None, country=None):
    """Fetch top indicators over time for correlation heatmap."""
    where_clauses = []
    if region:
        where_clauses.append(f"c.region = '{region}'")
    if country and country != "All Countries":
        where_clauses.append(f"c.country_name = '{country}'")
        
    where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    
    top_ind_query = f"""
        SELECT i.indicator_code
        FROM debt_records d
        JOIN indicators i ON d.indicator_code = i.indicator_code
        JOIN countries c ON d.country_code = c.country_code
        {where_str}
        GROUP BY i.indicator_code
        ORDER BY SUM(d.debt_value) DESC
        LIMIT 5;
    """
    top_ind_df = pd.read_sql(top_ind_query, engine)
    if top_ind_df.empty:
        return pd.DataFrame()
        
    top_codes = tuple(top_ind_df['indicator_code'].tolist())
    if len(top_codes) == 1:
        top_codes = f"('{top_codes[0]}')"
    
    query = f"""
        SELECT d.year, i.indicator_name, SUM(d.debt_value) as debt_value
        FROM debt_records d
        JOIN indicators i ON d.indicator_code = i.indicator_code
        JOIN countries c ON d.country_code = c.country_code
        {where_str}
        {("AND" if where_str else "WHERE")} d.indicator_code IN {top_codes}
        GROUP BY d.year, i.indicator_name;
    """
    df = pd.read_sql(query, engine)
    if df.empty:
         return df
    return df.pivot(index='year', columns='indicator_name', values='debt_value')

# (Filters have been moved to Tab 1)

RANKING_MODES = {
    "Total Debt (USD)":       "total",
    "Debt Per Capita (USD)":  "per_capita",
    "Debt as % of GNI":       "pct_gni",
}
INDICATOR_CODES = {
    "per_capita": "DT.DOD.DECT.PC.CD",
    "pct_gni":    "DT.DOD.DECT.GN.ZS",
}
AXIS_LABELS = {
    "total":      "Total Debt (USD)",
    "per_capita": "Debt Per Capita (USD)",
    "pct_gni":    "External Debt (% of GNI)",
}

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Overview & Trends",
    "Debt Extremes", 
    "Geospatial Analysis", 
    "Income Groups",
    "Debt vs Per Capita",
    "Indicator Correlation",
    "Analytical Queries"
])

with tab1:
    with st.expander("Filter Options", expanded=True):
        col_f1, col_f2, col_f3, _ = st.columns([1, 1, 1, 2])
        with col_f1:
            regions_df = load_regions()
            selected_region = st.selectbox("Select a Global Region", regions_df['region'])
        with col_f2:
            countries_df = load_countries_by_region(selected_region)
            country_options = ["All Countries"] + sorted(countries_df['country_name'].tolist())
            selected_country = st.selectbox("Select a Country", country_options)
        with col_f3:
            years_df = load_years()
            year_options = ["All Years"] + [int(y) for y in years_df['year']]
            selected_year = st.selectbox("Select a Year", year_options)

    # Dynamic subtitle depending on selection
    if selected_country != "All Countries":
        kpi_title = f"Debt Overview for {selected_country}"
    elif selected_region:
        kpi_title = f"Debt Overview for {selected_region}"
    else:
        kpi_title = "Global Debt Overview"

    st.markdown(f"#### {kpi_title}")

    kpi_df = load_kpis(selected_region, selected_country, selected_year)
    total_debt = kpi_df['total_debt'].iloc[0] if not kpi_df.empty else 0.0
    total_countries = kpi_df['active_countries'].iloc[0] if not kpi_df.empty else 0

    # Check for NaN and format
    if pd.isna(total_debt):
        total_debt = 0.0
    if pd.isna(total_countries):
        total_countries = 0

    col1, col2 = st.columns(2)
    col1.markdown(f"""
        <div style='margin-bottom: 1rem;'>
            <div style='color: gray; font-size: 0.9rem;'>Total Logged Debt (USD)</div>
            <div style='font-size: 1.8rem; font-weight: bold;'>${total_debt:,.2f} USD</div>
        </div>
    """, unsafe_allow_html=True)
    
    col2.markdown(f"""
        <div style='margin-bottom: 1rem;'>
            <div style='color: gray; font-size: 0.9rem;'>Total Borrowing Countries</div>
            <div style='font-size: 1.8rem; font-weight: bold;'>{int(total_countries)}</div>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

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

with tab2:
    selected_label_t2 = st.radio("Rank countries by:", options=list(RANKING_MODES.keys()), key="rank_t2", horizontal=True)
    ranking_mode_t2 = RANKING_MODES[selected_label_t2]
    axis_label_t2 = AXIS_LABELS[ranking_mode_t2]

    st.subheader(f"Country-Wise Debt Extremes — Ranked by {selected_label_t2}")
    if selected_country != "All Countries":
        st.info("Extremes ranking is shown at the region level. To view rankings, select 'All Countries' in the sidebar.")
    else:
        if ranking_mode_t2 == "total":
            df_highest, df_lowest = load_total_debt_ranking(selected_region, selected_year)
        else:
            indicator_code_t2 = INDICATOR_CODES[ranking_mode_t2]
            df_highest, df_lowest = load_indicator_ranking(selected_region, indicator_code_t2, selected_year)

        if df_highest.empty and df_lowest.empty:
            st.info(f"No ranking data available for '{selected_label_t2}' in this region/year.")
        else:
            df_lowest_display  = df_lowest.sort_values('metric_value', ascending=True)
            df_highest_display = df_highest.sort_values('metric_value', ascending=True)
            df_combined        = pd.concat([df_lowest_display, df_highest_display], ignore_index=True)

            fig_combined = px.bar(
                df_combined,
                x='metric_value',
                y='country_name',
                orientation='h',
                labels={'metric_value': axis_label_t2, 'country_name': 'Country'},
                color='metric_value',
                color_continuous_scale='RdYlGn_r',
            )

            fig_combined.update_layout(
                yaxis={
                    'categoryorder': 'array',
                    'categoryarray': df_combined['country_name'].tolist(),
                },
                height=560,
                coloraxis_colorbar=dict(title=axis_label_t2),
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

with tab3:
    st.subheader("Global Debt Choropleth Map")
    selected_label_t3 = st.radio("Show map for:", options=list(RANKING_MODES.keys()), key="rank_t3", horizontal=True)
    ranking_mode_t3 = RANKING_MODES[selected_label_t3]
    indicator_code_t3 = INDICATOR_CODES.get(ranking_mode_t3)
    axis_label_t3 = AXIS_LABELS[ranking_mode_t3]
    
    df_map = load_map_data(selected_year, ranking_mode_t3, indicator_code_t3)
    if not df_map.empty:
        # Calculate the 95th percentile to cap the color scale and avoid outlier skewing
        v_min = df_map['metric_value'].min()
        v_max = df_map['metric_value'].quantile(0.95)

        fig_map = px.choropleth(
            df_map,
            locations="country_code",
            color="metric_value",
            hover_name="country_name",
            color_continuous_scale="RdYlGn_r",
            range_color=[v_min, v_max],
            title=f"{selected_label_t3} by Country",
            labels={'metric_value': axis_label_t3}
        )
        fig_map.update_layout(
            height=550,
            margin={"r":0, "t":40, "l":0, "b":0}
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("No data available for the map.")

with tab4:
    st.subheader("Debt Composition & Income Group Analysis")
    df_sun = load_sunburst_data(selected_year)
    if not df_sun.empty:
        fig_box = px.box(
            df_sun,
            x='income_group',
            y='total_debt',
            color='region',
            title="Debt Distribution by Income Group",
            log_y=True
        )
        st.plotly_chart(fig_box, use_container_width=True)
    else:
        st.info("No data available for income group analysis.")

with tab5:
    st.subheader("Debt vs Per Capita")
    
    df_scatter = load_scatter_data(selected_year)
    if not df_scatter.empty:
        # Fill NaN values carefully for scatter
        df_scatter = df_scatter.dropna(subset=['total_debt', 'debt_per_capita'])
        fig_scatter = px.scatter(
            df_scatter,
            x="total_debt",
            y="debt_per_capita",
            color="region",
            hover_name="country_name",
            log_x=True,
            log_y=True,
            title="Total Debt vs Debt Per Capita"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("No scatter data available.")
        
with tab6:
    st.subheader("Indicator Correlation")
        
    df_heat = load_heatmap_data(selected_region, selected_country)
    if not df_heat.empty:
        # Drop year index for correlation and compute matrix
        corr = df_heat.corr()
        fig_heat = px.imshow(
            corr,
            text_auto=True,
            aspect="auto",
            title="Indicator Correlation Heatmap"
        )
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("No heatmap data available.")

with tab7:
    st.subheader("SQL Analytics Hub 📊")
    st.markdown("Explore database insights using predefined analytical queries. You can also customize and run custom SQL queries.")
    
    import re
    from pathlib import Path
    
    @st.cache_data
    def load_predefined_queries():
        sql_file_path = Path(__file__).resolve().parent.parent / "src" / "analytical queries.sql"
        if not sql_file_path.exists():
            return {}
            
        with open(sql_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        categories = re.split(r'-- ====================================================================\n-- SECTION \d+: (.*?)\n-- ====================================================================', content)
        
        queries = {}
        query_id = 1
        for i in range(1, len(categories), 2):
            category_name = categories[i].strip().title()
            category_content = categories[i+1]
            
            query_blocks = re.split(r'-- (\d+\.\s.*?)\n', category_content)
            
            for j in range(1, len(query_blocks), 2):
                title_desc = query_blocks[j].strip()
                sql = query_blocks[j+1].strip()
                
                queries[query_id] = {
                    "category": category_name,
                    "title": title_desc,
                    "description": title_desc,
                    "sql": sql
                }
                query_id += 1
                
        return queries

    predefined_queries = load_predefined_queries()
    
    if predefined_queries:
        categories = sorted(list(set(q["category"] for q in predefined_queries.values())))
        selected_category = st.selectbox("Select Query Category", options=categories)
        
        cat_queries = {qid: q for qid, q in predefined_queries.items() if q["category"] == selected_category}
        query_options = {q["title"]: qid for qid, q in cat_queries.items()}
        selected_title = st.selectbox("Select Query", options=list(query_options.keys()))
        selected_qid = query_options[selected_title]
        query_info = predefined_queries[selected_qid]
        
        st.info(f"**Query Description**: {query_info['description']}")
        
        edit_mode = st.checkbox("Edit / Customize SQL Query 📝", value=False)
        if edit_mode:
            sql_to_run = st.text_area("SQL Statement", value=query_info["sql"], height=200)
        else:
            sql_to_run = query_info["sql"]
            st.code(sql_to_run, language="sql")
            
        if st.button("Run Query ⚡", use_container_width=True):
            with st.spinner("Executing query..."):
                try:
                    # Strip out SQL comments before checking the command type
                    sql_no_comments = re.sub(r'--.*?\n', '', sql_to_run + '\n').strip().upper()
                    
                    if sql_no_comments.startswith(("SELECT", "WITH")):
                        res_df = pd.read_sql(sql_to_run, engine)
                        st.success(f"Query returned {len(res_df)} record(s).")
                        st.dataframe(res_df, use_container_width=True)
                    else:
                        from sqlalchemy import text
                        with engine.begin() as conn:
                            conn.execute(text(sql_to_run))
                        st.success("Query executed successfully. (No data to display)")
                except Exception as e:
                    st.error(f"Failed to execute query: {e}")
    else:
        st.error("Could not load predefined queries from the SQL file.")
