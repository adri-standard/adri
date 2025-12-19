"""
Tests for enhanced allowed_values with derivation rules.

This test suite validates:
- Backward compatibility with simple list format
- Enhanced dict format with category definitions
- Derivation rule structure and validation
- Schema validation integration
"""

import pytest
from src.adri.contracts.derivation import (
    DerivationRule,
    CategoryDefinition,
    validate_enhanced_allowed_values,
    get_category_values,
    get_categories_by_precedence,
)
from src.adri.contracts.schema import StandardSchema


class TestDerivationRule:
    """Test DerivationRule dataclass."""

    def test_create_valid_derivation_rule(self):
        """Test creating a valid derivation rule."""
        rule = DerivationRule(
            type="ordered_conditions",
            inputs=["project_status", "priority_order"],
            logic="IF project_status = 'At Risk' AND priority_order = 1 THEN 'Critical'"
        )
        
        assert rule.type == "ordered_conditions"
        assert rule.inputs == ["project_status", "priority_order"]
        assert "At Risk" in rule.logic
        assert rule.metadata is None

    def test_derivation_rule_with_metadata(self):
        """Test derivation rule with optional metadata."""
        rule = DerivationRule(
            type="formula",
            inputs=["field1", "field2"],
            logic="field1 + field2 > 100",
            metadata={"description": "Sum threshold check"}
        )
        
        assert rule.metadata["description"] == "Sum threshold check"

    def test_derivation_rule_validation_empty_type(self):
        """Test that empty type raises validation error."""
        with pytest.raises(ValueError, match="type cannot be empty"):
            DerivationRule(
                type="",
                inputs=["field1"],
                logic="some logic"
            )

    def test_derivation_rule_validation_invalid_inputs(self):
        """Test that non-list inputs raises validation error."""
        with pytest.raises(ValueError, match="inputs must be a list"):
            DerivationRule(
                type="test",
                inputs="not a list",  # type: ignore
                logic="some logic"
            )

    def test_derivation_rule_validation_empty_logic(self):
        """Test that empty logic raises validation error."""
        with pytest.raises(ValueError, match="logic cannot be empty"):
            DerivationRule(
                type="test",
                inputs=["field1"],
                logic=""
            )

    def test_derivation_rule_to_dict(self):
        """Test converting derivation rule to dict."""
        rule = DerivationRule(
            type="ordered_conditions",
            inputs=["status", "priority"],
            logic="IF status = 'High'",
            metadata={"version": "1.0"}
        )
        
        rule_dict = rule.to_dict()
        
        assert rule_dict["type"] == "ordered_conditions"
        assert rule_dict["inputs"] == ["status", "priority"]
        assert rule_dict["logic"] == "IF status = 'High'"
        assert rule_dict["metadata"]["version"] == "1.0"

    def test_derivation_rule_from_dict(self):
        """Test creating derivation rule from dict."""
        rule_dict = {
            "type": "formula",
            "inputs": ["field1", "field2"],
            "logic": "field1 > field2",
            "metadata": {"test": "data"}
        }
        
        rule = DerivationRule.from_dict(rule_dict)
        
        assert rule.type == "formula"
        assert rule.inputs == ["field1", "field2"]
        assert rule.logic == "field1 > field2"
        assert rule.metadata == {"test": "data"}


