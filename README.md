# International Debt Analysis System

---

### **Project Overview**

Global debt statistics from the World Bank provide critical insight into the financial health of low- and middle-income nations. This project builds an end-to-end data engineering and analytics platform to ingest, structure, and explore International Debt Statistics using Python, PostgreSQL, and Streamlit.

The system implements a complete ETL pipeline that cleans and normalizes raw World Bank CSV data into a PostgreSQL Star Schema, enabling high-performance analytical queries. An interactive Streamlit dashboard allows stakeholders to explore global debt trends, regional comparisons, and country-level breakdowns through rich visualizations.

---

### **Key Features**

* **ETL Data Pipeline:** Loads and transforms raw World Bank CSV data using Pandas into a normalized relational format.
* **Star Schema Database Design:** Models data into a PostgreSQL fact-dimension schema for optimized analytical queries.
* **High-Performance Ingestion:** Uses Psycopg2 `execute_values` to batch-ingest hundreds of thousands of records rapidly.
* **Interactive Streamlit Dashboard:** Live deployment with KPI cards, trend lines, donut charts, and ranked bar charts.
* **Advanced Query Caching:** Implements `st.cache_data` and `st.cache_resource` to minimize redundant database hits.
* **Dynamic Filtering:** Region, country, and year filters that propagate across all dashboard views.
* **SQL Injection Protection:** All user inputs are escaped via a custom `_esc()` helper before SQL interpolation.
* **Analytical SQL Scripts:** Includes curated SQL queries for exploratory and insight-driven analysis.

---

### **Dataset**

* **Source:** World Bank International Debt Statistics
* **In repo:** `IDS_ALLCountries_Data_sample.csv` plus full metadata CSVs
* **Full data:** Place `IDS_ALLCountries_Data.csv` in `data/` — see [data/DATA_SETUP.md](data/DATA_SETUP.md)
* **Coverage:** Low- and middle-income countries, multi-year debt records
* **Format:** Wide-format CSV (years as columns), normalized to long format

#### **Key Fields**

* Country name and country code
* Indicator name and indicator code
* Annual debt values by year
* World region classification

---

### **Project Structure**

```bash
InternationalDebtAnalysis/
│
├── app/                          # Streamlit application files
│   └── app.py                    # Main Streamlit dashboard
├── data/                         # Project datasets
├── docs/                         # Documentation and visualizations
├── models/                       # Saved trained models
├── notebooks/                    # Jupyter notebooks (Source of Truth)
├── src/                          # Core Python logic and scripts
├── requirements.txt              # Python dependencies
└── README.md
```

---

### **How It Works**

### **1. Data Preprocessing & ETL**

* Loads raw World Bank CSVs with Latin-1 encoding support
* Strips trailing whitespace and handles missing values
* Unpivots wide-format (year columns) into normalized long format

| Step                 | Operation                                      |
| -------------------- | ---------------------------------------------- |
| Encoding Fix         | Handles Latin-1 encoded characters             |
| Melt / Unpivot       | Converts year columns into row-level records   |
| Null Handling        | Drops rows with missing debt values            |
| Column Normalization | Standardizes column names for schema alignment |

---

### **2. Star Schema Database Design**

The system models the data into a PostgreSQL Star Schema with:

```sql
-- Dimension table: Countries
CREATE TABLE countries (
    country_code VARCHAR(10) PRIMARY KEY,
    country_name TEXT,
    region TEXT
);

-- Dimension table: Indicators
CREATE TABLE indicators (
    indicator_code VARCHAR(50) PRIMARY KEY,
    indicator_name TEXT
);

-- Fact table: Debt Records
CREATE TABLE debt_records (
    id SERIAL PRIMARY KEY,
    country_code VARCHAR(10) REFERENCES countries(country_code),
    indicator_code VARCHAR(50) REFERENCES indicators(indicator_code),
    year INT,
    debt_value NUMERIC
);
```

---

### **3. High-Performance Ingestion**

Batch ingestion using Psycopg2 `execute_values` for fast, transactional data loading:

```python
from psycopg2.extras import execute_values

execute_values(cursor, "INSERT INTO debt_records VALUES %s", records)
```

---

### **Model Performance**

| Metric                   | Result                    |
| ------------------------ | ------------------------- |
| Records Ingested         | 500,000+                  |
| Query Response Time      | Sub-second (with caching) |
| Dashboard Filter Latency | Minimal (cached queries)  |

---

### **Interactive Application Deployment**

The project features an interactive **Streamlit Web Application** with KPI cards, Plotly trend lines, donut charts, and ranked country bar charts — all driven by live PostgreSQL queries.

#### **To Launch the Platform Locally:**
```powershell
streamlit run app/app.py
```

---

### **Technology Stack**

| Category             | Tools                      |
| -------------------- | -------------------------- |
| Programming          | Python                     |
| Data Processing      | Pandas, NumPy              |
| Database             | PostgreSQL, Psycopg2       |
| ORM / Schema         | SQLAlchemy                 |
| Visualization        | Plotly                     |
| Notebook Environment | Jupyter Notebook           |
| Web Framework        | Streamlit                  |

---

### **Getting Started**

### **1. Clone Repository**

```bash
git clone https://github.com/jegadeesh17/International-Debt-Analysis-System.git

cd InternationalDebtAnalysis
```

---

### **2. Configure Database**

Ensure your local PostgreSQL server is running and has the `international_debt` database created. Update the `.env` file with your credentials:

```env
DB_HOST=localhost
DB_NAME=international_debt
DB_USER=your_user
DB_PASSWORD=your_password
```

---

### **3. Install Dependencies**

```bash
pip install -r requirements.txt
```

---

### **4. Run ETL Pipeline**

```bash
python -m src.load_data
```

---

### **5. Launch Dashboard**

```bash
streamlit run app/app.py
```

---

### **Example Use Case**

A policy analyst or economist can use this platform to:

1. Compare total debt levels across world regions over time
2. Identify the most heavily indebted countries within a region
3. Analyze which debt indicators (e.g., long-term debt, IDA debt) dominate
4. Drill down into a specific country's debt trajectory year by year

---

### **Future Improvements**

* Real-time World Bank API integration for live data updates
* Predictive debt forecasting using time-series models
* PDF report export for analytical summaries
* Country-level risk scoring and economic health indicators

---

### **Contributors**

* **Jegadeesh D** — Data engineering, ETL pipeline, PostgreSQL schema design, Streamlit dashboard, and analytical SQL

---

### **License**

MIT License
