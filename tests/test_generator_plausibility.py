import pandas as pd
from typing import Any, Dict

from src.adri.analysis.standard_generator import StandardGenerator


def test_generator_emits_active_plausibility_rules():
    """Test that the generator creates plausibility rules that are active by default."""
    # Create sample data that would trigger plausibility analysis
    df = pd.DataFrame({
        "id": ["r1", "r2", "r3", "r4", "r5"],
        "numeric_col": [10, 12, 11, 13, 9],  # Normal numeric data
        "category_col": ["A", "A", "B", "A", "A"],  # Some categorical data
        "text_col": ["text1", "text2", "text3", "text4", "text5"],
    })

    generator = StandardGenerator()
    standard = generator.generate_from_dataframe(df, "test_data")

    # Check that plausibility dimension is present and active
    dim_reqs = standard.get("requirements", {}).get("dimension_requirements", {})
    plaus_cfg = dim_reqs.get("plausibility", {})

    assert isinstance(plaus_cfg, dict), "Plausibility dimension should be present"
    assert plaus_cfg.get("weight", 0.0) == 1.0, "Plausibility should have default weight of 1.0"
    assert plaus_cfg.get("minimum_score", 0.0) == 12.0, "Plausibility should have minimum score of 12.0"

    # Check that scoring configuration has active rule weights
    scoring_cfg = plaus_cfg.get("scoring", {})
    rule_weights = scoring_cfg.get("rule_weights", {})

    assert isinstance(rule_weights, dict), "Rule weights should be present"
    assert "statistical_outliers" in rule_weights, "Statistical outliers rule should be present"
    assert "categorical_frequency" in rule_weights, "Categorical frequency rule should be present"
    assert "business_logic" in rule_weights, "Business logic rule should be present"
    assert "cross_field_consistency" in rule_weights, "Cross-field consistency rule should be present"

    # Check that weights are active (> 0)
    assert rule_weights.get("statistical_outliers", 0.0) > 0, "Statistical outliers should have active weight"
    assert rule_weights.get("categorical_frequency", 0.0) > 0, "Categorical frequency should have active weight"
    assert rule_weights.get("business_logic", 0.0) > 0, "Business logic should have active weight"
    assert rule_weights.get("cross_field_consistency", 0.0) > 0, "Cross-field consistency should have active weight"

    # Check expected weight distribution
    assert rule_weights.get("statistical_outliers") == 0.4
    assert rule_weights.get("categorical_frequency") == 0.3
    assert rule_weights.get("business_logic") == 0.2
    assert rule_weights.get("cross_field_consistency") == 0.1


def test_generator_plausibility_different_from_validity():
    """Test that plausibility rules are distinct from validity rules."""
    df = pd.DataFrame({
        "id": ["r1", "r2", "r3"],
        "text_field": ["valid1", "valid2", "valid3"],
        "num_field": [1, 2, 3],
    })

    generator = StandardGenerator()
    standard = generator.generate_from_dataframe(df, "test_data")

    dim_reqs = standard.get("requirements", {}).get("dimension_requirements", {})

    # Get validity and plausibility rule weights
    validity_rules = dim_reqs.get("validity", {}).get("scoring", {}).get("rule_weights", {})
    plausibility_rules = dim_reqs.get("plausibility", {}).get("scoring", {}).get("rule_weights", {})

    # Ensure no overlap in rule names between validity and plausibility
    validity_rule_names = set(validity_rules.keys())
    plausibility_rule_names = set(plausibility_rules.keys())

    overlap = validity_rule_names.intersection(plausibility_rule_names)
    assert len(overlap) == 0, f"Validity and plausibility rules should not overlap: {overlap}"

    # Check validity has its expected rules
    expected_validity_rules = {"type", "allowed_values", "pattern", "length_bounds", "numeric_bounds"}
    assert validity_rule_names.intersection(expected_validity_rules), "Validity should have expected rule types"

    # Check plausibility has its expected rules
    expected_plausibility_rules = {"statistical_outliers", "categorical_frequency", "business_logic", "cross_field_consistency"}
    assert plausibility_rule_names == expected_plausibility_rules, "Plausibility should have exactly the expected rule types"


def test_generator_plausibility_field_overrides_structure():
    """Test that plausibility dimension has proper field_overrides structure."""
    df = pd.DataFrame({
        "id": ["r1", "r2"],
        "field1": ["a", "b"],
    })

    generator = StandardGenerator()
    standard = generator.generate_from_dataframe(df, "test_data")

    dim_reqs = standard.get("requirements", {}).get("dimension_requirements", {})
    plaus_cfg = dim_reqs.get("plausibility", {})
    scoring_cfg = plaus_cfg.get("scoring", {})

    # Should have field_overrides dict (even if empty)
    assert "field_overrides" in scoring_cfg
    assert isinstance(scoring_cfg["field_overrides"], dict)


def test_generator_plausibility_compared_to_other_dimensions():
    """Test that plausibility follows same pattern as other dimensions."""
    df = pd.DataFrame({
        "id": ["r1", "r2", "r3"],
        "date_field": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "text_field": ["a", "b", "c"],
    })

    generator = StandardGenerator()
    standard = generator.generate_from_dataframe(df, "test_data")

    dim_reqs = standard.get("requirements", {}).get("dimension_requirements", {})

    # All dimensions should have same structure
    for dim_name in ["validity", "completeness", "consistency", "freshness", "plausibility"]:
        dim_cfg = dim_reqs.get(dim_name, {})
        assert isinstance(dim_cfg, dict), f"{dim_name} should be a dict"
        assert "weight" in dim_cfg, f"{dim_name} should have weight"
        assert "minimum_score" in dim_cfg, f"{dim_name} should have minimum_score"
        assert "scoring" in dim_cfg, f"{dim_name} should have scoring config"

        scoring = dim_cfg["scoring"]
        assert "rule_weights" in scoring, f"{dim_name} should have rule_weights"
        assert "field_overrides" in scoring, f"{dim_name} should have field_overrides"
        assert isinstance(scoring["rule_weights"], dict), f"{dim_name} rule_weights should be dict"
        assert isinstance(scoring["field_overrides"], dict), f"{dim_name} field_overrides should be dict"


def test_generator_plausibility_with_date_fields():
    """Test plausibility generation when date fields are present (should still be active)."""
    df = pd.DataFrame({
        "id": ["r1", "r2", "r3"],
        "date_field": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "numeric_field": [10, 20, 30],
    })

    generator = StandardGenerator()
    standard = generator.generate_from_dataframe(df, "test_data")

    dim_reqs = standard.get("requirements", {}).get("dimension_requirements", {})
    plaus_cfg = dim_reqs.get("plausibility", {})
    rule_weights = plaus_cfg.get("scoring", {}).get("rule_weights", {})

    # Plausibility should still be active even when freshness is also active
    assert sum(rule_weights.values()) > 0, "Plausibility should remain active alongside freshness"

    # Freshness might also be active due to date field
    fresh_cfg = dim_reqs.get("freshness", {})
    fresh_weights = fresh_cfg.get("scoring", {}).get("rule_weights", {})

    # Both can be active simultaneously without conflict
    assert isinstance(fresh_weights, dict), "Freshness should have rule weights"
    assert isinstance(rule_weights, dict), "Plausibility should have rule weights"
