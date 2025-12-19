"""Tests for consistency dimension severity-aware scoring.

Tests that consistency dimension correctly filters rules by severity.
"""

import pandas as pd
import pytest

from src.adri.validator.dimensions.consistency import ConsistencyAssessor
from src.adri.core.validation_rule import ValidationRule
from src.adri.core.severity import Severity


class TestConsistencySeverityAwareScoring:
    """Test that consistency dimension respects severity levels."""

    def test_consistency_with_critical_format_rules_failures(self):
        """Test that CRITICAL format rule failures reduce consistency score."""
        assessor = ConsistencyAssessor()

        # Create test data with inconsistent formats
        data = pd.DataFrame({
            "status": ["PAID", "pending", "PENDING"]  # Mixed case
        })

        # Create field requirements with CRITICAL format rules
        requirements = {
            "field_requirements": {
                "status": {
                    "type": "string",
                    "validation_rules": [
                        ValidationRule(
                            name="Status must be lowercase",
                            dimension="consistency",
                            severity=Severity.CRITICAL,
                            rule_type="format",
                            rule_expression="IS_LOWERCASE"
                        )
                    ]
                }
            }
        }

        score = assessor.assess(data, requirements)

        # Score should be reduced - only 1 out of 3 is lowercase
        assert score < 20.0
        assert abs(score - (1/3 * 20.0)) < 0.1  # Approximately 6.67

    def test_consistency_with_warning_format_rules_no_penalty(self):
        """Test that WARNING format rule failures don't reduce consistency score."""
        assessor = ConsistencyAssessor()

        # Create test data with format issues
        data = pd.DataFrame({
            "status": ["PAID", "PENDING", "CANCELLED"]  # All uppercase
        })

        # Create field requirements with only WARNING format rules
        requirements = {
            "field_requirements": {
                "status": {
                    "type": "string",
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

        # Score should be perfect because WARNING rules don't affect score
        assert score == 20.0

    def test_consistency_with_mixed_severity_format_rules(self):
        """Test mixed CRITICAL and WARNING format rules."""
        assessor = ConsistencyAssessor()

        # Create test data: all lowercase (passes CRITICAL, passes WARNING)
        data = pd.DataFrame({
            "status": ["paid", "pending", "cancelled"]
        })

        # Create field requirements with mixed severity
        requirements = {
            "field_requirements": {
                "status": {
                    "type": "string",
                    "validation_rules": [
                        ValidationRule(
                            name="Must be lowercase",
                            dimension="consistency",
                            severity=Severity.CRITICAL,
                            rule_type="format",
                            rule_expression="IS_LOWERCASE"
                        ),
                        ValidationRule(
                            name="Preference for short names",
                            dimension="consistency",
                            severity=Severity.WARNING,
                            rule_type="format",
                            rule_expression="LENGTH < 10"
                        )
                    ]
                }
            }
        }

        score = assessor.assess(data, requirements)

        # Score should be perfect - CRITICAL rules pass, WARNING ignored
        assert score == 20.0

    def test_consistency_backward_compatibility_old_format(self):
        """Test that old format (format_rules) still works."""
        assessor = ConsistencyAssessor()

        data = pd.DataFrame({
            "name": ["Alice", "Bob", "Charlie"]
        })

        # Old format with format_rules (not validation_rules)
        requirements = {
            "scoring": {
                "rule_weights": {
                    "format_consistency": 1.0
                }
            },
            "format_rules": {
                "name": "title_case"
            }
        }

        score = assessor.assess(data, requirements)

        # Should still work with old format
        assert score > 0.0  # Has some format checking

    def test_consistency_no_critical_rules_perfect_score(self):
        """Test that having no CRITICAL rules gives perfect score."""
        assessor = ConsistencyAssessor()

        data = pd.DataFrame({
            "status": ["PAID", "PENDING"]  # Uppercase (would fail lowercase)
        })

        # Only WARNING rules, no CRITICAL
        requirements = {
            "field_requirements": {
                "status": {
                    "type": "string",
                    "validation_rules": [
                        ValidationRule(
                            name="Lowercase suggestion",
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

        # Perfect score - no CRITICAL rules to fail
        assert score == 20.0

    def test_consistency_empty_dataframe(self):
        """Test that empty DataFrame returns perfect score."""
        assessor = ConsistencyAssessor()

        data = pd.DataFrame()

        requirements = {
            "field_requirements": {
                "status": {
                    "validation_rules": [
                        ValidationRule(
                            name="Test rule",
                            dimension="consistency",
                            severity=Severity.CRITICAL,
                            rule_type="format",
                            rule_expression="IS_LOWERCASE"
                        )
                    ]
                }
            }
        }

        score = assessor.assess(data, requirements)

        # Empty data is technically consistent
        assert score == 20.0
