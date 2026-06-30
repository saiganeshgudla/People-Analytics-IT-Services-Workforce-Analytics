-- ══════════════════════════════════════════════════════════════════════════════
-- PeopleLens — PostgreSQL Schema
-- Version: 1.0.0
-- Layers: RAW → STAGING → MARTS → ANALYTICS
-- ══════════════════════════════════════════════════════════════════════════════

-- ── Extensions ────────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Schemas ───────────────────────────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;
CREATE SCHEMA IF NOT EXISTS analytics;

-- ══════════════════════════════════════════════════════════════════════════════
-- RAW LAYER — Direct ingestion from source files, no transformations
-- ══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS raw.raw_employee (
    employee_id         VARCHAR(20) PRIMARY KEY,
    join_date           DATE,
    birth_year          INTEGER,
    gender              VARCHAR(10),
    department          VARCHAR(50),
    role                VARCHAR(50),
    level               VARCHAR(20),
    location            VARCHAR(50),
    college_tier        INTEGER,         -- 1=IIT/NIT, 2=State Engg, 3=Other
    is_active           BOOLEAN,
    exit_date           DATE,
    exit_reason         VARCHAR(50),
    manager_id          VARCHAR(20),
    _loaded_at          TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.raw_salary (
    record_id           SERIAL PRIMARY KEY,
    employee_id         VARCHAR(20),
    effective_date      DATE,
    base_salary         NUMERIC(12, 2),
    currency            VARCHAR(5) DEFAULT 'INR',
    salary_band         VARCHAR(10),
    _loaded_at          TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.raw_performance (
    record_id           SERIAL PRIMARY KEY,
    employee_id         VARCHAR(20),
    review_year         INTEGER,
    review_cycle        VARCHAR(20),     -- H1, H2, Annual
    rating              NUMERIC(3, 1),   -- 1.0 to 5.0
    _loaded_at          TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.raw_project (
    record_id           SERIAL PRIMARY KEY,
    employee_id         VARCHAR(20),
    project_id          VARCHAR(20),
    project_name        VARCHAR(100),
    project_type        VARCHAR(50),
    client_industry     VARCHAR(50),
    start_date          DATE,
    end_date            DATE,
    role_in_project     VARCHAR(50),
    _loaded_at          TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.raw_learning (
    record_id           SERIAL PRIMARY KEY,
    employee_id         VARCHAR(20),
    year                INTEGER,
    quarter             INTEGER,
    learning_hours      NUMERIC(6, 1),
    certifications      INTEGER,
    _loaded_at          TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.raw_exit (
    record_id           SERIAL PRIMARY KEY,
    employee_id         VARCHAR(20),
    exit_date           DATE,
    exit_reason         VARCHAR(50),
    last_manager_id     VARCHAR(20),
    tenure_days         INTEGER,
    voluntary           BOOLEAN,
    _loaded_at          TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.raw_manager (
    record_id           SERIAL PRIMARY KEY,
    manager_id          VARCHAR(20),
    level               VARCHAR(20),
    department          VARCHAR(50),
    location            VARCHAR(50),
    team_size           INTEGER,
    effective_date      DATE,
    _loaded_at          TIMESTAMP DEFAULT NOW()
);

-- ══════════════════════════════════════════════════════════════════════════════
-- STAGING LAYER — Cleaned, typed, deduplicated
-- ══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS staging.stg_employee (
    employee_id         VARCHAR(20) PRIMARY KEY,
    join_date           DATE NOT NULL,
    birth_year          INTEGER,
    gender              VARCHAR(10) NOT NULL,
    department          VARCHAR(50) NOT NULL,
    role                VARCHAR(50) NOT NULL,
    level               VARCHAR(20) NOT NULL,
    location            VARCHAR(50) NOT NULL,
    college_tier        INTEGER CHECK (college_tier IN (1, 2, 3)),
    is_active           BOOLEAN NOT NULL,
    exit_date           DATE,
    exit_reason         VARCHAR(50),
    manager_id          VARCHAR(20),
    tenure_days         INTEGER GENERATED ALWAYS AS (
                            COALESCE(exit_date, CURRENT_DATE) - join_date
                        ) STORED,
    _stg_loaded_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staging.stg_salary (
    record_id           SERIAL PRIMARY KEY,
    employee_id         VARCHAR(20) NOT NULL,
    effective_date      DATE NOT NULL,
    base_salary         NUMERIC(12, 2) NOT NULL,
    salary_band         VARCHAR(10),
    _stg_loaded_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staging.stg_performance (
    record_id           SERIAL PRIMARY KEY,
    employee_id         VARCHAR(20) NOT NULL,
    review_year         INTEGER NOT NULL,
    rating              NUMERIC(3, 1) CHECK (rating BETWEEN 1.0 AND 5.0),
    _stg_loaded_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staging.stg_exit (
    record_id           SERIAL PRIMARY KEY,
    employee_id         VARCHAR(20) NOT NULL UNIQUE,
    exit_date           DATE NOT NULL,
    exit_reason         VARCHAR(50),
    last_manager_id     VARCHAR(20),
    tenure_days         INTEGER,
    voluntary           BOOLEAN NOT NULL,
    _stg_loaded_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staging.stg_manager (
    record_id           SERIAL PRIMARY KEY,
    manager_id          VARCHAR(20) NOT NULL,
    level               VARCHAR(20),
    department          VARCHAR(50),
    location            VARCHAR(50),
    team_size           INTEGER,
    effective_date      DATE,
    _stg_loaded_at      TIMESTAMP DEFAULT NOW()
);

-- ══════════════════════════════════════════════════════════════════════════════
-- MARTS LAYER — Dimension & Fact tables (Star Schema)
-- ══════════════════════════════════════════════════════════════════════════════

-- Dimensions
CREATE TABLE IF NOT EXISTS marts.dim_employee (
    employee_key        SERIAL PRIMARY KEY,
    employee_id         VARCHAR(20) NOT NULL UNIQUE,
    join_date           DATE NOT NULL,
    birth_year          INTEGER,
    gender              VARCHAR(10) NOT NULL,
    department          VARCHAR(50) NOT NULL,
    role                VARCHAR(50) NOT NULL,
    level               VARCHAR(20) NOT NULL,
    location            VARCHAR(50) NOT NULL,
    college_tier        INTEGER,
    college_tier_label  VARCHAR(30),
    is_active           BOOLEAN NOT NULL,
    exit_date           DATE,
    exit_reason         VARCHAR(50),
    -- SCD Type 2 columns
    dbt_scd_id          UUID DEFAULT uuid_generate_v4(),
    dbt_updated_at      TIMESTAMP,
    dbt_valid_from      TIMESTAMP NOT NULL DEFAULT NOW(),
    dbt_valid_to        TIMESTAMP
);

CREATE TABLE IF NOT EXISTS marts.dim_manager (
    manager_key         SERIAL PRIMARY KEY,
    manager_id          VARCHAR(20) NOT NULL,
    level               VARCHAR(20),
    department          VARCHAR(50),
    location            VARCHAR(50),
    dbt_valid_from      TIMESTAMP NOT NULL DEFAULT NOW(),
    dbt_valid_to        TIMESTAMP
);

CREATE TABLE IF NOT EXISTS marts.dim_project (
    project_key         SERIAL PRIMARY KEY,
    project_id          VARCHAR(20) NOT NULL UNIQUE,
    project_name        VARCHAR(100),
    project_type        VARCHAR(50),
    client_industry     VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS marts.dim_location (
    location_key        SERIAL PRIMARY KEY,
    location_name       VARCHAR(50) NOT NULL UNIQUE,
    city                VARCHAR(50),
    state               VARCHAR(50),
    country             VARCHAR(50) DEFAULT 'India',
    tier                VARCHAR(10)
);

-- Facts
CREATE TABLE IF NOT EXISTS marts.fact_salary (
    salary_key          SERIAL PRIMARY KEY,
    employee_id         VARCHAR(20) NOT NULL,
    effective_date      DATE NOT NULL,
    base_salary         NUMERIC(12, 2) NOT NULL,
    salary_band         VARCHAR(10),
    comp_ratio          NUMERIC(6, 4),   -- salary / midpoint of band
    prior_salary        NUMERIC(12, 2),
    salary_change_pct   NUMERIC(6, 2)
);

CREATE TABLE IF NOT EXISTS marts.fact_attrition (
    attrition_key       SERIAL PRIMARY KEY,
    employee_id         VARCHAR(20) NOT NULL,
    manager_id          VARCHAR(20),
    department          VARCHAR(50),
    role                VARCHAR(50),
    level               VARCHAR(20),
    location            VARCHAR(50),
    gender              VARCHAR(10),
    college_tier        INTEGER,
    join_date           DATE,
    exit_date           DATE,
    tenure_days         INTEGER,
    tenure_years        NUMERIC(5, 2),
    exit_reason         VARCHAR(50),
    voluntary           BOOLEAN,
    join_year           INTEGER,
    join_quarter        INTEGER,
    exit_year           INTEGER,
    exit_quarter        INTEGER
);

CREATE TABLE IF NOT EXISTS marts.fact_learning (
    learning_key        SERIAL PRIMARY KEY,
    employee_id         VARCHAR(20) NOT NULL,
    year                INTEGER NOT NULL,
    quarter             INTEGER NOT NULL,
    learning_hours      NUMERIC(6, 1),
    certifications      INTEGER
);

CREATE TABLE IF NOT EXISTS marts.fact_performance (
    performance_key     SERIAL PRIMARY KEY,
    employee_id         VARCHAR(20) NOT NULL,
    review_year         INTEGER NOT NULL,
    rating              NUMERIC(3, 1),
    rating_category     VARCHAR(20)
);

-- ══════════════════════════════════════════════════════════════════════════════
-- ANALYTICS LAYER — Pre-computed aggregations for dashboards
-- ══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS analytics.executive_kpis (
    snapshot_date           DATE PRIMARY KEY DEFAULT CURRENT_DATE,
    total_headcount         INTEGER,
    active_employees        INTEGER,
    voluntary_attrition_rate NUMERIC(6, 4),
    avg_tenure_years        NUMERIC(5, 2),
    median_salary           NUMERIC(12, 2),
    avg_performance_rating  NUMERIC(4, 2),
    gender_diversity_pct    NUMERIC(6, 4),
    high_risk_employees     INTEGER,
    new_joiners_12m         INTEGER,
    year1_attrition_rate    NUMERIC(6, 4),
    _computed_at            TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analytics.manager_attrition (
    manager_id              VARCHAR(20) PRIMARY KEY,
    department              VARCHAR(50),
    level                   VARCHAR(20),
    location                VARCHAR(50),
    team_size               INTEGER,
    rolling_12m_attrition   NUMERIC(6, 4),
    peer_avg_attrition      NUMERIC(6, 4),
    attrition_delta         NUMERIC(6, 4),
    ci_lower                NUMERIC(6, 4),
    ci_upper                NUMERIC(6, 4),
    risk_flag               BOOLEAN,
    _computed_at            TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analytics.pay_fairness (
    bucket_id               SERIAL PRIMARY KEY,
    role                    VARCHAR(50),
    level                   VARCHAR(20),
    location                VARCHAR(50),
    gender                  VARCHAR(10),
    headcount               INTEGER,
    median_salary           NUMERIC(12, 2),
    avg_comp_ratio          NUMERIC(6, 4),
    gender_pay_ratio        NUMERIC(6, 4),
    ci_lower                NUMERIC(6, 4),
    ci_upper                NUMERIC(6, 4),
    disparity_flag          BOOLEAN,       -- TRUE if outside ±5%
    p_value                 NUMERIC(10, 6),
    _computed_at            TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analytics.retention_cohort (
    cohort_id               SERIAL PRIMARY KEY,
    college_tier            INTEGER,
    college_tier_label      VARCHAR(30),
    join_year               INTEGER,
    join_quarter            INTEGER,
    role                    VARCHAR(50),
    headcount               INTEGER,
    survived_6m             INTEGER,
    survived_12m            INTEGER,
    survived_24m            INTEGER,
    survived_36m            INTEGER,
    median_tenure_days      NUMERIC(8, 1),
    _computed_at            TIMESTAMP DEFAULT NOW()
);

-- ── Indexes ───────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_raw_salary_emp ON raw.raw_salary(employee_id);
CREATE INDEX IF NOT EXISTS idx_raw_perf_emp ON raw.raw_performance(employee_id);
CREATE INDEX IF NOT EXISTS idx_raw_project_emp ON raw.raw_project(employee_id);
CREATE INDEX IF NOT EXISTS idx_stg_emp_dept ON staging.stg_employee(department);
CREATE INDEX IF NOT EXISTS idx_stg_emp_active ON staging.stg_employee(is_active);
CREATE INDEX IF NOT EXISTS idx_fact_attrition_exit ON marts.fact_attrition(exit_date);
CREATE INDEX IF NOT EXISTS idx_fact_attrition_mgr ON marts.fact_attrition(manager_id);
CREATE INDEX IF NOT EXISTS idx_fact_salary_emp ON marts.fact_salary(employee_id);
