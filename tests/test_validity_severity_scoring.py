"""Tests for validity dimension severity-aware scoring.

Tests that validity dimension correctly filters rules by severity.
"""

import pandas as pd
import pytest

from src.adri.validator.dimensions.validity import ValidityAssessor
from src.adri.core.validation_rule import ValidationRule
from src.adri.core.severity import Severity


class TestValiditySeverityAwareScoring:
    """Test that validity dimension respects severity levels."""

    def test_validity_with_all_critical_rules_failures(self):
        """Test that CRITICAL rule failures reduce validity score."""
        assessor = ValidityAssessor()

        # Create test data with invalid values
        data = pd.DataFrame({
            "status": ["INVALID", "INVALID", "INVALID"]  # Not in allowed_values
        })

        # Create field requirements with CRITICAL rules
        requirements = {
            "field_requirements": {
                "status": {
                    "type": "string",
                    "validation_rules": [
                        ValidationRule(
                            name="Status allowed values",
                            dimension="validity",
                            severity=Severity.CRITICAL,
                            rule_type="allowed_values",
                            rule_expression="VALUE_IN(['paid', 'pending'])"
                        )
                    ],
                    "allowed_values": ["paid", "pending"]
                }
            }
        }

        score = assessor.assess(data, requirements)

        # Score should be low because CRITICAL rule failed
        assert score < 20.0
        assert score == 0.0  # All values failed

    def test_validity_with_all_warning_rules_failures(self):
        """Test that WARNING rule failures don't reduce validity score."""
        assessor = ValidityAssessor()

        # Create test data with format issues (but valid)
        data = pd.DataFrame({
            "status": ["PAID", "PENDING", "PAID"]  # Uppercase (format warning)
        })

        # Create field requirements with only WARNING rules
        requirements = {
            "field_requirements": {
                "status": {
                    "type": "string",
                    "validation_rules": [
                        ValidationRule(
                            name="Status lowercase preference",
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

        # Score should be perfect because WARNING rules don't affect score
        assert score == 20.0

    def test_validity_with_mixed_severity_rules(self):
        """Test mixed CRITICAL and WARNING rules - only CRITICAL affects score."""
        assessor = ValidityAssessor()

        # Create test data: valid values but wrong case
        data = pd.DataFrame({
            "status": ["paid", "pending", "paid"]  # Valid and lowercase
        })

        # Create field requirements with mixed severity
        requirements = {
            "field_requirements": {
                "status": {
                    "type": "string",
                    "validation_rules": [
                        ValidationRule(
                            name="Status allowed values",
                            dimension="validity",
                            severity=Severity.CRITICAL,
                            rule_type="allowed_values",
                            rule_expression="VALUE_IN(['paid', 'pending'])"
                        ),
                        ValidationRule(
                            name="Status lowercase",
                            dimension="validity",
                            severity=Severity.WARNING,
                            rule_type="format",
                            rule_expression="IS_LOWERCASE"
                        )
                    ],
                    "allowed_values": ["paid", "pending"]
                }
            }
        }

        score = assessor.assess(data, requirements)

        # Score should be perfect - CRITICAL rules pass, WARNING ignored for scoring
        assert score == 20.0

    def test_validity_backward_compatibility_old_format(self):
        """Test that old format (no validation_rules) still works."""
        assessor = ValidityAssessor()

        data = pd.DataFrame({
            "email": ["test@example.com", "user@domain.com"]
        })

        # Old format without validation_rules
        requirements = {
            "field_requirements": {
                "email": {
                    "type": "string",
                    "nullable": False
                }
            }
        }

        score = assessor.assess(data, requirements)

        # Should still work with old format
        assert score == 20.0

    def test_validity_no_critical_rules_perfect_score(self):
        """Test that having no CRITICAL rules gives perfect score."""
        assessor = ValidityAssessor()

        data = pd.DataFrame({
            "status": ["PAID", "PENDING"]  # Uppercase
        })

        # Only WARNING rules, no CRITICAL
        requirements = {
            "field_requirements": {
                "status": {
                    "type": "string",
                    "validation_rules": [
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

        # Perfect score - no CRITICAL rules to fail
        assert score == 20.0
