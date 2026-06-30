"""
database/load_data.py
─────────────────────
PeopleLens — CSV → PostgreSQL Loader

Reads synthetic CSVs from data/synthetic/ and bulk-loads them into the
raw schema. Validates schema, handles duplicates, and writes an audit log.

Usage:
    python database/load_data.py                   # loads all tables
    python database/load_data.py --table employee  # loads one table
    python database/load_data.py --dry-run         # validate only
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/load_data.log", mode="a"),
    ],
)
log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
load_dotenv()
BASE_DIR = Path(__file__).parent.parent
SYNTHETIC_DIR = BASE_DIR / "data" / "synthetic"

TABLE_CONFIG: dict[str, dict] = {
    "employee": {
        "csv": "employees.csv",
        "target": "raw.raw_employee",
        "pk": "employee_id",
        "required_cols": ["employee_id", "join_date", "gender", "department", "role", "level", "location"],
    },
    "salary": {
        "csv": "salary_history.csv",
        "target": "raw.raw_salary",
        "pk": None,
        "required_cols": ["employee_id", "effective_date", "base_salary"],
    },
    "performance": {
        "csv": "performance.csv",
        "target": "raw.raw_performance",
        "pk": None,
        "required_cols": ["employee_id", "review_year", "rating"],
    },
    "project": {
        "csv": "projects.csv",
        "target": "raw.raw_project",
        "pk": None,
        "required_cols": ["employee_id", "project_id", "start_date"],
    },
    "learning": {
        "csv": "learning.csv",
        "target": "raw.raw_learning",
        "pk": None,
        "required_cols": ["employee_id", "year", "quarter", "learning_hours"],
    },
    "exit": {
        "csv": "exits.csv",
        "target": "raw.raw_exit",
        "pk": "employee_id",
        "required_cols": ["employee_id", "exit_date", "exit_reason", "voluntary"],
    },
    "manager": {
        "csv": "managers.csv",
        "target": "raw.raw_manager",
        "pk": None,
        "required_cols": ["manager_id", "level", "department"],
    },
}


def get_engine():
    """Create SQLAlchemy engine from environment."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Build from parts
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "peoplelens")
        user = os.getenv("POSTGRES_USER", "peoplelens_user")
        password = os.getenv("POSTGRES_PASSWORD", "")
        db_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    return create_engine(db_url, pool_pre_ping=True)


def validate_csv(df: pd.DataFrame, config: dict, table_name: str) -> bool:
    """Validate that required columns exist and data is non-empty."""
    missing = [c for c in config["required_cols"] if c not in df.columns]
    if missing:
        log.error(f"[{table_name}] Missing required columns: {missing}")
        return False
    if df.empty:
        log.warning(f"[{table_name}] CSV is empty, skipping.")
        return False
    null_pcts = df[config["required_cols"]].isnull().mean() * 100
    high_null = null_pcts[null_pcts > 10]
    if not high_null.empty:
        log.warning(f"[{table_name}] High null % in columns:\n{high_null}")
    return True


def load_table(engine, table_name: str, config: dict, dry_run: bool = False) -> dict:
    """Load one CSV into the corresponding raw table."""
    csv_path = SYNTHETIC_DIR / config["csv"]
    result = {
        "table": table_name,
        "status": "skipped",
        "rows_read": 0,
        "rows_loaded": 0,
        "error": None,
    }

    if not csv_path.exists():
        log.warning(f"[{table_name}] CSV not found: {csv_path}")
        result["status"] = "missing_csv"
        return result

    try:
        df = pd.read_csv(csv_path, low_memory=False)
        result["rows_read"] = len(df)
        log.info(f"[{table_name}] Read {len(df):,} rows from {csv_path.name}")

        if not validate_csv(df, config, table_name):
            result["status"] = "validation_failed"
            return result

        if dry_run:
            log.info(f"[{table_name}] DRY RUN — skipping write.")
            result["status"] = "dry_run"
            return result

        # Truncate target table before load (idempotent)
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {config['target']} RESTART IDENTITY CASCADE"))

        # Bulk insert
        df.to_sql(
            config["target"].split(".")[1],
            engine,
            schema=config["target"].split(".")[0],
            if_exists="append",
            index=False,
            chunksize=1000,
            method="multi",
        )
        result["rows_loaded"] = len(df)
        result["status"] = "success"
        log.info(f"[{table_name}] ✅ Loaded {len(df):,} rows → {config['target']}")

    except SQLAlchemyError as e:
        result["status"] = "db_error"
        result["error"] = str(e)
        log.error(f"[{table_name}] DB error: {e}")
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        log.error(f"[{table_name}] Unexpected error: {e}")

    return result


def print_summary(results: list[dict]) -> None:
    """Print a formatted load summary."""
    print("\n" + "=" * 60)
    print(f"{'PeopleLens Data Load Summary':^60}")
    print(f"{'Timestamp: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'):^60}")
    print("=" * 60)
    print(f"{'Table':<20} {'Status':<20} {'Rows Read':>10} {'Rows Loaded':>12}")
    print("-" * 60)
    for r in results:
        print(
            f"{r['table']:<20} {r['status']:<20} {r['rows_read']:>10,} {r['rows_loaded']:>12,}"
        )
    print("=" * 60)
    successes = sum(1 for r in results if r["status"] == "success")
    print(f"✅ {successes}/{len(results)} tables loaded successfully.\n")


def main():
    parser = argparse.ArgumentParser(description="Load synthetic HR data into PostgreSQL.")
    parser.add_argument("--table", choices=list(TABLE_CONFIG.keys()), help="Load a single table.")
    parser.add_argument("--dry-run", action="store_true", help="Validate only, do not write.")
    args = parser.parse_args()

    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)

    log.info("PeopleLens Data Loader starting...")
    engine = get_engine()

    tables_to_load = {args.table: TABLE_CONFIG[args.table]} if args.table else TABLE_CONFIG

    results = []
    for name, config in tables_to_load.items():
        result = load_table(engine, name, config, dry_run=args.dry_run)
        results.append(result)

    print_summary(results)


if __name__ == "__main__":
    main()
