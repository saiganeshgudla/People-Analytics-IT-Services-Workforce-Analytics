-- =============================================================================
-- 05_learning.sql
-- PeopleLens Workforce Analytics
-- Business Questions:
--   • Which departments invest the most in learning?
--   • What skills are employees building?
--   • Is learning correlated with better performance?
--   • Who are the top learners?
-- =============================================================================


-- Q5.1  Total learning hours by department
SELECT
    e.department,
    SUM(l.hours_completed)          AS total_hours,
    ROUND(AVG(l.hours_completed), 2) AS avg_hours_per_course,
    COUNT(*)                         AS total_enrollments
FROM learning l
JOIN employees e ON l.employee_id = e.employee_id
GROUP BY e.department
ORDER BY total_hours DESC;


-- Q5.2  Skill category distribution — what is the workforce learning?
SELECT
    skill_category,
    COUNT(*)                        AS enrollments,
    SUM(hours_completed)            AS total_hours,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
        2
    )                               AS enrollment_share_pct
FROM learning
GROUP BY skill_category
ORDER BY enrollments DESC;


-- Q5.3  Completion rate by skill category
SELECT
    skill_category,
    COUNT(*)                        AS total_enrollments,
    SUM(CASE WHEN completion_status = 'Completed' THEN 1 ELSE 0 END)
                                    AS completed,
    ROUND(
        100.0 * SUM(CASE WHEN completion_status = 'Completed' THEN 1 ELSE 0 END)
              / COUNT(*),
        2
    )                               AS completion_rate_pct
FROM learning
GROUP BY skill_category
ORDER BY completion_rate_pct DESC;


-- Q5.4  Top 20 learners by total hours completed
SELECT
    l.employee_id,
    e.department,
    e.level,
    SUM(l.hours_completed)          AS total_hours,
    COUNT(*)                        AS courses_taken,
    RANK() OVER (ORDER BY SUM(l.hours_completed) DESC)
                                    AS learner_rank
FROM learning l
JOIN employees e ON l.employee_id = e.employee_id
GROUP BY l.employee_id, e.department, e.level
ORDER BY learner_rank
LIMIT 20;


-- Q5.5  Average learning hours per employee by level
--       Do senior employees invest more in L&D?
SELECT
    e.level,
    ROUND(AVG(emp_hours.total_hours), 2) AS avg_hours_per_employee
FROM (
    SELECT
        employee_id,
        SUM(hours_completed)        AS total_hours
    FROM learning
    GROUP BY employee_id
) AS emp_hours
JOIN employees e ON emp_hours.employee_id = e.employee_id
GROUP BY e.level
ORDER BY e.level;


-- Q5.6  Learning vs Performance correlation — CTE approach
--       Does more learning = higher ratings?
WITH emp_learning AS (
    SELECT
        employee_id,
        SUM(hours_completed)        AS total_learning_hours
    FROM learning
    GROUP BY employee_id
),
emp_rating AS (
    SELECT
        employee_id,
        ROUND(AVG(rating), 2)       AS avg_rating
    FROM performance
    GROUP BY employee_id
)
SELECT
    CASE
        WHEN el.total_learning_hours < 20  THEN 'Low  (<20 hrs)'
        WHEN el.total_learning_hours < 50  THEN 'Mid  (20-49 hrs)'
        WHEN el.total_learning_hours < 100 THEN 'High (50-99 hrs)'
        ELSE                                    'Top  (100+ hrs)'
    END                             AS learning_band,
    COUNT(*)                        AS employees,
    ROUND(AVG(er.avg_rating), 3)    AS avg_performance_rating
FROM emp_learning el
JOIN emp_rating er ON el.employee_id = er.employee_id
GROUP BY learning_band
ORDER BY avg_performance_rating DESC;


-- Q5.7  Year-over-year learning activity trend
SELECT
    EXTRACT(YEAR FROM completion_date) AS completion_year,
    COUNT(*)                           AS courses_completed,
    SUM(hours_completed)               AS hours_completed
FROM learning
WHERE completion_status = 'Completed'
  AND completion_date IS NOT NULL
GROUP BY completion_year
ORDER BY completion_year;
