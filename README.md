<div align="center">

# 🔬 PeopleLens

### Workforce Analytics Platform — NimbusTech IT Services

**Problem Code:** A4 | **Segment:** Insights & Decision Intelligence  
**Target Roles:** People Analytics, Data Analyst, HR Analytics, BI Analyst

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.36-red.svg)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📋 One-Line Description

> A workforce analytics platform that turns NimbusTech's HR data into attrition predictions, manager-effect rankings, pay-fairness audits, and retention curves — replacing 60% of CHRO spreadsheet time.

---

## 🏢 Business Context

You are the **People Analytics Partner at NimbusTech**, a 35,000-employee IT services company. Voluntary attrition is at 18% — above the industry norm of 14–16%. HR Business Partners spend 60% of their time in spreadsheets. The CHRO wants one platform that answers:

- Which managers have the highest attrition in their teams?
- Are we losing more people from specific projects?
- Are our pay bands fair across genders?
- What's the retention curve for new joiners by college tier?

**PeopleLens** answers all four.

---

## 🏗️ Architecture Diagram (C4 Level 1)

```
┌─────────────────────────────────────────────────────────────────┐
│                         NIMBUTECH HR SYSTEM                     │
│  [HR Data Sources] → Employee, Salary, Performance, Projects,   │
│                       Learning, Exit, Manager Hierarchy          │
└───────────────────────────────┬─────────────────────────────────┘
                                │ CSV Export / API
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA GENERATION LAYER                        │
│  Synthetic HR Data Generator (Faker + NumPy)                    │
│  10,000+ employees · 5 years · No PII                           │
└───────────────────────────────┬─────────────────────────────────┘
                                │ CSVs → data/synthetic/
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    POSTGRESQL DATA WAREHOUSE                    │
│  RAW → STAGING → MARTS (Star Schema) → ANALYTICS               │
│  dbt transformations · SCD-2 employee history                   │
└───────────────────────────────┬─────────────────────────────────┘
                                │ SQL views
                                ▼
┌────────────────────────────────────────────────────────────────┐
│              ANALYTICS & MACHINE LEARNING ENGINE                │
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────────────┐ │
│  │  Attrition Risk │  │Manager Effect│  │   Pay Fairness    │ │
│  │  XGBoost + SHAP │  │ Rolling 12m  │  │ Bootstrap CI + t  │ │
│  └─────────────────┘  └──────────────┘  └───────────────────┘ │
│  ┌──────────────────────────────────────┐                       │
│  │  Retention Analysis (Kaplan-Meier)   │                       │
│  └──────────────────────────────────────┘                       │
└───────────────────────────────┬────────────────────────────────┘
                                │ REST API
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                            │
│  /api/v1/executive · /attrition · /manager-effect               │
│  /pay-fairness · /retention                                     │
│  Privacy Layer: k-anonymity (k≥10) · Aggregated only            │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTP
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   STREAMLIT DASHBOARD                           │
│  Tab 1: Executive Briefing  Tab 2: Attrition Analysis           │
│  Tab 3: Manager Effect      Tab 4: Pay Fairness                 │
│  Tab 5: Retention Curves                                        │
└─────────────────────────────────────────────────────────────────┘
                                │ Deployed on
                                ▼
                    Render (Free Tier) + Railway (PostgreSQL)
```

---

## 🔧 Tech Stack

| Component | Choice | Why |
|-----------|--------|-----|
| **Language** | Python 3.11 | Ecosystem depth for data + ML + API |
| **Database** | PostgreSQL 16 | ACID transactions, SCD-2 support, dbt-native |
| **Analytics Engineering** | dbt | Version-controlled SQL transforms, lineage, tests |
| **ML Model** | XGBoost | GBDT handles imbalanced HR data well; SHAP-compatible |
| **Explainability** | SHAP | TreeExplainer for per-employee risk explanation |
| **Survival Analysis** | lifelines | Industry-standard Kaplan-Meier; Python-native |
| **Statistics** | scipy + statsmodels | Welch t-test, bootstrap CIs for pay fairness |
| **Backend** | FastAPI | Async, auto Swagger docs, Pydantic validation |
| **Dashboard** | Streamlit | Fastest time-to-demo for analytics products |
| **Visualisation** | Plotly | Interactive charts; works in Streamlit natively |
| **Containerisation** | Docker + Compose | One-command local dev + prod parity |
| **Deployment** | Render + Railway | Free tier; always-on dashboard + managed PG |
| **CI/CD** | GitHub Actions | Automated lint + test on every push |
| **Code Quality** | ruff + black | Fast linting + consistent formatting |

---

## 📁 Project Structure

```
PeopleLens/
├── backend/                   # FastAPI backend (5 analytics routes)
│   └── app/
│       ├── api/routes/        # executive, attrition, manager_effect, pay_fairness, retention
│       ├── core/              # config, database, security
│       └── main.py
├── dashboard/                 # Streamlit multi-page dashboard
│   ├── app.py                 # Home page
│   └── pages/                 # 5 analytical pages
├── data_generator/            # Synthetic HR data (7 generators + orchestrator)
├── analytics/                 # Core analytics modules (no ML dependencies)
├── ml/                        # XGBoost model pipeline
├── database/                  # PostgreSQL schema + loader
├── dbt/peoplelens/            # dbt models: staging → marts → analytics
├── docs/                      # ADRs, CHRO memo, API docs, data dictionary
├── sql/                       # SQL portfolio (6 workforce queries)
├── tests/                     # Unit + integration tests
├── models/                    # Trained model artifacts (gitignored)
├── data/synthetic/            # Generated CSV data (gitignored for large runs)
└── docker-compose.yml         # PostgreSQL + API + Dashboard
```

