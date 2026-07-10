-- =============================================================================
-- 03_manager_effect.sql
-- PeopleLens Workforce Analytics
-- CHRO Questions:
--   KPI 1  → How many employees report to each manager?
--   KPI 2  → Which managers lose the most employees? (Attrition Rate)
--   KPI 3  → Which teams perform the best?            (Avg Performance)
--   KPI 4  → What does each manager's team earn?      (Avg Salary)
--   KPI 5  → How much are teams investing in L&D?     (Learning Hours)
--   KPI 6  → Which managers promote the most?         (Promotion Rate)
--   KPI 7  → Full Manager Scorecard CTE               (All KPIs unified)
--   KPI 8  → Risk-rank managers by attrition          (RANK window fn)
--   KPI 9  → Benchmark each manager vs company avg    (CROSS JOIN CTE)
-- =============================================================================


-- ─────────────────────────────────────────────────────────────────────────────
-- KPI 1: Team Size per Manager
-- Business: Are any managers over-/under-staffed?
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    manager_id,
    COUNT(*)                          AS team_size
FROM employees
WHERE manager_id IS NOT NULL
GROUP BY manager_id
ORDER BY team_size DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- KPI 2: Manager Attrition Rate
-- Business: The most important manager-level KPI.
--           A manager with 40% attrition needs immediate coaching.
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    manager_id,
    COUNT(*)                          AS team_size,
    SUM(
        CASE WHEN status = 'Exited' THEN 1 ELSE 0 END
    )                                 AS exits,
    ROUND(
        100.0 *
        SUM(CASE WHEN status = 'Exited' THEN 1 ELSE 0 END)
        / COUNT(*),
        2
    )                                 AS attrition_rate_pct
FROM employees
WHERE manager_id IS NOT NULL
GROUP BY manager_id
ORDER BY attrition_rate_pct DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- KPI 3: Team Average Performance Rating
-- Business: Which managers build high-performing teams?
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    e.manager_id,
    ROUND(AVG(p.rating), 2)           AS avg_team_rating
FROM performance p
JOIN employees e ON p.employee_id = e.employee_id
WHERE e.manager_id IS NOT NULL
GROUP BY e.manager_id
ORDER BY avg_team_rating DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- KPI 4: Team Average Salary
-- Business: Are high-attrition managers also underpaying their teams?
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    e.manager_id,
    ROUND(AVG(c.salary))              AS avg_team_salary
FROM compensation c
JOIN employees e ON c.employee_id = e.employee_id
WHERE e.manager_id IS NOT NULL
GROUP BY e.manager_id
ORDER BY avg_team_salary DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- KPI 5: Team Learning Hours
-- Business: Managers who invest in their team's development retain better.
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    e.manager_id,
    SUM(l.hours_completed)            AS total_learning_hours,
    ROUND(AVG(l.hours_completed), 2)  AS avg_hours_per_course
FROM learning l
JOIN employees e ON l.employee_id = e.employee_id
WHERE e.manager_id IS NOT NULL
GROUP BY e.manager_id
ORDER BY total_learning_hours DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- KPI 6: Promotion Rate per Manager
-- Business: Which managers are developing and promoting people?
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    e.manager_id,
    COUNT(p.employee_id)              AS total_appraisals,
    SUM(CASE WHEN p.promotion = 'Yes' THEN 1 ELSE 0 END)
                                      AS promotions_given,
    ROUND(
        100.0 *
        SUM(CASE WHEN p.promotion = 'Yes' THEN 1 ELSE 0 END)
        / COUNT(p.employee_id),
        2
    )                                 AS promotion_rate_pct
