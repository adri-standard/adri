"""Tests for validation rules structure parsing and schema validation.

Tests the schema validation for the new validation_rules format in standards.
"""

import pytest

from src.adri.contracts.schema import StandardSchema
from src.adri.core.severity import Severity
from src.adri.core.validation_rule import ValidationRule


class TestValidationRuleSchemaValidation:
    """Test schema validation for validation rules."""

    def test_validate_validation_rule_valid_minimal(self):
        """Test validation of a minimal valid validation rule."""
        rule = {
            "name": "Test rule",
            "dimension": "validity",
            "severity": "CRITICAL",
            "rule_type": "type",
            "rule_expression": "IS_STRING"
        }

        errors = StandardSchema.validate_validation_rule(rule, "test_field")
        assert len(errors) == 0

    def test_validate_validation_rule_valid_full(self):
        """Test validation of a complete validation rule with all fields."""
        rule = {
            "name": "Email format validation",
            "dimension": "validity",
            "severity": "CRITICAL",
            "rule_type": "pattern",
            "rule_expression": "REGEX_MATCH('^[a-z]+@[a-z]+')",
            "error_message": "Invalid email format",
            "remediation": "Provide valid email",
            "penalty_weight": 2.0
        }

        errors = StandardSchema.validate_validation_rule(rule, "email_field")
        assert len(errors) == 0

    def test_validate_validation_rule_missing_required_field(self):
        """Test that missing required fields are detected."""
        rule = {
            "name": "Test rule",
            "dimension": "validity",
            # Missing: severity, rule_type, rule_expression
        }

        errors = StandardSchema.validate_validation_rule(rule, "test_field")
        assert len(errors) == 3
        assert any("severity" in err for err in errors)
        assert any("rule_type" in err for err in errors)
        assert any("rule_expression" in err for err in errors)

    def test_validate_validation_rule_invalid_severity(self):
        """Test that invalid severity values are detected."""
        rule = {
            "name": "Test rule",
            "dimension": "validity",
            "severity": "INVALID_SEVERITY",
            "rule_type": "type",
            "rule_expression": "IS_STRING"
        }

        errors = StandardSchema.validate_validation_rule(rule, "test_field")
        assert len(errors) == 1
        assert "invalid severity" in errors[0].lower()
        assert "INVALID_SEVERITY" in errors[0]

    def test_validate_validation_rule_valid_severities(self):
        """Test that all valid severity levels are accepted."""
        for severity in ["CRITICAL", "WARNING", "INFO"]:
            rule = {
                "name": "Test rule",
                "dimension": "validity",
                "severity": severity,
                "rule_type": "type",
                "rule_expression": "IS_STRING"
            }

            errors = StandardSchema.validate_validation_rule(rule, "test_field")
            assert len(errors) == 0, f"Severity {severity} should be valid"

    def test_validate_validation_rule_invalid_dimension(self):
        """Test that invalid dimension values are detected."""
        rule = {
            "name": "Test rule",
            "dimension": "invalid_dimension",
            "severity": "CRITICAL",
            "rule_type": "type",
            "rule_expression": "IS_STRING"
        }

        errors = StandardSchema.validate_validation_rule(rule, "test_field")
        assert len(errors) == 1
        assert "invalid dimension" in errors[0].lower()
        assert "invalid_dimension" in errors[0]

    def test_validate_validation_rule_valid_dimensions(self):
        """Test that all valid dimensions are accepted."""
        # Use dimension-appropriate rule types
        dimension_rules = {
            "validity": ("type", "IS_STRING"),
            "completeness": ("not_null", "IS_NOT_NULL"),
            "consistency": ("format", "IS_LOWERCASE"),
            "freshness": ("age_check", "AGE < 30"),
            "plausibility": ("range_check", "VALUE >= 0")
        }

        for dimension, (rule_type, expression) in dimension_rules.items():
            rule = {
                "name": "Test rule",
                "dimension": dimension,
                "severity": "CRITICAL",
                "rule_type": rule_type,
                "rule_expression": expression
            }

            errors = StandardSchema.validate_validation_rule(rule, "test_field")
            assert len(errors) == 0, f"Dimension {dimension} with rule_type {rule_type} should be valid"

    def test_validate_validation_rule_invalid_rule_type_for_dimension(self):
        """Test that rule_type is validated against dimension."""
        rule = {
            "name": "Test rule",
            "dimension": "validity",
            "severity": "CRITICAL",
            "rule_type": "not_null",  # not_null is for completeness, not validity
            "rule_expression": "IS_NOT_NULL"
        }

        errors = StandardSchema.validate_validation_rule(rule, "test_field")
        assert len(errors) == 1
        assert "invalid rule_type" in errors[0].lower()
        assert "not_null" in errors[0]

    def test_validate_validation_rule_valid_rule_types_per_dimension(self):
        """Test that rule types are correctly validated per dimension."""
        test_cases = [
            ("validity", "type"),
            ("validity", "allowed_values"),
            ("validity", "pattern"),
            ("completeness", "not_null"),
            ("completeness", "not_empty"),
            ("consistency", "format"),
            ("consistency", "uniqueness"),
            ("freshness", "age_check"),
            ("plausibility", "range_check"),
        ]

        for dimension, rule_type in test_cases:
            rule = {
                "name": f"Test {dimension} {rule_type}",
                "dimension": dimension,
                "severity": "CRITICAL",
                "rule_type": rule_type,
                "rule_expression": "TEST"
            }

            errors = StandardSchema.validate_validation_rule(rule, "test_field")
            assert len(errors) == 0, f"{rule_type} should be valid for {dimension}"

    def test_validate_validation_rule_negative_penalty_weight(self):
        """Test that negative penalty_weight is detected."""
        rule = {
            "name": "Test rule",
            "dimension": "validity",
            "severity": "CRITICAL",
            "rule_type": "type",
            "rule_expression": "IS_STRING",
            "penalty_weight": -1.0
        }

        errors = StandardSchema.validate_validation_rule(rule, "test_field")
        assert len(errors) == 1
        assert "negative penalty_weight" in errors[0].lower()

    def test_validate_validation_rule_invalid_penalty_weight_type(self):
        """Test that non-numeric penalty_weight is detected."""
        rule = {
            "name": "Test rule",
            "dimension": "validity",
            "severity": "CRITICAL",
            "rule_type": "type",
            "rule_expression": "IS_STRING",
            "penalty_weight": "invalid"
        }

        errors = StandardSchema.validate_validation_rule(rule, "test_field")
        assert len(errors) == 1
        assert "penalty_weight" in errors[0].lower()
        assert "type" in errors[0].lower()


