"""
dashboard/pages/5_Retention.py
────────────────────────────────
Retention Curves — Kaplan-Meier survival curves by college tier.
Cohort table with 6m, 12m, 24m, 36m retention rates.
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Retention Curves | PeopleLens", page_icon="📈", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
</style>
""", unsafe_allow_html=True)

st.title("📈 New-Joiner Retention Curves")
st.caption("Kaplan-Meier Survival Analysis · Stratified by College Tier · Cohort Analysis")
st.divider()


@st.cache_data(ttl=300)
def load_employees():
    path = ROOT / "data" / "synthetic" / "employees.csv"
    if not path.exists():
        return None
    return pd.read_csv(path, parse_dates=["join_date", "exit_date"])


employees = load_employees()
if employees is None:
    st.error("⚠️ No data. Run `python data_generator/generate_dataset.py`")
    st.stop()

from analytics.retention_analysis import compute_km_by_college_tier, compute_retention_cohort_table

# ── KM Curves ─────────────────────────────────────────────────────────────────
st.subheader("Kaplan-Meier Survival Curves by College Tier")

km_data = compute_km_by_college_tier(employees)

if not km_data:
    st.warning("lifelines library not installed or insufficient data. Run: `pip install lifelines`")
else:
    tier_colors = {
        "Tier 1 (IIT/NIT)": "#6BCB77",
        "Tier 2 (State Engg)": "#FFA500",
        "Tier 3 (Other)": "#FF5050",
    }

    fig = go.Figure()
    for tier, data in km_data.items():
        color = tier_colors.get(tier, "#7C83FF")
        timeline_yr = [t / 365.25 for t in data["timeline"]]

        # Confidence band
        fig.add_trace(go.Scatter(
            x=timeline_yr + timeline_yr[::-1],
            y=data["ci_upper"] + data["ci_lower"][::-1],
            fill="toself",
            fillcolor=color.replace("#", "rgba(") + ",0.1)" if "#" in color else color,
            line=dict(width=0),
            showlegend=False,
        ))
        # Survival curve
        fig.add_trace(go.Scatter(
            x=timeline_yr,
            y=data["survival"],
            mode="lines",
            name=f"{tier} (n={data['n']:,})",
            line=dict(color=color, width=2.5),
        ))

    # Annotation: Year-1 mark
    fig.add_vline(x=1.0, line_dash="dash", line_color="#888", annotation_text="Year 1")
    fig.add_vline(x=3.0, line_dash="dash", line_color="#555", annotation_text="Year 3")

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E0E0FF",
        height=450,
        xaxis=dict(title="Tenure (Years)", gridcolor="#2D3050", range=[0, 6]),
        yaxis=dict(title="Probability of Still Employed", gridcolor="#2D3050",
                   tickformat=".0%", range=[0, 1.05]),
        legend=dict(bgcolor="rgba(30,34,53,0.8)", bordercolor="#2D3050", borderwidth=1),
        margin=dict(t=20, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Shaded areas = 95% confidence intervals. Curves that drop faster → higher attrition risk.")

    # Median survival stats
    st.divider()
    c1, c2, c3 = st.columns(3)
    for col, (tier, data) in zip([c1, c2, c3], km_data.items()):
        col.metric(
            f"{tier}",
            f"{data['median_survival_days'] / 365.25:.1f} yrs median tenure",
            f"n = {data['n']:,}"
        )

st.divider()

# ── Cohort Retention Table ─────────────────────────────────────────────────────
st.subheader("Cohort Retention Table")
st.caption("Percentage still employed at each milestone, by college tier and joining cohort")

cohort_table = compute_retention_cohort_table(employees)
if cohort_table.empty:
    st.warning("Insufficient cohort sizes (minimum 10 per cohort).")
else:
    display = cohort_table.copy()
    for col in ["survived_6m", "survived_12m", "survived_24m", "survived_36m"]:
        display[col] = display[col].map("{:.0%}".format)
    display["median_tenure_days"] = display["median_tenure_days"].map("{:.0f} days".format)
    display = display.rename(columns={
        "college_tier": "College Tier",
        "join_cohort": "Join Cohort",
        "headcount": "Headcount",
        "events": "Attritions",
        "survived_6m": "6 Months",
        "survived_12m": "12 Months",
        "survived_24m": "24 Months",
        "survived_36m": "36 Months",
        "median_tenure_days": "Median Tenure",
    })
    st.dataframe(display, use_container_width=True, height=400)
