import pandas as pd
import pytest
from typing import Any, Dict

from src.adri.validator.engine import ValidationEngine


def _make_plausibility_standard(rule_weights: Dict[str, float], extra: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create a standard with plausibility rules for testing."""
    std: Dict[str, Any] = {
        "contracts": {"id": "test_standard", "name": "Test Standard", "version": "1.0.0", "authority": "ADRI Framework"},
        "requirements": {
            "overall_minimum": 75.0,
            "field_requirements": {
                "id": {"type": "string", "nullable": False},
                "numeric_field": {"type": "float", "nullable": True},
                "category_field": {"type": "string", "nullable": True},
            },
            "dimension_requirements": {
                "validity": {"weight": 1.0, "minimum_score": 15.0, "scoring": {"rule_weights": {"type": 1.0}}},
                "completeness": {"weight": 1.0, "minimum_score": 15.0, "scoring": {"rule_weights": {"missing_required": 1.0}}},
                "consistency": {"weight": 1.0, "minimum_score": 12.0, "scoring": {"rule_weights": {"primary_key_uniqueness": 1.0}}},
                "freshness": {"weight": 1.0, "minimum_score": 15.0, "scoring": {"rule_weights": {"recency_window": 0.0}}},
                "plausibility": {"weight": 1.0, "minimum_score": 12.0, "scoring": {"rule_weights": rule_weights}},
            },
        },
        "record_identification": {"primary_key_fields": ["id"]},
        "metadata": {}
    }
    if extra:
        for k, v in extra.items():
            if k == "metadata":
                std.setdefault("metadata", {}).update(v or {})
            elif k == "requirements":
                std["requirements"].update(v or {})
            else:
                std[k] = v
    return std


def test_plausibility_statistical_outliers():
    """Test statistical outliers detection using IQR method."""
    # Create data with clear outliers
    df = pd.DataFrame({
        "id": ["r1", "r2", "r3", "r4", "r5", "r6"],
        "numeric_field": [10, 12, 11, 13, 9, 100],  # 100 is an outlier
        "category_field": ["A"] * 6,
    })

    std = _make_plausibility_standard({"statistical_outliers": 1.0})
    engine = ValidationEngine()
    result = engine.assess_with_standard_dict(df, std)

    explain = (result.metadata or {}).get("explain", {})
    plaus = explain.get("plausibility", {})

    assert isinstance(plaus, dict)
    rule_counts = plaus.get("rule_counts", {})

    # Should have statistical_outliers counts
    outlier_counts = rule_counts.get("statistical_outliers", {})
    assert outlier_counts.get("total", 0) > 0  # Should have evaluated numeric values
    assert outlier_counts.get("passed", 0) < outlier_counts.get("total", 0)  # Should have some outliers

    # Check pass rate and score
    assert "pass_rate" in plaus
    assert "score_0_20" in plaus
    assert plaus.get("rule_weights_applied", {}).get("statistical_outliers") == 1.0


def test_plausibility_categorical_frequency():
    """Test categorical frequency detection for rare categories."""
    # Create data with one rare category (appears in <5% of data)
    df = pd.DataFrame({
        "id": [f"r{i}" for i in range(21)],  # 21 rows
        "numeric_field": [10] * 21,
        "category_field": ["Common"] * 20 + ["Rare"],  # "Rare" appears 1/21 times = 4.76% < 5%
    })

    std = _make_plausibility_standard({"categorical_frequency": 1.0})
    engine = ValidationEngine()
    result = engine.assess_with_standard_dict(df, std)

    explain = (result.metadata or {}).get("explain", {})
    plaus = explain.get("plausibility", {})

    assert isinstance(plaus, dict)
    rule_counts = plaus.get("rule_counts", {})

    # Should have categorical_frequency counts
    freq_counts = rule_counts.get("categorical_frequency", {})
    assert freq_counts.get("total", 0) == 42  # All string values evaluated (21 rows * 2 string columns)
    assert freq_counts.get("passed", 0) == 20  # Only 20 "Common" values pass (≥5%); all "id" values fail (unique = <5%)

    # Check pass rate
    pass_rate = plaus.get("pass_rate", 0.0)
    assert abs(pass_rate - (20/42)) < 0.01  # Should be ~47.6%

    assert plaus.get("rule_weights_applied", {}).get("categorical_frequency") == 1.0


def test_plausibility_multiple_active_rules():
    """Test multiple plausibility rules active simultaneously."""
    df = pd.DataFrame({
        "id": ["r1", "r2", "r3", "r4"],
        "numeric_field": [10, 12, 11, 100],  # 100 is outlier
        "category_field": ["A", "A", "A", "B"],  # B is rare (25% but we'll adjust threshold)
    })

    std = _make_plausibility_standard({
        "statistical_outliers": 0.4,
        "categorical_frequency": 0.3,
        "business_logic": 0.2,
        "cross_field_consistency": 0.1,
    })
    engine = ValidationEngine()
    result = engine.assess_with_standard_dict(df, std)

    explain = (result.metadata or {}).get("explain", {})
    plaus = explain.get("plausibility", {})

    assert isinstance(plaus, dict)
    rule_counts = plaus.get("rule_counts", {})

    # All rule types should have counts (even if zero for business_logic/cross_field)
    assert "statistical_outliers" in rule_counts
    assert "categorical_frequency" in rule_counts
    assert "business_logic" in rule_counts
    assert "cross_field_consistency" in rule_counts

    # Should have applied weights for all active rules
    applied_weights = plaus.get("rule_weights_applied", {})
    assert applied_weights.get("statistical_outliers") == 0.4
    assert applied_weights.get("categorical_frequency") == 0.3
    assert applied_weights.get("business_logic") == 0.2
    assert applied_weights.get("cross_field_consistency") == 0.1

    # Score should be weighted combination
    assert "score_0_20" in plaus
    assert plaus.get("score_0_20", 0.0) <= 20.0


def test_plausibility_no_active_rules():
    """Test plausibility when no rules are active (weights = 0)."""
    df = pd.DataFrame({
        "id": ["r1", "r2"],
        "numeric_field": [10, 12],
        "category_field": ["A", "B"],
    })

    std = _make_plausibility_standard({})  # No active rules
    engine = ValidationEngine()
    result = engine.assess_with_standard_dict(df, std)

    explain = (result.metadata or {}).get("explain", {})
    plaus = explain.get("plausibility", {})

    assert isinstance(plaus, dict)
    assert plaus.get("score_0_20") == 20.0  # Perfect baseline score
    assert "no active rules configured" in plaus.get("warnings", [""])[0]

    # All rule counts should be zero
    rule_counts = plaus.get("rule_counts", {})
    for rule_type in ["statistical_outliers", "categorical_frequency", "business_logic", "cross_field_consistency"]:
        counts = rule_counts.get(rule_type, {})
        assert counts.get("passed", 0) == 0
        assert counts.get("total", 0) == 0


def test_plausibility_empty_dataset():
    """Test plausibility with empty dataset."""
    df = pd.DataFrame(columns=["id", "numeric_field", "category_field"])

    std = _make_plausibility_standard({"statistical_outliers": 1.0})
    engine = ValidationEngine()
    result = engine.assess_with_standard_dict(df, std)

    explain = (result.metadata or {}).get("explain", {})
    plaus = explain.get("plausibility", {})

    assert isinstance(plaus, dict)
    # Should handle empty data gracefully
    assert plaus.get("pass_rate", 0.0) == 1.0  # No data = perfect pass rate
    assert plaus.get("score_0_20", 0.0) == 20.0  # Perfect score


def test_plausibility_statistical_outliers_edge_cases():
    """Test statistical outliers with edge cases."""
    # Test with insufficient data (< 4 values needed for IQR)
    df_small = pd.DataFrame({
        "id": ["r1", "r2"],
        "numeric_field": [10, 12],
        "category_field": ["A", "B"],
    })

    std = _make_plausibility_standard({"statistical_outliers": 1.0})
    engine = ValidationEngine()
    result = engine.assess_with_standard_dict(df_small, std)

    explain = (result.metadata or {}).get("explain", {})
    plaus = explain.get("plausibility", {})

    # Should handle insufficient data gracefully
    rule_counts = plaus.get("rule_counts", {})
    outlier_counts = rule_counts.get("statistical_outliers", {})
    assert outlier_counts.get("total", 0) == 0  # No evaluations with < 4 values

    # Test with all identical values (IQR = 0)
    df_identical = pd.DataFrame({
        "id": ["r1", "r2", "r3", "r4", "r5"],
        "numeric_field": [10, 10, 10, 10, 10],  # All same value
        "category_field": ["A"] * 5,
    })

    result2 = engine.assess_with_standard_dict(df_identical, std)
    explain2 = (result2.metadata or {}).get("explain", {})
    plaus2 = explain2.get("plausibility", {})

    # Should handle zero IQR gracefully (no outliers possible)
    rule_counts2 = plaus2.get("rule_counts", {})
    outlier_counts2 = rule_counts2.get("statistical_outliers", {})
    assert outlier_counts2.get("total", 0) == 0  # No evaluations when IQR = 0


def test_plausibility_mixed_data_types():
    """Test plausibility with mixed data types."""
    df = pd.DataFrame({
        "id": ["r1", "r2", "r3"],
        "numeric_field": [10.5, None, 15.2],  # Some nulls
        "category_field": [None, "A", "B"],   # Some nulls
        "non_numeric": ["text1", "text2", "text3"],  # String values
    })

    std = _make_plausibility_standard({
        "statistical_outliers": 0.5,
        "categorical_frequency": 0.5,
    })
    std["requirements"]["field_requirements"]["non_numeric"] = {"type": "string", "nullable": True}

    engine = ValidationEngine()
    result = engine.assess_with_standard_dict(df, std)

    explain = (result.metadata or {}).get("explain", {})
    plaus = explain.get("plausibility", {})

    assert isinstance(plaus, dict)
    # Should handle mixed types and nulls gracefully
    assert "pass_rate" in plaus
    assert "score_0_20" in plaus
