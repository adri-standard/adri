"""Tests for severity-aware scoring mathematical correctness.

Verifies that the severity-based scoring calculations are mathematically correct
across all dimensions and scenarios.
"""

import pandas as pd
import pytest

from src.adri.validator.dimensions.validity import ValidityAssessor
from src.adri.validator.dimensions.completeness import CompletenessAssessor
from src.adri.validator.dimensions.consistency import ConsistencyAssessor
from src.adri.core.validation_rule import ValidationRule
from src.adri.core.severity import Severity


class TestSeverityScoringMath:
    """Test mathematical correctness of severity-aware scoring."""

    def test_all_critical_pass_gives_perfect_score(self):
        """Test that all CRITICAL rules passing gives 20/20."""
        assessor = ValidityAssessor()

        # All values valid
        data = pd.DataFrame({
            "field": ["value1", "value2", "value3"]
        })

        requirements = {
            "field_requirements": {
                "field": {
                    "type": "string",
                    "validation_rules": [
                        ValidationRule(
                            name="Type check",
                            dimension="validity",
                            severity=Severity.CRITICAL,
                            rule_type="type",
                            rule_expression="IS_STRING"
                        )
                    ]
                }
            }
        }

        score = assessor.assess(data, requirements)
        assert score == 20.0, f"All CRITICAL pass should give 20/20, got {score}"

    def test_all_critical_fail_gives_zero_score(self):
        """Test that all CRITICAL rules failing gives 0/20."""
        assessor = ValidityAssessor()

        # All values invalid (not in allowed_values)
        data = pd.DataFrame({
            "field": ["invalid1", "invalid2", "invalid3"]
        })

        requirements = {
            "field_requirements": {
                "field": {
                    "type": "string",
                    "allowed_values": ["valid1", "valid2"],
                    "validation_rules": [
                        ValidationRule(
                            name="Allowed values",
                            dimension="validity",
                            severity=Severity.CRITICAL,
                            rule_type="allowed_values",
                            rule_expression="VALUE_IN(['valid1', 'valid2'])"
                        )
                    ]
                }
            }
        }

        score = assessor.assess(data, requirements)
        assert score == 0.0, f"All CRITICAL fail should give 0/20, got {score}"

    def test_half_critical_fail_gives_half_score(self):
        """Test that 50% CRITICAL failures gives 10/20."""
        assessor = CompletenessAssessor()

        # Half missing, half present
        data = pd.DataFrame({
            "field": [None, None, "value", "value"]
        })

        requirements = {
            "field_requirements": {
                "field": {
                    "validation_rules": [
                        ValidationRule(
                            name="Required",
                            dimension="completeness",
                            severity=Severity.CRITICAL,
                            rule_type="not_null",
                            rule_expression="IS_NOT_NULL"
                        )
                    ]
                }
            }
        }

        score = assessor.assess(data, requirements)
        assert abs(score - 10.0) < 0.1, f"50% CRITICAL fail should give ~10/20, got {score}"

    def test_quarter_critical_fail_gives_three_quarters_score(self):
        """Test that 25% CRITICAL failures gives 15/20."""
        assessor = CompletenessAssessor()

        # 1 missing, 3 present (25% fail)
        data = pd.DataFrame({
            "field": [None, "value", "value", "value"]
        })

        requirements = {
            "field_requirements": {
                "field": {
                    "validation_rules": [
                        ValidationRule(
                            name="Required",
                            dimension="completeness",
                            severity=Severity.CRITICAL,
                            rule_type="not_null",
                            rule_expression="IS_NOT_NULL"
                        )
                    ]
                }
            }
        }

        score = assessor.assess(data, requirements)
        assert abs(score - 15.0) < 0.1, f"25% CRITICAL fail should give ~15/20, got {score}"

    def test_all_warning_fail_gives_perfect_score(self):
        """Test that WARNING failures don't affect score - always 20/20."""
        assessor = ConsistencyAssessor()

        # All uppercase (fails lowercase WARNING rule)
        data = pd.DataFrame({
            "field": ["UPPER", "CASE", "TEXT"]
        })

        requirements = {
            "field_requirements": {
                "field": {
                    "validation_rules": [
                        ValidationRule(
                            name="Lowercase preference",
                            dimension="consistency",
                            severity=Severity.WARNING,
                            rule_type="format",
                            rule_expression="IS_LOWERCASE"
                        )
                    ]
                }
            }
        }

        score = assessor.assess(data, requirements)
        assert score == 20.0, f"All WARNING fail should still give 20/20, got {score}"

    def test_mixed_severity_only_critical_affects_score(self):
        """Test that in mixed scenario, only CRITICAL failures matter."""
        assessor = ValidityAssessor()

        # Data: all lowercase (passes WARNING), all valid (passes CRITICAL)
        data = pd.DataFrame({
            "field": ["paid", "pending", "paid"]
        })

        requirements = {
            "field_requirements": {
                "field": {
                    "type": "string",
                    "allowed_values": ["paid", "pending"],
                    "validation_rules": [
                        ValidationRule(
                            name="Must be valid",
                            dimension="validity",
                            severity=Severity.CRITICAL,
                            rule_type="allowed_values",
                            rule_expression="VALUE_IN(['paid', 'pending'])"
                        ),
                        ValidationRule(
                            name="Lowercase preference",
                            dimension="validity",
                            severity=Severity.WARNING,
                            rule_type="format",
                            rule_expression="IS_LOWERCASE"
                        )
                    ]
                }
            }
        }

        score = assessor.assess(data, requirements)
        assert score == 20.0, f"CRITICAL pass + WARNING fail should give 20/20, got {score}"

    def test_formula_score_equals_passed_critical_over_total_critical_times_20(self):
        """Test scoring formula: score = (passed_critical / total_critical) * 20."""
        assessor = CompletenessAssessor()

        # 7 present, 3 missing (70% pass rate)
        data = pd.DataFrame({
            "field": ["v", "v", "v", "v", "v", "v", "v", None, None, None]
        })

        requirements = {
            "field_requirements": {
                "field": {
                    "validation_rules": [
                        ValidationRule(
                            name="Required",
                            dimension="completeness",
                            severity=Severity.CRITICAL,
                            rule_type="not_null",
                            rule_expression="IS_NOT_NULL"
                        )
                    ]
                }
            }
        }

        score = assessor.assess(data, requirements)
        expected = (7 / 10) * 20  # 14.0
        assert abs(score - expected) < 0.1, f"Expected {expected}, got {score}"

    def test_no_critical_rules_gives_perfect_score(self):
        """Test that having no CRITICAL rules results in perfect score."""
        assessor = ValidityAssessor()

        # Data doesn't matter - no CRITICAL rules
        data = pd.DataFrame({
            "field": ["anything", "goes", "here"]
        })

        requirements = {
            "field_requirements": {
                "field": {
                    "validation_rules": []  # No rules
                }
            }
        }

        score = assessor.assess(data, requirements)
        assert score == 20.0, f"No CRITICAL rules should give 20/20, got {score}"

    def test_multiple_fields_aggregate_correctly(self):
        """Test that multiple fields with different pass rates aggregate correctly."""
        assessor = CompletenessAssessor()

        # field1: 2/2 pass (100%)
        # field2: 1/2 pass (50%)
        # Overall: 3/4 pass (75%)
        data = pd.DataFrame({
            "field1": ["v1", "v2"],
            "field2": [None, "v2"]
        })

        requirements = {
            "field_requirements": {
                "field1": {
                    "validation_rules": [
                        ValidationRule(
                            name="Field1 required",
                            dimension="completeness",
                            severity=Severity.CRITICAL,
                            rule_type="not_null",
                            rule_expression="IS_NOT_NULL"
                        )
                    ]
                },
                "field2": {
                    "validation_rules": [
                        ValidationRule(
                            name="Field2 required",
                            dimension="completeness",
                            severity=Severity.CRITICAL,
                            rule_type="not_null",
                            rule_expression="IS_NOT_NULL"
                        )
                    ]
                }
            }
        }

        score = assessor.assess(data, requirements)
        expected = (3 / 4) * 20  # 15.0
        assert abs(score - expected) < 0.1, f"Expected {expected}, got {score}"


