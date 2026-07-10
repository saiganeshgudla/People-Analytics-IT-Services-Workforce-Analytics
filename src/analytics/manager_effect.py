# src/analytics/manager_effect.py
"""
Manager Effect Analysis
=======================
Answers CHRO-level questions about manager performance by building
a comprehensive Manager Scorecard from the synthetic HR datasets.

KPIs computed:
  1. Team Size
  2. Attrition Rate
  3. Average Team Performance Rating
  4. Average Team Salary
  5. Team Learning Hours
  6. Promotion Rate
  7. Composite Risk Score
  8. Company-average benchmark & flag

Run:
    python -m src.analytics.manager_effect
    python src/analytics/manager_effect.py
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

DATA_DIR = os.path.join(ROOT, "data", "synthetic")

# ── ANSI colours ──────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"
WIDTH  = 70


def _c(text, colour):  return f"{colour}{text}{RESET}"
def _header(title):    print(_c("=" * WIDTH, CYAN)); print(_c(f"  {title}", BOLD + CYAN)); print(_c("=" * WIDTH, CYAN))
def _section(title):   print(f"\n{_c(BOLD + title, BOLD)}"); print(_c("-" * WIDTH, CYAN))


# ─────────────────────────────────────────────────────────────────────────────
# 1. Data Loading
# ─────────────────────────────────────────────────────────────────────────────

def load_data() -> dict[str, pd.DataFrame]:
    """Load all required CSVs; return as a dict of DataFrames."""
    files = {
        "employees":   "employees.csv",
        "performance": "performance.csv",
        "compensation":"compensation.csv",
        "learning":    "learning.csv",
    }
    dfs = {}
    for key, fname in files.items():
        path = os.path.join(DATA_DIR, fname)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing: {path}")
        dfs[key] = pd.read_csv(path)

    # Parse dates
    dfs["employees"]["joining_date"] = pd.to_datetime(
        dfs["employees"]["joining_date"], errors="coerce"
    )
    return dfs


# ─────────────────────────────────────────────────────────────────────────────
# 2. KPI Builders
# ─────────────────────────────────────────────────────────────────────────────

def kpi_team_size(emp: pd.DataFrame) -> pd.DataFrame:
    """KPI 1: How many employees report to each manager?"""
    return (
        emp[emp["manager_id"].notna()]
        .groupby("manager_id")
        .agg(team_size=("employee_id", "count"))
        .reset_index()
        .sort_values("team_size", ascending=False)
    )


def kpi_attrition(emp: pd.DataFrame) -> pd.DataFrame:
    """KPI 2: Attrition rate per manager — the headline CHRO metric."""
    grp = (
        emp[emp["manager_id"].notna()]
        .groupby("manager_id")
        .agg(
            team_size=("employee_id", "count"),
            exits=("status", lambda x: (x == "Exited").sum()),
        )
        .reset_index()
    )
    grp["attrition_rate_pct"] = (grp["exits"] / grp["team_size"] * 100).round(2)
    return grp.sort_values("attrition_rate_pct", ascending=False)


def kpi_performance(emp: pd.DataFrame, perf: pd.DataFrame) -> pd.DataFrame:
    """KPI 3: Average team performance rating per manager."""
    merged = perf.merge(emp[["employee_id", "manager_id"]], on="employee_id", how="left")
    return (
        merged[merged["manager_id"].notna()]
        .groupby("manager_id")
        .agg(avg_team_rating=("rating", "mean"))
        .round(2)
        .reset_index()
        .sort_values("avg_team_rating", ascending=False)
    )


def kpi_salary(emp: pd.DataFrame, comp: pd.DataFrame) -> pd.DataFrame:
    """KPI 4: Average team salary per manager (latest comp per employee)."""
    # Get most recent salary row per employee
    latest = (
        comp.sort_values("effective_date", ascending=False)
        .groupby("employee_id")
        .first()
        .reset_index()[["employee_id", "salary"]]
    )
    merged = latest.merge(emp[["employee_id", "manager_id"]], on="employee_id", how="left")
    return (
        merged[merged["manager_id"].notna()]
        .groupby("manager_id")
        .agg(avg_team_salary=("salary", "mean"))
        .round(0)
        .reset_index()
        .sort_values("avg_team_salary", ascending=False)
    )


def kpi_learning(emp: pd.DataFrame, learn: pd.DataFrame) -> pd.DataFrame:
    """KPI 5: Total and average learning hours per manager's team."""
    merged = learn.merge(emp[["employee_id", "manager_id"]], on="employee_id", how="left")
    return (
        merged[merged["manager_id"].notna()]
        .groupby("manager_id")
        .agg(
            total_learning_hours=("hours_completed", "sum"),
            avg_hours_per_course=("hours_completed", "mean"),
        )
        .round(2)
        .reset_index()
        .sort_values("total_learning_hours", ascending=False)
    )


