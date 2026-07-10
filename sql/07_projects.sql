-- =============================================================================
-- 07_projects.sql
-- PeopleLens Workforce Analytics
-- Business Questions:
--   • Which projects have the most employees?
--   • Which clients generate the most work?
--   • Are billable hours concentrated in a few projects?
--   • Which projects are losing people to attrition?
-- =============================================================================


-- Q7.1  Employee count per project
SELECT
    project_name,
    COUNT(*)                        AS employees_assigned
FROM projects
GROUP BY project_name
ORDER BY employees_assigned DESC;


-- Q7.2  Billable vs non-billable assignments
SELECT
    CASE WHEN billable THEN 'Billable' ELSE 'Non-Billable' END
                                    AS billing_type,
    COUNT(*)                        AS assignments,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
        2
    )                               AS percentage
FROM projects
GROUP BY billable;


-- Q7.3  Top clients by number of project assignments
SELECT
    client_name,
    COUNT(*)                        AS assignments,
    COUNT(DISTINCT project_name)    AS distinct_projects,
    COUNT(DISTINCT employee_id)     AS unique_employees
FROM projects
GROUP BY client_name
ORDER BY assignments DESC
LIMIT 15;


-- Q7.4  Project duration analysis — average project length in days
SELECT
    project_name,
    COUNT(*)                        AS team_size,
    ROUND(AVG(end_date - start_date))
                                    AS avg_duration_days,
    MIN(start_date)                 AS earliest_start,
    MAX(end_date)                   AS latest_end
FROM projects
WHERE end_date IS NOT NULL
GROUP BY project_name
ORDER BY avg_duration_days DESC;


-- Q7.5  Currently active projects (assignments where end_date >= today or null)
SELECT
    project_name,
    client_name,
    COUNT(*)                        AS active_assignments,
    SUM(CASE WHEN billable THEN 1 ELSE 0 END)
                                    AS billable_count
FROM projects
WHERE end_date >= CURRENT_DATE
   OR end_date IS NULL
GROUP BY project_name, client_name
ORDER BY active_assignments DESC;


-- Q7.6  Projects affected by attrition — exited employees per project
--       Useful for project continuity risk assessment
SELECT
    p.project_name,
    p.client_name,
    COUNT(*)                        AS total_assignments,
    SUM(CASE WHEN e.status = 'Exited' THEN 1 ELSE 0 END)
                                    AS exited_employees,
    ROUND(
        100.0 * SUM(CASE WHEN e.status = 'Exited' THEN 1 ELSE 0 END)
              / COUNT(*),
        2
    )                               AS attrition_rate_pct
FROM projects p
JOIN employees e ON p.employee_id = e.employee_id
GROUP BY p.project_name, p.client_name
ORDER BY attrition_rate_pct DESC
LIMIT 20;


-- Q7.7  Employee project load — how many concurrent projects per employee?
WITH project_counts AS (
    SELECT
        employee_id,
        COUNT(DISTINCT project_name) AS projects_worked_on
    FROM projects
    GROUP BY employee_id
)
SELECT
    pc.employee_id,
    e.department,
    e.level,
    pc.projects_worked_on,
    RANK() OVER (ORDER BY pc.projects_worked_on DESC)
                                    AS workload_rank
FROM project_counts pc
JOIN employees e ON pc.employee_id = e.employee_id
ORDER BY workload_rank
LIMIT 20;


-- Q7.8  Department distribution across projects (which depts are project-heavy?)
SELECT
    e.department,
    COUNT(DISTINCT p.project_name)  AS distinct_projects,
    COUNT(*)                        AS total_assignments,
    SUM(CASE WHEN p.billable THEN 1 ELSE 0 END)
                                    AS billable_assignments
FROM projects p
JOIN employees e ON p.employee_id = e.employee_id
GROUP BY e.department
ORDER BY total_assignments DESC;