---

## ⚡ Quick Start (15 minutes)

### Option A — Docker (Recommended)

```bash
# 1. Clone the repo
git clone https://github.com/saiganeshgudla/People-Analytics-IT-Services-Workforce-Analytics.git
cd People-Analytics-IT-Services-Workforce-Analytics

# 2. Set up environment
cp .env.example .env
# Edit .env if you want custom DB credentials

# 3. Start all services (PostgreSQL + API + Dashboard)
docker-compose up -d

# 4. Generate synthetic data
docker-compose exec api python data_generator/generate_dataset.py

# 5. Load data into PostgreSQL
docker-compose exec api python database/load_data.py

# 6. Train the attrition model
docker-compose exec api python ml/train.py

# 7. Open the dashboard
open http://localhost:8501
```

### Option B — Local (No Docker)

```bash
# Prerequisites: Python 3.11+, PostgreSQL 16+ (or skip DB, uses CSV directly)

# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate synthetic HR data (takes ~30-60s for 12,000 employees)
python data_generator/generate_dataset.py

# 3. (Optional) Load into PostgreSQL
cp .env.example .env  # edit with your DB credentials
python database/load_data.py

# 4. Train the ML model
python ml/train.py

# 5. Run the dashboard (works without PostgreSQL using CSVs directly)
streamlit run dashboard/app.py

# 6. (Optional) Run the API separately
uvicorn backend.app.main:app --reload
# API docs: http://localhost:8000/docs
```

---

## 📊 Dashboard Tabs

| Tab | What it shows |
|-----|--------------|
| 🎯 **Executive Briefing** | 5 KPI cards + 3 CHRO insight sentences + yearly trend + dept attrition |
| ⚠️ **Attrition Analysis** | Risk distribution (Low/Med/High), breakdowns by dept/location/level/tenure |
| 👔 **Manager Effect** | Rolling 12m team attrition vs peer benchmark, flagged managers, error bars |
| ⚖️ **Pay Fairness** | Gender pay ratio by level/dept/location, ±5% disparity flags, bootstrap CIs |
| 📈 **Retention Curves** | Kaplan-Meier by college tier, cohort retention table (6m/12m/24m/36m) |

---

## 🔒 Privacy Design

PeopleLens is built **privacy-first**:

- ✅ **No PII**: Only `employee_id` used — no names, emails, phone numbers
- ✅ **k-Anonymity (k≥10)**: Groups with <10 members suppressed in all dashboard views
- ✅ **Aggregated output only**: No row-level data exposed via API or dashboard
- ✅ **RBAC-ready**: API JWT auth with role-based access (admin/analyst/viewer)
- ✅ **GDPR-aligned schema design**: No sensitive personal data in warehouse

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage report
pytest tests/ --cov=. --cov-report=html

# Run a specific test
pytest tests/test_api.py -v
```

---

## 📄 Documentation

| Document | Location |
|----------|----------|
| Architecture Decision Records (4 ADRs) | `docs/adr/` |
| CHRO Memo: Year-1 Attrition Crisis | `docs/memo/CHRO_Memo.md` |
| API Reference | `docs/api/api_documentation.md` |
| Data Dictionary | `docs/database/data_dictionary.md` |
| SQL Portfolio (6 queries) | `sql/workforce_queries.sql` |

---

## 📅 Week 1 Status (30 June 2026)

**What's done:**
- ✅ Full project scaffold (10 phases, 60+ files)
- ✅ Synthetic HR data generator (7 generators, 12,000 employees, 5 years)
- ✅ PostgreSQL schema (raw → staging → marts → analytics, 4 schemas, 18+ tables)
- ✅ Analytics engine (attrition, manager-effect, pay fairness, retention, exec KPIs)
- ✅ ML pipeline (feature engineering, XGBoost training, SHAP, batch prediction)
- ✅ FastAPI backend (5 routes, k-anonymity, aggregated output only)
- ✅ Streamlit dashboard (5 pages, dark mode, Plotly charts)
- ✅ Documentation starter (ADRs, CHRO Memo, SQL portfolio)

**What's stuck:** Nothing — proceeding to dbt models and tests in Week 2.

**Week 2 goals:**
1. Complete dbt staging → mart → analytics model chain and run end-to-end
2. Write full test suite (unit + integration, target 80% coverage)
3. Deploy to Render (dashboard) + Railway (PostgreSQL)

---

## 👤 Author

**Student:** Sai Ganesh Gudla  
**Segment:** A4 — People Analytics (IT Services Workforce Analytics)  
**Target Roles:** People Analytics Engineer, Data Analyst, HR Analytics  
**Target Companies:** TCS, Infosys, Wipro, LTIMindtree, Mphasis, Goldman Sachs GCC

---

*NimbusTech is a fictional company used for this internship project. All data is fully synthetic.*