def kpi_promotion(emp: pd.DataFrame, perf: pd.DataFrame) -> pd.DataFrame:
    """KPI 6: Promotion rate per manager."""
    merged = perf.merge(emp[["employee_id", "manager_id"]], on="employee_id", how="left")
    grp = (
        merged[merged["manager_id"].notna()]
        .groupby("manager_id")
        .agg(
            total_appraisals=("employee_id", "count"),
            promotions=("promotion", lambda x: (x == "Yes").sum()),
        )
        .reset_index()
    )
    grp["promotion_rate_pct"] = (
        grp["promotions"] / grp["total_appraisals"] * 100
    ).round(2)
    return grp.sort_values("promotion_rate_pct", ascending=False)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Master Scorecard
# ─────────────────────────────────────────────────────────────────────────────

def build_scorecard(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    KPI 7: Full Manager Scorecard.
    Joins all 6 KPIs into a single DataFrame — one row per manager.
    """
    emp   = dfs["employees"]
    perf  = dfs["performance"]
    comp  = dfs["compensation"]
    learn = dfs["learning"]

    ts  = kpi_team_size(emp)
    att = kpi_attrition(emp)[["manager_id", "exits", "attrition_rate_pct"]]
    pf  = kpi_performance(emp, perf)
    sal = kpi_salary(emp, comp)
    lrn = kpi_learning(emp, learn)[["manager_id", "total_learning_hours"]]
    prm = kpi_promotion(emp, perf)[["manager_id", "promotion_rate_pct"]]

    scorecard = (
        ts
        .merge(att, on="manager_id", how="left")
        .merge(pf,  on="manager_id", how="left")
        .merge(sal, on="manager_id", how="left")
        .merge(lrn, on="manager_id", how="left")
        .merge(prm, on="manager_id", how="left")
    )

    # ── KPI 8: Risk rank (RANK by attrition_rate_pct) ──────────────────────
    scorecard["risk_rank"] = (
        scorecard["attrition_rate_pct"]
        .rank(method="min", ascending=False)
        .astype(int)
    )

    # ── KPI 9: Company-average benchmark ────────────────────────────────────
    company_avg_attrition = (
        (emp["status"] == "Exited").sum() / len(emp) * 100
    ).round(2)
    scorecard["company_avg_attrition_pct"] = company_avg_attrition
    scorecard["variance_from_avg"] = (
        scorecard["attrition_rate_pct"] - company_avg_attrition
    ).round(2)

    # Auto-flag managers
    def _flag(variance: float) -> str:
        if variance > 5:
            return "🔴 HIGH RISK  — Needs Coaching"
        elif variance < -5:
            return "🟢 STAR       — Best Practice"
        else:
            return "🟡 AVERAGE    — Monitor"

    scorecard["manager_flag"] = scorecard["variance_from_avg"].apply(_flag)

    # ── Composite Risk Score ─────────────────────────────────────────────────
    # Higher attrition and lower performance → higher risk score (0–100)
    att_norm  = (scorecard["attrition_rate_pct"] - scorecard["attrition_rate_pct"].min()) / \
                (scorecard["attrition_rate_pct"].max() - scorecard["attrition_rate_pct"].min() + 1e-9)
    perf_norm = 1 - (scorecard["avg_team_rating"] - scorecard["avg_team_rating"].min()) / \
                    (scorecard["avg_team_rating"].max() - scorecard["avg_team_rating"].min() + 1e-9)
    scorecard["composite_risk_score"] = (
        (att_norm * 0.6 + perf_norm * 0.4) * 100
    ).round(1)

    return scorecard.sort_values("attrition_rate_pct", ascending=False).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Report Printer
# ─────────────────────────────────────────────────────────────────────────────

def print_report(scorecard: pd.DataFrame) -> None:
    total_managers  = len(scorecard)
    company_avg     = scorecard["company_avg_attrition_pct"].iloc[0]
    high_risk_count = (scorecard["manager_flag"].str.startswith("🔴")).sum()
    star_count      = (scorecard["manager_flag"].str.startswith("🟢")).sum()

    _header("PeopleLens  ·  Manager Effect Analysis")
    print(f"\n  Total Managers Analysed : {total_managers}")
    print(f"  Company Attrition Avg   : {company_avg}%")
    print(f"  🔴 High-Risk Managers   : {_c(str(high_risk_count), RED + BOLD)}")
    print(f"  🟢 Star Managers        : {_c(str(star_count), GREEN + BOLD)}")

    # ── Top 10 highest-attrition managers ────────────────────────────────────
    _section("TOP 10 HIGHEST-RISK MANAGERS  (by Attrition Rate)")
    top10 = scorecard.head(10)[
        ["manager_id", "team_size", "exits", "attrition_rate_pct",
         "avg_team_rating", "variance_from_avg", "manager_flag"]
    ]
    col_w = [10, 10, 8, 16, 13, 14, 35]
    headers = ["Manager", "Team Sz", "Exits", "Attrition %", "Avg Rating", "vs Avg", "Flag"]
    row_fmt = "  " + "  ".join(f"{{:<{w}}}" for w in col_w)
    print(row_fmt.format(*headers))
    print("  " + "-" * (sum(col_w) + 2 * len(col_w)))
    for _, r in top10.iterrows():
        colour = RED if r["variance_from_avg"] > 5 else (GREEN if r["variance_from_avg"] < -5 else YELLOW)
        attrition_str = _c(f"{r['attrition_rate_pct']}%", colour)
        print("  " + "  ".join([
            f"{str(r['manager_id']):<10}",
            f"{str(int(r['team_size'])):<10}",
            f"{str(int(r['exits'])):<8}",
            f"{attrition_str:<{16 + len(colour) + len(RESET)}}",
            f"{str(r['avg_team_rating']):<13}",
            f"{str(r['variance_from_avg']):<14}",
            f"{str(r['manager_flag']):<35}",
        ]))

    # ── Top 10 best-performing managers ──────────────────────────────────────
    _section("TOP 10 STAR MANAGERS  (Lowest Attrition + Highest Performance)")
    stars = scorecard.sort_values(
        ["attrition_rate_pct", "avg_team_rating"],
        ascending=[True, False]
    ).head(10)[
        ["manager_id", "team_size", "attrition_rate_pct",
         "avg_team_rating", "promotion_rate_pct", "total_learning_hours"]
    ]
    col_w2 = [10, 10, 14, 12, 16, 18]
    headers2 = ["Manager", "Team Sz", "Attrition %", "Avg Rating", "Promo Rate %", "Learning Hrs"]
    print(row_fmt.replace("  ".join(f"{{:<{w}}}" for w in col_w), "  ".join(f"{{:<{w}}}" for w in col_w2)).format(*headers2))
    print("  " + "-" * (sum(col_w2) + 2 * len(col_w2)))
    for _, r in stars.iterrows():
        print("  " + "  ".join([
            f"{str(r['manager_id']):<10}",
            f"{str(int(r['team_size'])):<10}",
            f"{_c(str(r['attrition_rate_pct']) + '%', GREEN):<{14 + len(GREEN) + len(RESET)}}",
            f"{str(r['avg_team_rating']):<12}",
            f"{str(r['promotion_rate_pct']):<16}",
            f"{str(int(r['total_learning_hours'])):<18}",
        ]))

    # ── Company benchmarks ────────────────────────────────────────────────────
    _section("COMPANY BENCHMARK SUMMARY")
    flag_dist = scorecard["manager_flag"].value_counts()
    for flag, count in flag_dist.items():
        pct = round(count / total_managers * 100, 1)
        print(f"  {flag:<40} {count:>4} managers  ({pct}%)")

    # ── Distribution stats ────────────────────────────────────────────────────
    _section("ATTRITION RATE DISTRIBUTION ACROSS MANAGERS")
    stats = scorecard["attrition_rate_pct"].describe()
    print(f"  Min     : {stats['min']:.2f}%")
    print(f"  Q1      : {stats['25%']:.2f}%")
    print(f"  Median  : {stats['50%']:.2f}%")
    print(f"  Mean    : {stats['mean']:.2f}%  ← company average")
    print(f"  Q3      : {stats['75%']:.2f}%")
    print(f"  Max     : {stats['max']:.2f}%")

    print()
    print(_c("=" * WIDTH, CYAN))
    print(_c("  Analysis complete — scorecard saved to data/processed/manager_scorecard.csv", GREEN + BOLD))
    print(_c("=" * WIDTH, CYAN))


# ─────────────────────────────────────────────────────────────────────────────
# 5. Export
# ─────────────────────────────────────────────────────────────────────────────

def save_scorecard(scorecard: pd.DataFrame) -> str:
    """Save the full scorecard to data/processed/ for Power BI / dashboard use."""
    out_dir = os.path.join(ROOT, "data", "processed")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "manager_scorecard.csv")
    scorecard.to_csv(out_path, index=False)
    return out_path


# ─────────────────────────────────────────────────────────────────────────────
# 6. Public API
# ─────────────────────────────────────────────────────────────────────────────

def run_manager_analysis(save: bool = True) -> pd.DataFrame:
    """
    End-to-end manager effect analysis.

    Args:
        save: If True, writes scorecard CSV to data/processed/.

    Returns:
        Full manager scorecard DataFrame.
    """
    dfs       = load_data()
    scorecard = build_scorecard(dfs)
    print_report(scorecard)

    if save:
        path = save_scorecard(scorecard)
        print(f"\n  Saved → {path}")

    return scorecard


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    scorecard = run_manager_analysis(save=True)
