# src/analytics/retention_analysis.py
"""
Kaplan–Meier Retention Curve Analysis
======================================
Answers the CHRO question:
  "Are Tier-2 graduates leaving earlier than Tier-1 graduates?"

Instead of one attrition %, we compute the probability an employee is
still with the company after X months — for each cohort.

Key concepts:
  • Survival function  S(t) = P(employee still here at time t)
  • Right-censored obs = active employees with no exit date
  • Median survival    = time at which S(t) = 0.50

Outputs:
  data/processed/km_retention.csv        — overall KM survival table
  data/processed/km_by_college_tier.csv  — per-tier survival tables
  data/processed/km_by_role.csv          — per-role survival tables (top 8)
  data/processed/retention_summary.csv   — executive KPI summary

Run:
    python -m src.analytics.retention_analysis
    python src/analytics/retention_analysis.py
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from lifelines import KaplanMeierFitter
from lifelines.statistics import logrank_test

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

DATA_DIR   = os.path.join(ROOT, "data", "synthetic")
OUTPUT_DIR = os.path.join(ROOT, "data", "processed")

# ── ANSI colours ──────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"
WIDTH  = 70

def _c(text, colour): return f"{colour}{text}{RESET}"
def _header(t):       print(_c("=" * WIDTH, CYAN)); print(_c(f"  {t}", BOLD + CYAN)); print(_c("=" * WIDTH, CYAN))
def _section(t):      print(f"\n{_c(BOLD + t, BOLD)}"); print(_c("-" * WIDTH, CYAN))


# ─────────────────────────────────────────────────────────────────────────────
# 1. Data Loading & Preparation
# ─────────────────────────────────────────────────────────────────────────────

def load_and_prepare() -> pd.DataFrame:
    """
    Merge employees + exit_records, compute tenure_months and event flag.

    Right-censored handling:
      Active employees have no exit date → their end_date = today.
      The event flag is 0 (censored) for them.
      Exited employees have event = 1.

    Returns:
        DataFrame with columns:
          employee_id, gender, age, location, department, role, level,
          joining_date, college_tier, manager_id, status,
          exit_date, tenure_months, event
    """
    emp  = pd.read_csv(os.path.join(DATA_DIR, "employees.csv"))
    exits = pd.read_csv(os.path.join(DATA_DIR, "exit_records.csv"))

    # Left join — active employees get NaN for exit columns (censored)
    df = emp.merge(exits[["employee_id", "exit_date"]], on="employee_id", how="left")

    # Parse dates
    today = pd.Timestamp.today().normalize()
    df["joining_date"] = pd.to_datetime(df["joining_date"], errors="coerce")
    df["exit_date"]    = pd.to_datetime(df["exit_date"],    errors="coerce")

    # end_date: exit_date if exited, else today (right-censored)
    df["end_date"] = df["exit_date"].fillna(today)

    # Tenure in months (avg days/month = 30.44)
    df["tenure_months"] = (
        (df["end_date"] - df["joining_date"]).dt.days / 30.44
    ).round(2)

    # Drop rows with invalid tenure (negative or NaN)
    df = df[df["tenure_months"] > 0].copy()

    # Event indicator: 1 = exited, 0 = still active (censored)
    df["event"] = (df["status"] == "Exited").astype(int)

    # Joining quarter for cohort analysis
    df["joining_quarter"] = df["joining_date"].dt.to_period("Q").astype(str)
    df["joining_year"]    = df["joining_date"].dt.year

    return df


# ─────────────────────────────────────────────────────────────────────────────
# 2. Kaplan–Meier Fitter Helpers
# ─────────────────────────────────────────────────────────────────────────────

def fit_km(durations: pd.Series, events: pd.Series, label: str = "Overall") -> KaplanMeierFitter:
    """Fit and return a KaplanMeierFitter on the given subset."""
    kmf = KaplanMeierFitter()
    kmf.fit(durations=durations, event_observed=events, label=label)
    return kmf


def retention_at(kmf: KaplanMeierFitter, months: int) -> float:
    """Return retention probability at a given month (0–1 scale)."""
    sf = kmf.survival_function_
    # Find the last index <= target month
    valid = sf.index[sf.index <= months]
    if len(valid) == 0:
        return 1.0  # no events yet, still 100%
    return round(float(sf.loc[valid[-1]].iloc[0]), 4)


def cohort_summary(kmf: KaplanMeierFitter, label: str) -> dict:
    """Build a summary dict for one cohort."""
    return {
        "cohort":              label,
        "median_tenure_months": kmf.median_survival_time_,
        "retention_12m":        retention_at(kmf, 12),
        "retention_24m":        retention_at(kmf, 24),
        "retention_36m":        retention_at(kmf, 36),
        "retention_48m":        retention_at(kmf, 48),
        "retention_60m":        retention_at(kmf, 60),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. Analysis Functions
# ─────────────────────────────────────────────────────────────────────────────

def analyse_overall(df: pd.DataFrame) -> tuple[KaplanMeierFitter, dict]:
    """Overall company-wide retention curve."""
    kmf     = fit_km(df["tenure_months"], df["event"], label="Overall")
    summary = cohort_summary(kmf, "Overall")
    return kmf, summary


def analyse_by_college_tier(df: pd.DataFrame) -> tuple[dict[str, KaplanMeierFitter], pd.DataFrame]:
    """
    KM curves per college tier.
    Returns dict of fitted KMF objects + a summary DataFrame.
    """
    tiers   = sorted(df["college_tier"].dropna().unique())
    kmfs    = {}
    records = []

    for tier in tiers:
        subset = df[df["college_tier"] == tier]
        kmf    = fit_km(subset["tenure_months"], subset["event"], label=tier)
        kmfs[tier]  = kmf
        records.append(cohort_summary(kmf, tier))

    return kmfs, pd.DataFrame(records)


def analyse_by_role(df: pd.DataFrame, top_n: int = 8) -> tuple[dict[str, KaplanMeierFitter], pd.DataFrame]:
    """
    KM curves for the top-N roles by headcount.
    (45 roles would make the plot unreadable — we keep the biggest ones.)
    """
    top_roles = df["role"].value_counts().head(top_n).index.tolist()
    kmfs      = {}
    records   = []

    for role in top_roles:
        subset = df[df["role"] == role]
        kmf    = fit_km(subset["tenure_months"], subset["event"], label=role)
        kmfs[role]  = kmf
        records.append(cohort_summary(kmf, role))

    return kmfs, pd.DataFrame(records)


def analyse_by_joining_year(df: pd.DataFrame) -> tuple[dict[str, KaplanMeierFitter], pd.DataFrame]:
    """
    KM curves by joining year (annual cohort analysis).
    Older cohorts are more "mature" — their curve drops further.
    """
    years   = sorted(df["joining_year"].dropna().unique())
    kmfs    = {}
    records = []

    for year in years:
        subset = df[df["joining_year"] == year]
        if len(subset) < 30:            # skip tiny cohorts
            continue
        label  = str(int(year))
        kmf    = fit_km(subset["tenure_months"], subset["event"], label=label)
        kmfs[label]  = kmf
        records.append(cohort_summary(kmf, label))

    return kmfs, pd.DataFrame(records)


def analyse_by_department(df: pd.DataFrame) -> tuple[dict[str, KaplanMeierFitter], pd.DataFrame]:
    """KM curves per department."""
    depts   = sorted(df["department"].dropna().unique())
    kmfs    = {}
    records = []

    for dept in depts:
        subset = df[df["department"] == dept]
        if len(subset) < 20:
            continue
        kmf = fit_km(subset["tenure_months"], subset["event"], label=dept)
        kmfs[dept]  = kmf
        records.append(cohort_summary(kmf, dept))

    return kmfs, pd.DataFrame(records)


def logrank_tier_test(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pairwise log-rank test across college tiers.
    p-value < 0.05 → statistically significant difference in retention curves.
    """
    tiers   = sorted(df["college_tier"].dropna().unique())
    results = []

    for i, t1 in enumerate(tiers):
        for t2 in tiers[i + 1:]:
            g1 = df[df["college_tier"] == t1]
            g2 = df[df["college_tier"] == t2]
            lr = logrank_test(
                g1["tenure_months"], g2["tenure_months"],
                g1["event"],         g2["event"]
            )
            results.append({
                "group_1":   t1,
                "group_2":   t2,
                "test_stat": round(lr.test_statistic, 4),
                "p_value":   round(lr.p_value, 6),
                "significant": "Yes" if lr.p_value < 0.05 else "No"
            })

    return pd.DataFrame(results)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Report Printer
