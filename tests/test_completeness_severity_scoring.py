"""Tests for completeness dimension severity-aware scoring.

Tests that completeness dimension correctly filters rules by severity.
"""

import pandas as pd
import pytest

from src.adri.validator.dimensions.completeness import CompletenessAssessor
from src.adri.core.validation_rule import ValidationRule
from src.adri.core.severity import Severity


class TestCompletenessSeverityAwareScoring:
    """Test that completeness dimension respects severity levels."""

    def test_completeness_with_critical_rules_failures(self):
        """Test that CRITICAL rule failures reduce completeness score."""
        assessor = CompletenessAssessor()

        # Create test data with missing values
        data = pd.DataFrame({
            "email": [None, None, "test@example.com"]  # 2 out of 3 missing
        })

        # Create field requirements with CRITICAL completeness rules
        requirements = {
            "field_requirements": {
                "email": {
                    "type": "string",
                    "validation_rules": [
                        ValidationRule(
                            name="Email required",
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

        # Score should be reduced - 1/3 pass rate
        assert score < 20.0
        assert abs(score - (1/3 * 20.0)) < 0.1  # Approximately 6.67

    def test_completeness_with_warning_rules_no_penalty(self):
        """Test that WARNING rule failures don't reduce completeness score."""
        assessor = CompletenessAssessor()

        # Create test data with missing values
        data = pd.DataFrame({
            "optional_field": [None, None, "value"]  # 2 out of 3 missing
        })

        # Create field requirements with only WARNING completeness rules
        requirements = {
            "field_requirements": {
                "optional_field": {
                    "type": "string",
                    "validation_rules": [
                        ValidationRule(
                            name="Optional field suggestion",
                            dimension="completeness",
                            severity=Severity.WARNING,
                            rule_type="not_null",
                            rule_expression="IS_NOT_NULL"
                        )
                    ]
                }
            }
        }

        score = assessor.assess(data, requirements)

        # Score should be perfect because WARNING rules don't affect score
        assert score == 20.0

    def test_completeness_with_mixed_severity_rules(self):
        """Test mixed CRITICAL and WARNING rules - only CRITICAL affects score."""
        assessor = CompletenessAssessor()

        # Create test data: all values present
        data = pd.DataFrame({
            "email": ["test1@example.com", "test2@example.com", "test3@example.com"]
        })

        # Create field requirements with mixed severity
        requirements = {
            "field_requirements": {
                "email": {
                    "type": "string",
                    "validation_rules": [
                        ValidationRule(
                            name="Email required",
                            dimension="completeness",
                            severity=Severity.CRITICAL,
                            rule_type="not_null",
                            rule_expression="IS_NOT_NULL"
                        ),
                        ValidationRule(
                            name="Email not empty suggestion",
                            dimension="completeness",
                            severity=Severity.WARNING,
                            rule_type="not_empty",
                            rule_expression="IS_NOT_EMPTY"
                        )
                    ]
                }
            }
        }

        score = assessor.assess(data, requirements)

        # Score should be perfect - CRITICAL rules pass, WARNING ignored
        assert score == 20.0

    def test_completeness_backward_compatibility_old_format(self):
        """Test that old format (nullable flag) still works."""
        assessor = CompletenessAssessor()

        data = pd.DataFrame({
            "required_field": ["value1", "value2", "value3"]
        })

        # Old format with nullable flag
        requirements = {
            "field_requirements": {
                "required_field": {
                    "type": "string",
                    "nullable": False
                }
            }
        }

        score = assessor.assess(data, requirements)

        # Should still work with old format
        assert score == 20.0

    def test_completeness_no_critical_rules_perfect_score(self):
        """Test that having no CRITICAL rules gives perfect score."""
        assessor = CompletenessAssessor()

        data = pd.DataFrame({
            "field": [None, None, None]  # All missing
        })

        # Only WARNING rules, no CRITICAL
        requirements = {
            "field_requirements": {
                "field": {
                    "type": "string",
                    "validation_rules": [
                        ValidationRule(
                            name="Suggestion to fill",
                            dimension="completeness",
                            severity=Severity.WARNING,
                            rule_type="not_null",
                            rule_expression="IS_NOT_NULL"
                        )
                    ]
                }
            }
        }

        score = assessor.assess(data, requirements)

        # Perfect score - no CRITICAL rules to fail
        assert score == 20.0

    def test_completeness_multiple_fields_mixed_severity(self):
        """Test multiple fields with different severity configurations."""
        assessor = CompletenessAssessor()

        data = pd.DataFrame({
            "critical_field": ["value", "value", "value"],  # All present
            "warning_field": [None, None, None]  # All missing but WARNING only
        })

        requirements = {
            "field_requirements": {
                "critical_field": {
                    "validation_rules": [
                        ValidationRule(
                            name="Critical field required",
                            dimension="completeness",
                            severity=Severity.CRITICAL,
                            rule_type="not_null",
                            rule_expression="IS_NOT_NULL"
                        )
                    ]
                },
                "warning_field": {
                    "validation_rules": [
                        ValidationRule(
                            name="Warning field optional",
                            dimension="completeness",
                            severity=Severity.WARNING,
                            rule_type="not_null",
                            rule_expression="IS_NOT_NULL"
                        )
                    ]
                }
            }
        }

        score = assessor.assess(data, requirements)

        # Perfect score - CRITICAL field complete, WARNING field ignored
        assert score == 20.0
