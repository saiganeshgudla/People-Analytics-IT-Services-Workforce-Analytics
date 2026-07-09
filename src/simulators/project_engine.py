# src/simulators/project_engine.py
import random
from datetime import timedelta
from src.config.config import PROJECTS_CATALOG

# Seed for reproducibility
random.seed(42)

def assign_project(employee_id, department, start_date, limit_date, is_exited):
    """
    Allocates a department-appropriate project from the catalog.
    - Resolves start/end dates.
    - Sets billable status.
    - Returns assignment details including project difficulty for stress/attrition analysis.
    """
    project_pool = PROJECTS_CATALOG[department]
    selected_project = random.choice(project_pool)
    
    duration = random.randint(180, 540)  # 6 to 18 months
    end_date = start_date + timedelta(days=duration)
    
    is_ongoing = False
    if end_date >= limit_date:
        if is_exited:
            end_date = limit_date
        else:
            end_date = None
            is_ongoing = True
            
    billable = selected_project["client_name"] != "Internal"
    
    return {
        "employee_id": employee_id,
        "project_name": selected_project["project_name"],
        "client_name": selected_project["client_name"],
        "start_date": start_date,
        "end_date": end_date if not is_ongoing else None,
        "billable": billable,
        "difficulty": selected_project["difficulty"]  # High/Medium/Low (used for simulation stress)
    }