# ─────────────────────────────────────────────────────────────────────────────

def _retention_bar(prob: float, width: int = 20) -> str:
    """ASCII sparkline for a retention probability."""
    filled = int(round(prob * width))
    bar    = "█" * filled + "░" * (width - filled)
    colour = GREEN if prob >= 0.75 else (YELLOW if prob >= 0.50 else RED)
    return _c(f"[{bar}] {prob*100:5.1f}%", colour)


def print_report(
    overall_summary:    dict,
    tier_df:            pd.DataFrame,
    role_df:            pd.DataFrame,
    dept_df:            pd.DataFrame,
    year_df:            pd.DataFrame,
    logrank_df:         pd.DataFrame,
) -> None:

    _header("PeopleLens  ·  Retention Curve Analysis  (Kaplan–Meier)")

    # ── Overall KPIs ──────────────────────────────────────────────────────────
    _section("OVERALL COMPANY RETENTION")
    med = overall_summary["median_tenure_months"]
    med_str = f"{med:.1f} months ({med/12:.1f} yrs)" if not (
        isinstance(med, float) and np.isinf(med)
    ) else "Not reached (>50% still active)"

    print(f"  Median Survival Time   : {_c(med_str, BOLD)}")
    print(f"  Retention at 12 months : {_retention_bar(overall_summary['retention_12m'])}")
    print(f"  Retention at 24 months : {_retention_bar(overall_summary['retention_24m'])}")
    print(f"  Retention at 36 months : {_retention_bar(overall_summary['retention_36m'])}")
    print(f"  Retention at 48 months : {_retention_bar(overall_summary['retention_48m'])}")
    print(f"  Retention at 60 months : {_retention_bar(overall_summary['retention_60m'])}")

    # ── College Tier ─────────────────────────────────────────────────────────
    _section("RETENTION BY COLLEGE TIER  (CHRO Priority Question)")
    col_fmt = "  {:<12}  {:>10}  {:>8}  {:>8}  {:>8}  {:>8}  {:>8}"
    print(col_fmt.format("Tier", "Median(mo)", "12-mo", "24-mo", "36-mo", "48-mo", "60-mo"))
    print("  " + "-" * 66)
    best_36  = tier_df.loc[tier_df["retention_36m"].idxmax(),  "cohort"]
    worst_36 = tier_df.loc[tier_df["retention_36m"].idxmin(), "cohort"]
    for _, row in tier_df.sort_values("retention_36m", ascending=False).iterrows():
        flag = _c(" ← BEST",  GREEN) if row["cohort"] == best_36  else (
               _c(" ← WORST", RED)   if row["cohort"] == worst_36 else "")
        med_val = row["median_tenure_months"]
        med_disp = f"{med_val:.1f}" if not (isinstance(med_val, float) and np.isinf(med_val)) else "∞"
        print(col_fmt.format(
            row["cohort"], med_disp,
            f"{row['retention_12m']*100:.1f}%",
            f"{row['retention_24m']*100:.1f}%",
            f"{row['retention_36m']*100:.1f}%",
            f"{row['retention_48m']*100:.1f}%",
            f"{row['retention_60m']*100:.1f}%",
        ) + flag)

    # ── Log-rank significance test ────────────────────────────────────────────
    _section("LOG-RANK TEST — Are Tier Differences Statistically Significant?")
    print("  (p < 0.05 → the curves are significantly different)")
    print(f"  {'Tier A':<10}  {'Tier B':<10}  {'Test Stat':>10}  {'p-value':>10}  {'Sig?':>8}")
    print("  " + "-" * 55)
    for _, row in logrank_df.iterrows():
        sig_col = GREEN if row["significant"] == "Yes" else YELLOW
        print(f"  {row['group_1']:<10}  {row['group_2']:<10}  "
              f"{row['test_stat']:>10.4f}  {row['p_value']:>10.6f}  "
              f"{_c(row['significant'], sig_col):>8}")

    # ── By Role ───────────────────────────────────────────────────────────────
    _section("RETENTION BY ROLE  (Top 8 Roles by Headcount — 36-Month Window)")
    for _, row in role_df.sort_values("retention_36m", ascending=False).iterrows():
        bar = _retention_bar(row["retention_36m"])
        print(f"  {row['cohort']:<30}  {bar}")

    # ── By Department ─────────────────────────────────────────────────────────
    _section("RETENTION BY DEPARTMENT  (36-Month)")
    for _, row in dept_df.sort_values("retention_36m", ascending=False).iterrows():
        bar = _retention_bar(row["retention_36m"])
        print(f"  {row['cohort']:<25}  {bar}")

    # ── By Joining Year ───────────────────────────────────────────────────────
    _section("COHORT ANALYSIS — BY JOINING YEAR")
    print(f"  {'Year':<8}  {'12-mo':>8}  {'24-mo':>8}  {'36-mo':>8}  {'Median(mo)':>12}")
    print("  " + "-" * 50)
    for _, row in year_df.sort_values("cohort").iterrows():
        med_val  = row["median_tenure_months"]
        med_disp = f"{med_val:.1f}" if not (isinstance(med_val, float) and np.isinf(med_val)) else "∞"
        print(f"  {row['cohort']:<8}  "
              f"{row['retention_12m']*100:>7.1f}%  "
              f"{row['retention_24m']*100:>7.1f}%  "
              f"{row['retention_36m']*100:>7.1f}%  "
              f"{med_disp:>12}")

    print()
    print(_c("=" * WIDTH, CYAN))
    print(_c("  Analysis complete — CSVs saved to data/processed/", GREEN + BOLD))
    print(_c("=" * WIDTH, CYAN))


