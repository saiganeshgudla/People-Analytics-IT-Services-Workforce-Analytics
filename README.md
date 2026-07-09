# People Analytics - IT Services Workforce Analytics

A professional-grade people analytics repository designed to analyze IT services workforce data.

## Project Structure

The project follows a clean, modular structure for data science and machine learning development:

```text
.
├── data/                       # Dataset directories
│   ├── raw/                    # Original, immutable data dumps
│   ├── processed/              # Cleaned and transformed data ready for modeling
│   └── synthetic/              # Artificially generated data for testing/demos
├── notebooks/                  # Jupyter notebooks for exploration and prototyping
├── sql/                        # SQL queries for database extraction and manipulation
├── src/                        # Core source code of the project
│   ├── data_generation/        # Scripts to generate synthetic datasets
│   ├── preprocessing/          # Data cleaning, transformation, and feature engineering
│   ├── analytics/              # Statistical analysis and business intelligence logic
│   ├── models/                 # Model training, evaluation, and inference code
│   └── visualization/          # Custom plotting and visualization utilities
├── dashboard/                  # Dashboard applications (e.g., Streamlit, Dash, etc.)
├── docs/                       # Project documentation, design docs, and reports
├── tests/                      # Unit and integration tests
├── requirements.txt            # Project dependencies
├── README.md                   # Project overview (this file)
└── .gitignore                  # Git ignore file
```

## Setup and Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
