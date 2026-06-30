# MEMORANDUM

**TO:** CHRO, NimbusTech  
**FROM:** People Analytics Partner  
**DATE:** 30 June 2026  
**RE:** FY2024 Workforce Attrition — Critical Findings and Recommended Actions  
**CLASSIFICATION:** Confidential — HR Leadership Only  

---

## Executive Summary

PeopleLens analysis of NimbusTech's 12,000-employee workforce reveals **three compounding attrition crises** that collectively cost the company approximately **₹47 Cr in replacement costs annually**. The problems are structural, measurable, and — critically — fixable within the current HR budget.

---

## Finding 1: We Are Losing 22% of New Joiners in Year 1

**The number:** 22% of employees who joined in 2022–2023 exited within their first 12 months.  
**The cost:** Assuming a ₹5L average hiring + ramp-up cost per replacement, and ~800 year-1 exits annually, this represents **₹40 Cr in avoidable replacement costs per year**.

**The cause is concentrated:** This is not uniform across the company. Year-1 attrition is **41% for Tier-3 college hires** versus **18% for Tier-1 (IIT/NIT) hires**. The onboarding experience, project assignment quality, and manager attention are demonstrably worse for Tier-3 joiners.

**The fix:**
1. Structured 90-day onboarding programme with bi-weekly check-ins (mandatory for all new joiners, not just campus hires)
2. Mentoring pairing: every Tier-3 joiner paired with a L4+ buddy for the first 6 months
3. Targeted intervention: flag new joiners who have not logged >20 learning hours in their first quarter — these employees are 2.3× more likely to leave within Year 1

**Estimated impact:** If we reduce Tier-3 Year-1 attrition by 30% (achievable in 18 months based on industry benchmarks), we save **₹12 Cr annually**.

---

## Finding 2: 8 Managers Explain Disproportionate Attrition

**The number:** Bottom-quartile managers show team attrition rates **18–25 percentage points above their peers at the same level and department**.  
**The cost:** ~₹5 Cr in replacement costs attributable to high-attrition managers annually.

**How we know:** Using rolling 12-month attrition of direct reports (not skip-level), controlling for department and level, 8 managers have team attrition >30% versus a peer average of ~12%. These 8 managers collectively manage 340 employees.

**The fix:**
1. Mandatory manager effectiveness review for managers with team attrition >25% — quarterly 360° feedback, not annual
2. "Attrition dashboard" access for HRBPs assigned to these managers, enabling early intervention
3. Manager development programme targeting the bottom 10% of manager-effect scores

---

## Finding 3: The Gender Pay Gap Persists at L1–L3

**The number:** Female employees at L1–L3 earn, on average, **6.2% less than male peers in the same role, level, and location** (statistically significant at p<0.05, Welch's t-test).  
**The risk:** Pay fairness exposure; potential regulatory attention; talent retention risk for female employees (who have 4% higher attrition than male peers at L1–L3).

**The fix:**
1. Immediate compensation review for all L1–L3 female employees with comp-ratio below 0.93 (i.e., more than 7% below bucket median)
2. Salary band midpoints should be the floor for new offers, not the starting point for negotiation
3. Bi-annual pay equity audit (automated via PeopleLens) with results reported to the CHRO

**Estimated cost to remediate:** ₹2.1 Cr one-time salary correction for the ~180 flagged employees. Cost of NOT remediating: ₹15 Cr in talent pipeline damage and regulatory exposure over 3 years.

---

## Recommended Next Steps (90 Days)

| Action | Owner | Timeline | Expected Impact |
|--------|-------|----------|----------------|
| Launch 90-day onboarding programme | L&D Head + HRBPs | 30 days | -30% Year-1 attrition (Tier-3) |
| Activate manager intervention programme | HR Head | 45 days | -20% attrition in flagged teams |
| Pay equity correction (L1–L3 females) | Comp & Benefits | 60 days | Close 6% gap; reduce female attrition by 4pp |
| Deploy PeopleLens dashboard to all HRBPs | People Analytics | 15 days | 60% reduction in CHRO data requests |

---

## Methodology Note

All analysis uses synthetic data representative of NimbusTech's workforce profile. The attrition model (XGBoost, AUC ~0.75) uses features known at prediction time only — no leakage. Pay fairness analysis uses bootstrap confidence intervals (n=1,000 iterations, 95% CI). Manager-effect analysis uses Wilson score intervals for proportions. All dashboard outputs enforce k-anonymity (k≥10) — no individual employee is identifiable.

---

*Prepared by the People Analytics team using PeopleLens v0.1.0*
