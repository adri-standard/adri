"""Tests for BundledStandardWrapper rule extraction methods.

Tests the new validation rule extraction and filtering methods added in Step 4.
"""

import pytest

from src.adri.validator.engine import BundledStandardWrapper
from src.adri.core.severity import Severity
from src.adri.core.validation_rule import ValidationRule


class TestBundledStandardWrapperRuleExtraction:
    """Test rule extraction methods of BundledStandardWrapper."""

    def test_get_validation_rules_for_field_single_dimension(self):
        """Test extracting rules for a field from a single dimension."""
        standard_dict = {
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 5,
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
                                        name="Email format",
                                        dimension="validity",
                                        severity=Severity.CRITICAL,
                                        rule_type="pattern",
                                        rule_expression="REGEX"
                                    )
                                ]
                            }
                        }
                    }
                }
            }
        }

        wrapper = BundledStandardWrapper(standard_dict)
        rules = wrapper.get_validation_rules_for_field("email")

        assert len(rules) == 2
        assert all(isinstance(r, ValidationRule) for r in rules)
        assert rules[0].name == "Email required"
        assert rules[1].name == "Email format"

    def test_get_validation_rules_for_field_multiple_dimensions(self):
        """Test extracting rules for a field across multiple dimensions."""
        standard_dict = {
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 5,
                        "field_requirements": {
                            "status": {
                                "validation_rules": [
                                    ValidationRule(
                                        name="Status format",
                                        dimension="validity",
                                        severity=Severity.CRITICAL,
                                        rule_type="allowed_values",
                                        rule_expression="VALUE_IN(['paid', 'pending'])"
                                    )
                                ]
                            }
                        }
                    },
                    "completeness": {
                        "weight": 4,
                        "field_requirements": {
                            "status": {
                                "validation_rules": [
                                    ValidationRule(
                                        name="Status required",
                                        dimension="completeness",
                                        severity=Severity.CRITICAL,
                                        rule_type="not_null",
                                        rule_expression="IS_NOT_NULL"
                                    )
                                ]
                            }
                        }
                    },
                    "consistency": {
                        "weight": 3,
                        "field_requirements": {
                            "status": {
                                "validation_rules": [
                                    ValidationRule(
                                        name="Status lowercase",
                                        dimension="consistency",
                                        severity=Severity.WARNING,
                                        rule_type="format",
                                        rule_expression="IS_LOWERCASE"
                                    )
                                ]
                            }
                        }
                    }
                }
            }
        }

        wrapper = BundledStandardWrapper(standard_dict)
        rules = wrapper.get_validation_rules_for_field("status")

        assert len(rules) == 3
        assert rules[0].dimension == "validity"
        assert rules[1].dimension == "completeness"
        assert rules[2].dimension == "consistency"
        assert rules[2].severity == Severity.WARNING

    def test_get_validation_rules_for_field_nonexistent(self):
        """Test that nonexistent fields return empty list."""
        standard_dict = {
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 5,
                        "field_requirements": {
                            "email": {
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
                }
            }
        }

        wrapper = BundledStandardWrapper(standard_dict)
        rules = wrapper.get_validation_rules_for_field("nonexistent_field")

        assert rules == []

    def test_get_all_validation_rules(self):
        """Test extracting all validation rules organized by field."""
        standard_dict = {
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 5,
                        "field_requirements": {
                            "email": {
                                "validation_rules": [
                                    ValidationRule(
                                        name="Email format",
                                        dimension="validity",
                                        severity=Severity.CRITICAL,
                                        rule_type="pattern",
                                        rule_expression="REGEX"
                                    )
                                ]
                            },
                            "status": {
                                "validation_rules": [
                                    ValidationRule(
                                        name="Status values",
                                        dimension="validity",
                                        severity=Severity.CRITICAL,
                                        rule_type="allowed_values",
                                        rule_expression="VALUE_IN"
                                    )
                                ]
                            }
                        }
                    },
                    "completeness": {
                        "weight": 4,
                        "field_requirements": {
                            "email": {
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
                }
            }
        }

        wrapper = BundledStandardWrapper(standard_dict)
        rules_by_field = wrapper.get_all_validation_rules()

        assert len(rules_by_field) == 2
        assert "email" in rules_by_field
        assert "status" in rules_by_field
        assert len(rules_by_field["email"]) == 2  # One from validity, one from completeness
        assert len(rules_by_field["status"]) == 1

    def test_get_all_validation_rules_empty_standard(self):
        """Test that empty standard returns empty dict."""
        standard_dict = {"requirements": {}}

        wrapper = BundledStandardWrapper(standard_dict)
        rules_by_field = wrapper.get_all_validation_rules()

        assert rules_by_field == {}

    def test_filter_rules_by_dimension(self):
        """Test filtering rules by dimension."""
        # Create a standard with rules in multiple dimensions
        validity_rule = ValidationRule(
            name="Type check",
            dimension="validity",
            severity=Severity.CRITICAL,
            rule_type="type",
            rule_expression="IS_STRING"
        )

        completeness_rule = ValidationRule(
            name="Not null",
            dimension="completeness",
            severity=Severity.CRITICAL,
            rule_type="not_null",
            rule_expression="IS_NOT_NULL"
        )

        consistency_rule = ValidationRule(
            name="Format check",
            dimension="consistency",
            severity=Severity.WARNING,
            rule_type="format",
            rule_expression="IS_LOWERCASE"
        )

        standard_dict = {
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 5,
                        "field_requirements": {
                            "email": {
                                "validation_rules": [validity_rule, completeness_rule]
                            }
                        }
                    },
                    "consistency": {
                        "weight": 3,
                        "field_requirements": {
                            "email": {
                                "validation_rules": [consistency_rule]
                            }
                        }
                    }
                }
            }
        }

        wrapper = BundledStandardWrapper(standard_dict)

        # Filter by validity dimension
        validity_rules = wrapper.filter_rules_by_dimension("validity")
        assert len(validity_rules) == 1
        assert validity_rules[0].dimension == "validity"

        # Filter by completeness dimension
        completeness_rules = wrapper.filter_rules_by_dimension("completeness")
        assert len(completeness_rules) == 1
        assert completeness_rules[0].dimension == "completeness"

        # Filter by consistency dimension
        consistency_rules = wrapper.filter_rules_by_dimension("consistency")
        assert len(consistency_rules) == 1
        assert consistency_rules[0].dimension == "consistency"

    def test_filter_rules_by_dimension_with_provided_list(self):
        """Test filtering a specific list of rules by dimension."""
        rule1 = ValidationRule(
            name="Rule 1",
            dimension="validity",
            severity=Severity.CRITICAL,
            rule_type="type",
            rule_expression="IS_STRING"
        )

        rule2 = ValidationRule(
            name="Rule 2",
            dimension="completeness",
            severity=Severity.CRITICAL,
            rule_type="not_null",
            rule_expression="IS_NOT_NULL"
        )

        rule3 = ValidationRule(
            name="Rule 3",
            dimension="validity",
            severity=Severity.WARNING,
            rule_type="pattern",
            rule_expression="REGEX"
        )

        standard_dict = {"requirements": {}}
        wrapper = BundledStandardWrapper(standard_dict)

        # Filter provided list
        all_rules = [rule1, rule2, rule3]
        validity_rules = wrapper.filter_rules_by_dimension("validity", all_rules)

        assert len(validity_rules) == 2
        assert all(r.dimension == "validity" for r in validity_rules)

    def test_filter_rules_by_severity_critical(self):
        """Test filtering rules by CRITICAL severity."""
        critical_rule1 = ValidationRule(
            name="Critical 1",
            dimension="validity",
            severity=Severity.CRITICAL,
            rule_type="type",
            rule_expression="IS_STRING"
        )

        critical_rule2 = ValidationRule(
            name="Critical 2",
            dimension="completeness",
            severity=Severity.CRITICAL,
            rule_type="not_null",
            rule_expression="IS_NOT_NULL"
        )

        warning_rule = ValidationRule(
            name="Warning",
            dimension="consistency",
            severity=Severity.WARNING,
            rule_type="format",
            rule_expression="IS_LOWERCASE"
        )

        standard_dict = {
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 5,
                        "field_requirements": {
                            "field1": {
                                "validation_rules": [critical_rule1, warning_rule]
                            }
                        }
                    },
                    "completeness": {
                        "weight": 4,
                        "field_requirements": {
                            "field1": {
                                "validation_rules": [critical_rule2]
                            }
                        }
                    }
                }
            }
        }

        wrapper = BundledStandardWrapper(standard_dict)
        critical_rules = wrapper.filter_rules_by_severity(Severity.CRITICAL)

        assert len(critical_rules) == 2
        assert all(r.severity == Severity.CRITICAL for r in critical_rules)
        assert all(r.should_penalize_score() for r in critical_rules)

    def test_filter_rules_by_severity_warning(self):
        """Test filtering rules by WARNING severity."""
        critical_rule = ValidationRule(
            name="Critical",
            dimension="validity",
            severity=Severity.CRITICAL,
            rule_type="type",
            rule_expression="IS_STRING"
        )

        warning_rule1 = ValidationRule(
            name="Warning 1",
            dimension="consistency",
            severity=Severity.WARNING,
            rule_type="format",
            rule_expression="IS_LOWERCASE"
        )

        warning_rule2 = ValidationRule(
            name="Warning 2",
            dimension="consistency",
            severity=Severity.WARNING,
            rule_type="case",
            rule_expression="IS_TITLE_CASE"
        )

        standard_dict = {
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 5,
                        "field_requirements": {
                            "field1": {
                                "validation_rules": [critical_rule]
                            }
                        }
                    },
                    "consistency": {
                        "weight": 3,
                        "field_requirements": {
                            "field1": {
                                "validation_rules": [warning_rule1, warning_rule2]
                            }
                        }
                    }
                }
            }
        }

        wrapper = BundledStandardWrapper(standard_dict)
        warning_rules = wrapper.filter_rules_by_severity(Severity.WARNING)

        assert len(warning_rules) == 2
        assert all(r.severity == Severity.WARNING for r in warning_rules)
        assert all(not r.should_penalize_score() for r in warning_rules)

    def test_filter_rules_by_severity_string_input(self):
        """Test filtering rules using string severity (not enum)."""
        rule1 = ValidationRule(
            name="Rule 1",
            dimension="validity",
            severity=Severity.CRITICAL,
            rule_type="type",
            rule_expression="IS_STRING"
        )

        rule2 = ValidationRule(
            name="Rule 2",
            dimension="consistency",
            severity=Severity.WARNING,
            rule_type="format",
            rule_expression="IS_LOWERCASE"
        )

        standard_dict = {
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 5,
                        "field_requirements": {
                            "field1": {
                                "validation_rules": [rule1, rule2]
                            }
                        }
                    }
                }
            }
        }

        wrapper = BundledStandardWrapper(standard_dict)

        # Test with string input (should auto-convert)
        critical_rules = wrapper.filter_rules_by_severity("CRITICAL")
        assert len(critical_rules) == 1
        assert critical_rules[0].severity == Severity.CRITICAL

        warning_rules = wrapper.filter_rules_by_severity("WARNING")
        assert len(warning_rules) == 1
        assert warning_rules[0].severity == Severity.WARNING

    def test_filter_rules_by_severity_with_provided_list(self):
        """Test filtering a specific list of rules by severity."""
        rule1 = ValidationRule(
            name="Critical",
            dimension="validity",
            severity=Severity.CRITICAL,
            rule_type="type",
            rule_expression="IS_STRING"
        )

        rule2 = ValidationRule(
            name="Warning",
            dimension="consistency",
            severity=Severity.WARNING,
            rule_type="format",
            rule_expression="IS_LOWERCASE"
        )

        rule3 = ValidationRule(
            name="Info",
            dimension="plausibility",
            severity=Severity.INFO,
            rule_type="outlier",
            rule_expression="Z_SCORE"
        )

        standard_dict = {"requirements": {}}
        wrapper = BundledStandardWrapper(standard_dict)

        # Filter provided list
        all_rules = [rule1, rule2, rule3]
        critical_rules = wrapper.filter_rules_by_severity(Severity.CRITICAL, all_rules)

        assert len(critical_rules) == 1
        assert critical_rules[0].name == "Critical"

    def test_filter_combined_dimension_and_severity(self):
        """Test combining dimension and severity filters."""
        rule1 = ValidationRule(
            name="Critical validity",
            dimension="validity",
            severity=Severity.CRITICAL,
            rule_type="type",
            rule_expression="IS_STRING"
        )

        rule2 = ValidationRule(
            name="Warning validity",
            dimension="validity",
            severity=Severity.WARNING,
            rule_type="pattern",
            rule_expression="REGEX"
        )

        rule3 = ValidationRule(
            name="Critical completeness",
            dimension="completeness",
            severity=Severity.CRITICAL,
            rule_type="not_null",
            rule_expression="IS_NOT_NULL"
        )

        standard_dict = {
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 5,
                        "field_requirements": {
                            "field1": {
                                "validation_rules": [rule1, rule2]
                            }
                        }
                    },
                    "completeness": {
                        "weight": 4,
                        "field_requirements": {
                            "field1": {
                                "validation_rules": [rule3]
                            }
                        }
                    }
                }
            }
        }

        wrapper = BundledStandardWrapper(standard_dict)

        # First filter by dimension, then by severity
        all_rules = []
        for field_rules in wrapper.get_all_validation_rules().values():
            all_rules.extend(field_rules)

        validity_rules = wrapper.filter_rules_by_dimension("validity", all_rules)
        critical_validity_rules = wrapper.filter_rules_by_severity(Severity.CRITICAL, validity_rules)

        assert len(critical_validity_rules) == 1
        assert critical_validity_rules[0].name == "Critical validity"
        assert critical_validity_rules[0].dimension == "validity"
        assert critical_validity_rules[0].severity == Severity.CRITICAL


