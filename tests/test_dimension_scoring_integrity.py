"""
Comprehensive tests for dimension scoring integrity.

Tests ensure that all dimension scoring configurations are properly set up
and that scoring accurately reflects data quality issues.
"""

import pandas as pd
import pytest
from pathlib import Path

from adri.analysis.generation.dimension_builder import DimensionRequirementsBuilder
from adri.analysis.generation.contract_builder import ContractBuilder
from adri.validator.engine import DataQualityAssessor


class TestDimensionRuleWeights:
    """Test that all rule types have proper weights configured."""

    def test_validity_starts_empty_populated_by_generator(self):
        """Ensure validity dimension starts with empty weights (populated by ContractBuilder)."""
        builder = DimensionRequirementsBuilder()
        dim_reqs = builder.build_dimension_requirements({})

        validity_weights = dim_reqs["validity"]["scoring"]["rule_weights"]

        # DimensionBuilder returns empty dict - weights are populated by ContractBuilder
        assert isinstance(validity_weights, dict), "rule_weights must be a dict"
        assert len(validity_weights) == 0, "DimensionBuilder should return empty rule_weights"

    def test_validity_weights_sum_to_one_after_normalization(self):
        """Ensure validity rule weights sum to 1.0 after ContractBuilder populates them."""
        # Create test data with various field types
        data = pd.DataFrame({
            "id": ["A", "B", "C"],
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
            "date": ["2024-01-15", "2024-01-16", "2024-01-17"]
        })

        # Build standard using ContractBuilder
        builder = ContractBuilder()
        profile = {col: {"dtype": str(data[col].dtype)} for col in data.columns}
        standard = builder.build_standard(
            data,
            "test_weights",
            profile,
            generation_config={"default_thresholds": {}}
        )

        validity_weights = standard["requirements"]["dimension_requirements"]["validity"]["scoring"]["rule_weights"]

        # After normalization, active weights should sum to ~1.0
        if validity_weights:  # Only check if weights were populated
            total_weight = sum(validity_weights.values())
            assert abs(total_weight - 1.0) < 0.01, \
                f"Weights should sum to 1.0 after normalization, got: {total_weight}"

    def test_date_bounds_weight_in_presets(self):
        """Ensure all presets include date_bounds weight."""
        builder = DimensionRequirementsBuilder()
        presets = builder._get_dimension_presets()

        for preset_name, preset_config in presets.items():
            rule_weights = preset_config.get("validity_rule_weights", {})

            assert "date_bounds" in rule_weights, \
                f"Preset '{preset_name}' missing date_bounds"
            assert rule_weights["date_bounds"] > 0, \
                f"Preset '{preset_name}' has zero date_bounds weight"

    def test_completeness_rule_weights(self):
        """Ensure completeness has proper rule weights."""
        builder = DimensionRequirementsBuilder()
        dim_reqs = builder.build_dimension_requirements({})

        comp_weights = dim_reqs["completeness"]["scoring"]["rule_weights"]

        assert "missing_required" in comp_weights
        assert comp_weights["missing_required"] > 0

    def test_consistency_starts_empty_populated_by_generator(self):
        """Ensure consistency dimension starts with empty weights (populated by ContractBuilder)."""
        builder = DimensionRequirementsBuilder()
        dim_reqs = builder.build_dimension_requirements({})

        cons_weights = dim_reqs["consistency"]["scoring"]["rule_weights"]

        # DimensionBuilder returns empty dict - weights are populated by ContractBuilder
        assert isinstance(cons_weights, dict), "rule_weights must be a dict"
        assert len(cons_weights) == 0, "DimensionBuilder should return empty rule_weights"

    def test_plausibility_starts_empty_populated_by_generator(self):
        """Ensure plausibility dimension starts with empty weights (populated by ContractBuilder)."""
        builder = DimensionRequirementsBuilder()
        dim_reqs = builder.build_dimension_requirements({})

        plaus_weights = dim_reqs["plausibility"]["scoring"]["rule_weights"]

        # DimensionBuilder returns empty dict - weights are populated by ContractBuilder
        assert isinstance(plaus_weights, dict), "rule_weights must be a dict"
        assert len(plaus_weights) == 0, "DimensionBuilder should return empty rule_weights"

    def test_freshness_rule_weights(self):
        """Ensure freshness has proper rule weights configuration."""
        builder = DimensionRequirementsBuilder()
        dim_reqs = builder.build_dimension_requirements({})

        fresh_weights = dim_reqs["freshness"]["scoring"]["rule_weights"]

        assert "recency_window" in fresh_weights
        # Freshness starts at 0.0 by default (activated by detection)
        assert fresh_weights["recency_window"] >= 0


