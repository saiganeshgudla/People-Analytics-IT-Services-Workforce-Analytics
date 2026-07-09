# main.py
import os
import sys

# Ensure project root is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.generators.employee_generator import generate_base_employees
from src.generators.manager_generator import generate_managers_master
from src.simulators.career_engine import run_workforce_simulation
from src.validators.validate_all import run_all_validations

def main():
    print("="*60)
    print("      NIMBUSTECH HR SIMULATION ENGINE (PHASE 2)")
    print("="*60)
    
    # 1. Generate base employees
    emp_base = generate_base_employees()
    
    # 2. Generate managers master
    mgr_base = generate_managers_master(emp_base)
    
    # 3. Run chronological yearly career lifecycles simulation
    (
        employees_df,
        compensation_df,
        performance_df,
        projects_df,
        learning_df,
        exits_df,
        managers_df
    ) = run_workforce_simulation(emp_base, mgr_base)
    
    # Create synthetic directory if not exists
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/synthetic")
    os.makedirs(output_dir, exist_ok=True)
    
    # 4. Save results to CSVs
    print("\nSaving simulation tables to CSV...")
    employees_df.to_csv(os.path.join(output_dir, "employees.csv"), index=False)
    managers_df.to_csv(os.path.join(output_dir, "managers.csv"), index=False)
    compensation_df.to_csv(os.path.join(output_dir, "compensation.csv"), index=False)
    performance_df.to_csv(os.path.join(output_dir, "performance.csv"), index=False)
    projects_df.to_csv(os.path.join(output_dir, "project_assignments.csv"), index=False)
    learning_df.to_csv(os.path.join(output_dir, "learning.csv"), index=False)
    exits_df.to_csv(os.path.join(output_dir, "exit_records.csv"), index=False)
    
    print("CSVs saved successfully.")
    
    # 5. Run validation report
    print("\nExecuting Validation Audits...")
    run_all_validations()

if __name__ == '__main__':
    main()
