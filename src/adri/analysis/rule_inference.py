"""
Generic rule inference utilities for ADRI standard generation.

This module provides dataset-agnostic inference helpers:
- allowed_values (enums)
- numeric ranges
- string length bounds
- regex patterns (only if 100% coverage)
- date bounds
- primary key detection (single or smallest pair)
- simple money field heuristic
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import combinations
from typing import Any

import pandas as pd


# -----------------------------
# Configuration Types
# -----------------------------
@dataclass
class InferenceConfig:
    """Configuration options controlling inference behavior."""

    enum_max_unique: int = 30
    enum_min_coverage: float = 0.95  # fraction of total rows covered by non-null values
    range_margin_pct: float = (
        # widen numeric range by +/- margin% of range (used when range_strategy='span')
        0.10
    )
    date_margin_days: int = 3  # widen date bounds by +/- this many days
    nullable_zero_is_required: bool = True
    max_pk_combo_size: int = 2
    regex_inference_enabled: bool = True
    money_fields_hints: Sequence[str] = tuple(
        ["amount", "total", "price", "cost", "balance"]
    )
    # Dataset-agnostic range strategy (default keeps existing behavior)
    range_strategy: str = "iqr"  # 'span' | 'iqr' | 'quantile' | 'mad'
    quantile_low: float = 0.005
    quantile_high: float = 0.995
    iqr_k: float = 1.5
    mad_k: float = 3.0
    # Enum strategy (default keeps existing behavior)
    enum_strategy: str = "coverage"  # 'coverage' | 'tolerant'
    enum_top_k: int = 10


# -----------------------------
# Enums / Allowed Values
# -----------------------------
def infer_allowed_values(
    series: pd.Series, max_unique: int, min_coverage: float
) -> list[Any] | None:
    """
    Infer an allowed_values set (enumeration) for a series.

    - Only emit when unique_count <= max_unique AND non-null coverage >= min_coverage of total rows
    - The set contains ALL observed unique non-null values (max_unique guards explosion)
    - If values are unhashable (e.g., dict/list), skip enum inference to avoid errors
    """
    total_rows = int(len(series))
    non_null = series.dropna()
    non_null_count = int(len(non_null))
    if total_rows == 0 or non_null_count == 0:
        return None

    # Bail out if any unhashable types present (e.g., dicts) to avoid
    # "unhashable type" errors
    try:
        for v in non_null:
            hash(v)
    except TypeError:
        return None

    try:
        unique_vals = non_null.unique()
    except Exception:
        # Be safe if pandas cannot compute unique reliably
        return None

    unique_count = len(unique_vals)
    coverage = non_null_count / total_rows

    if unique_count <= max_unique and coverage >= min_coverage:
        # Convert numpy types to native Python for YAML-friendliness
        vals = [v.item() if hasattr(v, "item") else v for v in unique_vals]
        # Keep original order of appearance (unique() in pandas preserves order
        # since 0.24)
        return list(vals)
    return None


def infer_allowed_values_tolerant(
    series: pd.Series, min_coverage: float, top_k: int, max_unique: int
) -> list[Any] | None:
    """
    Tolerant enum inference:
    - pick top-K most frequent values whose cumulative coverage >= min_coverage
    - only emit if resulting set size <= max_unique
    - skip if unhashable values present
    """
    total_rows = int(len(series))
    non_null = series.dropna()
    if total_rows == 0 or len(non_null) == 0:
        return None

    # Unhashable guard
    try:
        for v in non_null:
            hash(v)
    except TypeError:
        return None

    vc = non_null.value_counts(dropna=False)
    cumulative = 0
    selected: list[Any] = []
    for val, cnt in vc.items():
        selected.append(val.item() if hasattr(val, "item") else val)
        cumulative += cnt
        if len(selected) >= top_k or (cumulative / total_rows) >= min_coverage:
            break

    if (cumulative / total_rows) >= min_coverage and len(selected) <= max_unique:
        return list(selected)
    return None


# -----------------------------
# Numeric Range
# -----------------------------
def infer_numeric_range(
    series: pd.Series, margin_pct: float
) -> tuple[float, float] | None:
    """
    Infer numeric min/max, widened outward by +/- margin_pct of the observed span.
    """
    non_null = pd.to_numeric(series.dropna(), errors="coerce").dropna()
    if non_null.empty:
        return None

    observed_min = float(non_null.min())
    observed_max = float(non_null.max())
    span = observed_max - observed_min
    # If all values identical, span=0; widen by fixed 1% of abs(val) or 1.0 default
    if span == 0.0:
        fudge = max(abs(observed_min), abs(observed_max), 1.0) * margin_pct
        return (observed_min - fudge, observed_max + fudge)

    return (observed_min - span * margin_pct, observed_max + span * margin_pct)


def infer_numeric_range_robust(
    series: pd.Series,
    strategy: str = "iqr",
    iqr_k: float = 1.5,
    quantile_low: float = 0.005,
    quantile_high: float = 0.995,
    mad_k: float = 3.0,
) -> tuple[float, float] | None:
    """
    Robust range inference options:
    - iqr: [Q1 - iqr_k*IQR, Q3 + iqr_k*IQR]
    - quantile: [quantile_low, quantile_high]
    - mad: [median - mad_k*scaled_mad, median + mad_k*scaled_mad], scaled_mad = 1.4826 * MAD
    Always clamps outward to include observed min/max to guarantee training-pass coverage.
    """
    x = pd.to_numeric(series.dropna(), errors="coerce").dropna()
    if x.empty:
        return None

    obs_min = float(x.min())
    obs_max = float(x.max())

    try:
        if strategy == "iqr":
            q1 = float(x.quantile(0.25))
            q3 = float(x.quantile(0.75))
            iqr = q3 - q1
            lower = q1 - iqr_k * iqr
            upper = q3 + iqr_k * iqr
        elif strategy == "quantile":
            lower = float(x.quantile(quantile_low))
            upper = float(x.quantile(quantile_high))
        elif strategy == "mad":
            med = float(x.median())
            abs_dev = (x - med).abs()
            mad = float(abs_dev.median())
            scaled = 1.4826 * mad
            lower = med - mad_k * scaled
            upper = med + mad_k * scaled
        else:
            return None

        # Ensure we at least cover the observed training range
        lower = min(lower, obs_min)
        upper = max(upper, obs_max)
        # Avoid inverted intervals
        if lower > upper:
            lower, upper = obs_min, obs_max
        return (float(lower), float(upper))
    except Exception:
        return (obs_min, obs_max)


# -----------------------------
# String Length Bounds
# -----------------------------
def infer_length_bounds(
    series: pd.Series, widen: float | None = None
) -> tuple[int, int] | None:
    """
    Infer string length min/max; optionally widen by a fractional amount (e.g., 0.1 -> +-10%).
    """
    non_null = series.dropna().astype(str)
    if non_null.empty:
        return None

    lengths = non_null.str.len()
    min_len = int(lengths.min())
    max_len = int(lengths.max())

    if widen and widen > 0:
        # Widen symmetrically, clamp at 0 for min
        min_len = max(0, int(min_len * (1.0 - widen)))
        # Ensure max_len increases at least by 1 when widening for very short strings
        max_len = int(max_len * (1.0 + widen)) if max_len > 0 else 1

    return (min_len, max_len)


# -----------------------------
# Regex Pattern Inference
# -----------------------------
_CANDIDATE_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("email", re.compile(r"^[^@]+@[^@]+\.[^@]+$")),
    ("phone", re.compile(r"^[\+]?[0-9\s\-\(\)]+$")),
    ("iso_date", re.compile(r"^\d{4}-\d{2}-\d{2}$")),
    # Generic ID-like shape: letters, hyphen, 3+ digits (e.g., INV-001, CUST-12345)
    ("letters_hyphen_digits", re.compile(r"^[A-Za-z]+-\d{3,}$")),
    ("uuid_like", re.compile(r"^[0-9a-fA-F-]{36}$")),
    ("alnum_dash", re.compile(r"^[A-Za-z0-9\-_]+$")),
    ("digits_only", re.compile(r"^\d+$")),
]


def infer_regex_pattern(series: pd.Series) -> str | None:
    """
    Infer a regex pattern only if 100% of non-null values match the same candidate pattern.
    Uses a small, safe set of known patterns to avoid overfitting.
    """
    non_null = series.dropna().astype(str)
    if non_null.empty:
        return None

    candidates = list(_CANDIDATE_PATTERNS)
    for name, pat in candidates:
        if non_null.apply(lambda s: bool(pat.match(s))).all():
            return pat.pattern

    return None


# -----------------------------
# Date Bounds
# -----------------------------
def _try_parse_date(val: Any) -> datetime | None:
    """
    Attempt to parse various common date/datetime formats; return None if parsing fails.
    """
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None

    # Fast-path ISO-like
    try:
        # Handles YYYY-MM-DD and YYYY-MM-DDTHH:MM:SS[.fff][Z]
        return datetime.fromisoformat(s.replace("Z", "+00:00"))  # tolerate Z -> UTC
    except Exception:
        pass

    # Try a few common alternatives
    fmts = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
    ]
    for fmt in fmts:
        parsed_dt = None
        try:
            parsed_dt = datetime.strptime(s, fmt)
        except Exception:
            parsed_dt = None
        if parsed_dt is not None:
            return parsed_dt

    return None


def infer_date_bounds(series: pd.Series, margin_days: int) -> tuple[str, str] | None:
    """
    Infer min/max date bounds (inclusive) widened by +/- margin_days.
    Returns (after_date_iso, before_date_iso) as ISO date strings (YYYY-MM-DD).
    """
    parsed = series.dropna().map(_try_parse_date).dropna()
    if parsed.empty:
        return None

    min_dt = parsed.min()
    max_dt = parsed.max()
    min_dt = (min_dt - timedelta(days=margin_days)).date()
    max_dt = (max_dt + timedelta(days=margin_days)).date()

    return (min_dt.isoformat(), max_dt.isoformat())


# -----------------------------
# Primary Key Detection
# -----------------------------
def detect_primary_key(df: pd.DataFrame, max_combo: int = 2) -> list[str]:  # noqa: C901
    """
    Detect a minimal primary key with strong heuristics:
    - Prefer a single column that is unique/no-nulls AND name looks identifier-like (id/key/code/number/uuid/guid)
    - Otherwise, try combinations up to 'max_combo' size; prefer combos that include identifier-like columns
    - Avoid selecting measure-like columns as PK (amount,total,price,cost,value,val,score,qty,quantity,count,Sum/Avg/etc.)
    - Skip unhashable/object-like columns (e.g., dicts/lists) that cannot be used for uniqueness checks
    - As a last resort, fallback to any remaining single unique column
    """
    n = len(df)
    if n == 0 or df.empty:
        return []

    def _is_id_like(name: str) -> bool:
        lname = (name or "").lower()
        tokens = ["id", "key", "code", "number", "num", "uuid", "guid"]
        return any(tok in lname for tok in tokens)

    def _is_measure_like(name: str) -> bool:
        lname = (name or "").lower()
        tokens = [
            "amount",
            "total",
            "price",
            "cost",
            "value",
            "val",
            "score",
            "qty",
            "quantity",
            "count",
            "sum",
            "avg",
            "mean",
        ]
        return any(tok in lname for tok in tokens)

    def _is_series_hashable(s: pd.Series) -> bool:
        try:
            for v in s.dropna():
                hash(v)
            return True
        except TypeError:
            return False

    # Single-column unique candidates
    unique_cols: list[str] = []
    for col in df.columns:
        s = df[col]
        if not _is_series_hashable(s):
            continue
        ok_unique = False
        try:
            ok_unique = s.notna().all() and s.nunique(dropna=True) == n
        except Exception:
            ok_unique = False
        if ok_unique:
            unique_cols.append(col)

    # Rank single unique columns: id-like first, then non-measure strings, then others
    id_like_uniques = [c for c in unique_cols if _is_id_like(c)]
    non_measure_uniques = [
        c for c in unique_cols if not _is_id_like(c) and not _is_measure_like(c)
    ]

    def avg_len(col_name: str) -> float:
        try:
            return df[col_name].astype(str).str.len().mean()
        except Exception:
            return float("inf")

    if id_like_uniques:
        id_like_uniques.sort(key=lambda c: (avg_len(c), c))
        return [id_like_uniques[0]]

    # Try combinations up to max_combo, prefer those including id-like columns
    cols = list(df.columns)
    best_combo: list[str] | None = None
    best_score = -1  # number of id-like columns in combo

    for k in range(2, max(2, max_combo) + 1):
        for combo in combinations(cols, k):
            subset = list(combo)
            # Skip combos with nulls
            if df[subset].isnull().any(axis=1).any():
                continue
            # All columns in subset must be hashable
            if any(not _is_series_hashable(df[c]) for c in subset):
                continue
            # Must be unique across rows
            dupe_check_failed = False
            is_dup = False
            try:
                is_dup = df.duplicated(subset=subset, keep=False).any()
            except Exception:
                dupe_check_failed = True
            if dupe_check_failed:
                continue
            if is_dup:
                continue

            score = sum(1 for c in subset if _is_id_like(c))
            # Prefer combos with more id-like columns; break ties using shorter
            # combined average length
            if score > best_score:
                best_combo = subset
                best_score = score
            elif score == best_score and best_combo is not None:
                # tie-breaker: prefer shorter average length
                if sum(avg_len(c) for c in subset) < sum(
                    avg_len(c) for c in best_combo
                ):
                    best_combo = subset

        if best_combo:
            return best_combo

    # If no good combo, consider non-measure single unique columns next
    if non_measure_uniques:
        non_measure_uniques.sort(key=lambda c: (avg_len(c), c))
        return [non_measure_uniques[0]]

    # Fallback: any single unique (even measure-like)
    if unique_cols:
        unique_cols.sort(key=lambda c: (avg_len(c), c))
        return [unique_cols[0]]

    return []


# -----------------------------
# Money Field Heuristic
# -----------------------------
def is_money_field(name: str, hints: Iterable[str]) -> bool:
    """Identify money-like fields using a simple name-based heuristic."""
    lname = (name or "").lower()
    for h in hints:
        if h.lower() in lname:
            return True
    return False