class TestSeverityIsolation:
    """Test that severity levels are properly isolated."""

    def test_critical_and_warning_rules_independent(self):
        """Test that CRITICAL and WARNING rules don't interfere."""
        assessor = ValidityAssessor()

        # Passes CRITICAL, fails WARNING
        data = pd.DataFrame({
            "field": ["VALID1", "VALID2"]  # Uppercase fails WARNING lowercase
        })

        requirements = {
            "field_requirements": {
                "field": {
                    "type": "string",
                    "allowed_values": ["VALID1", "VALID2"],
                    "validation_rules": [
                        ValidationRule(
                            name="Must be valid",
                            dimension="validity",
                            severity=Severity.CRITICAL,
                            rule_type="allowed_values",
                            rule_expression="VALUE_IN"
                        ),
                        ValidationRule(
                            name="Lowercase pref",
                            dimension="validity",
                            severity=Severity.WARNING,
                            rule_type="format",
                            rule_expression="IS_LOWERCASE"
                        )
                    ]
                }
            }
        }

        score = assessor.assess(data, requirements)
        assert score == 20.0, "CRITICAL pass should give 20/20 regardless of WARNING"

    def test_info_rules_dont_affect_score(self):
        """Test that INFO severity never affects score."""
        assessor = ValidityAssessor()

        # Data doesn't matter for INFO rules
        data = pd.DataFrame({
            "field": ["test1", "test2", "test3"]
        })

        requirements = {
            "field_requirements": {
                "field": {
                    "validation_rules": [
                        ValidationRule(
                            name="Info only",
                            dimension="validity",
                            severity=Severity.INFO,
                            rule_type="custom",
                            rule_expression="ALWAYS_FAIL"
                        )
                    ]
                }
            }
        }

        score = assessor.assess(data, requirements)
        assert score == 20.0, "INFO severity should never affect score"
