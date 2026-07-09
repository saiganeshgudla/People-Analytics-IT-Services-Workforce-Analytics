# src/database/load_data.py
import os
import sys
import getpass
import pandas as pd
from sqlalchemy import create_engine

def load_database():
    """
    ETL loading routine that imports all generated CSV data into local PostgreSQL.
    Tolerates connection timeouts and falls back to macOS system username if postgres fails.
    """
    print("\nConnecting to PostgreSQL database...")
    
    # Try default 'postgres' user, then fall back to current macOS system user
    usernames = ["postgres", getpass.getuser()]
    engine = None
    last_error = None
    
    for username in usernames:
        if username == "postgres":
            uri = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/peoplelens")
        else:
            uri = os.getenv("DATABASE_URL", f"postgresql://{username}@localhost:5432/peoplelens")
            
        try:
            # Short connection timeout for fast checks
            test_engine = create_engine(uri, connect_args={'connect_timeout': 3})
            # Test connectivity
            with test_engine.connect() as conn:
                pass
            engine = test_engine
            print(f"  Successfully established connection as user '{username}'.")
            break
        except Exception as e:
            last_error = e
            
    if engine is None:
        print("\n" + "!"*60)
        print("DATABASE LOAD WARNING:")
        print(f"Could not load data into PostgreSQL database. Last Error: {last_error}")
        print("Make sure PostgreSQL is running and database 'peoplelens' exists.")
        print("CSVs are fully generated and saved under data/synthetic/")
        print("!"*60 + "\n")
        return False
        
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.abspath(os.path.join(script_dir, "../..", "data/synthetic"))
        
        def load_table(filename, table_name):
            filepath = os.path.join(data_dir, filename)
            if not os.path.exists(filepath):
                print(f"  Warning: CSV file not found: {filename}")
                return
            df = pd.read_csv(filepath)
            df.to_sql(table_name, engine, if_exists="replace", index=False)
            print(f"  Table '{table_name}' loaded successfully into database.")
            
        load_table("employees.csv", "employees")
        load_table("managers.csv", "managers")
        load_table("performance.csv", "performance")
        load_table("compensation.csv", "compensation")
        load_table("learning.csv", "learning")
        load_table("project_assignments.csv", "projects")
        load_table("exit_records.csv", "exits")
        
        print("Database loading complete.")
        return True
    except Exception as e:
        print(f"Error during table ingestion: {e}")
        return False
