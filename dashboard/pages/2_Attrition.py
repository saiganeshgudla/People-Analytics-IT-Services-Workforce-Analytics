"""
dashboard/pages/2_Attrition.py
────────────────────────────────
Attrition Analysis — Risk distribution, SHAP feature importance,
attrition by department/location/level, tenure band analysis.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Attrition Analysis | PeopleLens", page_icon="⚠️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
</style>
""", unsafe_allow_html=True)

st.title("⚠️ Attrition Analysis")
st.caption("XGBoost Risk Model · SHAP Explanations · Privacy-Preserving (k≥10)")
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

from analytics.attrition_analysis import (
    compute_attrition_by_dimension,
    compute_tenure_attrition_bands,
    compute_overall_attrition_kpis,
)

kpis = compute_overall_attrition_kpis(employees)

# ── Header Metrics ─────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Overall Attrition", f"{kpis['overall_attrition_rate']:.1%}", delta=f"+{(kpis['overall_attrition_rate'] - 0.16):.1%} vs benchmark")
col2.metric("Year-1 Attrition", f"{kpis['year_1_attrition_rate']:.1%}", delta=None)
col3.metric("Employees Exited", f"{kpis['exited_employees']:,}")
col4.metric("Active Headcount", f"{kpis['active_employees']:,}")

st.divider()

# ── Risk Score Distribution ─────────────────────────────────────────────────────
scores_path = ROOT / "data" / "analytics" / "attrition_scores.csv"
if scores_path.exists():
    st.subheader("🎯 Attrition Risk Distribution")
    scores = pd.read_csv(scores_path)
    col_a, col_b = st.columns([1, 2])
    with col_a:
        tier_counts = scores["risk_tier"].value_counts().reset_index()
        tier_counts.columns = ["Risk Tier", "Count"]
        colors = {"High": "#FF5050", "Medium": "#FFA500", "Low": "#6BCB77"}
        fig = px.pie(tier_counts, names="Risk Tier", values="Count",
                     color="Risk Tier", color_discrete_map=colors, hole=0.5)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#E0E0FF", height=300, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    with col_b:
        fig2 = px.histogram(scores, x="risk_score", nbins=40, color_discrete_sequence=["#7C83FF"])
        fig2.add_vline(x=0.30, line_dash="dash", line_color="#6BCB77", annotation_text="Low/Medium")
        fig2.add_vline(x=0.60, line_dash="dash", line_color="#FF5050", annotation_text="Medium/High")
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#E0E0FF", height=300, margin=dict(t=10, b=10),
            xaxis=dict(gridcolor="#2D3050"), yaxis=dict(gridcolor="#2D3050"),
        )
        st.plotly_chart(fig2, use_container_width=True)
    st.divider()
else:
    st.info("💡 **Risk scores not available.** Train the model: `python ml/train.py && python ml/predict.py`")

# ── Tabs: by Dimension ─────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["By Department", "By Location", "By Level", "Tenure Bands"])

with tab1:
    data = compute_attrition_by_dimension(employees, "department")
    fig = px.bar(data, x="attrition_rate", y="department", orientation="h",
                 color="attrition_rate", color_continuous_scale=["#6BCB77", "#FFA500", "#FF5050"],
                 text=data["attrition_rate"].map("{:.1%}".format))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="#E0E0FF", height=400, coloraxis_showscale=False,
                      xaxis=dict(tickformat=".0%", gridcolor="#2D3050"), margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    data = compute_attrition_by_dimension(employees, "location")
    fig = px.bar(data, x="attrition_rate", y="location", orientation="h",
                 color="attrition_rate", color_continuous_scale=["#6BCB77", "#FFA500", "#FF5050"],
                 text=data["attrition_rate"].map("{:.1%}".format))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="#E0E0FF", height=400, coloraxis_showscale=False,
                      xaxis=dict(tickformat=".0%", gridcolor="#2D3050"), margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    data = compute_attrition_by_dimension(employees, "level")
    fig = px.bar(data, x="level", y="attrition_rate",
                 color="attrition_rate", color_continuous_scale=["#6BCB77", "#FFA500", "#FF5050"],
                 text=data["attrition_rate"].map("{:.1%}".format))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="#E0E0FF", height=350, coloraxis_showscale=False,
                      yaxis=dict(tickformat=".0%", gridcolor="#2D3050"), margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    data = compute_tenure_attrition_bands(employees)
    fig = px.bar(data, x="tenure_band", y="attrition_rate",
                 color="attrition_rate", color_continuous_scale=["#6BCB77", "#FFA500", "#FF5050"],
                 text=data["attrition_rate"].map("{:.1%}".format))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="#E0E0FF", height=350, coloraxis_showscale=False,
                      yaxis=dict(tickformat=".0%", gridcolor="#2D3050"), margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("⚠️ Year-1 (6–12 month) attrition is the highest risk window for NimbusTech.")
