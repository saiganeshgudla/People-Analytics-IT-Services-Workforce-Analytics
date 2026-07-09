# src/database/export_data.py
import os

def save_dataframe(df, filename):
    """
    Saves a pandas DataFrame to the synthetic data folder in data/synthetic.
    Creates the directory if it does not exist.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.abspath(os.path.join(script_dir, "../..", "data/synthetic"))
    os.makedirs(folder, exist_ok=True)
    
    filepath = os.path.join(folder, filename)
    df.to_csv(filepath, index=False)
    print(f"  {filename} saved to {filepath}")
