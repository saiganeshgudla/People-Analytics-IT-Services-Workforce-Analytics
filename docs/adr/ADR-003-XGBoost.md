# ADR-003: XGBoost for Attrition Prediction

**Status:** Accepted  
**Date:** 2026-06-24  
**Deciders:** People Analytics Team  

---

## Context

PeopleLens needs to compute an attrition risk score per active employee. The model must: (a) handle class imbalance (~18% positive rate), (b) be explainable (SHAP), (c) not leak future information (time-based split), and (d) work on a ~10k sample without GPU.

## Decision

We use **XGBoost** (gradient boosting) as the primary model.

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| **Logistic Regression** | Lower AUC on non-linear feature interactions common in HR data |
| **Random Forest** | Similar AUC to XGBoost but slower inference and less SHAP-efficient |
| **LightGBM** | Comparable performance but XGBoost has better SHAP TreeExplainer support |
| **Neural Networks** | Black box without extra effort; overkill for 10k samples |

## Consequences

**Positive:**
- `scale_pos_weight` parameter handles class imbalance natively
- `shap.TreeExplainer` provides exact (not approximate) SHAP values
- Cross-validation AUC typically 0.72–0.78 on HR attrition datasets
- Feature importance interpretable by HR business partners (no stat background needed)
- Serialised to `.pkl` — minimal deployment overhead

**Negative:**
- Requires parameter tuning (n_estimators, max_depth, learning_rate)
- Not a causal model — SHAP shows correlation, not causation
- Mitigation: Always accompany SHAP with the caveat "correlation, not causation" in the UI

## Leakage Prevention

**Critical rule:** All features must be computed from data known at least 1 year before the prediction date.
- Exit date, exit reason: **NEVER** used as features (only as labels)
- Salary at time of exit: **NEVER** used (use salary 1 year prior)
- Performance rating of exit year: **NEVER** used
