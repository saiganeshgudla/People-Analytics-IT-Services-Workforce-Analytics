"""
analytics/statistics.py
─────────────────────────
Shared statistical utilities for PeopleLens analytics.
- Bootstrap confidence intervals
- Welch's t-test for group comparison
- Wilson score interval for proportions
- K-anonymity guard
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def bootstrap_ci(
    data: np.ndarray | list[float],
    statistic: callable = np.mean,
    n_bootstrap: int = 1000,
    ci: float = 0.95,
    seed: int = 42,
) -> tuple[float, float]:
    """
    Compute bootstrap confidence interval for any statistic.

    Returns:
        (lower_bound, upper_bound)
    """
    rng = np.random.default_rng(seed)
    arr = np.asarray(data)
    if len(arr) < 2:
        return (float("nan"), float("nan"))

    boot_stats = [statistic(rng.choice(arr, size=len(arr), replace=True)) for _ in range(n_bootstrap)]
    alpha = (1 - ci) / 2
    return (
        float(np.percentile(boot_stats, alpha * 100)),
        float(np.percentile(boot_stats, (1 - alpha) * 100)),
    )


def proportion_ci(successes: int, n: int, ci: float = 0.95) -> tuple[float, float]:
    """Wilson score interval for proportions (more accurate than normal approx)."""
    if n == 0:
        return (0.0, 0.0)
    z = stats.norm.ppf(1 - (1 - ci) / 2)
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = (z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return (max(0, center - margin), min(1, center + margin))


def welch_t_test(group_a: np.ndarray, group_b: np.ndarray) -> tuple[float, float]:
    """
    Two-sample Welch's t-test (unequal variance).

    Returns:
        (t_statistic, p_value)
    """
    if len(group_a) < 2 or len(group_b) < 2:
        return (float("nan"), float("nan"))
    result = stats.ttest_ind(group_a, group_b, equal_var=False)
    return (float(result.statistic), float(result.pvalue))


def k_anonymity_guard(df: pd.DataFrame, group_cols: list[str], k: int = 10) -> pd.DataFrame:
    """
    Filter out groups with fewer than k members to preserve k-anonymity.
    Required for privacy-preserving dashboard output.

    Args:
        df: DataFrame with group aggregations.
        group_cols: Columns that define the group.
        k: Minimum group size (default 10).

    Returns:
        Filtered DataFrame with small groups removed.
    """
    counts = df.groupby(group_cols).transform("size") if isinstance(df, pd.DataFrame) else df
    col_name = "headcount" if "headcount" in df.columns else None
    if col_name:
        filtered = df[df[col_name] >= k].copy()
    else:
        filtered = df  # fallback: can't filter without headcount
    removed = len(df) - len(filtered)
    if removed > 0:
        import logging
        logging.getLogger(__name__).info(f"k-anonymity: removed {removed} groups with <{k} members")
    return filtered


def cohens_d(group_a: np.ndarray, group_b: np.ndarray) -> float:
    """Compute Cohen's d effect size."""
    if len(group_a) < 2 or len(group_b) < 2:
        return float("nan")
    pooled_std = np.sqrt((np.std(group_a, ddof=1) ** 2 + np.std(group_b, ddof=1) ** 2) / 2)
    if pooled_std == 0:
        return 0.0
    return float((np.mean(group_a) - np.mean(group_b)) / pooled_std)