class TestCategoryDefinition:
    """Test CategoryDefinition dataclass."""

    def test_create_valid_category_definition(self):
        """Test creating a valid category definition."""
        cat_def = CategoryDefinition(
            definition="High priority items requiring immediate attention",
            precedence=1
        )
        
        assert cat_def.definition == "High priority items requiring immediate attention"
        assert cat_def.precedence == 1
        assert cat_def.derivation_rule is None
        assert cat_def.examples is None

    def test_category_definition_with_derivation_rule(self):
        """Test category definition with derivation rule."""
        rule = DerivationRule(
            type="ordered_conditions",
            inputs=["status"],
            logic="IF status = 'Critical'"
        )
        
        cat_def = CategoryDefinition(
            definition="Critical issues",
            precedence=1,
            derivation_rule=rule,
            examples=["System down", "Data loss"]
        )
        
        assert cat_def.derivation_rule == rule
        assert len(cat_def.examples) == 2

    def test_category_definition_validation_empty_definition(self):
        """Test that empty definition raises validation error."""
        with pytest.raises(ValueError, match="definition cannot be empty"):
            CategoryDefinition(
                definition="",
                precedence=1
            )

    def test_category_definition_validation_invalid_precedence_type(self):
        """Test that non-integer precedence raises validation error."""
        with pytest.raises(ValueError, match="precedence must be an integer"):
            CategoryDefinition(
                definition="Test",
                precedence="1"  # type: ignore
            )

    def test_category_definition_validation_negative_precedence(self):
        """Test that negative precedence raises validation error."""
        with pytest.raises(ValueError, match="precedence must be >= 1"):
            CategoryDefinition(
                definition="Test",
                precedence=0
            )

    def test_category_definition_to_dict(self):
        """Test converting category definition to dict."""
        rule = DerivationRule(
            type="test",
            inputs=["f1"],
            logic="test"
        )
        
        cat_def = CategoryDefinition(
            definition="Test category",
            precedence=2,
            derivation_rule=rule,
            examples=["ex1", "ex2"],
            metadata={"key": "value"}
        )
        
        cat_dict = cat_def.to_dict()
        
        assert cat_dict["definition"] == "Test category"
        assert cat_dict["precedence"] == 2
        assert "derivation_rule" in cat_dict
        assert cat_dict["examples"] == ["ex1", "ex2"]
        assert cat_dict["metadata"]["key"] == "value"

    def test_category_definition_from_dict(self):
        """Test creating category definition from dict."""
        cat_dict = {
            "definition": "High priority",
            "precedence": 1,
            "derivation_rule": {
                "type": "ordered_conditions",
                "inputs": ["priority"],
                "logic": "priority = 1"
            },
            "examples": ["Critical bug"],
            "metadata": {"severity": "high"}
        }
        
        cat_def = CategoryDefinition.from_dict(cat_dict)
        
        assert cat_def.definition == "High priority"
        assert cat_def.precedence == 1
        assert cat_def.derivation_rule is not None
        assert cat_def.derivation_rule.type == "ordered_conditions"
        assert cat_def.examples == ["Critical bug"]
        assert cat_def.metadata["severity"] == "high"


class TestEnhancedAllowedValuesValidation:
    """Test validation of enhanced allowed_values structures."""

    def test_validate_simple_list_format(self):
        """Test validation of simple list format (backward compatible)."""
        allowed_values = ["High", "Medium", "Low"]
        errors = validate_enhanced_allowed_values(allowed_values, "RISK_LEVEL")
        
        assert len(errors) == 0

    def test_validate_empty_list(self):
        """Test validation rejects empty list."""
        allowed_values = []
        errors = validate_enhanced_allowed_values(allowed_values, "FIELD1")
        
        assert len(errors) == 1
        assert "empty" in errors[0].lower()

    def test_validate_enhanced_dict_format(self):
        """Test validation of enhanced dict format."""
        allowed_values = {
            "Critical": {
                "definition": "Highest priority",
                "precedence": 1,
                "derivation_rule": {
                    "type": "ordered_conditions",
                    "inputs": ["status"],
                    "logic": "status = 'Critical'"
                }
            },
            "High": {
                "definition": "High priority",
                "precedence": 2
            }
        }
        
        errors = validate_enhanced_allowed_values(allowed_values, "RISK_LEVEL")
        
        assert len(errors) == 0

    def test_validate_missing_definition(self):
        """Test validation catches missing definition."""
        allowed_values = {
            "High": {
                "precedence": 1
                # Missing definition
            }
        }
        
        errors = validate_enhanced_allowed_values(allowed_values, "FIELD1")
        
        assert len(errors) == 1
        assert "definition" in errors[0].lower()

    def test_validate_missing_precedence(self):
        """Test validation catches missing precedence."""
        allowed_values = {
            "High": {
                "definition": "High priority item"
                # Missing precedence
            }
        }
        
        errors = validate_enhanced_allowed_values(allowed_values, "FIELD1")
        
        assert len(errors) == 1
        assert "precedence" in errors[0].lower()

    def test_validate_duplicate_precedence(self):
        """Test validation catches duplicate precedence values."""
        allowed_values = {
            "High": {
                "definition": "High priority",
                "precedence": 1
            },
            "Critical": {
                "definition": "Critical priority",
                "precedence": 1  # Duplicate!
            }
        }
        
        errors = validate_enhanced_allowed_values(allowed_values, "FIELD1")
        
        assert len(errors) == 1
        assert "duplicate precedence" in errors[0].lower()

    def test_validate_invalid_precedence_type(self):
        """Test validation catches invalid precedence type."""
        allowed_values = {
            "High": {
                "definition": "High priority",
                "precedence": "1"  # Should be int
            }
        }
        
        errors = validate_enhanced_allowed_values(allowed_values, "FIELD1")
        
        assert len(errors) == 1
        assert "integer" in errors[0].lower()

    def test_validate_negative_precedence(self):
        """Test validation catches negative precedence."""
        allowed_values = {
            "High": {
                "definition": "High priority",
                "precedence": 0  # Must be >= 1
            }
        }
        
        errors = validate_enhanced_allowed_values(allowed_values, "FIELD1")
        
        assert len(errors) == 1
        assert ">= 1" in errors[0]

    def test_validate_derivation_rule_structure(self):
        """Test validation of derivation rule structure."""
        allowed_values = {
            "High": {
                "definition": "High priority",
                "precedence": 1,
                "derivation_rule": {
                    "type": "ordered_conditions",
                    "inputs": ["status"],
                    "logic": "status = 'High'"
                }
            }
        }
        
        errors = validate_enhanced_allowed_values(allowed_values, "FIELD1")
        
        assert len(errors) == 0

    def test_validate_incomplete_derivation_rule(self):
        """Test validation catches incomplete derivation rule."""
        allowed_values = {
            "High": {
                "definition": "High priority",
                "precedence": 1,
                "derivation_rule": {
                    "type": "ordered_conditions"
                    # Missing inputs and logic
                }
            }
        }
        
        errors = validate_enhanced_allowed_values(allowed_values, "FIELD1")
        
        assert len(errors) >= 2  # Should catch missing inputs and logic