class TestBundledStandardWrapperBackwardCompatibility:
    """Test that existing wrapper methods still work."""

    def test_get_field_requirements_still_works(self):
        """Test that old get_field_requirements() method still works."""
        standard_dict = {
            "requirements": {
                "field_requirements": {
                    "email": {
                        "type": "string",
                        "nullable": False
                    }
                }
            }
        }

        wrapper = BundledStandardWrapper(standard_dict)
        field_reqs = wrapper.get_field_requirements()

        assert "email" in field_reqs
        assert field_reqs["email"]["type"] == "string"

    def test_get_dimension_requirements_still_works(self):
        """Test that get_dimension_requirements() still works."""
        standard_dict = {
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 5,
                        "minimum_score": 15
                    }
                }
            }
        }

        wrapper = BundledStandardWrapper(standard_dict)
        dim_reqs = wrapper.get_dimension_requirements()

        assert "validity" in dim_reqs
        assert dim_reqs["validity"]["weight"] == 5

    def test_get_overall_minimum_still_works(self):
        """Test that get_overall_minimum() still works."""
        standard_dict = {
            "requirements": {
                "overall_minimum": 80
            }
        }

        wrapper = BundledStandardWrapper(standard_dict)
        minimum = wrapper.get_overall_minimum()

        assert minimum == 80.0