# ─────────────────────────────────────────────────────────────────────────────
# 5. Export
# ─────────────────────────────────────────────────────────────────────────────

def save_outputs(
    overall_kmf:   KaplanMeierFitter,
    tier_kmfs:     dict[str, KaplanMeierFitter],
    overall_summary: dict,
    tier_df:       pd.DataFrame,
    role_df:       pd.DataFrame,
    dept_df:       pd.DataFrame,
    year_df:       pd.DataFrame,
) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Overall KM survival function
    overall_kmf.survival_function_.to_csv(
        os.path.join(OUTPUT_DIR, "km_retention.csv")
    )

    # 2. Per-tier survival functions (wide format for Power BI)
    tier_sf = pd.concat(
        [kmf.survival_function_.rename(columns={tier: tier}) for tier, kmf in tier_kmfs.items()],
        axis=1
    )
    tier_sf.to_csv(os.path.join(OUTPUT_DIR, "km_by_college_tier.csv"))

    # 3. Per-role summary
    role_df.to_csv(os.path.join(OUTPUT_DIR, "km_by_role.csv"), index=False)

    # 4. Executive retention summary
    best_tier  = tier_df.loc[tier_df["retention_36m"].idxmax(), "cohort"]
    worst_tier = tier_df.loc[tier_df["retention_36m"].idxmin(), "cohort"]

    med = overall_summary["median_tenure_months"]
    summary_data = {
        "metric": [
            "Median Retention (months)",
            "Retention at 12 months (%)",
            "Retention at 24 months (%)",
            "Retention at 36 months (%)",
            "Retention at 48 months (%)",
            "Retention at 60 months (%)",
            "Best Retention College Tier",
            "Worst Retention College Tier",
        ],
        "value": [
            round(med, 1) if not (isinstance(med, float) and np.isinf(med)) else "Not reached",
            round(overall_summary["retention_12m"] * 100, 1),
            round(overall_summary["retention_24m"] * 100, 1),
            round(overall_summary["retention_36m"] * 100, 1),
            round(overall_summary["retention_48m"] * 100, 1),
            round(overall_summary["retention_60m"] * 100, 1),
            best_tier,
            worst_tier,
        ]
    }
    pd.DataFrame(summary_data).to_csv(
        os.path.join(OUTPUT_DIR, "retention_summary.csv"), index=False
    )

    # 5. Full tier-level summary
    tier_df.to_csv(os.path.join(OUTPUT_DIR, "km_by_college_tier_summary.csv"), index=False)

    # 6. Department summary
    dept_df.to_csv(os.path.join(OUTPUT_DIR, "km_by_department.csv"), index=False)

    # 7. Year cohort summary
    year_df.to_csv(os.path.join(OUTPUT_DIR, "km_by_joining_year.csv"), index=False)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Public API
