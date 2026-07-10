-- =============================================================================
-- 08_dashboard_queries.sql
-- PeopleLens Workforce Analytics
-- Purpose:
--   Production-ready views and queries that power the executive dashboard.
--   These are materialized/reusable — each CREATE VIEW can be queried directly
--   by BI tools (Grafana, Metabase, Streamlit, etc.)
-- =============================================================================


-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION A: SQL VIEWS (persistent, reusable by any BI layer)
-- ─────────────────────────────────────────────────────────────────────────────

-- VIEW 1: Latest compensation per employee
--         Resolves the comp-history table into one current row per employee
CREATE OR REPLACE VIEW vw_latest_compensation AS
WITH ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY employee_id
            ORDER BY effective_date DESC
        )                           AS rn
    FROM compensation
)
SELECT
    employee_id,
    level,
    salary,
    bonus,
    stock,
    effective_date
FROM ranked
WHERE rn = 1;


-- VIEW 2: Employee 360 — single flat view joining all core tables
--         This is the go-to view for ad hoc analysis
CREATE OR REPLACE VIEW vw_employee_360 AS
SELECT
    e.employee_id,
    e.gender,
    e.age,
    e.location,
    e.department,
    e.role,
    e.level,
    e.joining_date,
    e.college_tier,
    e.manager_id,
    e.status,
    -- Compensation
    lc.salary,
    lc.bonus,
    lc.stock,
    -- Performance
    ROUND(AVG(p.rating) OVER (PARTITION BY e.employee_id), 2)
                                    AS avg_performance_rating,
    -- Tenure
    ROUND(
        EXTRACT(
            YEAR FROM AGE(COALESCE(ex.exit_date, CURRENT_DATE), e.joining_date)
        ) +
        EXTRACT(
            MONTH FROM AGE(COALESCE(ex.exit_date, CURRENT_DATE), e.joining_date)
        ) / 12.0,
        2
    )                               AS tenure_years,
    -- Exit info
    ex.exit_date,
    ex.exit_reason,
    ex.voluntary                    AS voluntary_exit
FROM employees e
LEFT JOIN vw_latest_compensation lc ON e.employee_id = lc.employee_id
LEFT JOIN performance p             ON e.employee_id = p.employee_id
LEFT JOIN exits ex                  ON e.employee_id = ex.employee_id;


-- VIEW 3: Department KPI summary — one row per department
CREATE OR REPLACE VIEW vw_dept_kpis AS
SELECT
    department,
    COUNT(*)                        AS total_employees,
    SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END)
                                    AS active,
    SUM(CASE WHEN status = 'Exited' THEN 1 ELSE 0 END)
                                    AS exited,
    ROUND(
        100.0 * SUM(CASE WHEN status = 'Exited' THEN 1 ELSE 0 END)
              / COUNT(*),
        2
    )                               AS attrition_rate_pct
FROM employees
GROUP BY department;


-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION B: EXECUTIVE DASHBOARD QUERIES
-- Run these against the views above for instant BI results
-- ─────────────────────────────────────────────────────────────────────────────

-- D1. Company-wide KPI snapshot (top of dashboard)
SELECT
    COUNT(*)                        AS total_employees,
    SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END)
                                    AS active_employees,
    SUM(CASE WHEN status = 'Exited' THEN 1 ELSE 0 END)
                                    AS total_exits,
    ROUND(
        100.0 * SUM(CASE WHEN status = 'Exited' THEN 1 ELSE 0 END) / COUNT(*),
        2
    )                               AS attrition_pct,
    ROUND(
        AVG(EXTRACT(YEAR FROM AGE(CURRENT_DATE, joining_date)))
    FILTER (WHERE status = 'Active'),
        2
    )                               AS avg_tenure_active_yrs
FROM employees;


-- D2. Department-level KPI table for dashboard grid
SELECT *
FROM vw_dept_kpis
ORDER BY attrition_rate_pct DESC;


-- D3. Rolling 12-month attrition trend (one row per month)
SELECT
    TO_CHAR(DATE_TRUNC('month', exit_date), 'Mon YYYY')
                                    AS month,
    COUNT(*)                        AS exits,
    SUM(COUNT(*)) OVER (
        ORDER BY DATE_TRUNC('month', exit_date)
        ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
    )                               AS rolling_12m_exits
FROM exits
WHERE exit_date >= CURRENT_DATE - INTERVAL '2 years'
GROUP BY DATE_TRUNC('month', exit_date)
ORDER BY DATE_TRUNC('month', exit_date);


