-- ══════════════════════════════════════════════════════════════════════════════
-- PeopleLens — SQL Portfolio
-- 6 Workforce Intelligence Questions
-- Target: Interview-ready SQL for People Analytics roles
-- ══════════════════════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────────────────────
-- Q1. What is the rolling 12-month voluntary attrition rate by department?
-- (Window function + date arithmetic)
-- ─────────────────────────────────────────────────────────────────────────────
WITH monthly_attrition AS (
    SELECT
        DATE_TRUNC('month', exit_date) AS exit_month,
        department,
        COUNT(*)                        AS exits_this_month
    FROM marts.fact_attrition
    WHERE voluntary = TRUE
    GROUP BY 1, 2
),
headcount_snapshot AS (
    SELECT
        DATE_TRUNC('month', join_date) AS join_month,
        department,
        COUNT(*)                        AS joiners
    FROM marts.dim_employee
    GROUP BY 1, 2
)
SELECT
    m.exit_month,
    m.department,
    SUM(m.exits_this_month) OVER (
        PARTITION BY m.department
        ORDER BY m.exit_month
        ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
    ) AS rolling_12m_exits,
    SUM(h.joiners) OVER (
        PARTITION BY m.department
        ORDER BY m.exit_month
        ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
    ) AS rolling_12m_joiners,
    ROUND(
        SUM(m.exits_this_month) OVER (
            PARTITION BY m.department
            ORDER BY m.exit_month
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        )::NUMERIC /
        NULLIF(SUM(h.joiners) OVER (
            PARTITION BY m.department
            ORDER BY m.exit_month
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ), 0),
    4) AS rolling_12m_attrition_rate
FROM monthly_attrition m
LEFT JOIN headcount_snapshot h
    ON m.exit_month = h.join_month AND m.department = h.department
WHERE m.exit_month >= '2023-01-01'
ORDER BY m.department, m.exit_month;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q2. Which managers have attrition rates more than 10pp above their peers?
-- (Subquery + HAVING + peer benchmarking)
-- ─────────────────────────────────────────────────────────────────────────────
WITH manager_attrition AS (
    SELECT
        e.manager_id,
        m.level,
        m.department,
        COUNT(e.employee_id)                        AS team_size,
        SUM(CASE WHEN e.exit_date >= CURRENT_DATE - INTERVAL '12 months'
                      AND e.exit_date IS NOT NULL THEN 1 ELSE 0 END) AS exits_12m
    FROM marts.dim_employee e
    LEFT JOIN marts.dim_manager m ON e.manager_id = m.manager_id
    WHERE e.manager_id IS NOT NULL
    GROUP BY e.manager_id, m.level, m.department
    HAVING COUNT(e.employee_id) >= 5  -- k-anonymity guard
),
peer_avg AS (
    SELECT
        level,
        department,
        AVG(exits_12m::NUMERIC / NULLIF(team_size, 0)) AS peer_attrition_rate
    FROM manager_attrition
    GROUP BY level, department
)
SELECT
    ma.manager_id,
    ma.level,
    ma.department,
    ma.team_size,
    ROUND(ma.exits_12m::NUMERIC / ma.team_size, 4) AS attrition_rate,
    ROUND(pa.peer_attrition_rate, 4)                AS peer_avg_attrition_rate,
    ROUND(
        (ma.exits_12m::NUMERIC / ma.team_size) - pa.peer_attrition_rate,
    4) AS delta_vs_peers
FROM manager_attrition ma
JOIN peer_avg pa USING (level, department)
WHERE (ma.exits_12m::NUMERIC / NULLIF(ma.team_size, 0)) - pa.peer_attrition_rate > 0.10
ORDER BY delta_vs_peers DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q3. Compute the median gender pay ratio within each (role, level, location)
-- bucket. Flag buckets where the ratio is outside ±5%.
-- (Percentile functions + conditional aggregation)
-- ─────────────────────────────────────────────────────────────────────────────
WITH latest_salary AS (
    SELECT DISTINCT ON (employee_id)
        employee_id,
        base_salary
    FROM marts.fact_salary
    ORDER BY employee_id, effective_date DESC
),
employee_salary AS (
    SELECT
        e.employee_id,
        e.gender,
        e.role,
        e.level,
        e.location,
        ls.base_salary
    FROM marts.dim_employee e
    JOIN latest_salary ls USING (employee_id)
    WHERE e.is_active = TRUE
),
bucket_stats AS (
    SELECT
        role,
        level,
        location,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY base_salary)
            FILTER (WHERE gender = 'Male')   AS male_median,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY base_salary)
            FILTER (WHERE gender = 'Female') AS female_median,
        COUNT(*) FILTER (WHERE gender = 'Male')   AS male_count,
        COUNT(*) FILTER (WHERE gender = 'Female') AS female_count
    FROM employee_salary
    GROUP BY role, level, location
    HAVING COUNT(*) FILTER (WHERE gender = 'Male')   >= 10
       AND COUNT(*) FILTER (WHERE gender = 'Female') >= 10  -- k-anonymity
)
SELECT
    role,
    level,
    location,
    male_count,
    female_count,
    ROUND(male_median, 0)   AS male_median_salary,
    ROUND(female_median, 0) AS female_median_salary,
    ROUND(female_median / NULLIF(male_median, 0), 4) AS gender_pay_ratio,
    CASE
        WHEN ABS(female_median / NULLIF(male_median, 0) - 1) > 0.05
        THEN TRUE ELSE FALSE
    END AS disparity_flag