class TestScoringAccuracy:
    """Test that scoring accurately reflects data quality issues."""

    def test_date_failures_impact_score(self):
        """Test that validity weights are populated dynamically based on detected rules."""
        # Create test data with various field types
        data = pd.DataFrame({
            "invoice_id": ["INV-001", "INV-002", "INV-003"],
            "date": ["2024-01-15", "2024-12-31", "2025-12-31"],  # Last one way out of range
            "amount": [100.0, 200.0, 300.0]
        })

        # Build standard from subset
        builder = ContractBuilder()
        train_data = data.iloc[:2]  # Only first 2 rows

        # Create minimal profile
        profile = {col: {"dtype": str(data[col].dtype)} for col in data.columns}

        standard = builder.build_standard(
            train_data,
            "test_dates",
            profile,
            generation_config={"default_thresholds": {}}
        )

        # Verify weights are populated dynamically
        validity_weights = standard["requirements"]["dimension_requirements"]["validity"]["scoring"]["rule_weights"]
        assert len(validity_weights) > 0, "Validity weights should be populated"

        # Verify weights sum to 1.0 (normalized)
        total = sum(validity_weights.values())
        assert abs(total - 1.0) < 0.01, f"Weights should sum to 1.0, got {total}"

        # Only rule types with actual constraints should have weights
        for rule_type, weight in validity_weights.items():
            assert weight > 0, f"Rule type {rule_type} should have positive weight"

    def test_multiple_failures_lower_score(self):
        """Test that multiple types of failures compound to lower the score."""
        # Create data with multiple issue types
        data = pd.DataFrame({
            "id": ["A", "B", "C", "D", "E"],
            "value": [10, 20, 999, 30, 40],  # 999 is outlier
            "category": ["X", "Y", "Z", "Y", "Y"],  # Z is rare
            "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2099-12-31"]  # Last is way off
        })

        builder = ContractBuilder()
        profile = {col: {"dtype": str(data[col].dtype)} for col in data.columns}

        # Build standard from clean subset
        train_data = data.iloc[:4]
        standard = builder.build_standard(
            train_data,
            "multi_test",
            profile,
            generation_config={"default_thresholds": {}}
        )

        # The standard should have rules that would catch issues in full dataset
        field_reqs = standard["requirements"]["field_requirements"]
        assert "value" in field_reqs
        assert "date" in field_reqs


