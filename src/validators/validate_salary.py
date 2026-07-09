# src/validators/validate_salary.py
import os
import sys
import pandas as pd

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    salary_path = os.path.abspath(os.path.join(script_dir, "../../data/synthetic/compensation.csv"))
    
    if not os.path.exists(salary_path):
        print(f"Error: Compensation history file not found at {salary_path}")
        sys.exit(1)
        
    salary = pd.read_csv(salary_path)
    
    print("="*60)
    print("          SALARY ENGINE AUDIT REPORT")
    print("="*60)
    print("Overall Salary Description:")
    print(salary["salary"].describe().round(2))
    print("\nMean Salary by Grade/Level:")
    print(salary.groupby("level")["salary"].mean().round(2))
    print("="*60)

if __name__ == '__main__':
    main()