-- D4. Performance distribution (for rating histogram widget)
SELECT
    rating,
    COUNT(*)                        AS count,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
        2
    )                               AS percentage
FROM performance
GROUP BY rating
ORDER BY rating;


-- D5. Average salary vs average rating by department (scatter plot data)
WITH dept_salary AS (
    SELECT
        e.department,
        ROUND(AVG(lc.salary))       AS avg_salary
    FROM employees e
    JOIN vw_latest_compensation lc ON e.employee_id = lc.employee_id
    GROUP BY e.department
),
dept_rating AS (
    SELECT
        e.department,
        ROUND(AVG(p.rating), 2)     AS avg_rating
    FROM performance p
    JOIN employees e ON p.employee_id = e.employee_id
    GROUP BY e.department
)
SELECT
    ds.department,
    ds.avg_salary,
    dr.avg_rating
FROM dept_salary ds
JOIN dept_rating dr ON ds.department = dr.department
ORDER BY ds.avg_salary DESC;


-- D6. Overall promotion rate
SELECT
    ROUND(
        100.0 * SUM(CASE WHEN promotion = 'Yes' THEN 1 ELSE 0 END) / COUNT(*),
        2
    )                               AS overall_promotion_rate_pct
FROM performance;


-- D7. Top 10 employees near promotion (avg rating >= 4, Active)
SELECT
    e.employee_id,
    e.department,
    e.level,
    e.location,
    ROUND(AVG(p.rating), 2)         AS avg_rating,
    COUNT(p.review_year)            AS years_reviewed
FROM performance p
JOIN employees e ON p.employee_id = e.employee_id
WHERE e.status = 'Active'
GROUP BY e.employee_id, e.department, e.level, e.location
HAVING AVG(p.rating) >= 4
ORDER BY avg_rating DESC
LIMIT 10;


-- D8. Learning investment vs attrition — departments with high L&D spend & lower attrition
WITH dept_learning AS (
    SELECT
        e.department,
        ROUND(AVG(l.hours_completed), 2)
                                    AS avg_learning_hrs
    FROM learning l
    JOIN employees e ON l.employee_id = e.employee_id
    GROUP BY e.department
)
SELECT
    dk.department,
    dl.avg_learning_hrs,
    dk.attrition_rate_pct
FROM vw_dept_kpis dk
JOIN dept_learning dl ON dk.department = dl.department
ORDER BY dk.attrition_rate_pct ASC;


-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION C: ADVANCED WINDOW FUNCTION SHOWCASE
-- ─────────────────────────────────────────────────────────────────────────────

-- W1. Year-over-year salary growth per employee using LAG()
WITH yearly_salary AS (
    SELECT
        employee_id,
        EXTRACT(YEAR FROM effective_date)   AS comp_year,
        salary
    FROM compensation
),
salary_with_lag AS (
    SELECT
        employee_id,
        comp_year,
        salary,
        LAG(salary) OVER (
            PARTITION BY employee_id
            ORDER BY comp_year
        )                                   AS prev_year_salary
    FROM yearly_salary
)
SELECT
    employee_id,
    comp_year,
    salary,
    prev_year_salary,
    ROUND(
        100.0 * (salary - prev_year_salary) / NULLIF(prev_year_salary, 0),
        2
    )                                       AS yoy_growth_pct
FROM salary_with_lag
WHERE prev_year_salary IS NOT NULL
ORDER BY employee_id, comp_year;


-- W2. Running total of hires by month (cumulative headcount growth)
SELECT
    TO_CHAR(DATE_TRUNC('month', joining_date), 'YYYY-MM')
                                    AS hire_month,
    COUNT(*)                        AS new_hires,
    SUM(COUNT(*)) OVER (
        ORDER BY DATE_TRUNC('month', joining_date)
        ROWS UNBOUNDED PRECEDING
    )                               AS cumulative_hires
FROM employees
GROUP BY DATE_TRUNC('month', joining_date)
ORDER BY hire_month;


-- W3. NTILE quartile segmentation of employees by salary
--     Q4 = top earners, Q1 = lowest earners
WITH latest_comp AS (
    SELECT
        employee_id,
        salary,
        ROW_NUMBER() OVER (
            PARTITION BY employee_id
            ORDER BY effective_date DESC
        )                           AS rn
    FROM compensation
)
SELECT
    e.employee_id,
    e.department,
    e.level,
    lc.salary,
    NTILE(4) OVER (ORDER BY lc.salary)
                                    AS salary_quartile
FROM latest_comp lc
JOIN employees e ON lc.employee_id = e.employee_id
WHERE lc.rn = 1
ORDER BY salary_quartile DESC, lc.salary DESC;