# ─────────────────────────────────────────────────────────────────────────────

def run_retention_analysis(save: bool = True) -> dict:
    """
    End-to-end Kaplan–Meier retention analysis.

    Returns a dict with keys:
        df              — prepared DataFrame
        overall_kmf     — overall KaplanMeierFitter
        tier_kmfs       — dict of tier → KaplanMeierFitter
        role_kmfs       — dict of role → KaplanMeierFitter
        dept_kmfs       — dict of dept → KaplanMeierFitter
        year_kmfs       — dict of year → KaplanMeierFitter
        tier_summary    — DataFrame
        role_summary    — DataFrame
        dept_summary    — DataFrame
        year_summary    — DataFrame
        overall_summary — dict
        logrank_df      — DataFrame (pairwise tier test)
    """
    df = load_and_prepare()

    overall_kmf,  overall_summary  = analyse_overall(df)
    tier_kmfs,    tier_df          = analyse_by_college_tier(df)
    role_kmfs,    role_df          = analyse_by_role(df, top_n=8)
    dept_kmfs,    dept_df          = analyse_by_department(df)
    year_kmfs,    year_df          = analyse_by_joining_year(df)
    logrank_df                     = logrank_tier_test(df)

    print_report(overall_summary, tier_df, role_df, dept_df, year_df, logrank_df)

    if save:
        save_outputs(
            overall_kmf, tier_kmfs,
            overall_summary, tier_df, role_df, dept_df, year_df
        )

    return {
        "df":               df,
        "overall_kmf":      overall_kmf,
        "tier_kmfs":        tier_kmfs,
        "role_kmfs":        role_kmfs,
        "dept_kmfs":        dept_kmfs,
        "year_kmfs":        year_kmfs,
        "tier_summary":     tier_df,
        "role_summary":     role_df,
        "dept_summary":     dept_df,
        "year_summary":     year_df,
        "overall_summary":  overall_summary,
        "logrank_df":       logrank_df,
    }


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_retention_analysis(save=True)