class TestUtilityFunctions:
    """Test utility functions for working with enhanced allowed_values."""

    def test_get_category_values_from_list(self):
        """Test extracting values from simple list format."""
        allowed_values = ["High", "Medium", "Low"]
        values = get_category_values(allowed_values)
        
        assert values == ["High", "Medium", "Low"]

    def test_get_category_values_from_dict(self):
        """Test extracting values from enhanced dict format."""
        allowed_values = {
            "Critical": {"definition": "...", "precedence": 1},
            "High": {"definition": "...", "precedence": 2},
            "Low": {"definition": "...", "precedence": 3}
        }
        values = get_category_values(allowed_values)
        
        assert set(values) == {"Critical", "High", "Low"}

    def test_get_category_values_invalid_type(self):
        """Test extracting values from invalid type returns empty list."""
        allowed_values = "not a list or dict"  # type: ignore
        values = get_category_values(allowed_values)
        
        assert values == []

    def test_get_categories_by_precedence(self):
        """Test getting categories sorted by precedence."""
        allowed_values = {
            "Low": {"definition": "Low priority", "precedence": 3},
            "Critical": {"definition": "Critical priority", "precedence": 1},
            "High": {"definition": "High priority", "precedence": 2}
        }
        
        categories = get_categories_by_precedence(allowed_values)
        
        assert len(categories) == 3
        assert categories[0][0] == "Critical"
        assert categories[0][1].precedence == 1
        assert categories[1][0] == "High"
        assert categories[1][1].precedence == 2
        assert categories[2][0] == "Low"
        assert categories[2][1].precedence == 3

    def test_get_categories_by_precedence_with_derivation_rules(self):
        """Test getting categories with derivation rules."""
        allowed_values = {
            "High": {
                "definition": "High priority",
                "precedence": 1,
                "derivation_rule": {
                    "type": "ordered_conditions",
                    "inputs": ["priority"],
                    "logic": "priority = 1"
                }
            },
            "Low": {
                "definition": "Low priority",
                "precedence": 2
            }
        }
        
        categories = get_categories_by_precedence(allowed_values)
        
        assert len(categories) == 2
        assert categories[0][1].derivation_rule is not None
        assert categories[1][1].derivation_rule is None


