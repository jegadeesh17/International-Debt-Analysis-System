# International Debt Analysis System

---

### **Project Overview**

Developing nations frequently rely on external debt to fund critical infrastructure projects, healthcare, and economic expansion. Managing and auditing this debt is vital to prevent default risk and economic instability. This project builds an **International Debt Analysis System** using database management (PostgreSQL), data engineering, and interactive analytics to explore global debt statistics.

The system ingests the World Bank's International Debt Statistics (IDS), processes and structures the information into a relational database, executes complex analytical queries, and serves interactive visualizations through a Streamlit dashboard.

---

### **Key Features**

* **Relational Database Pipeline:** Loads large-scale International Debt Statistics into PostgreSQL.
* **Data Inspection & Cleaning:** Standardizes country names, handles missing indicators, and normalizes column headers.
* **Advanced Debt Analytics (SQL):** Runs analytical queries (aggregates, window functions, and rankings) to discover top debtors and category trends.
* **Interactive Streamlit Web Dashboard:** Visualizes debt concentration, regional breakdowns, and indicators.
* **Detailed Search & Filter Engine:** Allows filtering debt metrics by country, region, and specific economic series.

---

### **Dataset**

* **Source:** World Bank International Debt Statistics (IDS)
* **Coverage:** Low- and middle-income countries' external debt statistics
* **Data Type:** Multi-table relational and time-series metadata files

#### **Included Files**

* `IDS_ALLCountries_Data.csv`: Primary time-series debt statistics.
* `IDS_CountryMetaData.csv`: Geographic regions and classification groups.
* `IDS_SeriesMetaData.csv`: Descriptions of debt indicators (e.g. PPG bilateral, multilateral, IMF buybacks).
* `IDS_FootNoteMetaData.csv`: Specific dataset annotations.

---

### **Project Structure**

```bash
International-Debt-Analysis/
│
├── data/                         # World Bank IDS CSV datasets
│
├── src/
│   ├── load_data.py              # PostgreSQL ingestion pipeline
│   ├── inspect_and_clean.py      # Preprocessing and standardizing script
│   └── analytical queries.sql    # Analytical PostgreSQL scripts
│
├── app/
│   └── app.py                    # Streamlit web application
│
├── .gitignore
└── README.md
```

---

### **How It Works**

### **1. Data Ingestion & Relational Setup**

* Reads source metadata and large-scale data series.
* Standardizes records, maps regional metadata, and streams them into a structured database schema:

```python
# From src/load_data.py
import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine

# Load credentials and establish engine
load_dotenv()
db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(db_url)
df.to_sql('debt_data', engine, if_exists='replace', index=False)
```

---

### **2. Analytical Queries (PostgreSQL)**

Executes queries to uncover high-level insights:
* **Total Debt Accumulated:** Sum of overall external debt across nations.
* **Top Debtor Nations:** Ranks countries by outstanding liabilities.
* **Debt Categories:** Evaluates differences between multilateral, bilateral, and private creditor loans.

---

### **Interactive Application Deployment**

The project features a rich **Streamlit Web Application** displaying debt distribution maps and indicators.

#### **To Launch the Platform Locally:**
```powershell
python -m streamlit run ".\International Debt Analysis System\app\app.py"
```

---

### **Technology Stack**

| Category             | Tools                                         |
| -------------------- | --------------------------------------------- |
| Programming          | Python                                        |
| Database Engine      | PostgreSQL                                    |
| Database Connection  | SQLAlchemy, Psycopg2                          |
| Data Processing      | Pandas, NumPy                                 |
| Web Framework        | Streamlit                                     |
| Visualization        | Plotly, Matplotlib, Seaborn                   |

---

### **Getting Started**

### **1. Setup Database**

Create a PostgreSQL database named `debt_analysis` and ensure your database server is running.

---

### **2. Install Dependencies**

```bash
pip install pandas numpy streamlit psycopg2 sqlalchemy plotly matplotlib seaborn python-dotenv
```

---

### **3. Configure Environment Variables**

Create a `.env` file in the root of the project folder:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=international_debt
DB_USER=postgres
DB_PASSWORD=your_postgres_password
```

---

### **3. Ingest Data**

Execute the loading and processing scripts to populate your database tables:

```bash
python src/load_data.py
python src/inspect_and_clean.py
```

---

### **4. Launch the Dashboard**

Start the Streamlit application server:

```bash
streamlit run app/app.py
```

---

### **Example Use Case**

Financial analysts and policy researchers can use this platform to:
1. Identify regions experiencing severe debt accumulation trends.
2. Track repayments due to private vs. official lenders.
3. Compare debt-to-GNI ratios of developing economies.

---

### **Future Improvements**

* Predictive modeling to forecast risk of default based on historic trends.
* Automated report exporter (PDF) summarizing country profiles.
* Dynamic integration with real-time World Bank APIs.

---

### **Contributors**

* **Jegadeesh D** — Database setup, SQL analytics, ingestion pipeline, and interactive dashboard creation

---

### **License**

MIT License
