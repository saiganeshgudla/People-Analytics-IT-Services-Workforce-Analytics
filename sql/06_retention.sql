-- =============================================================================
-- 06_retention.sql
-- PeopleLens Workforce Analytics
-- Business Questions:
--   • Who are the flight-risk employees?
--   • What is the tenure distribution of active employees?
--   • Do high performers stay longer?
--   • What is the average tenure before exit?
-- =============================================================================


-- Q6.1  Average tenure of active employees (in years)
SELECT
    ROUND(
        AVG(
            EXTRACT(YEAR FROM AGE(CURRENT_DATE, joining_date))
        ),
        2
    )                               AS avg_tenure_years
FROM employees
WHERE status = 'Active';


-- Q6.2  Average tenure of exited employees before exit
SELECT
    ROUND(
        AVG(
            EXTRACT(YEAR FROM AGE(ex.exit_date, e.joining_date))
        ),
        2
    )                               AS avg_tenure_before_exit_years
FROM exits ex
JOIN employees e ON ex.employee_id = e.employee_id;


-- Q6.3  Tenure bucket distribution of active employees
SELECT
    CASE
        WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, joining_date)) < 1
            THEN '< 1 year'
        WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, joining_date)) < 3
            THEN '1–3 years'
        WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, joining_date)) < 5
            THEN '3–5 years'
        WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, joining_date)) < 10
            THEN '5–10 years'
        ELSE '10+ years'
    END                             AS tenure_bucket,
    COUNT(*)                        AS employees
FROM employees
WHERE status = 'Active'
GROUP BY tenure_bucket
ORDER BY MIN(EXTRACT(YEAR FROM AGE(CURRENT_DATE, joining_date)));


-- Q6.4  Flight-risk dashboard — low performers + long tenure (disengaged)
--       CTE finds employees with avg rating < 3 who have been active > 3 years
WITH emp_avg_rating AS (
    SELECT
        employee_id,
        ROUND(AVG(rating), 2)       AS avg_rating
    FROM performance
    GROUP BY employee_id
)
SELECT
    e.employee_id,
    e.department,
    e.level,
    e.location,
    ROUND(
        EXTRACT(YEAR FROM AGE(CURRENT_DATE, e.joining_date)),
        1
    )                               AS tenure_years,
    ear.avg_rating
FROM employees e
JOIN emp_avg_rating ear ON e.employee_id = ear.employee_id
WHERE e.status = 'Active'
  AND ear.avg_rating < 3
  AND EXTRACT(YEAR FROM AGE(CURRENT_DATE, e.joining_date)) >= 3
ORDER BY ear.avg_rating, tenure_years DESC;


-- Q6.5  High-potential retention risk — top performers with low salary percentile
--       These are people you cannot afford to lose
WITH latest_comp AS (
    SELECT
        employee_id,
        salary,
        ROW_NUMBER() OVER (
            PARTITION BY employee_id
            ORDER BY effective_date DESC
        )                           AS rn
    FROM compensation
),
emp_salary AS (
    SELECT employee_id, salary
    FROM latest_comp
    WHERE rn = 1
),
emp_avg_rating AS (
    SELECT
        employee_id,
        ROUND(AVG(rating), 2)       AS avg_rating
    FROM performance
    GROUP BY employee_id
),
salary_percentiles AS (
    SELECT
        es.employee_id,
        es.salary,
        e.level,
        ROUND(
            PERCENT_RANK() OVER (
                PARTITION BY e.level
                ORDER BY es.salary
            ) * 100,
            1
        )                           AS salary_percentile
    FROM emp_salary es
    JOIN employees e ON es.employee_id = e.employee_id
)
SELECT
    e.employee_id,
    e.department,
    e.level,
    ear.avg_rating,
    sp.salary,
    sp.salary_percentile,
    'HIGH RISK'                     AS retention_flag
FROM employees e
JOIN emp_avg_rating ear  ON e.employee_id = ear.employee_id
JOIN salary_percentiles sp ON e.employee_id = sp.employee_id
WHERE e.status = 'Active'
  AND ear.avg_rating >= 4           -- high performer
  AND sp.salary_percentile < 40     -- paid below peers
ORDER BY ear.avg_rating DESC, sp.salary_percentile;


-- Q6.6  Retention rate by department (% of all ever-hired who are still Active)
SELECT
    department,
    COUNT(*)                        AS ever_hired,
    SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END)
                                    AS still_active,
    ROUND(
        100.0 * SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END)
              / COUNT(*),
        2
    )                               AS retention_rate_pct
FROM employees
GROUP BY department
ORDER BY retention_rate_pct DESC;


-- Q6.7  Month-by-month exits in the last 2 years (trend analysis)
SELECT
    TO_CHAR(exit_date, 'YYYY-MM')   AS exit_month,
    COUNT(*)                        AS exits
FROM exits
WHERE exit_date >= CURRENT_DATE - INTERVAL '2 years'
GROUP BY exit_month
ORDER BY exit_month;