class TestValidationRulesListValidation:
    """Test schema validation for lists of validation rules."""

    def test_validate_validation_rules_list_valid(self):
        """Test validation of a valid list of validation rules."""
        rules = [
            {
                "name": "Required field",
                "dimension": "completeness",
                "severity": "CRITICAL",
                "rule_type": "not_null",
                "rule_expression": "IS_NOT_NULL"
            },
            {
                "name": "Format check",
                "dimension": "consistency",
                "severity": "WARNING",
                "rule_type": "format",
                "rule_expression": "IS_LOWERCASE"
            }
        ]

        errors = StandardSchema.validate_validation_rules_list(rules, "test_field")
        assert len(errors) == 0

    def test_validate_validation_rules_list_not_list(self):
        """Test that non-list types are detected."""
        rules = {"not": "a list"}

        errors = StandardSchema.validate_validation_rules_list(rules, "test_field")
        assert len(errors) == 1
        assert "must be a list" in errors[0].lower()

    def test_validate_validation_rules_list_empty(self):
        """Test that empty lists are detected."""
        rules = []

        errors = StandardSchema.validate_validation_rules_list(rules, "test_field")
        assert len(errors) == 1
        assert "empty" in errors[0].lower()

    def test_validate_validation_rules_list_non_dict_element(self):
        """Test that non-dict elements in list are detected."""
        rules = [
            {
                "name": "Valid rule",
                "dimension": "validity",
                "severity": "CRITICAL",
                "rule_type": "type",
                "rule_expression": "IS_STRING"
            },
            "not a dict"
        ]

        errors = StandardSchema.validate_validation_rules_list(rules, "test_field")
        assert len(errors) == 1
        assert "must be a dictionary" in errors[0].lower()

    def test_validate_validation_rules_list_multiple_invalid_rules(self):
        """Test that multiple invalid rules are all detected."""
        rules = [
            {
                "name": "Missing fields",
                "dimension": "validity",
                # Missing severity, rule_type, rule_expression
            },
            {
                "name": "Invalid severity",
                "dimension": "validity",
                "severity": "INVALID",
                "rule_type": "type",
                "rule_expression": "IS_STRING"
            }
        ]

        errors = StandardSchema.validate_validation_rules_list(rules, "test_field")
        # First rule should have 3 errors (missing fields)
        # Second rule should have 1 error (invalid severity)
        assert len(errors) >= 4

    def test_validate_validation_rules_list_field_path_in_errors(self):
        """Test that field paths are correctly included in error messages."""
        rules = [
            {
                "name": "Invalid rule",
                "dimension": "invalid_dimension",
                "severity": "CRITICAL",
                "rule_type": "type",
                "rule_expression": "IS_STRING"
            }
        ]

        errors = StandardSchema.validate_validation_rules_list(rules, "customer_email")
        assert len(errors) == 1
        assert "customer_email[0]" in errors[0]


