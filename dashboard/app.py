"""
dashboard/app.py
─────────────────
PeopleLens — Streamlit Multi-Page Dashboard

Executive-facing HR analytics platform for NimbusTech.
4 analytical tabs + 1 executive briefing tab.

Run: streamlit run dashboard/app.py
"""

import streamlit as st

st.set_page_config(
    page_title="PeopleLens | NimbusTech Workforce Analytics",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main { background: #0F1117; }
    .stApp { background: linear-gradient(135deg, #0F1117 0%, #1A1D2E 100%); }

    .metric-card {
        background: linear-gradient(135deg, #1E2235 0%, #252840 100%);
        border: 1px solid #2D3050;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: transform 0.2s ease;
    }
    .metric-card:hover { transform: translateY(-2px); }

    .alert-high {
        background: rgba(255, 80, 80, 0.15);
        border-left: 4px solid #FF5050;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
    }
    .alert-medium {
        background: rgba(255, 165, 0, 0.15);
        border-left: 4px solid #FFA500;
        border-radius: 8px;
        padding: 12px 16px;
    }
    .alert-low {
        background: rgba(50, 205, 50, 0.15);
        border-left: 4px solid #32CD32;
        border-radius: 8px;
        padding: 12px 16px;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #13161F 0%, #1A1D2E 100%);
        border-right: 1px solid #2D3050;
    }
    [data-testid="stMetricValue"] { color: #7C83FF; font-weight: 700; }
</style>
""", unsafe_allow_html=True)


# ── Home Page ──────────────────────────────────────────────────────────────────
st.markdown("""
# 🔬 PeopleLens
### NimbusTech Workforce Analytics Platform

---

**PeopleLens** gives NimbusTech's CHRO and HR Business Partners a single source of truth
for workforce intelligence — replacing 60% of spreadsheet time with real-time, privacy-preserving analytics.
""")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="metric-card">
        <h3 style="color:#7C83FF; margin:0">🎯</h3>
        <h4 style="color:#E0E0FF; margin:8px 0 4px">Executive Briefing</h4>
        <p style="color:#8B8FA8; font-size:0.85rem; margin:0">3 KPIs. 3 sentences. What the CHRO needs.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-card">
        <h3 style="color:#FF6B6B; margin:0">⚠️</h3>
        <h4 style="color:#E0E0FF; margin:8px 0 4px">Attrition Analysis</h4>
        <p style="color:#8B8FA8; font-size:0.85rem; margin:0">XGBoost risk scores + SHAP explanations.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-card">
        <h3 style="color:#FFD93D; margin:0">👔</h3>
        <h4 style="color:#E0E0FF; margin:8px 0 4px">Manager Effect</h4>
        <p style="color:#8B8FA8; font-size:0.85rem; margin:0">Rolling 12-month team attrition vs peers.</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="metric-card">
        <h3 style="color:#6BCB77; margin:0">⚖️</h3>
        <h4 style="color:#E0E0FF; margin:8px 0 4px">Pay Fairness</h4>
        <p style="color:#8B8FA8; font-size:0.85rem; margin:0">Gender pay gap audit with bootstrap CIs.</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()
st.info("👈 **Navigate using the sidebar** to explore each analytical module.")

# Data status
import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent
data_exists = (ROOT / "data" / "synthetic" / "employees.csv").exists()
model_exists = (ROOT / "models" / "attrition_model.pkl").exists()

col_a, col_b = st.columns(2)
with col_a:
    if data_exists:
        st.success("✅ **Synthetic data**: Ready")
    else:
        st.warning("⚠️ **Synthetic data**: Not generated yet. Run `python data_generator/generate_dataset.py`")

with col_b:
    if model_exists:
        st.success("✅ **ML Model**: Trained and ready")
    else:
        st.warning("⚠️ **ML Model**: Not trained. Run `python ml/train.py` after generating data")
