# src/generators/manager_generator.py
import random
import pandas as pd
from src.config.config import NUM_MANAGERS

# Seed for reproducibility
random.seed(42)

def generate_managers_master(employees_df, num_managers=NUM_MANAGERS):
    """
    Selects senior employees (L4/L5) to act as people managers, 
    and generates the managers master table.
    """
    print(f"Generating Manager Master from senior employee candidates (Target: {num_managers})...")
    
    # We identify candidates who joined at L4 or L5 (senior roles)
    # L4 joining age is 32-36, L5 is 37+
    candidates = employees_df[employees_df['joining_age'] >= 32].copy()
    
    if len(candidates) < num_managers:
        print(f"Warning: Not enough candidates ({len(candidates)}) for managers. Selecting from all employees.")
        candidates = employees_df.copy()
        
    # Sample exactly num_managers
    selected_managers = candidates.sample(n=num_managers, random_state=42).reset_index(drop=True)
    
    records = []
    for i, row in selected_managers.iterrows():
        m_id = f"MGR{i+1:04d}"
        exp_years = random.randint(8, 22)
        # Managers initially have a capacity/targeted team size of 8 to 15 employees
        targeted_team_size = random.randint(8, 15)
        
        records.append({
            'manager_id': m_id,
            'employee_id': row['employee_id'],
            'department': row['department'],
            'location': row['location'],
            'team_size': 0,  # Will be updated dynamically as employees are assigned
            'targeted_team_size': targeted_team_size, # Capacity limit
            'experience_years': exp_years
        })
        
    return pd.DataFrame(records)