FROM bucket_stats
ORDER BY gender_pay_ratio;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q4. What are the 6-month, 12-month, and 24-month retention rates
-- for employees who joined in each year, stratified by college tier?
-- (Cohort analysis + survival rates)
-- ─────────────────────────────────────────────────────────────────────────────
WITH cohort AS (
    SELECT
        employee_id,
        EXTRACT(YEAR FROM join_date)::INT AS join_year,
        college_tier,
        COALESCE(
            (exit_date - join_date),
            (CURRENT_DATE - join_date)
        ) AS tenure_days,
        NOT is_active AS has_exited
    FROM marts.dim_employee
    WHERE join_date >= '2019-01-01'
),
cohort_agg AS (
    SELECT
        join_year,
        college_tier,
        COUNT(*)                                                   AS cohort_size,
        SUM(CASE WHEN tenure_days >= 180 OR NOT has_exited THEN 1 ELSE 0 END)  AS survived_6m,
        SUM(CASE WHEN tenure_days >= 365 OR NOT has_exited THEN 1 ELSE 0 END)  AS survived_12m,
        SUM(CASE WHEN tenure_days >= 730 OR NOT has_exited THEN 1 ELSE 0 END)  AS survived_24m
    FROM cohort
    GROUP BY join_year, college_tier
    HAVING COUNT(*) >= 10  -- k-anonymity
)
SELECT
    join_year,
    CASE college_tier
        WHEN 1 THEN 'Tier 1 (IIT/NIT)'
        WHEN 2 THEN 'Tier 2 (State Engg)'
        WHEN 3 THEN 'Tier 3 (Other)'
    END AS college_tier_label,
    cohort_size,
    ROUND(survived_6m::NUMERIC  / cohort_size, 3) AS retention_6m,
    ROUND(survived_12m::NUMERIC / cohort_size, 3) AS retention_12m,
    ROUND(survived_24m::NUMERIC / cohort_size, 3) AS retention_24m
FROM cohort_agg
ORDER BY join_year, college_tier;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q5. For each employee active in the last 12 months, compute:
-- (a) their percentile rank within their department by salary
-- (b) the department's salary budget utilisation vs headcount budget
-- (Using RANK, NTILE, and window functions)
-- ─────────────────────────────────────────────────────────────────────────────
WITH latest_salary AS (
    SELECT DISTINCT ON (employee_id)
        employee_id,
        base_salary
    FROM marts.fact_salary
    ORDER BY employee_id, effective_date DESC
),
emp_with_salary AS (
    SELECT
        e.employee_id,
        e.department,
        e.level,
        e.gender,
        ls.base_salary,
        PERCENT_RANK() OVER (
            PARTITION BY e.department
            ORDER BY ls.base_salary
        ) AS salary_pct_rank_in_dept,
        NTILE(4) OVER (
            PARTITION BY e.department
            ORDER BY ls.base_salary
        ) AS salary_quartile_in_dept
    FROM marts.dim_employee e
    JOIN latest_salary ls USING (employee_id)
    WHERE e.is_active = TRUE
)
SELECT
    department,
    level,
    gender,
    COUNT(*)                                AS headcount,
    ROUND(AVG(base_salary), 0)              AS avg_salary,
    ROUND(AVG(salary_pct_rank_in_dept), 3) AS avg_pct_rank,
    SUM(base_salary) / 1e7                  AS total_salary_cr
FROM emp_with_salary
GROUP BY department, level, gender
ORDER BY department, level;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q6. Identify "flight risk" employees: active employees whose last 2
-- performance ratings have both declined AND whose salary growth is
-- below the median for their level in the past 2 years.
-- (Self-join + LAG + conditional filtering)
-- ─────────────────────────────────────────────────────────────────────────────
WITH perf_trend AS (
    SELECT
        employee_id,
        review_year,
        rating,
        LAG(rating) OVER (PARTITION BY employee_id ORDER BY review_year) AS prev_rating
    FROM marts.fact_performance
    WHERE review_year >= EXTRACT(YEAR FROM CURRENT_DATE) - 2
),
declining_perf AS (
    SELECT employee_id
    FROM perf_trend
    WHERE prev_rating IS NOT NULL
      AND rating < prev_rating
    GROUP BY employee_id
    HAVING COUNT(*) >= 2  -- declined in both of last 2 cycles
),
salary_growth AS (
    SELECT
        employee_id,
        (MAX(base_salary) - MIN(base_salary)) / NULLIF(MIN(base_salary), 0) AS salary_growth_2yr
    FROM marts.fact_salary
    WHERE effective_date >= CURRENT_DATE - INTERVAL '2 years'
    GROUP BY employee_id
),
median_growth_by_level AS (
    SELECT
        e.level,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sg.salary_growth_2yr) AS median_growth
    FROM marts.dim_employee e
    JOIN salary_growth sg USING (employee_id)
    WHERE e.is_active = TRUE
    GROUP BY e.level
)
SELECT
    e.employee_id,
    e.department,
    e.level,
    e.location,
    ROUND(sg.salary_growth_2yr, 4) AS salary_growth_2yr,
    ROUND(mg.median_growth, 4)     AS median_growth_for_level,
    'High Flight Risk'             AS risk_label
FROM marts.dim_employee e
JOIN declining_perf dp     USING (employee_id)
JOIN salary_growth sg      USING (employee_id)
JOIN median_growth_by_level mg ON e.level = mg.level
WHERE e.is_active = TRUE
  AND sg.salary_growth_2yr < mg.median_growth
ORDER BY sg.salary_growth_2yr;
