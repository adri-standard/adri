"""Unit tests for Severity enum and ValidationRule dataclass.

Tests the core types for explicit severity levels in validation rules.
"""

import pytest
from dataclasses import FrozenInstanceError

from src.adri.core.severity import Severity
from src.adri.core.validation_rule import ValidationRule


class TestSeverity:
    """Test cases for the Severity enum."""

    def test_severity_values(self):
        """Test that all severity levels are defined correctly."""
        assert Severity.CRITICAL.value == "CRITICAL"
        assert Severity.WARNING.value == "WARNING"
        assert Severity.INFO.value == "INFO"

    def test_severity_string_representation(self):
        """Test string conversion of severity levels."""
        assert str(Severity.CRITICAL) == "CRITICAL"
        assert str(Severity.WARNING) == "WARNING"
        assert str(Severity.INFO) == "INFO"

    def test_severity_from_string_valid(self):
        """Test creating Severity from valid string values."""
        assert Severity.from_string("CRITICAL") == Severity.CRITICAL
        assert Severity.from_string("WARNING") == Severity.WARNING
        assert Severity.from_string("INFO") == Severity.INFO

        # Test case insensitivity
        assert Severity.from_string("critical") == Severity.CRITICAL
        assert Severity.from_string("Warning") == Severity.WARNING
        assert Severity.from_string("info") == Severity.INFO

    def test_severity_from_string_invalid(self):
        """Test that invalid severity strings raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            Severity.from_string("INVALID")
        assert "Invalid severity level: 'INVALID'" in str(exc_info.value)
        assert "Must be one of: CRITICAL, WARNING, INFO" in str(exc_info.value)

    def test_severity_should_penalize_score(self):
        """Test that only CRITICAL severity penalizes scores."""
        assert Severity.CRITICAL.should_penalize_score() is True
        assert Severity.WARNING.should_penalize_score() is False
        assert Severity.INFO.should_penalize_score() is False

    def test_severity_enum_comparison(self):
        """Test that severity levels can be compared."""
        assert Severity.CRITICAL == Severity.CRITICAL
        assert Severity.CRITICAL != Severity.WARNING
        assert Severity.WARNING != Severity.INFO

    def test_severity_is_string_enum(self):
        """Test that Severity is a string enum (can be used as string)."""
        severity = Severity.CRITICAL
        assert isinstance(severity, str)
        assert severity == "CRITICAL"


class TestValidationRule:
    """Test cases for the ValidationRule dataclass."""

    def test_validation_rule_creation_minimal(self):
        """Test creating a ValidationRule with minimal required fields."""
        rule = ValidationRule(
            name="Test rule",
            dimension="validity",
            severity=Severity.CRITICAL,
            rule_type="not_null",
            rule_expression="IS_NOT_NULL"
        )

        assert rule.name == "Test rule"
        assert rule.dimension == "validity"
        assert rule.severity == Severity.CRITICAL
        assert rule.rule_type == "not_null"
        assert rule.rule_expression == "IS_NOT_NULL"
        assert rule.error_message is None
        assert rule.remediation is None
        assert rule.penalty_weight == 1.0

    def test_validation_rule_creation_full(self):
        """Test creating a ValidationRule with all fields."""
        rule = ValidationRule(
            name="Email format validation",
            dimension="validity",
            severity=Severity.CRITICAL,
            rule_type="pattern",
            rule_expression="REGEX_MATCH('^[a-z]+@[a-z]+\\.[a-z]+$')",
            error_message="Email must be valid format",
            remediation="Provide email in format: user@domain.com",
            penalty_weight=2.0
        )

        assert rule.name == "Email format validation"
        assert rule.error_message == "Email must be valid format"
        assert rule.remediation == "Provide email in format: user@domain.com"
        assert rule.penalty_weight == 2.0

    def test_validation_rule_string_severity_conversion(self):
        """Test that string severity is automatically converted to enum."""
        rule = ValidationRule(
            name="Test rule",
            dimension="completeness",
            severity="CRITICAL",  # String instead of enum
            rule_type="not_null",
            rule_expression="IS_NOT_NULL"
        )

        assert isinstance(rule.severity, Severity)
        assert rule.severity == Severity.CRITICAL

    def test_validation_rule_invalid_dimension(self):
        """Test that invalid dimension raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ValidationRule(
                name="Test rule",
                dimension="invalid_dimension",
                severity=Severity.CRITICAL,
                rule_type="not_null",
                rule_expression="IS_NOT_NULL"
            )
        assert "Invalid dimension: 'invalid_dimension'" in str(exc_info.value)

    def test_validation_rule_valid_dimensions(self):
        """Test that all valid dimensions are accepted."""
        valid_dimensions = ["validity", "completeness", "consistency", "freshness", "plausibility"]

        for dimension in valid_dimensions:
            rule = ValidationRule(
                name="Test rule",
                dimension=dimension,
                severity=Severity.CRITICAL,
                rule_type="test",
                rule_expression="TEST"
            )
            assert rule.dimension == dimension

    def test_validation_rule_negative_penalty_weight(self):
        """Test that negative penalty_weight raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ValidationRule(
                name="Test rule",
                dimension="validity",
                severity=Severity.CRITICAL,
                rule_type="not_null",
                rule_expression="IS_NOT_NULL",
                penalty_weight=-1.0
            )
        assert "penalty_weight must be >= 0" in str(exc_info.value)

    def test_validation_rule_from_dict_minimal(self):
        """Test creating ValidationRule from dictionary with minimal fields."""
        rule_dict = {
            "name": "Test rule",
            "dimension": "validity",
            "severity": "CRITICAL",
            "rule_type": "not_null",
            "rule_expression": "IS_NOT_NULL"
        }

        rule = ValidationRule.from_dict(rule_dict)

        assert rule.name == "Test rule"
        assert rule.dimension == "validity"
        assert rule.severity == Severity.CRITICAL
        assert rule.rule_type == "not_null"
        assert rule.rule_expression == "IS_NOT_NULL"

    def test_validation_rule_from_dict_full(self):
        """Test creating ValidationRule from dictionary with all fields."""
        rule_dict = {
            "name": "Email format",
            "dimension": "validity",
            "severity": "WARNING",
            "rule_type": "pattern",
            "rule_expression": "REGEX_MATCH('^[a-z]+@[a-z]+')",
            "error_message": "Invalid email",
            "remediation": "Fix email format",
            "penalty_weight": 1.5
        }

        rule = ValidationRule.from_dict(rule_dict)

        assert rule.name == "Email format"
        assert rule.severity == Severity.WARNING
        assert rule.error_message == "Invalid email"
        assert rule.remediation == "Fix email format"
        assert rule.penalty_weight == 1.5

    def test_validation_rule_from_dict_missing_required_field(self):
        """Test that from_dict raises ValueError for missing required fields."""
        rule_dict = {
            "name": "Test rule",
            "dimension": "validity",
            # Missing: severity, rule_type, rule_expression
        }

        with pytest.raises(ValueError) as exc_info:
            ValidationRule.from_dict(rule_dict)
        assert "Missing required fields in validation rule" in str(exc_info.value)

    def test_validation_rule_to_dict_minimal(self):
        """Test converting ValidationRule to dictionary with minimal fields."""
        rule = ValidationRule(
            name="Test rule",
            dimension="validity",
            severity=Severity.CRITICAL,
            rule_type="not_null",
            rule_expression="IS_NOT_NULL"
        )

        rule_dict = rule.to_dict()

        assert rule_dict == {
            "name": "Test rule",
            "dimension": "validity",
            "severity": "CRITICAL",
            "rule_type": "not_null",
            "rule_expression": "IS_NOT_NULL"
        }
        # Optional fields should not be included
        assert "error_message" not in rule_dict
        assert "remediation" not in rule_dict
        assert "penalty_weight" not in rule_dict  # Default 1.0 not included

    def test_validation_rule_to_dict_full(self):
        """Test converting ValidationRule to dictionary with all fields."""
        rule = ValidationRule(
            name="Email format",
            dimension="validity",
            severity=Severity.WARNING,
            rule_type="pattern",
            rule_expression="REGEX",
            error_message="Invalid",
            remediation="Fix it",
            penalty_weight=2.0
        )

        rule_dict = rule.to_dict()

        assert rule_dict["error_message"] == "Invalid"
        assert rule_dict["remediation"] == "Fix it"
        assert rule_dict["penalty_weight"] == 2.0

    def test_validation_rule_round_trip(self):
        """Test that from_dict and to_dict are inverses."""
        original_dict = {
            "name": "Test rule",
            "dimension": "consistency",
            "severity": "WARNING",
            "rule_type": "format",
            "rule_expression": "IS_LOWERCASE",
            "error_message": "Should be lowercase",
            "penalty_weight": 0.5
        }

        rule = ValidationRule.from_dict(original_dict)
        result_dict = rule.to_dict()

        assert result_dict["name"] == original_dict["name"]
        assert result_dict["dimension"] == original_dict["dimension"]
        assert result_dict["severity"] == original_dict["severity"]
        assert result_dict["rule_type"] == original_dict["rule_type"]
        assert result_dict["rule_expression"] == original_dict["rule_expression"]
        assert result_dict["error_message"] == original_dict["error_message"]
        assert result_dict["penalty_weight"] == original_dict["penalty_weight"]

    def test_validation_rule_should_penalize_score_critical(self):
        """Test that CRITICAL rules should penalize score."""
        rule = ValidationRule(
            name="Critical rule",
            dimension="validity",
            severity=Severity.CRITICAL,
            rule_type="type",
            rule_expression="TYPE_CHECK"
        )

        assert rule.should_penalize_score() is True

    def test_validation_rule_should_penalize_score_warning(self):
        """Test that WARNING rules should not penalize score."""
        rule = ValidationRule(
            name="Warning rule",
            dimension="consistency",
            severity=Severity.WARNING,
            rule_type="format",
            rule_expression="IS_LOWERCASE"
        )

        assert rule.should_penalize_score() is False

    def test_validation_rule_should_penalize_score_info(self):
        """Test that INFO rules should not penalize score."""
        rule = ValidationRule(
            name="Info rule",
            dimension="plausibility",
            severity=Severity.INFO,
            rule_type="statistical",
            rule_expression="OUTLIER_CHECK"
        )

        assert rule.should_penalize_score() is False

    def test_validation_rule_repr(self):
        """Test string representation of ValidationRule."""
        rule = ValidationRule(
            name="Test rule",
            dimension="validity",
            severity=Severity.CRITICAL,
            rule_type="not_null",
            rule_expression="IS_NOT_NULL"
        )

        repr_str = repr(rule)
        assert "ValidationRule" in repr_str
        assert "Test rule" in repr_str
        assert "validity" in repr_str
        assert "CRITICAL" in repr_str
        assert "not_null" in repr_str

    def test_validation_rule_equality(self):
        """Test that identical ValidationRules are equal."""
        rule1 = ValidationRule(
            name="Test rule",
            dimension="validity",
            severity=Severity.CRITICAL,
            rule_type="not_null",
            rule_expression="IS_NOT_NULL"
        )

        rule2 = ValidationRule(
            name="Test rule",
            dimension="validity",
            severity=Severity.CRITICAL,
            rule_type="not_null",
            rule_expression="IS_NOT_NULL"
        )

        assert rule1 == rule2

    def test_validation_rule_different_severity_not_equal(self):
        """Test that rules with different severity are not equal."""
        rule1 = ValidationRule(
            name="Test rule",
            dimension="validity",
            severity=Severity.CRITICAL,
            rule_type="not_null",
            rule_expression="IS_NOT_NULL"
        )

        rule2 = ValidationRule(
            name="Test rule",
            dimension="validity",
            severity=Severity.WARNING,
            rule_type="not_null",
            rule_expression="IS_NOT_NULL"
        )

        assert rule1 != rule2


class TestValidationRuleSeverityIntegration:
    """Integration tests between Severity and ValidationRule."""

    def test_multiple_rules_different_severities(self):
        """Test creating multiple rules with different severities."""
        rules = [
            ValidationRule(
                name="Required field",
                dimension="completeness",
                severity=Severity.CRITICAL,
                rule_type="not_null",
                rule_expression="IS_NOT_NULL"
            ),
            ValidationRule(
                name="Format preference",
                dimension="consistency",
                severity=Severity.WARNING,
                rule_type="format",
                rule_expression="IS_LOWERCASE"
            ),
            ValidationRule(
                name="Statistical outlier",
                dimension="plausibility",
                severity=Severity.INFO,
                rule_type="outlier",
                rule_expression="Z_SCORE < 3"
            )
        ]

        # Verify we can filter by severity
        critical_rules = [r for r in rules if r.should_penalize_score()]
        assert len(critical_rules) == 1
        assert critical_rules[0].name == "Required field"

        non_critical_rules = [r for r in rules if not r.should_penalize_score()]
        assert len(non_critical_rules) == 2

    def test_rule_severity_affects_scoring_decision(self):
        """Test that severity level determines if rule affects scoring."""
        # Create rules for same validation but different severities
        critical_null_check = ValidationRule(
            name="Critical null check",
            dimension="completeness",
            severity=Severity.CRITICAL,
            rule_type="not_null",
            rule_expression="IS_NOT_NULL"
        )

        warning_null_check = ValidationRule(
            name="Warning null check",
            dimension="completeness",
            severity=Severity.WARNING,
            rule_type="not_null",
            rule_expression="IS_NOT_NULL"
        )

        # Same validation logic, different scoring behavior
        assert critical_null_check.should_penalize_score() is True
        assert warning_null_check.should_penalize_score() is False
