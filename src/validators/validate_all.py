# src/validators/validate_all.py
import os
import sys
import pandas as pd
from src.config.config import SALARY_BANDS, RATING_DISTRIBUTION, EXIT_REASONS

def run_all_validations():
    print("="*60)
    print("          UNIFIED DATASET VALIDATION REPORTS")
    print("="*60)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.abspath(os.path.join(script_dir, "../../data/synthetic"))
    
    files = {
        "employees": os.path.join(data_dir, "employees.csv"),
        "managers": os.path.join(data_dir, "managers.csv"),
        "compensation": os.path.join(data_dir, "compensation.csv"),
        "performance": os.path.join(data_dir, "performance.csv"),
        "projects": os.path.join(data_dir, "project_assignments.csv"),
        "learning": os.path.join(data_dir, "learning.csv"),
        "exits": os.path.join(data_dir, "exit_records.csv")
    }
    
    # Check if all files exist
    missing_files = [name for name, path in files.items() if not os.path.exists(path)]
    if missing_files:
        print(f"Error: Missing files for validation: {missing_files}")
        return False
        
    # Load all files
    emp = pd.read_csv(files["employees"])
    mgr = pd.read_csv(files["managers"])
    comp = pd.read_csv(files["compensation"])
    perf = pd.read_csv(files["performance"])
    proj = pd.read_csv(files["projects"])
    learn = pd.read_csv(files["learning"])
    exits = pd.read_csv(files["exits"])
    
    print(f"Loaded records:")
    print(f"  Employees : {len(emp)}")
    print(f"  Managers  : {len(mgr)}")
    print(f"  Comp      : {len(comp)}")
    print(f"  Appraisals: {len(perf)}")
    # project assignments name check
    print(f"  Projects  : {len(proj)}")
    print(f"  Learning  : {len(learn)}")
    print(f"  Exits     : {len(exits)}")
    print("-"*60)
    
    # 1. Attrition Rate Validation
    print("1. ATTRITION STATS:")
    attr_rate = emp["status"].value_counts(normalize=True) * 100
    print(attr_rate.round(2).to_string())
    print(f"  Exits count: {len(exits)} ({len(exits)/len(emp)*100:.2f}%)")
    print("-"*60)
    
    # 2. Performance Rating Distribution Validation
    print("2. PERFORMANCE APPRAISAL DISTRIBUTIONS:")
    perf_dist = perf["rating"].value_counts(normalize=True) * 100
    print(perf_dist.sort_index().round(2).to_string())
    print("-"*60)
    
    # 3. Salary Band Compliance Validation
    print("3. SALARY BANDS ENFORCEMENT AUDIT:")
    comp_merged = comp
    violations = 0
    for level, group in comp_merged.groupby("level"):
        min_sal, max_sal = SALARY_BANDS[level]
        min_actual = group["salary"].min()
        max_actual = group["salary"].max()
        print(f"  {level} Band: Target ({min_sal:,} - {max_sal:,}) | Actual ({min_actual:,} - {max_actual:,})")
        if min_actual < min_sal or max_actual > max_sal:
            violations += 1
    if violations == 0:
        print("  Status: SUCCESS - 100% Salary Band Compliance!")
    else:
        print(f"  Status: WARNING - {violations} levels have salary drift/cap issues.")
    print("-"*60)
    
    # 4. Course Categories & status
    print("4. LEARNING COMPLETION & PROFILE ALIGNMENT:")
    print(learn["skill_category"].value_counts().to_string())
    print("\nCompletion Status:")
    print((learn["completion_status"].value_counts(normalize=True) * 100).round(2).to_string())
    print("-"*60)
    
    # 5. Project Billability & client names
    print("5. PROJECT ALLOCATIONS & BILLABILITY:")
    print(proj["client_name"].value_counts().to_string())
    print("\nBillable Status:")
    print(proj["billable"].value_counts().to_string())
    print("-"*60)
    
    # 6. Team Churn / Manager allocations
    print("6. TEAM SIZE CAPACITY CHECKS (8-15 TARGET):")
    # Exclude managers themselves from team counts if needed, but team_size column handles active employees
    team_sizes = emp[emp["status"] == "Active"].groupby("manager_id").size()
    print(f"  Average Active Team Size per Manager: {team_sizes.mean():.2f}")
    print(f"  Min Team Size: {team_sizes.min()}")
    print(f"  Max Team Size: {team_sizes.max()}")
    print("-"*60)
    
    # 7. Exit reasons & voluntariness
    print("7. EXIT REASONS & VOLUNTARINESS:")
    print((exits["exit_reason"].value_counts(normalize=True) * 100).round(2).to_string())
    print("\nVoluntary vs Involuntary:")
    print(exits["voluntary"].value_counts().to_string())
    print("="*60)
    return True

if __name__ == '__main__':
    run_all_validations()
