# src/generators/employee_generator.py
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.config.config import NUM_EMPLOYEES, DEPARTMENTS, LOCATIONS, COLLEGE_TIERS

# Seed for reproducibility
np.random.seed(42)
random.seed(42)

GENDERS = ['Male', 'Female', 'Non-binary']
GENDER_PROBS = [0.58, 0.41, 0.01]

def generate_base_employees(num_employees=NUM_EMPLOYEES):
    """
    Generates the initial cohort of employees with joining dates, locations, 
    departments, genders, and college tiers.
    """
    print(f"Generating {num_employees} base employee profiles...")
    employee_ids = list(range(200001, 200001 + num_employees))
    
    start_join_dt = datetime(2018, 1, 1)
    end_join_dt = datetime(2025, 12, 31)
    days_range = (end_join_dt - start_join_dt).days
    
    records = []
    for emp_id in employee_ids:
        gender = np.random.choice(GENDERS, p=GENDER_PROBS)
        dept = np.random.choice(DEPARTMENTS)
        loc = np.random.choice(LOCATIONS)
        college_tier = np.random.choice(COLLEGE_TIERS, p=[0.15, 0.35, 0.50])
        
        # Random joining date
        joining_date = start_join_dt + timedelta(days=np.random.randint(0, days_range))
        
        # Age today = joining_age + (2026 - joining_year)
        # We start with joining age (21 to 45)
        joining_age = np.random.randint(21, 46)
        
        records.append({
            'employee_id': emp_id,
            'gender': gender,
            'joining_age': joining_age,
            'location': loc,
            'department': dept,
            'joining_date': joining_date.date(),
            'college_tier': college_tier,
            'manager_id': None,  # Will be allocated dynamically by manager_generator / career_engine
            'status': 'Active'   # Will be updated to 'Exited' if simulated exit occurs
        })
        
    return pd.DataFrame(records)
