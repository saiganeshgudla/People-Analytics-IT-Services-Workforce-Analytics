# src/visualization/retention_plots.py
"""
Retention Curve Visualization
==============================
Generates publication-quality Kaplan–Meier survival curve plots
for the PeopleLens workforce analytics dashboard.

Plots produced:
  1. Overall retention curve
  2. Retention by college tier       ← primary CHRO question
  3. Retention by role (top 8)
  4. Retention by department
  5. Retention by joining year (cohort)
  6. Executive 4-panel summary

All plots are saved to docs/plots/ as high-resolution PNG files
and returned as Matplotlib Figure objects for embedding in notebooks.

Run:
    python -m src.visualization.retention_plots
    python src/visualization/retention_plots.py
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless — no display needed
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.lines import Line2D

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

PLOT_DIR = os.path.join(ROOT, "docs", "plots")

# ── Design tokens ─────────────────────────────────────────────────────────────
PALETTE = [
    "#4C72B0", "#DD8452", "#55A868", "#C44E52",
    "#8172B3", "#937860", "#DA8BC3", "#8C8C8C",
    "#CCB974", "#64B5CD",
]

TIER_COLOURS = {
    "Tier-1": "#2ecc71",   # green  — best
    "Tier-2": "#f39c12",   # amber
    "Tier-3": "#e74c3c",   # red    — worst (often)
}

PLOT_STYLE = {
    "figure.facecolor":  "#0f1117",
    "axes.facecolor":    "#1a1d27",
    "axes.edgecolor":    "#3a3f52",
    "axes.labelcolor":   "#e0e0e0",
    "xtick.color":       "#a0a0a0",
    "ytick.color":       "#a0a0a0",
    "grid.color":        "#2a2d3a",
    "grid.linestyle":    "--",
    "grid.alpha":        0.5,
    "text.color":        "#e0e0e0",
    "legend.facecolor":  "#1e2130",
    "legend.edgecolor":  "#3a3f52",
    "legend.labelcolor": "#e0e0e0",
    "font.family":       "DejaVu Sans",
}


def _apply_style() -> None:
    plt.rcParams.update(PLOT_STYLE)


def _finalize(fig: plt.Figure, ax: plt.Axes, title: str, subtitle: str = "") -> None:
    """Apply consistent title, labels, and formatting."""
    ax.set_title(
        f"{title}\n{subtitle}" if subtitle else title,
        fontsize=14, fontweight="bold", color="#ffffff", pad=12
    )
    ax.set_xlabel("Tenure (Months)", fontsize=11, labelpad=8)
    ax.set_ylabel("Retention Probability", fontsize=11, labelpad=8)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1.0, decimals=0))
    ax.set_ylim(0, 1.05)
    ax.set_xlim(left=0)
    ax.axhline(0.50, color="#555566", linewidth=1, linestyle=":", alpha=0.8,
               label="50% threshold")
    ax.grid(True, alpha=0.3)
    ax.tick_params(labelsize=9)
    fig.tight_layout()


def _save(fig: plt.Figure, filename: str) -> str:
    os.makedirs(PLOT_DIR, exist_ok=True)
    path = os.path.join(PLOT_DIR, filename)
    fig.savefig(path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    return path


def _km_line(ax: plt.Axes, kmf, colour: str, lw: float = 2.0,
             alpha: float = 0.85, ci_alpha: float = 0.12) -> None:
    """
    Draw the step-function KM curve + confidence interval band manually.
    Avoids lifelines' built-in plot (which has legacy API quirks).
    """
    sf   = kmf.survival_function_
    ci   = kmf.confidence_interval_survival_function_
    t    = sf.index.values
    sv   = sf.iloc[:, 0].values
    ci_l = ci.iloc[:, 0].values
    ci_u = ci.iloc[:, 1].values
    label = kmf.label if hasattr(kmf, "label") else ""

    ax.step(t, sv,  where="post", color=colour, linewidth=lw,
            alpha=alpha, label=label)
    ax.fill_between(t, ci_l, ci_u, step="post",
                    alpha=ci_alpha, color=colour)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Overall Retention Curve
# ─────────────────────────────────────────────────────────────────────────────

def plot_overall(overall_kmf, overall_summary: dict) -> str:
    _apply_style()
    fig, ax = plt.subplots(figsize=(10, 6), facecolor=PLOT_STYLE["figure.facecolor"])
    ax.set_facecolor(PLOT_STYLE["axes.facecolor"])

    _km_line(ax, overall_kmf, colour="#4C72B0", lw=2.5)

    # Annotate median
    med = overall_summary["median_tenure_months"]
    if not (isinstance(med, float) and np.isinf(med)):
        ax.axvline(med, color="#f1c40f", linewidth=1.2, linestyle="--", alpha=0.7)
        ax.text(med + 1, 0.52, f"Median\n{med:.0f} mo", color="#f1c40f",
                fontsize=8.5, va="bottom")

    # Annotate milestone retention values
    for mo, label_str in [(12, "12-mo"), (24, "24-mo"), (36, "36-mo")]:
        from src.analytics.retention_analysis import retention_at
        val = retention_at(overall_kmf, mo)
        ax.annotate(
            f"{label_str}\n{val*100:.1f}%",
            xy=(mo, val), xytext=(mo + 2, val + 0.05),
            fontsize=8, color="#cccccc",
            arrowprops=dict(arrowstyle="->", color="#666677", lw=0.8),
        )

    ax.legend(loc="upper right", framealpha=0.7, fontsize=9)
    subtitle = (
        f"12-mo: {overall_summary['retention_12m']*100:.1f}%  |  "
        f"36-mo: {overall_summary['retention_36m']*100:.1f}%  |  "
        f"60-mo: {overall_summary['retention_60m']*100:.1f}%"
    )
    _finalize(fig, ax, "Overall Employee Retention Curve", subtitle)

    path = _save(fig, "01_overall_retention.png")
    plt.close(fig)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# 2. Retention by College Tier  (Primary CHRO Question)
# ─────────────────────────────────────────────────────────────────────────────

def plot_by_college_tier(tier_kmfs: dict, tier_summary) -> str:
    _apply_style()
    fig, ax = plt.subplots(figsize=(11, 6.5), facecolor=PLOT_STYLE["figure.facecolor"])
    ax.set_facecolor(PLOT_STYLE["axes.facecolor"])

    for tier, kmf in sorted(tier_kmfs.items()):
        colour = TIER_COLOURS.get(tier, "#888888")
        _km_line(ax, kmf, colour=colour, lw=2.2)

    # 36-month annotation per tier
    for tier, kmf in tier_kmfs.items():
        from src.analytics.retention_analysis import retention_at
        val    = retention_at(kmf, 36)
        colour = TIER_COLOURS.get(tier, "#888888")
        ax.annotate(
            f"{tier}\n{val*100:.1f}% @ 36-mo",
            xy=(36, val),
            xytext=(38, val + (0.03 if tier == "Tier-1" else -0.03 if tier == "Tier-3" else 0)),
            fontsize=8.5, color=colour,
            arrowprops=dict(arrowstyle="-", color=colour, lw=0.6),
        )

    ax.legend(loc="upper right", framealpha=0.8, fontsize=10)
    _finalize(
        fig, ax,
        "Retention by College Tier",
        "CHRO Question: Are Tier-1 graduates retained longer?"
    )
    path = _save(fig, "02_retention_by_college_tier.png")
    plt.close(fig)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# 3. Retention by Role (Top 8)
# ─────────────────────────────────────────────────────────────────────────────

def plot_by_role(role_kmfs: dict) -> str:
    _apply_style()
    fig, ax = plt.subplots(figsize=(12, 7), facecolor=PLOT_STYLE["figure.facecolor"])
    ax.set_facecolor(PLOT_STYLE["axes.facecolor"])

    for i, (role, kmf) in enumerate(role_kmfs.items()):
        _km_line(ax, kmf, colour=PALETTE[i % len(PALETTE)], lw=1.8, ci_alpha=0.06)

    ax.legend(
        loc="lower left", framealpha=0.85, fontsize=8.5,
        ncol=2, columnspacing=1.0
    )
    _finalize(fig, ax, "Retention by Role", "Top 8 Roles by Headcount")
    path = _save(fig, "03_retention_by_role.png")
    plt.close(fig)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# 4. Retention by Department
# ─────────────────────────────────────────────────────────────────────────────

def plot_by_department(dept_kmfs: dict) -> str:
    _apply_style()
    fig, ax = plt.subplots(figsize=(12, 7), facecolor=PLOT_STYLE["figure.facecolor"])
    ax.set_facecolor(PLOT_STYLE["axes.facecolor"])

    for i, (dept, kmf) in enumerate(dept_kmfs.items()):
        _km_line(ax, kmf, colour=PALETTE[i % len(PALETTE)], lw=1.8, ci_alpha=0.06)

    ax.legend(loc="lower left", framealpha=0.85, fontsize=8.5, ncol=2)
    _finalize(fig, ax, "Retention by Department", "Which departments retain employees longest?")
    path = _save(fig, "04_retention_by_department.png")
    plt.close(fig)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# 5. Retention by Joining Year (Cohort Analysis)
# ─────────────────────────────────────────────────────────────────────────────

def plot_by_joining_year(year_kmfs: dict) -> str:
    _apply_style()
    fig, ax = plt.subplots(figsize=(12, 7), facecolor=PLOT_STYLE["figure.facecolor"])
    ax.set_facecolor(PLOT_STYLE["axes.facecolor"])

    years = sorted(year_kmfs.keys())
    cmap  = matplotlib.colormaps.get_cmap("plasma").resampled(len(years))

    for i, year in enumerate(years):
        kmf    = year_kmfs[year]
        colour = matplotlib.colors.to_hex(cmap(i))
        _km_line(ax, kmf, colour=colour, lw=1.6, ci_alpha=0.05)

    ax.legend(loc="lower left", framealpha=0.85, fontsize=8.5, ncol=3,
              title="Joining Year", title_fontsize=9)
    _finalize(
        fig, ax,
        "Retention by Joining Year (Cohort Analysis)",
        "Older cohorts have more mature curves — recent hires are still early in tenure"
    )
    path = _save(fig, "05_retention_by_joining_year.png")
    plt.close(fig)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# 6. Executive 4-Panel Summary
# ─────────────────────────────────────────────────────────────────────────────

def plot_executive_summary(
    overall_kmf,
    tier_kmfs:  dict,
    role_kmfs:  dict,
    tier_summary,
) -> str:
    _apply_style()
    fig, axes = plt.subplots(
        2, 2, figsize=(16, 10),
        facecolor=PLOT_STYLE["figure.facecolor"]
    )
    fig.suptitle(
        "PeopleLens  ·  Retention Analysis  —  Executive Summary",
        fontsize=16, fontweight="bold", color="#ffffff", y=1.01
    )

    # Panel A — Overall
    ax = axes[0, 0]
    ax.set_facecolor(PLOT_STYLE["axes.facecolor"])
    _km_line(ax, overall_kmf, colour="#4C72B0", lw=2.0)
    ax.set_title("A  Overall Retention", color="#ffffff", fontsize=11, fontweight="bold")
    ax.set_xlabel("Tenure (months)", fontsize=9)
    ax.set_ylabel("Retention Prob.", fontsize=9)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1.0, decimals=0))
    ax.set_ylim(0, 1.05); ax.set_xlim(left=0)
    ax.axhline(0.5, color="#555566", lw=0.8, ls=":")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)

    # Panel B — College Tier
    ax = axes[0, 1]
    ax.set_facecolor(PLOT_STYLE["axes.facecolor"])
    for tier, kmf in sorted(tier_kmfs.items()):
        colour = TIER_COLOURS.get(tier, "#888888")
        _km_line(ax, kmf, colour=colour, lw=2.0)
    ax.set_title("B  By College Tier", color="#ffffff", fontsize=11, fontweight="bold")
    ax.set_xlabel("Tenure (months)", fontsize=9)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1.0, decimals=0))
    ax.set_ylim(0, 1.05); ax.set_xlim(left=0)
    ax.axhline(0.5, color="#555566", lw=0.8, ls=":")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)

    # Panel C — Top 5 Roles
    ax = axes[1, 0]
    ax.set_facecolor(PLOT_STYLE["axes.facecolor"])
    for i, (role, kmf) in enumerate(list(role_kmfs.items())[:5]):
        _km_line(ax, kmf, colour=PALETTE[i], lw=1.8, ci_alpha=0.04)
    ax.set_title("C  By Role (Top 5)", color="#ffffff", fontsize=11, fontweight="bold")
    ax.set_xlabel("Tenure (months)", fontsize=9)
    ax.set_ylabel("Retention Prob.", fontsize=9)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1.0, decimals=0))
    ax.set_ylim(0, 1.05); ax.set_xlim(left=0)
    ax.axhline(0.5, color="#555566", lw=0.8, ls=":")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7, ncol=1)

    # Panel D — Tier 36-month bar chart
    ax = axes[1, 1]
    ax.set_facecolor(PLOT_STYLE["axes.facecolor"])
    tier_summary_sorted = tier_summary.sort_values("retention_36m", ascending=True)
    bars = ax.barh(
        tier_summary_sorted["cohort"],
        tier_summary_sorted["retention_36m"] * 100,
        color=[TIER_COLOURS.get(t, "#888") for t in tier_summary_sorted["cohort"]],
        alpha=0.85, edgecolor="#2a2d3a"
    )
    for bar, val in zip(bars, tier_summary_sorted["retention_36m"] * 100):
        ax.text(val + 0.3, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", ha="left",
                color="#e0e0e0", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 105)
    ax.set_xlabel("36-Month Retention (%)", fontsize=9)
    ax.set_title("D  36-Month Retention by Tier", color="#ffffff", fontsize=11, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=0))

    fig.tight_layout(rect=[0, 0, 1, 0.98])
    path = _save(fig, "00_executive_summary.png")
    plt.close(fig)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# 7. Main runner
# ─────────────────────────────────────────────────────────────────────────────

def generate_all_plots(results: dict) -> list[str]:
    """
    Generate all 6 plots from a results dict returned by run_retention_analysis().

    Returns:
        List of saved file paths.
    """
    paths = []

    print("\n  Generating plots…")

    p = plot_overall(results["overall_kmf"], results["overall_summary"])
    print(f"  ✓  {os.path.basename(p)}")
    paths.append(p)

    p = plot_by_college_tier(results["tier_kmfs"], results["tier_summary"])
    print(f"  ✓  {os.path.basename(p)}")
    paths.append(p)

    p = plot_by_role(results["role_kmfs"])
    print(f"  ✓  {os.path.basename(p)}")
    paths.append(p)

    p = plot_by_department(results["dept_kmfs"])
    print(f"  ✓  {os.path.basename(p)}")
    paths.append(p)

    p = plot_by_joining_year(results["year_kmfs"])
    print(f"  ✓  {os.path.basename(p)}")
    paths.append(p)

    p = plot_executive_summary(
        results["overall_kmf"],
        results["tier_kmfs"],
        results["role_kmfs"],
        results["tier_summary"],
    )
    print(f"  ✓  {os.path.basename(p)}")
    paths.append(p)

    print(f"\n  All plots saved → {PLOT_DIR}/")
    return paths


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from src.analytics.retention_analysis import run_retention_analysis

    results = run_retention_analysis(save=True)
    paths   = generate_all_plots(results)