FROM performance p
JOIN employees e ON p.employee_id = e.employee_id
WHERE e.manager_id IS NOT NULL
GROUP BY e.manager_id
ORDER BY promotion_rate_pct DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- KPI 7: Full Manager Scorecard (Multi-CTE — all 5 KPIs in one table)
-- Business: The single source of truth for CHRO review meetings.
--           One row per manager with every metric side-by-side.
-- ─────────────────────────────────────────────────────────────────────────────
WITH team AS (
    -- Headcount and attrition
    SELECT
        manager_id,
        COUNT(*)                      AS team_size,
        SUM(CASE WHEN status = 'Exited' THEN 1 ELSE 0 END)
                                      AS exits,
        ROUND(
            100.0 *
            SUM(CASE WHEN status = 'Exited' THEN 1 ELSE 0 END) / COUNT(*),
            2
        )                             AS attrition_rate_pct
    FROM employees
    WHERE manager_id IS NOT NULL
    GROUP BY manager_id
),
perf AS (
    -- Average team performance rating
    SELECT
        e.manager_id,
        ROUND(AVG(p.rating), 2)       AS avg_team_rating
    FROM performance p
    JOIN employees e ON p.employee_id = e.employee_id
    WHERE e.manager_id IS NOT NULL
    GROUP BY e.manager_id
),
comp AS (
    -- Latest average salary per team
    SELECT
        e.manager_id,
        ROUND(AVG(c.salary))          AS avg_team_salary
    FROM compensation c
    JOIN employees e ON c.employee_id = e.employee_id
    WHERE e.manager_id IS NOT NULL
    GROUP BY e.manager_id
),
learn AS (
    -- Total learning hours per team
    SELECT
        e.manager_id,
        SUM(l.hours_completed)        AS total_learning_hours
    FROM learning l
    JOIN employees e ON l.employee_id = e.employee_id
    WHERE e.manager_id IS NOT NULL
    GROUP BY e.manager_id
),
promo AS (
    -- Promotion rate per manager
    SELECT
        e.manager_id,
        ROUND(
            100.0 *
            SUM(CASE WHEN p.promotion = 'Yes' THEN 1 ELSE 0 END)
            / COUNT(*),
            2
        )                             AS promotion_rate_pct
    FROM performance p
    JOIN employees e ON p.employee_id = e.employee_id
    WHERE e.manager_id IS NOT NULL
    GROUP BY e.manager_id
)
SELECT
    t.manager_id,
    m.department,
    m.experience_years,
    t.team_size,
    t.exits,
    t.attrition_rate_pct,
    p.avg_team_rating,
    c.avg_team_salary,
    l.total_learning_hours,
    pr.promotion_rate_pct
FROM team t
JOIN managers  m  ON t.manager_id = m.manager_id
JOIN perf      p  ON t.manager_id = p.manager_id
JOIN comp      c  ON t.manager_id = c.manager_id
JOIN learn     l  ON t.manager_id = l.manager_id
JOIN promo     pr ON t.manager_id = pr.manager_id
ORDER BY t.attrition_rate_pct DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- KPI 8: Risk-Rank Managers by Attrition (Window Function)
-- Business: Produces a ranked leaderboard — Rank 1 = highest risk.
--           RANK() is one of the most cited window functions in interviews.
-- ─────────────────────────────────────────────────────────────────────────────
WITH manager_summary AS (
    SELECT
        e.manager_id,
        m.department,
        COUNT(*)                      AS team_size,
        SUM(CASE WHEN e.status = 'Exited' THEN 1 ELSE 0 END)
                                      AS exits,
        ROUND(
            100.0 *
            SUM(CASE WHEN e.status = 'Exited' THEN 1 ELSE 0 END) / COUNT(*),
            2
        )                             AS attrition_rate_pct
    FROM employees e
    JOIN managers m ON e.manager_id = m.manager_id
    WHERE e.manager_id IS NOT NULL
    GROUP BY e.manager_id, m.department
)
SELECT
    manager_id,
    department,
    team_size,
    exits,
    attrition_rate_pct,
    RANK()       OVER (ORDER BY attrition_rate_pct DESC)
                                      AS risk_rank,
    DENSE_RANK() OVER (
        PARTITION BY department
        ORDER BY attrition_rate_pct DESC
    )                                 AS risk_rank_within_dept,
    NTILE(4) OVER (ORDER BY attrition_rate_pct DESC)
                                      AS risk_quartile   -- Q1 = highest risk
FROM manager_summary
ORDER BY risk_rank;


-- ─────────────────────────────────────────────────────────────────────────────
-- KPI 9: Benchmark Each Manager Against Company Average
-- Business: Instantly identifies managers above/below the company baseline.
--           CROSS JOIN ensures every row gets the single company-wide figure.
-- ─────────────────────────────────────────────────────────────────────────────
WITH manager_summary AS (
    SELECT
        manager_id,
        ROUND(
            100.0 *
            SUM(CASE WHEN status = 'Exited' THEN 1 ELSE 0 END) / COUNT(*),
            2
        )                             AS attrition_rate_pct
    FROM employees
    WHERE manager_id IS NOT NULL
    GROUP BY manager_id
),
company_avg AS (
    SELECT
        ROUND(
            100.0 *
            SUM(CASE WHEN status = 'Exited' THEN 1 ELSE 0 END) / COUNT(*),
            2
        )                             AS company_attrition_pct
    FROM employees
)
SELECT
    ms.manager_id,
    ms.attrition_rate_pct,
    ca.company_attrition_pct,
    ROUND(ms.attrition_rate_pct - ca.company_attrition_pct, 2)
                                      AS variance_from_avg,
    CASE
        WHEN ms.attrition_rate_pct > ca.company_attrition_pct + 5
            THEN 'HIGH RISK  — Needs Coaching'
        WHEN ms.attrition_rate_pct < ca.company_attrition_pct - 5
            THEN 'STAR       — Best Practice'
        ELSE
            'AVERAGE    — Monitor'
    END                               AS manager_flag
FROM manager_summary ms
CROSS JOIN company_avg ca
ORDER BY variance_from_avg DESC;
