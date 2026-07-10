-- =============================================================================
-- 02_attrition.sql
-- PeopleLens Workforce Analytics
-- Business Questions:
--   • What is the overall attrition rate?
--   • Which departments / locations lose the most people?
--   • How does attrition vary by level and gender?
--   • Is attrition getting better or worse year-over-year?
-- =============================================================================


-- Q2.1  Overall attrition rate
SELECT
    ROUND(
        100.0 * SUM(CASE WHEN status = 'Exited' THEN 1 ELSE 0 END)
              / COUNT(*),
        2
    )                               AS overall_attrition_pct
FROM employees;


-- Q2.2  Attrition rate by department
SELECT
    department,
    COUNT(*)                        AS total_employees,
    SUM(CASE WHEN status = 'Exited' THEN 1 ELSE 0 END)
                                    AS exited,
    ROUND(
        100.0 * SUM(CASE WHEN status = 'Exited' THEN 1 ELSE 0 END)
              / COUNT(*),
        2
    )                               AS attrition_rate_pct
FROM employees
GROUP BY department
ORDER BY attrition_rate_pct DESC;


-- Q2.3  Attrition rate by location
SELECT
    location,
    COUNT(*)                        AS total_employees,
    SUM(CASE WHEN status = 'Exited' THEN 1 ELSE 0 END)
                                    AS exited,
    ROUND(
        100.0 * SUM(CASE WHEN status = 'Exited' THEN 1 ELSE 0 END)
              / COUNT(*),
        2
    )                               AS attrition_rate_pct
FROM employees
GROUP BY location
ORDER BY attrition_rate_pct DESC;


-- Q2.4  Attrition rate by level — are senior employees leaving more?
SELECT
    level,
    COUNT(*)                        AS total_employees,
    SUM(CASE WHEN status = 'Exited' THEN 1 ELSE 0 END)
                                    AS exited,
    ROUND(
        100.0 * SUM(CASE WHEN status = 'Exited' THEN 1 ELSE 0 END)
              / COUNT(*),
        2
    )                               AS attrition_rate_pct
FROM employees
GROUP BY level
ORDER BY level;


-- Q2.5  Attrition rate by gender
SELECT
    gender,
    COUNT(*)                        AS total_employees,
    SUM(CASE WHEN status = 'Exited' THEN 1 ELSE 0 END)
                                    AS exited,
    ROUND(
        100.0 * SUM(CASE WHEN status = 'Exited' THEN 1 ELSE 0 END)
              / COUNT(*),
        2
    )                               AS attrition_rate_pct
FROM employees
GROUP BY gender
ORDER BY attrition_rate_pct DESC;


-- Q2.6  Year-over-year attrition trend
--       Uses exit_date from the exits table so we get actual exit year
SELECT
    EXTRACT(YEAR FROM ex.exit_date)  AS exit_year,
    COUNT(*)                         AS exits_in_year
FROM exits ex
GROUP BY exit_year
ORDER BY exit_year;


-- Q2.7  Voluntary vs Involuntary attrition breakdown
SELECT
    CASE WHEN voluntary THEN 'Voluntary' ELSE 'Involuntary' END
                                    AS attrition_type,
    COUNT(*)                        AS exits,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
        2
    )                               AS percentage
FROM exits
GROUP BY voluntary
ORDER BY exits DESC;


-- Q2.8  Exit reasons ranked by frequency
SELECT
    exit_reason,
    COUNT(*)                        AS total_exits,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
        2
    )                               AS percentage
FROM exits
GROUP BY exit_reason
ORDER BY total_exits DESC;


-- Q2.9  CTE: Departments with attrition above company average
--       (interview favourite — shows CTE + subquery reasoning)
WITH dept_attrition AS (
    SELECT
        department,
        ROUND(
            100.0 * SUM(CASE WHEN status = 'Exited' THEN 1 ELSE 0 END)
                  / COUNT(*),
            2
        )                           AS attrition_pct
    FROM employees
    GROUP BY department
),
company_avg AS (
    SELECT ROUND(
        100.0 * SUM(CASE WHEN status = 'Exited' THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS avg_attrition
    FROM employees
)
SELECT
    d.department,
    d.attrition_pct,
    c.avg_attrition,
    ROUND(d.attrition_pct - c.avg_attrition, 2) AS variance_from_avg
FROM dept_attrition d
CROSS JOIN company_avg c
WHERE d.attrition_pct > c.avg_attrition
ORDER BY variance_from_avg DESC;
