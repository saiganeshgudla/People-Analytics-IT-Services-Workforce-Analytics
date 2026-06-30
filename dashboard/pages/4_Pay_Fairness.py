"""
dashboard/pages/4_Pay_Fairness.py
───────────────────────────────────
Pay Fairness Audit — Gender pay ratio by role/level/location.
Bootstrap CIs, statistical flags, comp-ratio heatmaps.
Privacy: Only groups with n >= 10 per gender shown.
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Pay Fairness | PeopleLens", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
</style>
""", unsafe_allow_html=True)

st.title("⚖️ Pay Fairness Audit")
st.caption("Gender Pay Ratio · Bootstrap CI · Welch t-test · Disparity Threshold ±5%")
st.divider()


@st.cache_data(ttl=300)
def load_data():
    emp_path = ROOT / "data" / "synthetic" / "employees.csv"
    sal_path = ROOT / "data" / "synthetic" / "salary_history.csv"
    if not emp_path.exists() or not sal_path.exists():
        return None, None
    employees = pd.read_csv(emp_path)
    salary = pd.read_csv(sal_path, parse_dates=["effective_date"])
    return employees, salary


employees, salary = load_data()
if employees is None:
    st.error("⚠️ No data. Run `python data_generator/generate_dataset.py`")
    st.stop()

from analytics.pay_fairness import compute_comp_ratios, compute_pay_fairness_by_gender, compute_overall_pay_fairness

comp = compute_comp_ratios(salary, employees)

# ── Overall KPIs ──────────────────────────────────────────────────────────────
overall = compute_overall_pay_fairness(comp)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Overall Gender Pay Ratio", f"{overall['overall_gender_pay_ratio']:.3f}",
          help="Female median / Male median. 1.0 = perfect parity.")
c2.metric("Pay Gap", f"{overall['pay_gap_pct']:.1f}%",
          delta=f"{'Above' if overall['pay_gap_pct'] < 0 else 'Below'} parity",
          delta_color="inverse")
c3.metric("Male Median Salary", f"₹{overall['male_median_salary']/100_000:.1f}L")
c4.metric("Female Median Salary", f"₹{overall['female_median_salary']/100_000:.1f}L")
st.divider()

# ── Analysis Tabs ──────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["By Level", "By Department", "By Location"])

for tab, group_col in zip([tab1, tab2, tab3], ["level", "department", "location"]):
    with tab:
        fairness = compute_pay_fairness_by_gender(comp, group_cols=[group_col])
        if fairness.empty:
            st.warning(f"Insufficient data by {group_col} (groups < 10 per gender excluded).")
            continue

        flagged = fairness[fairness["disparity_flag"]]
        if not flagged.empty:
            st.error(f"🚨 **{len(flagged)} bucket(s) flagged** for gender pay disparity >5%")

        # Bar chart
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=fairness[group_col],
            y=fairness["male_median_salary"] / 100_000,
            name="Male Median (₹L)",
            marker_color="#7C83FF",
        ))
        fig.add_trace(go.Bar(
            x=fairness[group_col],
            y=fairness["female_median_salary"] / 100_000,
            name="Female Median (₹L)",
            marker_color="#FF6B9D",
        ))
        fig.add_hline(y=overall["male_median_salary"] / 100_000, line_dash="dot",
                      line_color="#888", annotation_text="Male Overall Median")
        fig.update_layout(
            barmode="group",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#E0E0FF",
            height=380,
            yaxis=dict(title="Salary (₹ Lakhs)", gridcolor="#2D3050"),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            margin=dict(t=20),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Pay ratio chart
        fig2 = px.bar(
            fairness, x=group_col, y="gender_pay_ratio",
            color="disparity_flag",
            color_discrete_map={True: "#FF5050", False: "#6BCB77"},
            error_y=fairness["ci_upper"] - fairness["gender_pay_ratio"],
            error_y_minus=fairness["gender_pay_ratio"] - fairness["ci_lower"],
            text=fairness["gender_pay_ratio"].map("{:.3f}".format),
        )
        fig2.add_hline(y=1.0, line_dash="dash", line_color="white", annotation_text="Parity (1.0)")
        fig2.add_hrect(y0=0.95, y1=1.05, fillcolor="rgba(108,203,119,0.1)",
                       line_width=0, annotation_text="±5% band")
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#E0E0FF",
            height=320,
            yaxis=dict(gridcolor="#2D3050", title="Female/Male Pay Ratio"),
            legend_title="Flagged",
            margin=dict(t=20),
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("Error bars = 95% bootstrap CI. Red = outside ±5% parity band.")
