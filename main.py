# main.py
import os
import sys

# Ensure project root is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.generators.employee_generator import generate_base_employees
from src.generators.manager_generator import generate_managers_master
from src.simulators.career_engine import run_workforce_simulation
from src.database.export_data import save_dataframe
from src.database.load_data import load_database
from src.validators.validate_all import run_all_validations

def main():
    print("="*60)
    print("      PEOPLELENS WORKFORCE SIMULATION PIPELINE")
    print("="*60)
    
    # 1. Generate base employees
    emp_base = generate_base_employees()
    
    # 2. Generate managers master
    mgr_base = generate_managers_master(emp_base)
    
    # 3. Run chronological yearly career lifecycles simulation
    print("\nRunning Career Simulation...")
    (
        employees_df,
        compensation_df,
        performance_df,
        projects_df,
        learning_df,
        exits_df,
        managers_df
    ) = run_workforce_simulation(emp_base, mgr_base)
    
    # 4. Save results to CSVs using the export module
    print("\nExporting Simulation Tables...")
    save_dataframe(employees_df, "employees.csv")
    save_dataframe(managers_df, "managers.csv")
    save_dataframe(compensation_df, "compensation.csv")
    save_dataframe(performance_df, "performance.csv")
    save_dataframe(projects_df, "project_assignments.csv")
    save_dataframe(learning_df, "learning.csv")
    save_dataframe(exits_df, "exit_records.csv")
    print("CSVs exported successfully.")
    
    # 5. Load into PostgreSQL database
    print("\nLoading PostgreSQL Database...")
    load_database()
    
    # 6. Run validation audits
    print("\nExecuting Validation Audits...")
    run_all_validations()
    
    print("\n" + "="*60)
    print("PEOPLELENS WORKFORCE SIMULATION COMPLETE")
    print("="*60)

if __name__ == '__main__':
    main()