class TestSchemaConstants:
    """Test that schema constants are correctly defined."""

    def test_valid_severity_levels(self):
        """Test that valid severity levels are defined."""
        assert StandardSchema.VALID_SEVERITY_LEVELS == {"CRITICAL", "WARNING", "INFO"}

    def test_required_validation_rule_fields(self):
        """Test that required fields list is correct."""
        expected = ["name", "dimension", "severity", "rule_type", "rule_expression"]
        assert StandardSchema.REQUIRED_VALIDATION_RULE_FIELDS == expected

    def test_valid_rule_types_by_dimension_completeness(self):
        """Test that completeness dimension has correct rule types."""
        rule_types = StandardSchema.VALID_RULE_TYPES_BY_DIMENSION["completeness"]
        assert "not_null" in rule_types
        assert "not_empty" in rule_types
        assert "required_fields" in rule_types

    def test_valid_rule_types_by_dimension_validity(self):
        """Test that validity dimension has correct rule types."""
        rule_types = StandardSchema.VALID_RULE_TYPES_BY_DIMENSION["validity"]
        assert "type" in rule_types
        assert "allowed_values" in rule_types
        assert "pattern" in rule_types
        assert "numeric_bounds" in rule_types

    def test_valid_rule_types_by_dimension_consistency(self):
        """Test that consistency dimension has correct rule types."""
        rule_types = StandardSchema.VALID_RULE_TYPES_BY_DIMENSION["consistency"]
        assert "format" in rule_types
        assert "case" in rule_types
        assert "uniqueness" in rule_types

    def test_valid_rule_types_by_dimension_all_dimensions(self):
        """Test that all dimensions have rule types defined."""
        dimensions = ["validity", "completeness", "consistency", "freshness", "plausibility"]

        for dimension in dimensions:
            assert dimension in StandardSchema.VALID_RULE_TYPES_BY_DIMENSION
            assert len(StandardSchema.VALID_RULE_TYPES_BY_DIMENSION[dimension]) > 0


