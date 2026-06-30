# ADR-004: Streamlit for the Analytics Dashboard

**Status:** Accepted  
**Date:** 2026-06-24  
**Deciders:** People Analytics Team  

---

## Context

The CHRO and HR Business Partners need an interactive dashboard that non-technical users can navigate without training. It must support multi-page navigation, Plotly charts, data tables, and filters — and be deployable in 1 week.

## Decision

We use **Streamlit** for the analytics dashboard.

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| **Power BI** | Requires Microsoft licensing, no code-first development, harder to version-control |
| **Tableau** | Licensing cost, no Python integration, harder CI/CD |
| **Dash (Plotly)** | More code for the same result; Streamlit handles multi-page natively since v1.28 |
| **Next.js + React** | 3–5x more development time; overkill for an analytics internship |
| **Metabase** | No ML model integration; limited to SQL queries |

## Consequences

**Positive:**
- Multi-page app with sidebar navigation out of the box (`pages/` directory)
- `st.cache_data` caches expensive computations (analytics, ML predictions)
- Plotly charts render interactively natively
- Free deployment on Streamlit Community Cloud or Render
- Python-first: analytics code runs directly (no API call needed for local dev)

**Negative:**
- Not suitable for high-concurrency production (>50 simultaneous users)
- Mitigation: FastAPI backend handles aggregation; dashboard is read-only and cached
- Custom styling limited (CSS injection required for dark mode)
- Mitigation: Global CSS injected via `st.markdown(..., unsafe_allow_html=True)`

## Privacy Enforcement

The dashboard enforces k-anonymity at the display layer:
- All analytics functions filter groups < k before returning data
- Dashboard pages never display individual employee records
- Row-level data is only accessible to `admin` role via API (not dashboard)
