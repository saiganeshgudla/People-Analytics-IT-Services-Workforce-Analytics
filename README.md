# People-Analytics-IT-Services-Workforce-Analytics

# 🏗️ System Architecture

## Overview

PeopleLens follows a modern **multi-layered enterprise architecture** that separates data ingestion, storage, transformation, machine learning, analytics, API services, visualization, and governance. This design ensures scalability, maintainability, security, and explainability while supporting workforce analytics for large organizations.

The architecture simulates a real-world HR analytics platform capable of processing workforce data, generating predictive insights, and delivering executive dashboards for HR leaders.

---

## Architecture Diagram

> *(Insert Architecture Diagram Here)*

<p align="center">
  <img src="docs/images/architecture.png" alt="PeopleLens Architecture" width="100%">
</p>

---

# Architecture Layers

## Layer 1 — Data Sources

The platform ingests workforce information from multiple HR domains along with a synthetic data generator used for development and testing.

### HR Data Sources

- Employee Master
- Compensation History
- Performance Ratings
- Project Assignments
- Learning Records
- Exit Records
- Manager Hierarchy

### Synthetic Data Generator

- Faker
- Pandas
- NumPy
- Random
- 10,000+ Employees
- 5 Years Historical Workforce Data

---

## Layer 2 — Data Ingestion & Validation

This layer validates and standardizes incoming HR data before it is stored.

### Components

- CSV Loader
- Data Validation
- Schema Validation
- Missing Value Handling
- Duplicate Detection
- Logging & Audit Trail

**Technology**

- Python
- Pandas

---

## Layer 3 — PostgreSQL Data Warehouse

All workforce information is organized using a dimensional data warehouse.

### RAW Layer

- raw_employee
- raw_salary
- raw_project
- raw_learning
- raw_exit
- raw_manager

### STAGING Layer

- stg_employee
- stg_salary
- stg_project
- stg_manager
- stg_exit

### MARTS Layer

Dimensions

- dim_employee
- dim_manager
- dim_project
- dim_location

Facts

- fact_salary
- fact_attrition
- fact_learning
- fact_performance

### Analytics Layer

- Executive KPIs
- ML Features
- Aggregated Reports
- Business Metrics

---

## Layer 4 — Analytics Engineering (dbt)

dbt transforms raw HR data into analytics-ready datasets.

### Responsibilities

- Data Cleaning
- Business Rules
- Feature Engineering
- Slowly Changing Dimensions (SCD Type 2)
- Dimension Modeling
- Fact Modeling
- Business Metrics

Technology:

- dbt

---

## Layer 5 — Analytics & Machine Learning Engine

The core intelligence layer performs workforce analytics and predictive modeling.

### Attrition Prediction

- Feature Engineering
- Logistic Regression
- Gradient Boosting
- XGBoost
- Attrition Risk Score
- SHAP Explainability

### Manager Effect Analysis

- Rolling 12-Month Attrition
- Peer Benchmarking
- Confidence Intervals
- Manager Ranking

### Pay Fairness Analysis

- Compensation Ratio
- Gender Pay Analysis
- Bootstrap Confidence Intervals
- Statistical Testing
- Fairness Flags

### Retention Analytics

- Kaplan-Meier Survival Analysis
- College Tier Analysis
- Joining Cohort Analysis
- Role-Based Retention
- Retention Curves

### Executive KPI Engine

- Overall Attrition
- Average Salary
- Promotion Rate
- Learning Hours
- Diversity Metrics
- High-Risk Employees

Technologies

- Scikit-Learn
- XGBoost
- SHAP
- SciPy
- Statsmodels
- lifelines

---

## Layer 6 — Model Registry

Stores trained machine learning artifacts.

### Components

- Trained Models
- Feature Store
- SHAP Artifacts
- Model Versioning

Technology

- Pickle
- MLflow (Optional)

---

## Layer 7 — FastAPI Backend

Provides secure APIs for dashboards and analytics.

### Features

- REST APIs
- Authentication
- Role-Based Access Control (RBAC)
- Aggregation Engine
- Privacy Layer
- JSON Response Formatter

### API Endpoints

- `/dashboard`
- `/attrition`
- `/manager-effect`
- `/pay-fairness`
- `/retention`
- `/executive`

Technology

- FastAPI

---

## Layer 8 — Executive Dashboard

Interactive dashboards provide workforce insights to HR leaders.

### Dashboard Modules

### Executive Briefing

- KPI Cards
- Executive Summary
- Business Insights

### Attrition Dashboard

- Risk Distribution
- SHAP Feature Importance
- Department Attrition
- Location Analysis

### Manager Effect Dashboard

- Manager Rankings
- Benchmark Comparison
- Rolling Attrition

### Pay Fairness Dashboard

- Salary Distribution
- Gender Pay Ratio
- Heatmaps

### Retention Dashboard

- Kaplan-Meier Curves
- Cohort Analysis
- College Tier Comparison

Technologies

- Streamlit
- Plotly
- Power BI

---

## Layer 9 — Business Users

The platform serves multiple stakeholders.

- CHRO
- HR Business Partners
- Department Managers
- People Analytics Team
- Business Leaders
- Executives

---

# Security & Governance

PeopleLens is designed with privacy-first principles.

### Security Features

- Authentication
- Role-Based Access Control (RBAC)
- Encryption
- Data Masking
- K-Anonymity (k ≥ 10)
- Aggregated Reporting Only
- Audit Logs
- GDPR-Compliant Design
- No Personally Identifiable Information (PII)

---

# Deployment & DevOps

Deployment pipeline follows modern DevOps practices.

GitHub

↓

GitHub Actions

↓

Docker

↓

Render

↓

Railway

↓

PostgreSQL Cloud

↓

Monitoring & Logging

---

# End-to-End Data Flow

```text
HR Data Sources
        │
        ▼
Data Ingestion & Validation
        │
        ▼
PostgreSQL Data Warehouse
        │
        ▼
dbt Transformations
        │
        ▼
Analytics & Machine Learning Engine
        │
        ▼
Model Registry
        │
        ▼
FastAPI Backend
        │
        ▼
Executive Dashboard
        │
        ▼
Business Users
```

---

# Design Principles

- Modular Architecture
- Scalable Data Pipeline
- Explainable AI (SHAP)
- Privacy by Design
- Enterprise Security
- Analytics-First Design
- Cloud Ready
- Production-Oriented
- Maintainable & Extensible

---

# Key Technologies

| Category | Technology |
|-----------|------------|
| Programming | Python |
| Database | PostgreSQL |
| Analytics Engineering | dbt |
| Machine Learning | Scikit-Learn, XGBoost |
| Statistics | SciPy, Statsmodels |
| Survival Analysis | lifelines |
| Explainability | SHAP |
| Backend | FastAPI |
| Dashboard | Streamlit, Plotly, Power BI |
| DevOps | Docker, GitHub Actions |
| Deployment | Render, Railway |

---

# Architecture Highlights

- Enterprise-grade layered architecture
- End-to-end workforce analytics pipeline
- Explainable AI for attrition prediction
- Privacy-preserving analytics (k-anonymity)
- Modular microservice-ready backend
- Executive dashboards for strategic HR decision-making
- Cloud-ready deployment architecture
- Production-oriented design inspired by Fortune 500 HR analytics platforms