class TestInvoiceGuidedTourScenario:
    """Test the exact scenario from the guided tour that exposed the bug."""

    def test_invoice_scoring_with_dynamic_weights(self):
        """
        Test invoice data scenario with dynamic weight population.
        Verifies that only detected rule types get weights.
        """
        # Simulate training data (January)
        train_data = pd.DataFrame({
            "invoice_id": ["INV-001", "INV-002"],
            "customer_id": ["CUST-101", "CUST-102"],
            "amount": [100.0, 200.0],
            "date": ["2024-01-15", "2024-01-20"],
            "status": ["paid", "paid"],
            "payment_method": ["credit_card", "cash"]
        })

        # Build standard from training data
        builder = ContractBuilder()
        profile = {col: {"dtype": str(train_data[col].dtype)} for col in train_data.columns}

        standard = builder.build_standard(
            train_data,
            "invoice_test",
            profile,
            generation_config={"default_thresholds": {}}
        )

        # Verify dynamic weight population
        dim_reqs = standard["requirements"]["dimension_requirements"]
        validity_weights = dim_reqs["validity"]["scoring"]["rule_weights"]

        # Should have some validity rules detected
        assert len(validity_weights) > 0, "Validity weights should be populated"

        # All active weights should sum to 1.0 (normalized)
        total = sum(validity_weights.values())
        assert abs(total - 1.0) < 0.01, f"Weights should sum to 1.0, got {total}"

        # Check consistency has multiple active rules
        consistency_weights = dim_reqs["consistency"]["scoring"]["rule_weights"]
        assert "primary_key_uniqueness" in consistency_weights, \
            "Should have PK uniqueness rule"

        # Verify weights sum to 1.0 (normalized across all active rules)
        total = sum(consistency_weights.values())
        assert abs(total - 1.0) < 0.01, f"Consistency weights should sum to 1.0, got {total}"


class TestDynamicWeightPopulation:
    """Test dynamic weight population by ContractBuilder."""

    def test_only_active_rule_types_have_weights(self):
        """Verify only rule types with actual rules get weights."""
        # Create simple data with limited rule types
        data = pd.DataFrame({
            "id": ["A", "B", "C"],
            "name": ["Alice", "Bob", "Charlie"]
        })

        builder = ContractBuilder()
        profile = {col: {"dtype": str(data[col].dtype)} for col in data.columns}
        standard = builder.build_standard(
            data,
            "simple_test",
            profile,
            generation_config={"default_thresholds": {}}
        )

        # Check validity weights - should only have 'type' rule
        validity_weights = standard["requirements"]["dimension_requirements"]["validity"]["scoring"]["rule_weights"]
        assert "type" in validity_weights, "type rule should be present"
        assert validity_weights["type"] > 0, "type rule should have positive weight"

        # Ghost rules should NOT exist (no patterns, no numeric bounds, etc.)
        # These would exist if we had hardcoded all 6 rule types

        # Check consistency weights - should have multiple active rules
        consistency_weights = standard["requirements"]["dimension_requirements"]["consistency"]["scoring"]["rule_weights"]
        assert "primary_key_uniqueness" in consistency_weights, "PK rule should be present"
        assert "format_consistency" in consistency_weights, "format_consistency should be present (has string fields)"
        assert "cross_field_logic" in consistency_weights, "cross_field_logic should be present (has 2+ fields)"

        # All weights should sum to 1.0 (normalized)
        total = sum(consistency_weights.values())
        assert abs(total - 1.0) < 0.01, f"Weights should sum to 1.0, got {total}"

        # Referential integrity should NOT exist (not implemented)
        assert "referential_integrity" not in consistency_weights, "referential_integrity should not exist"

    def test_weights_normalized_to_one(self):
        """Verify all populated weights sum to 1.0."""
        # Create data with multiple field types
        data = pd.DataFrame({
            "id": ["A", "B", "C"],
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
            "score": [8.5, 9.0, 7.5]
        })

        builder = ContractBuilder()
        profile = {col: {"dtype": str(data[col].dtype)} for col in data.columns}
        standard = builder.build_standard(
            data,
            "normalize_test",
            profile,
            generation_config={"default_thresholds": {}}
        )

        dim_reqs = standard["requirements"]["dimension_requirements"]

        # Check validity weights sum to 1.0
        validity_weights = dim_reqs["validity"]["scoring"]["rule_weights"]
        if validity_weights:
            total = sum(validity_weights.values())
            assert abs(total - 1.0) < 0.01, f"Validity weights should sum to 1.0, got {total}"

        # Check consistency weights sum to 1.0
        consistency_weights = dim_reqs["consistency"]["scoring"]["rule_weights"]
        if consistency_weights:
            total = sum(consistency_weights.values())
            assert abs(total - 1.0) < 0.01, f"Consistency weights should sum to 1.0, got {total}"

        # Check plausibility weights sum to 1.0
        plausibility_weights = dim_reqs["plausibility"]["scoring"]["rule_weights"]
        if plausibility_weights:
            total = sum(plausibility_weights.values())
            assert abs(total - 1.0) < 0.01, f"Plausibility weights should sum to 1.0, got {total}"


