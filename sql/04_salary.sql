-- =============================================================================
-- 04_salary.sql
-- PeopleLens Workforce Analytics
-- Business Questions:
--   • Are salaries fair across levels?
--   • Is there a gender pay gap?
--   • Which departments pay the most?
--   • How has compensation grown year over year?
--   • Who are the highest earners relative to their peers?
-- =============================================================================


-- Q4.1  Average, min, max salary by level
SELECT
    level,
    ROUND(AVG(salary))              AS avg_salary,
    ROUND(MIN(salary))              AS min_salary,
    ROUND(MAX(salary))              AS max_salary,
    ROUND(STDDEV(salary))           AS salary_stddev
FROM compensation
GROUP BY level
ORDER BY level;


-- Q4.2  Average salary by department
SELECT
    e.department,
    ROUND(AVG(c.salary))            AS avg_salary
FROM employees e
JOIN compensation c ON e.employee_id = c.employee_id
GROUP BY e.department
ORDER BY avg_salary DESC;


-- Q4.3  Gender pay gap — average salary by gender and level
--       Key DEI metric for CHRO
SELECT
    e.level,
    e.gender,
    ROUND(AVG(c.salary))            AS avg_salary
FROM employees e
JOIN compensation c ON e.employee_id = c.employee_id
GROUP BY e.level, e.gender
ORDER BY e.level, avg_salary DESC;


-- Q4.4  Latest compensation per employee (using window ROW_NUMBER)
--       Because compensation is a history table, we need the most recent record
WITH latest_comp AS (
    SELECT
        employee_id,
        level,
        salary,
        bonus,
        stock,
        effective_date,
        ROW_NUMBER() OVER (
            PARTITION BY employee_id
            ORDER BY effective_date DESC
        )                           AS rn
    FROM compensation
)
SELECT
    lc.employee_id,
    e.department,
    e.level,
    lc.salary,
    lc.bonus,
    lc.stock,
    lc.effective_date
FROM latest_comp lc
JOIN employees e ON lc.employee_id = e.employee_id
WHERE lc.rn = 1
ORDER BY lc.salary DESC;


-- Q4.5  Salary percentile rank within each level
--       PERCENT_RANK() = (rank - 1) / (total rows - 1)
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
    lc.employee_id,
    e.department,
    e.level,
    lc.salary,
    ROUND(
        PERCENT_RANK() OVER (
            PARTITION BY e.level
            ORDER BY lc.salary
        ) * 100,
        1
    )                               AS salary_percentile
FROM latest_comp lc
JOIN employees e ON lc.employee_id = e.employee_id
WHERE lc.rn = 1
ORDER BY e.level, salary_percentile DESC;


-- Q4.6  Year-over-year average salary growth
SELECT
    EXTRACT(YEAR FROM effective_date) AS comp_year,
    ROUND(AVG(salary))                AS avg_salary,
    ROUND(AVG(bonus))                 AS avg_bonus
FROM compensation
GROUP BY comp_year
ORDER BY comp_year;


-- Q4.7  Total compensation cost per department (salary + bonus + stock)
WITH latest_comp AS (
    SELECT
        employee_id,
        salary,
        bonus,
        stock,
        ROW_NUMBER() OVER (
            PARTITION BY employee_id
            ORDER BY effective_date DESC
        )                           AS rn
    FROM compensation
)
SELECT
    e.department,
    ROUND(SUM(lc.salary + lc.bonus + lc.stock))
                                    AS total_comp_cost,
    COUNT(DISTINCT lc.employee_id)  AS headcount,
    ROUND(AVG(lc.salary + lc.bonus + lc.stock))
                                    AS avg_total_comp_per_employee
FROM latest_comp lc
JOIN employees e ON lc.employee_id = e.employee_id
WHERE lc.rn = 1
GROUP BY e.department
ORDER BY total_comp_cost DESC;


-- Q4.8  Salary band compliance audit — are any employees outside their level band?
SELECT
    c.employee_id,
    e.department,
    c.level,
    c.salary,
    CASE c.level
        WHEN 'L1' THEN 370000  WHEN 'L2' THEN 600000
        WHEN 'L3' THEN 1000000 WHEN 'L4' THEN 1600000
        WHEN 'L5' THEN 2500000
    END                             AS band_min,
    CASE c.level
        WHEN 'L1' THEN 550000  WHEN 'L2' THEN 950000
        WHEN 'L3' THEN 1500000 WHEN 'L4' THEN 2400000
        WHEN 'L5' THEN 4500000
    END                             AS band_max,
    CASE
        WHEN c.salary < CASE c.level
            WHEN 'L1' THEN 370000  WHEN 'L2' THEN 600000
            WHEN 'L3' THEN 1000000 WHEN 'L4' THEN 1600000
            WHEN 'L5' THEN 2500000 END
        THEN 'BELOW BAND'
        WHEN c.salary > CASE c.level
            WHEN 'L1' THEN 550000  WHEN 'L2' THEN 950000
            WHEN 'L3' THEN 1500000 WHEN 'L4' THEN 2400000
            WHEN 'L5' THEN 4500000 END
        THEN 'ABOVE BAND'
        ELSE 'IN BAND'
    END                             AS band_status
FROM compensation c
JOIN employees e ON c.employee_id = e.employee_id
ORDER BY band_status, c.level;
