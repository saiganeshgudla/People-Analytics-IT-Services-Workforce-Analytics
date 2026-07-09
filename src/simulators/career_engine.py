# src/simulators/career_engine.py
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.config.config import (
    LEVELS, SALARY_BANDS, ROLES_MAP, RATING_DISTRIBUTION, EXIT_REASONS
)
from src.simulators.promotion_engine import check_promotion
from src.simulators.salary_engine import update_salary
from src.simulators.learning_engine import generate_learning
from src.simulators.project_engine import assign_project
from src.simulators.attrition_engine import check_attrition

from faker import Faker

# Seed for reproducibility
random.seed(42)
np.random.seed(42)
fake = Faker("en_IN")
Faker.seed(42)

class CareerState:
    def __init__(self, emp_row):
        self.employee_id = emp_row['employee_id']
        self.gender = emp_row['gender']
        self.joining_age = emp_row['joining_age']
        self.location = emp_row['location']
        self.department = emp_row['department']
        self.joining_date = emp_row['joining_date']
        self.college_tier = emp_row['college_tier']
        
        # Initialize career progression metrics
        # L1: 21-25, L2: 26-31, L3: 32-36, L4: 37-41, L5: 42+
        if self.joining_age <= 25:
            self.level = "L1"
        elif self.joining_age <= 31:
            self.level = "L2"
        elif self.joining_age <= 36:
            self.level = "L3"
        elif self.joining_age <= 41:
            self.level = "L4"
        else:
            self.level = "L5"
            
        self.role = ROLES_MAP[self.department][self.level]
        
        # Initialize salary inside level band
        min_sal, max_sal = SALARY_BANDS[self.level]
        self.salary = random.randint(min_sal, int(min_sal + 0.25 * (max_sal - min_sal)))
        
        self.manager_id = None
        self.status = "Active"
        self.exit_date = None
        self.exit_reason = None
        self.voluntary = None
        
        self.years_in_level = 0
        self.total_tenure = 0
        self.learning_hours_at_level = 0
        self.active_project = None
        
        # Track histories
        self.performance_history = []
        self.performance_history_at_level = []
        self.compensation_history = []
        self.project_history = []
        self.learning_history = []