class TestStandardLoaderParsing:
    """Test standard loader parsing of validation_rules."""

    def test_parse_validation_rules_empty_standard(self):
        """Test parsing empty standard returns unchanged."""
        from src.adri.validator.loaders import _parse_validation_rules

        standard = {}
        result = _parse_validation_rules(standard)
        assert result == {}

    def test_parse_validation_rules_no_dimension_requirements(self):
        """Test parsing standard without dimension_requirements."""
        from src.adri.validator.loaders import _parse_validation_rules

        standard = {
            "contracts": {"id": "test", "name": "Test", "version": "1.0", "description": "Test"},
            "requirements": {"overall_minimum": 80}
        }
        result = _parse_validation_rules(standard)
        assert result == standard

    def test_parse_validation_rules_old_format(self):
        """Test that old format (no validation_rules) is left unchanged."""
        from src.adri.validator.loaders import _parse_validation_rules

        standard = {
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 5,
                        "field_requirements": {
                            "email": {
                                "type": "string",
                                "nullable": False
                            }
                        }
                    }
                }
            }
        }
        result = _parse_validation_rules(standard)
        # Should be unchanged since no validation_rules present
        assert "validation_rules" not in result["requirements"]["dimension_requirements"]["validity"]["field_requirements"]["email"]

    def test_parse_validation_rules_new_format(self):
        """Test parsing new format with validation_rules."""
        from src.adri.validator.loaders import _parse_validation_rules

        standard = {
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 5,
                        "field_requirements": {
                            "email": {
                                "type": "string",
                                "validation_rules": [
                                    {
                                        "name": "Email required",
                                        "dimension": "completeness",
                                        "severity": "CRITICAL",
                                        "rule_type": "not_null",
                                        "rule_expression": "IS_NOT_NULL"
                                    },
                                    {
                                        "name": "Email format",
                                        "dimension": "validity",
                                        "severity": "CRITICAL",
                                        "rule_type": "pattern",
                                        "rule_expression": "REGEX_MATCH('^[a-z]+@')"
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }

        result = _parse_validation_rules(standard)

        # Check that validation_rules were parsed into ValidationRule objects
        email_field = result["requirements"]["dimension_requirements"]["validity"]["field_requirements"]["email"]
        assert "validation_rules" in email_field
        assert isinstance(email_field["validation_rules"], list)
        assert len(email_field["validation_rules"]) == 2

        # Check first rule
        rule1 = email_field["validation_rules"][0]
        assert isinstance(rule1, ValidationRule)
        assert rule1.name == "Email required"
        assert rule1.severity == Severity.CRITICAL
        assert rule1.dimension == "completeness"

        # Check second rule
        rule2 = email_field["validation_rules"][1]
        assert isinstance(rule2, ValidationRule)
        assert rule2.name == "Email format"
        assert rule2.dimension == "validity"

    def test_parse_validation_rules_multiple_fields(self):
        """Test parsing multiple fields with validation_rules."""
        from src.adri.validator.loaders import _parse_validation_rules

        standard = {
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 5,
                        "field_requirements": {
                            "email": {
                                "validation_rules": [
                                    {
                                        "name": "Email required",
                                        "dimension": "completeness",
                                        "severity": "CRITICAL",
                                        "rule_type": "not_null",
                                        "rule_expression": "IS_NOT_NULL"
                                    }
                                ]
                            },
                            "status": {
                                "validation_rules": [
                                    {
                                        "name": "Status required",
                                        "dimension": "completeness",
                                        "severity": "CRITICAL",
                                        "rule_type": "not_null",
                                        "rule_expression": "IS_NOT_NULL"
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }

        result = _parse_validation_rules(standard)

        field_reqs = result["requirements"]["dimension_requirements"]["validity"]["field_requirements"]
        assert len(field_reqs["email"]["validation_rules"]) == 1
        assert len(field_reqs["status"]["validation_rules"]) == 1
        assert isinstance(field_reqs["email"]["validation_rules"][0], ValidationRule)
        assert isinstance(field_reqs["status"]["validation_rules"][0], ValidationRule)

    def test_parse_validation_rules_multiple_dimensions(self):
        """Test parsing validation_rules across multiple dimensions."""
        from src.adri.validator.loaders import _parse_validation_rules

        standard = {
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 5,
                        "field_requirements": {
                            "email": {
                                "validation_rules": [
                                    {
                                        "name": "Email format",
                                        "dimension": "validity",
                                        "severity": "CRITICAL",
                                        "rule_type": "pattern",
                                        "rule_expression": "REGEX"
                                    }
                                ]
                            }
                        }
                    },
                    "completeness": {
                        "weight": 4,
                        "field_requirements": {
                            "email": {
                                "validation_rules": [
                                    {
                                        "name": "Email required",
                                        "dimension": "completeness",
                                        "severity": "CRITICAL",
                                        "rule_type": "not_null",
                                        "rule_expression": "IS_NOT_NULL"
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }

        result = _parse_validation_rules(standard)

        validity_rules = result["requirements"]["dimension_requirements"]["validity"]["field_requirements"]["email"]["validation_rules"]
        completeness_rules = result["requirements"]["dimension_requirements"]["completeness"]["field_requirements"]["email"]["validation_rules"]

        assert len(validity_rules) == 1
        assert len(completeness_rules) == 1
        assert validity_rules[0].dimension == "validity"
        assert completeness_rules[0].dimension == "completeness"


class TestValidationRuleIntegrationWithSchema:
    """Integration tests between ValidationRule class and schema validation."""

    def test_validation_rule_from_dict_passes_schema_validation(self):
        """Test that ValidationRule.from_dict creates schema-valid objects."""
        rule_dict = {
            "name": "Test rule",
            "dimension": "validity",
            "severity": "CRITICAL",
            "rule_type": "type",
            "rule_expression": "IS_STRING"
        }

        # Validate with schema first
        schema_errors = StandardSchema.validate_validation_rule(rule_dict, "test")
        assert len(schema_errors) == 0

        # Then create ValidationRule object
        rule = ValidationRule.from_dict(rule_dict)
        assert rule.name == "Test rule"
        assert rule.severity == Severity.CRITICAL

    def test_validation_rule_to_dict_passes_schema_validation(self):
        """Test that ValidationRule.to_dict creates schema-valid dictionaries."""
        rule = ValidationRule(
            name="Test rule",
            dimension="validity",
            severity=Severity.CRITICAL,
            rule_type="type",
            rule_expression="IS_STRING"
        )

        rule_dict = rule.to_dict()

        # Validate the resulting dictionary
        schema_errors = StandardSchema.validate_validation_rule(rule_dict, "test")
        assert len(schema_errors) == 0

    def test_validation_rule_with_invalid_dimension_caught_by_both(self):
        """Test that invalid dimensions are caught by both ValidationRule and schema."""
        rule_dict = {
            "name": "Test rule",
            "dimension": "invalid_dimension",
            "severity": "CRITICAL",
            "rule_type": "type",
            "rule_expression": "IS_STRING"
        }

        # Schema validation should fail
        schema_errors = StandardSchema.validate_validation_rule(rule_dict, "test")
        assert len(schema_errors) > 0

        # ValidationRule creation should also fail
        with pytest.raises(ValueError) as exc_info:
            ValidationRule.from_dict(rule_dict)
        assert "invalid dimension" in str(exc_info.value).lower()
