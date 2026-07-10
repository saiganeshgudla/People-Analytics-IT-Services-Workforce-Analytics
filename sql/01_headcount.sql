-- =============================================================================
-- 01_headcount.sql
-- PeopleLens Workforce Analytics
-- Business Questions:
--   • How many employees do we have in total?
--   • What is the Active vs Exited breakdown?
--   • How are employees distributed across departments?
--   • What is the gender split?
--   • How does headcount trend year-over-year?
-- =============================================================================


-- Q1.1  Total headcount
SELECT
    COUNT(*)                        AS total_employees
FROM employees;


-- Q1.2  Active vs Exited split
SELECT
    status,
    COUNT(*)                        AS employees,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
        2
    )                               AS percentage
FROM employees
GROUP BY status
ORDER BY employees DESC;


-- Q1.3  Department headcount (descending)
SELECT
    department,
    COUNT(*)                        AS employees
FROM employees
GROUP BY department
ORDER BY employees DESC;


-- Q1.4  Gender distribution with window-function percentage
SELECT
    gender,
    COUNT(*)                        AS employees,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
        2
    )                               AS percentage
FROM employees
GROUP BY gender
ORDER BY employees DESC;


-- Q1.5  Headcount by college tier (talent pipeline quality)
SELECT
    college_tier,
    COUNT(*)                        AS employees,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
        2
    )                               AS percentage
FROM employees
GROUP BY college_tier
ORDER BY college_tier;


-- Q1.6  Headcount by level (org shape / pyramid health)
SELECT
    level,
    COUNT(*)                        AS employees
FROM employees
GROUP BY level
ORDER BY level;


-- Q1.7  Year-over-year hiring trend (joining date cohorts)
SELECT
    EXTRACT(YEAR FROM joining_date)  AS hire_year,
    COUNT(*)                         AS new_hires
FROM employees
GROUP BY hire_year
ORDER BY hire_year;


-- Q1.8  Active headcount by location — useful for real-estate planning
SELECT
    location,
    COUNT(*)                         AS active_employees
FROM employees
WHERE status = 'Active'
GROUP BY location
ORDER BY active_employees DESC;