def run_workforce_simulation(employees_df, managers_df):
    """
    Main simulation loop orchestrator.
    Runs a chronological yearly simulation from 2018 to 2026.
    """
    print("Initializing Employee Career States...")
    states = [CareerState(row) for _, row in employees_df.iterrows()]
    states_dict = {s.employee_id: s for s in states}
    
    # Manager lookup dictionary for team allocations
    # We want to assign managers to employees in the same department
    dept_managers = {}
    for _, mgr in managers_df.iterrows():
        dept = mgr['department']
        if dept not in dept_managers:
            dept_managers[dept] = []
        dept_managers[dept].append(mgr)
        
    print("Running Career Lifecycles year-by-year...")
    
    # Simulation calendar range
    start_year = 2018
    end_year = 2026
    
    today = datetime(2026, 7, 10).date()  # Current simulation timeline boundary
    
    comp_records = []
    perf_records = []
    project_records = []
    learning_records = []
    exit_records = []
    
    # We simulate employee career steps chronologically
    for current_year in range(start_year, end_year + 1):
        year_end_date = datetime(current_year, 12, 31).date()
        if year_end_date > today:
            year_end_date = today
            
        # Filter active employees who have already joined by this year
        active_cohort = [
            s for s in states 
            if s.status == "Active" and s.joining_date.year <= current_year
        ]
        
        # Assign Managers for new joiners who don't have a manager yet
        for s in active_cohort:
            if s.manager_id is None:
                # Select manager in same department
                mgrs = dept_managers.get(s.department, [])
                if mgrs:
                    # Sort managers by current team size to distribute load (respect 8-15 size)
                    mgrs.sort(key=lambda m: m['team_size'])
                    # Select the manager with the smallest team size
                    chosen_mgr = mgrs[0]
                    s.manager_id = chosen_mgr['manager_id']
                    chosen_mgr['team_size'] += 1
                    
        for s in active_cohort:
            s.total_tenure += 1
            s.years_in_level += 1
            
            # 1. Performance Appraisal
            # Assign rating
            rating = random.choices(
                list(RATING_DISTRIBUTION.keys()), 
                weights=list(RATING_DISTRIBUTION.values())
            )[0]
            s.performance_history.append(rating)
            s.performance_history_at_level.append(rating)
            
            # 2. Learning Progression
            # 75% chance of completing training per year
            if random.random() < 0.75:
                start_limit = max(s.joining_date, datetime(current_year, 1, 1).date())
                end_limit = year_end_date
                
                # Exits will be determined at the end of the year loop, 
                # so treat them as active for now
                le = generate_learning(
                    s.employee_id, s.department, start_limit, end_limit, is_exited=False
                )
                learning_records.append(le)
                s.learning_history.append(le)
                s.learning_hours_at_level += le["hours_completed"]
                
            # 3. Project Allocation
            # Check if current project has ended or is non-existent
            if s.active_project is None or (s.active_project["end_date"] is not None and s.active_project["end_date"] < year_end_date):
                start_proj_date = max(s.joining_date, datetime(current_year, 1, 1).date())
                if s.active_project and s.active_project["end_date"]:
                    start_proj_date = max(start_proj_date, s.active_project["end_date"] + timedelta(days=1))
                    
                pe = assign_project(
                    s.employee_id, s.department, start_proj_date, year_end_date, is_exited=False
                )
                project_records.append(pe)
                s.active_project = pe
                s.project_history.append(pe)
                
            # 4. Promotion Assessment
            new_level, promoted = check_promotion(
                s.level, s.years_in_level, s.performance_history_at_level, s.learning_hours_at_level
            )
            
            old_level = s.level
            if promoted:
                # Level Up
                s.level = new_level
                s.role = ROLES_MAP[s.department][s.level]
                s.years_in_level = 0
                s.learning_hours_at_level = 0  # Reset learning hours counter for new level
                s.performance_history_at_level = []  # Reset rating history for new level
                
            # 5. Salary Increments
            # Determine salary ratio relative to level median
            min_sal, max_sal = SALARY_BANDS[s.level]
            median_sal = (min_sal + max_sal) / 2.0
            salary_ratio = s.salary / median_sal
            
            new_salary, bonus, stock = update_salary(
                s.salary, s.level, rating, promoted
            )
            s.salary = new_salary
            
            # Record Compensation history
            comp_records.append({
                "employee_id": s.employee_id,
                "effective_date": year_end_date,
                "level": s.level,
                "salary": s.salary,
                "bonus": bonus,
                "stock": stock
            })
            
            # Record Performance review
            perf_records.append({
                "employee_id": s.employee_id,
                "review_year": current_year,
                "rating": rating,
                "promotion": "Yes" if promoted else "No"
            })
            
            # 6. Attrition / Exit check
            # Stress is based on current project difficulty
            proj_stress = s.active_project["difficulty"] if s.active_project else "Medium"
            
            exited = check_attrition(
                rating, salary_ratio, s.years_in_level, proj_stress, 
                s.learning_hours_at_level, s.total_tenure, s.college_tier
            )
            
            if exited:
                s.status = "Exited"
                reason = random.choices(
                    list(EXIT_REASONS.keys()), 
                    weights=list(EXIT_REASONS.values())
                )[0]
                voluntary = reason != "Performance Issues"
                
                # Generate exit date within this year
                year_start = max(s.joining_date, datetime(current_year, 1, 1).date())
                if year_start >= year_end_date:
                    exit_date = year_end_date
                else:
                    exit_date = fake.date_between(start_date=year_start, end_date=year_end_date)
                    
                s.exit_date = exit_date
                s.exit_reason = reason
                s.voluntary = voluntary
                
                # Close ongoing projects and learning
                if s.active_project and s.active_project["end_date"] is None:
                    s.active_project["end_date"] = exit_date
                    # Update in the list of records too
                    for p in project_records:
                        if p["employee_id"] == s.employee_id and p["end_date"] is None:
                            p["end_date"] = exit_date
                            
                # Decrement manager's team size
                for dept_list in dept_managers.values():
                    for m in dept_list:
                        if m['manager_id'] == s.manager_id:
                            m['team_size'] = max(0, m['team_size'] - 1)
                            
                exit_records.append({
                    "employee_id": s.employee_id,
                    "exit_date": exit_date,
                    "exit_reason": reason,
                    "voluntary": voluntary
                })
                
    # Reconstruct updated Employees master dataframe
    updated_emp_records = []
    for s in states:
        updated_emp_records.append({
            'employee_id': s.employee_id,
            'gender': s.gender,
            'age': s.joining_age + int((today - s.joining_date).days / 365.25),
            'location': s.location,
            'department': s.department,
            'role': s.role,
            'level': s.level,
            'joining_date': s.joining_date,
            'college_tier': s.college_tier,
            'manager_id': s.manager_id,
            'status': s.status
        })
        
    # Drop internal helper columns from exports
    clean_project_records = []
    for p in project_records:
        clean_project_records.append({
            "employee_id": p["employee_id"],
            "project_name": p["project_name"],
            "client_name": p["client_name"],
            "start_date": p["start_date"],
            "end_date": p["end_date"],
            "billable": p["billable"]
        })
        
    return (
        pd.DataFrame(updated_emp_records),
        pd.DataFrame(comp_records),
        pd.DataFrame(perf_records),
        pd.DataFrame(clean_project_records),
        pd.DataFrame(learning_records),
        pd.DataFrame(exit_records),
        managers_df
    )