class TestSchemaIntegration:
    """Test integration with StandardSchema validation."""

    def test_schema_validates_simple_allowed_values(self):
        """Test schema validation accepts simple allowed_values."""
        field_req = {
            "type": "string",
            "allowed_values": ["High", "Medium", "Low"]
        }
        
        errors = StandardSchema.validate_field_requirement(
            "RISK_LEVEL", field_req, "requirements.field_requirements"
        )
        
        assert len(errors) == 0

    def test_schema_validates_enhanced_allowed_values(self):
        """Test schema validation accepts enhanced allowed_values."""
        field_req = {
            "type": "string",
            "is_derived": True,
            "allowed_values": {
                "High": {
                    "definition": "High priority items",
                    "precedence": 1,
                    "derivation_rule": {
                        "type": "ordered_conditions",
                        "inputs": ["priority"],
                        "logic": "priority = 1"
                    }
                },
                "Low": {
                    "definition": "Low priority items",
                    "precedence": 2
                }
            }
        }
        
        errors = StandardSchema.validate_field_requirement(
            "RISK_LEVEL", field_req, "requirements.field_requirements"
        )
        
        assert len(errors) == 0

    def test_schema_rejects_is_derived_without_allowed_values(self):
        """Test schema rejects is_derived flag without allowed_values."""
        field_req = {
            "type": "string",
            "is_derived": True
            # Missing allowed_values
        }
        
        errors = StandardSchema.validate_field_requirement(
            "FIELD1", field_req, "requirements.field_requirements"
        )
        
        assert len(errors) == 1
        assert "is_derived=true" in errors[0]
        assert "no allowed_values" in errors[0]

    def test_schema_rejects_is_derived_with_simple_list(self):
        """Test schema rejects is_derived with simple list format."""
        field_req = {
            "type": "string",
            "is_derived": True,
            "allowed_values": ["High", "Low"]  # Simple list not allowed for derived
        }
        
        errors = StandardSchema.validate_field_requirement(
            "FIELD1", field_req, "requirements.field_requirements"
        )
        
        assert len(errors) == 1
        assert "is_derived=true" in errors[0]
        assert "simple list format" in errors[0]

    def test_get_allowed_values_as_list_utility(self):
        """Test StandardSchema utility to extract values as list."""
        # Test simple list
        values1 = StandardSchema.get_allowed_values_as_list(["High", "Low"])
        assert values1 == ["High", "Low"]
        
        # Test enhanced dict
        values2 = StandardSchema.get_allowed_values_as_list({
            "High": {"definition": "...", "precedence": 1},
            "Low": {"definition": "...", "precedence": 2}
        })
        assert set(values2) == {"High", "Low"}


class TestRoadmapUseCase:
    """Test real-world use case from roadmap playbook."""

    def test_risk_level_enhanced_definition(self):
        """Test RISK_LEVEL with enhanced allowed_values matching roadmap use case."""
        field_req = {
            "type": "string",
            "is_derived": True,
            "allowed_values": {
                "Critical": {
                    "definition": "Regulatory/compliance risk with execution challenges",
                    "precedence": 1,
                    "derivation_rule": {
                        "type": "ordered_conditions",
                        "inputs": ["project_status", "priority_order"],
                        "logic": "IF project_status = 'At Risk' AND priority_order = 1"
                    }
                },
                "High": {
                    "definition": "Highest priority OR at risk project",
                    "precedence": 2,
                    "derivation_rule": {
                        "type": "ordered_conditions",
                        "inputs": ["priority_order", "project_status"],
                        "logic": "IF priority_order = 1 OR project_status = 'At Risk'"
                    }
                },
                "Medium": {
                    "definition": "Active project not in top priority or at risk",
                    "precedence": 3,
                    "derivation_rule": {
                        "type": "ordered_conditions",
                        "inputs": ["project_status"],
                        "logic": "IF project_status = 'Active'"
                    }
                },
                "Low": {
                    "definition": "Default category for other statuses",
                    "precedence": 4,
                    "derivation_rule": {
                        "type": "ordered_conditions",
                        "inputs": [],
                        "logic": "DEFAULT"
                    }
                }
            }
        }
        
        # Validate the structure
        errors = StandardSchema.validate_field_requirement(
            "RISK_LEVEL", field_req, "requirements.field_requirements"
        )
        
        assert len(errors) == 0
        
        # Verify we can extract values
        values = get_category_values(field_req["allowed_values"])
        assert set(values) == {"Critical", "High", "Medium", "Low"}
        
        # Verify precedence order
        categories = get_categories_by_precedence(field_req["allowed_values"])
        assert categories[0][0] == "Critical"
        assert categories[1][0] == "High"
        assert categories[2][0] == "Medium"
        assert categories[3][0] == "Low"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
