"""
ADRI Rule Inference Utilities.

Provides robust inference helpers used by the standard generator and tests:
- InferenceConfig: configuration for inference
- infer_allowed_values / infer_allowed_values_tolerant
- infer_numeric_range / infer_numeric_range_robust
- infer_length_bounds
- infer_regex_pattern
- infer_date_bounds
- detect_primary_key
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import combinations
from math import floor
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import pandas as pd


@dataclass
class InferenceConfig:
    # Enums
    enum_min_coverage: float = 0.95
    enum_max_unique: int = 30
    enum_top_k: int = 10
    enum_strategy: str = "coverage"  # or "tolerant"

    # Numeric ranges
    range_strategy: str = "span"  # "span" | "iqr" | "quantile" | "mad"
    range_margin_pct: float = 0.10
    iqr_k: float = 1.5
    quantile_low: float = 0.005
    quantile_high: float = 0.995
    mad_k: float = 3.0

    # Dates
    date_margin_days: int = 3

    # Primary key detection
    max_pk_combo_size: int = 2

    # Regex inference toggle
    regex_inference_enabled: bool = True


# ----------------------------- ENUMS -----------------------------------


def _non_null_series(s: pd.Series) -> pd.Series:
    try:
        return s.dropna()
    except Exception:
        return s


def infer_allowed_values(
    series: pd.Series, max_unique: int = 30, min_coverage: float = 0.95
) -> Optional[List[Any]]:
    """
    Return list of allowed values when:
      - fraction of non-null values covered by the unique set >= min_coverage
      - number of unique values <= max_unique
    Else return None.
    """
    x = _non_null_series(series)
    if len(x) == 0:
        return None
    uniq = x.unique().tolist()
    if len(uniq) <= max_unique:
        coverage = len(x) / len(series) if len(series) else 1.0
        if coverage >= min_coverage:
            # Preserve first-seen order
            seen = set()
            ordered = []
            for v in x.tolist():
                if v not in seen:
                    seen.add(v)
                    ordered.append(v)
            return ordered
    return None


def infer_allowed_values_tolerant(
    series: pd.Series,
    min_coverage: float = 0.95,
    top_k: int = 10,
    max_unique: int = 30,
) -> Optional[List[Any]]:
    """
    Tolerant enum inference: accumulate most frequent values until coverage reaches min_coverage,
    respecting top_k and max_unique limits.
    """
    x = _non_null_series(series)
    if len(x) == 0:
        return None
    vc = x.value_counts(dropna=True)
    total = int(vc.sum())
    acc = 0
    picked: List[Any] = []
    for val, cnt in vc.items():
        if len(picked) >= top_k:
            break
        picked.append(val)
        acc += int(cnt)
        if acc / total >= min_coverage:
            break
    if len(picked) == 0 or len(picked) > max_unique:
        return None
    return picked


# --------------------------- NUMERIC RANGES -----------------------------


def infer_numeric_range(
    series: pd.Series, margin_pct: float = 0.10
) -> Optional[Tuple[float, float]]:
    """
    Span-based numeric range with margin:
      - Compute observed min/max
      - If span > 0: widen both sides by margin_pct * span
      - If span == 0: widen by margin_pct * abs(value) (or 1.0 if value is 0)
    """
    x = pd.to_numeric(_non_null_series(series), errors="coerce").dropna()
    if len(x) == 0:
        return None
    obs_min = float(x.min())
    obs_max = float(x.max())
    span = obs_max - obs_min
    if span == 0:
        base = abs(obs_min) if obs_min != 0.0 else 1.0
        delta = base * margin_pct
        return (obs_min - delta, obs_max + delta)
    delta = span * margin_pct
    return (obs_min - delta, obs_max + delta)


def infer_numeric_range_robust(
    series: pd.Series,
    strategy: str = "iqr",
    iqr_k: float = 1.5,
    quantile_low: float = 0.005,
    quantile_high: float = 0.995,
    mad_k: float = 3.0,
) -> Optional[Tuple[float, float]]:
    """
    Robust numeric range strategies:
      - iqr: [Q1 - k*IQR, Q3 + k*IQR]
      - quantile: [q_low, q_high]
      - mad: [median - k*MAD, median + k*MAD]
    Always outward-clamp the computed bounds to include observed min/max to guarantee training pass.
    """
    x = pd.to_numeric(_non_null_series(series), errors="coerce").dropna()
    if len(x) == 0:
        return None

    obs_min = float(x.min())
    obs_max = float(x.max())

    if strategy == "quantile":
        low = float(x.quantile(quantile_low))
        high = float(x.quantile(quantile_high))
        min_v = min(low, obs_min)
        max_v = max(high, obs_max)
        return (min_v, max_v)

    if strategy == "mad":
        med = float(x.median())
        mad = float((x - med).abs().median())
        if mad == 0.0:
            # Fallback to small widening around the median
            delta = max(abs(med) * 0.05, 1e-6)
            return (min(med - delta, obs_min), max(med + delta, obs_max))
        low = med - mad_k * mad
        high = med + mad_k * mad
        return (min(low, obs_min), max(high, obs_max))

    # default: IQR
    q1 = float(x.quantile(0.25))
    q3 = float(x.quantile(0.75))
    iqr = q3 - q1
    if iqr == 0.0:
        # Fallback to span widening
        return infer_numeric_range(series, margin_pct=0.10)
    low = q1 - iqr_k * iqr
    high = q3 + iqr_k * iqr
    return (min(low, obs_min), max(high, obs_max))


# --------------------------- LENGTH BOUNDS ------------------------------


def infer_length_bounds(
    series: pd.Series, widen: Optional[float] = None
) -> Optional[Tuple[int, int]]:
    """
    Infer min/max length of stringified values. If widen is provided:
      - min_len = floor(min_len * (1 - widen))
      - max_len = int(max_len * (1 + widen))  # truncation as in tests
    """
    try:
        x = _non_null_series(series).astype(str)
    except Exception:
        return None
    if len(x) == 0:
        return None
    lengths = x.str.len()
    min_len = int(lengths.min())
    max_len = int(lengths.max())
    if widen is not None:
        min_len = int(floor(min_len * (1.0 - widen)))
        if min_len < 0:
            min_len = 0
        max_len = int(max_len * (1.0 + widen))
    return (min_len, max_len)


# ----------------------------- REGEX -----------------------------------


def infer_regex_pattern(series: pd.Series) -> Optional[str]:
    """
    Infer safe regex patterns only when coverage is 100% for non-null values.
    Currently supports a conservative email pattern used by tests.
    """
    try:
        non_null = _non_null_series(series).astype(str)
    except Exception:
        return None
    if len(non_null) == 0:
        return None

    import re

    email_pat = r"^[^@]+@[^@]+\.[^@]+$"
    if non_null.apply(lambda v: bool(re.match(email_pat, v))).all():
        return email_pat

    # Future: add token-class patterns for IDs when 100% coverage (e.g., ^[A-Za-z]+-\d{3,}$)
    return None


# ----------------------------- DATES -----------------------------------


def _parse_yyyy_mm_dd(s: str) -> Optional[datetime]:
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except Exception:
        return None


def infer_date_bounds(
    series: pd.Series, margin_days: int = 3
) -> Optional[Tuple[str, str]]:
    """
    Infer inclusive date window (YYYY-MM-DD) widened by margin_days.
    Returns (after_date, before_date).
    """
    x = _non_null_series(series).astype(str)
    if len(x) == 0:
        return None
    dates = x.apply(_parse_yyyy_mm_dd).dropna()
    if len(dates) == 0:
        return None
    dmin = min(dates)
    dmax = max(dates)
    after = (dmin - timedelta(days=margin_days)).date().isoformat()
    before = (dmax + timedelta(days=margin_days)).date().isoformat()
    return (after, before)


# ------------------------- PRIMARY KEY DETECTION ------------------------


def detect_primary_key(df: pd.DataFrame, max_combo: int = 2) -> List[str]:
    """
    Detect a primary key with semantics aligned to ADRI generator tests:
      - Prefer ID-like single-column keys (column name contains id/key/code/number/num/uuid/guid)
        where values are unique and non-null across all rows
      - Otherwise, prefer composite keys (up to max_combo) that are unique and non-null
      - Only as a final fallback, accept a non-id-like single unique column
    Returns list of column names (single or composite). Empty list if none found.
    """

    def _is_id_like(col_name: Any) -> bool:
        try:
            s = str(col_name).lower()
        except Exception:
            return False
        tokens = ["id", "key", "code", "number", "num", "uuid", "guid"]
        return any(tok in s for tok in tokens)

    n = len(df)
    if n == 0:
        return []

    cols = list(df.columns)
    id_like_cols = [c for c in cols if _is_id_like(c)]

    # 1) Prefer single unique among ID-like columns
    for col in id_like_cols:
        try:
            if df[col].notna().all() and df[col].nunique(dropna=True) == n:
                return [col]
        except Exception:
            continue

    # 2) Prefer composite (unique, non-null) - try ID-like combos first if there are enough
    try_composite_sets: List[List[str]] = []
    if len(id_like_cols) >= 2:
        try_composite_sets.extend(
            [
                list(c)
                for r in range(2, max_combo + 1)
                for c in combinations(id_like_cols, r)
            ]
        )
    # then all-column combos
    try_composite_sets.extend(
        [list(c) for r in range(2, max_combo + 1) for c in combinations(cols, r)]
    )

    for combo in try_composite_sets:
        try:
            if df[combo].isnull().any(axis=1).any():
                continue
            if df.duplicated(subset=combo).sum() == 0:
                return combo
        except Exception:
            continue

    # 3) Fallback: any single unique (non ID-like) if nothing else found
    for col in cols:
        if col in id_like_cols:
            continue
        try:
            if df[col].notna().all() and df[col].nunique(dropna=True) == n:
                return [col]
        except Exception:
            continue

    return []