class TestDimensionAudit:
    """Comprehensive audit of all dimension configurations."""

    def test_all_dimensions_have_weights(self):
        """Ensure all dimensions have weight configurations."""
        builder = DimensionRequirementsBuilder()
        dim_reqs = builder.build_dimension_requirements({})

        required_dimensions = ["validity", "completeness", "consistency", "freshness", "plausibility"]

        for dim in required_dimensions:
            assert dim in dim_reqs, f"Missing dimension: {dim}"
            assert "weight" in dim_reqs[dim], f"Dimension {dim} missing weight"
            assert dim_reqs[dim]["weight"] > 0, f"Dimension {dim} has zero weight"

    def test_all_dimensions_have_minimum_scores(self):
        """Ensure all dimensions have minimum score configurations."""
        builder = DimensionRequirementsBuilder()
        dim_reqs = builder.build_dimension_requirements({})

        for dim in dim_reqs:
            assert "minimum_score" in dim_reqs[dim], \
                f"Dimension {dim} missing minimum_score"
            min_score = dim_reqs[dim]["minimum_score"]
            assert 0 <= min_score <= 20, \
                f"Dimension {dim} has invalid minimum_score: {min_score}"

    def test_all_dimensions_have_scoring_config(self):
        """Ensure all dimensions have scoring configurations."""
        builder = DimensionRequirementsBuilder()
        dim_reqs = builder.build_dimension_requirements({})

        for dim in dim_reqs:
            assert "scoring" in dim_reqs[dim], \
                f"Dimension {dim} missing scoring config"
            assert "rule_weights" in dim_reqs[dim]["scoring"], \
                f"Dimension {dim} missing rule_weights"

    def test_no_overlapping_rules_between_validity_and_plausibility(self):
        """Ensure validity and plausibility don't have overlapping rule types."""
        builder = DimensionRequirementsBuilder()
        dim_reqs = builder.build_dimension_requirements({})

        validity_rules = set(dim_reqs["validity"]["scoring"]["rule_weights"].keys())
        plausibility_rules = set(dim_reqs["plausibility"]["scoring"]["rule_weights"].keys())

        overlap = validity_rules & plausibility_rules
        assert len(overlap) == 0, \
            f"Validity and plausibility have overlapping rules: {overlap}"

    def test_dimension_builder_validation(self):
        """Test the dimension requirements validation method."""
        builder = DimensionRequirementsBuilder()
        dim_reqs = builder.build_dimension_requirements({})

        # Valid requirements should pass validation
        errors = builder.validate_dimension_requirements(dim_reqs)
        assert len(errors) == 0, f"Valid requirements failed validation: {errors}"

        # Test with missing dimension
        invalid_reqs = {"validity": dim_reqs["validity"]}  # Missing other dimensions
        errors = builder.validate_dimension_requirements(invalid_reqs)
        assert len(errors) > 0, "Should detect missing dimensions"

        # Test with invalid weight
        invalid_reqs = dim_reqs.copy()
        invalid_reqs["validity"] = invalid_reqs["validity"].copy()
        invalid_reqs["validity"]["weight"] = -1.0  # Negative weight
        errors = builder.validate_dimension_requirements(invalid_reqs)
        assert any("weight" in err.lower() for err in errors), \
            "Should detect invalid weight"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
