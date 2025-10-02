import math
from datetime import datetime

import pandas as pd

from src.adri.analysis.rule_inference import (
    InferenceConfig,
    infer_allowed_values,
    infer_numeric_range,
    infer_length_bounds,
    infer_regex_pattern,
    detect_primary_key,
    infer_date_bounds,
)


def test_infer_allowed_values_emits_when_under_cap_and_coverage_met():
    # 20 rows, 19 non-null (95% coverage), 2 unique -> should emit
    series = pd.Series(["A"] * 10 + ["B"] * 9 + [None])
    vals = infer_allowed_values(series, max_unique=30, min_coverage=0.95)
    assert vals == ["A", "B"]


def test_infer_allowed_values_skips_when_low_coverage():
    # 50% non-null only -> below threshold
    series = pd.Series(["A"] * 5 + [None] * 5)
    vals = infer_allowed_values(series, max_unique=30, min_coverage=0.95)
    assert vals is None


def test_infer_numeric_range_with_margin():
    series = pd.Series([10, 20, 30])
    min_v, max_v = infer_numeric_range(series, margin_pct=0.10)  # +/-10% of span (20) => 2
    assert math.isclose(min_v, 8.0)
    assert math.isclose(max_v, 32.0)


def test_infer_numeric_range_identical_values_widens():
    series = pd.Series([100, 100, 100])
    min_v, max_v = infer_numeric_range(series, margin_pct=0.10)
    # With identical values, widen by 10% of abs(val) => 10
    assert math.isclose(min_v, 90.0)
    assert math.isclose(max_v, 110.0)


def test_infer_length_bounds_with_widen():
    series = pd.Series(["aa", "bbbb"])
    min_len, max_len = infer_length_bounds(series, widen=0.10)  # 10% widen
    # min 2 -> floor(2*0.9)=1; max 4 -> int(4*1.1)=4 (int truncation)
    assert min_len == 1
    assert max_len == 4


def test_infer_length_bounds_no_widen():
    series = pd.Series(["x", "hello", "world"])
    min_len, max_len = infer_length_bounds(series, widen=None)
    assert min_len == 1
    assert max_len == 5


def test_infer_regex_pattern_100_percent_coverage():
    series = pd.Series(["user@example.com", "a@b.co", "x@y.z"])
    pat = infer_regex_pattern(series)
    assert pat == r"^[^@]+@[^@]+\.[^@]+$"


def test_infer_regex_pattern_partial_coverage_skips():
    series = pd.Series(["user@example.com", "not an email"])
    pat = infer_regex_pattern(series)
    assert pat is None


def test_detect_primary_key_single_unique():
    df = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})
    pk = detect_primary_key(df, max_combo=2)
    assert pk == ["id"]


def test_detect_primary_key_composite_when_no_single_unique():
    df = pd.DataFrame(
        {
            "dept": ["A", "A", "B", "B"],
            "emp": [1, 2, 1, 2],
            "val": [10, 20, 30, 40],
        }
    )
    # No single unique, but (dept, emp) is unique
    pk = detect_primary_key(df, max_combo=2)
    assert set(pk) == {"dept", "emp"}


def test_infer_date_bounds_widened():
    series = pd.Series(["2024-01-10", "2024-01-20"])
    after, before = infer_date_bounds(series, margin_days=3)
    assert after == "2024-01-07"
    assert before == "2024-01-23"
