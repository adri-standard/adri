"""Tests for ADRI Schema Diff Service.

Comprehensive test coverage for schema comparison, diff generation,
and impact classification.
"""

import pytest
from typing import Dict, Any

from src.adri.utils.schema_diff import (
    SchemaDiffService,
    ChangeType,
    ImpactLevel,
    SchemaChange,
    SchemaDiffResult,
    compare_schemas,
    format_diff_report,
    format_diff_markdown,
    format_diff_for_autotune
)


@pytest.fixture
def diff_service():
    """Create a SchemaDiffService instance."""
    return SchemaDiffService()


@pytest.fixture
def base_schema():
    """Basic schema for testing."""
    return {
        "requirements": {
            "field_requirements": {
                "customer_name": {
                    "type": "string",
                    "description": "Name of the customer",
                    "min_length": 1,
                    "max_length": 100
                },
                "age": {
                    "type": "integer",
                    "description": "Customer age in years",
                    "min_value": 0,
                    "max_value": 150
                },
                "email": {
                    "type": "string",
                    "description": "Customer email address",
                    "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
                }
            }
        }
    }


class TestSchemaDiffService:
    """Tests for SchemaDiffService class."""
    
    def test_initialization(self, diff_service):
        """Test service initialization."""
        assert isinstance(diff_service, SchemaDiffService)
        assert diff_service.STRUCTURAL_PROPERTIES
        assert diff_service.CONSTRAINT_PROPERTIES
        assert diff_service.VALIDATION_PROPERTIES
        assert diff_service.METADATA_PROPERTIES
    
    def test_extract_field_requirements_nested(self, diff_service):
        """Test extraction of field requirements from nested structure."""
        schema = {
            "requirements": {
                "field_requirements": {
                    "field1": {"type": "string"}
                }
            }
        }
        
        result = diff_service._extract_field_requirements(schema)
        assert "field1" in result
        assert result["field1"]["type"] == "string"
    
    def test_extract_field_requirements_flat(self, diff_service):
        """Test extraction of field requirements from flat structure."""
        schema = {
            "field_requirements": {
                "field1": {"type": "string"}
            }
        }
        
        result = diff_service._extract_field_requirements(schema)
        assert "field1" in result
    
    def test_extract_field_requirements_empty(self, diff_service):
        """Test extraction from empty schema."""
        result = diff_service._extract_field_requirements({})
        assert result == {}
        
        result = diff_service._extract_field_requirements(None)
        assert result == {}


class TestFieldChanges:
    """Tests for field addition, removal, and modification detection."""
    
    def test_detect_field_addition(self, diff_service, base_schema):
        """Test detection of field additions."""
        modified_schema = {
            "requirements": {
                "field_requirements": {
                    **base_schema["requirements"]["field_requirements"],
                    "phone": {
                        "type": "string",
                        "description": "Phone number"
                    }
                }
            }
        }
        
        result = diff_service.diff_dicts(base_schema, modified_schema)
        
        assert result.has_changes()
        assert result.non_breaking_changes_count == 1
        assert result.breaking_changes_count == 0
        
        added_changes = [c for c in result.changes if c.change_type == ChangeType.FIELD_ADDED]
        assert len(added_changes) == 1
        assert added_changes[0].field_name == "phone"
        assert added_changes[0].impact_level == ImpactLevel.NON_BREAKING
    
    def test_detect_field_removal(self, diff_service, base_schema):
        """Test detection of field removals."""
        modified_schema = {
            "requirements": {
                "field_requirements": {
                    "customer_name": base_schema["requirements"]["field_requirements"]["customer_name"],
                    "age": base_schema["requirements"]["field_requirements"]["age"]
                    # email removed
                }
            }
        }
        
        result = diff_service.diff_dicts(base_schema, modified_schema)
        
        assert result.has_changes()
        assert result.breaking_changes_count == 1
        assert result.has_breaking_changes()
        
        removed_changes = [c for c in result.changes if c.change_type == ChangeType.FIELD_REMOVED]
        assert len(removed_changes) == 1
        assert removed_changes[0].field_name == "email"
        assert removed_changes[0].impact_level == ImpactLevel.BREAKING
    
    def test_detect_multiple_field_changes(self, diff_service, base_schema):
        """Test detection of multiple simultaneous field changes."""
        modified_schema = {
            "requirements": {
                "field_requirements": {
                    "customer_name": base_schema["requirements"]["field_requirements"]["customer_name"],
                    # age removed
                    # email removed
                    "phone": {"type": "string", "description": "Phone number"},
                    "address": {"type": "string", "description": "Mailing address"}
                }
            }
        }
        
        result = diff_service.diff_dicts(base_schema, modified_schema)
        
        assert result.has_changes()
        assert len(result.changes) == 4  # 2 added, 2 removed
        
        added_count = sum(1 for c in result.changes if c.change_type == ChangeType.FIELD_ADDED)
        removed_count = sum(1 for c in result.changes if c.change_type == ChangeType.FIELD_REMOVED)
        
        assert added_count == 2
        assert removed_count == 2


class TestTypeChanges:
    """Tests for field type change detection."""
    
    def test_detect_type_change_breaking(self, diff_service, base_schema):
        """Test detection of breaking type changes."""
        modified_schema = {
            "requirements": {
                "field_requirements": {
                    **base_schema["requirements"]["field_requirements"],
                    "age": {
                        "type": "string",  # Changed from integer to string
                        "description": "Customer age in years"
                    }
                }
            }
        }
        
        result = diff_service.diff_dicts(base_schema, modified_schema)
        
        assert result.has_breaking_changes()
        
        type_changes = [c for c in result.changes if c.change_type == ChangeType.TYPE_CHANGED]
        assert len(type_changes) == 1
        assert type_changes[0].field_name == "age"
        assert type_changes[0].before_value == "integer"
        assert type_changes[0].after_value == "string"
        assert type_changes[0].impact_level == ImpactLevel.BREAKING


class TestConstraintChanges:
    """Tests for constraint change detection and impact classification."""
    
    def test_detect_constraint_tightening_breaking(self, diff_service, base_schema):
        """Test detection of constraint tightening (breaking change)."""
        modified_schema = {
            "requirements": {
                "field_requirements": {
                    **base_schema["requirements"]["field_requirements"],
                    "customer_name": {
                        "type": "string",
                        "description": "Name of the customer",
                        "min_length": 5,  # Increased from 1
                        "max_length": 100
                    }
                }
            }
        }
        
        result = diff_service.diff_dicts(base_schema, modified_schema)
        
        constraint_changes = [c for c in result.changes 
                            if c.change_type == ChangeType.CONSTRAINT_CHANGED
                            and c.field_name == "customer_name"]
        
        assert len(constraint_changes) > 0
        min_length_change = next(c for c in constraint_changes 
                                 if c.before_value == 1 and c.after_value == 5)
        assert min_length_change.impact_level == ImpactLevel.BREAKING
    
    def test_detect_constraint_relaxation_non_breaking(self, diff_service, base_schema):
        """Test detection of constraint relaxation (non-breaking change)."""
        modified_schema = {
            "requirements": {
                "field_requirements": {
                    **base_schema["requirements"]["field_requirements"],
                    "customer_name": {
                        "type": "string",
                        "description": "Name of the customer",
                        "min_length": 1,
                        "max_length": 200  # Increased from 100
                    }
                }
            }
        }
        
        result = diff_service.diff_dicts(base_schema, modified_schema)
        
        constraint_changes = [c for c in result.changes 
                            if c.change_type == ChangeType.CONSTRAINT_CHANGED
                            and c.field_name == "customer_name"]
        
        assert len(constraint_changes) > 0
        max_length_change = next(c for c in constraint_changes 
                                 if c.before_value == 100 and c.after_value == 200)
        assert max_length_change.impact_level == ImpactLevel.NON_BREAKING
    
    def test_detect_constraint_removal_non_breaking(self, diff_service, base_schema):
        """Test detection of constraint removal (non-breaking change)."""
        modified_schema = {
            "requirements": {
                "field_requirements": {
                    **base_schema["requirements"]["field_requirements"],
                    "customer_name": {
                        "type": "string",
                        "description": "Name of the customer",
                        # min_length and max_length removed
                    }
                }
            }
        }
        
        result = diff_service.diff_dicts(base_schema, modified_schema)
        
        constraint_changes = [c for c in result.changes 
                            if c.change_type == ChangeType.CONSTRAINT_CHANGED
                            and c.field_name == "customer_name"]
        
        assert len(constraint_changes) == 2  # min_length and max_length
        for change in constraint_changes:
            assert change.after_value is None
            assert change.impact_level == ImpactLevel.NON_BREAKING
    
    def test_detect_constraint_addition_breaking(self, diff_service):
        """Test detection of constraint addition (breaking change)."""
        source_schema = {
            "requirements": {
                "field_requirements": {
                    "score": {
                        "type": "integer",
                        "description": "Score value"
                    }
                }
            }
        }
        
        target_schema = {
            "requirements": {
                "field_requirements": {
                    "score": {
                        "type": "integer",
                        "description": "Score value",
                        "min_value": 0,  # Added constraint
                        "max_value": 100  # Added constraint
                    }
                }
            }
        }
        
        service = SchemaDiffService()
        result = service.diff_dicts(source_schema, target_schema)
        
        constraint_changes = [c for c in result.changes 
                            if c.change_type == ChangeType.CONSTRAINT_CHANGED]
        
        assert len(constraint_changes) == 2
        for change in constraint_changes:
            assert change.before_value is None
            assert change.after_value is not None
            assert change.impact_level == ImpactLevel.BREAKING


class TestValidationRuleChanges:
    """Tests for validation rule change detection."""
    
    def test_detect_validation_rule_addition(self, diff_service):
        """Test detection of validation rule additions."""
        source_schema = {
            "field_requirements": {
                "email": {
                    "type": "string",
                    "description": "Email address"
                }
            }
        }
        
        target_schema = {
            "field_requirements": {
                "email": {
                    "type": "string",
                    "description": "Email address",
                    "validation_rules": [
                        {
                            "name": "valid_email",
                            "code": "contains(@, email)"
                        }
                    ]
                }
            }
        }
        
        result = diff_service.diff_dicts(source_schema, target_schema)
        
        rule_changes = [c for c in result.changes 
                       if c.change_type == ChangeType.VALIDATION_RULE_ADDED]
        
        assert len(rule_changes) == 1
        assert rule_changes[0].field_name == "email"
        assert rule_changes[0].impact_level == ImpactLevel.BREAKING
    
    def test_detect_validation_rule_removal(self, diff_service):
        """Test detection of validation rule removals."""
        source_schema = {
            "field_requirements": {
                "email": {
                    "type": "string",
                    "description": "Email address",
                    "validation_rules": [
                        {
                            "name": "valid_email",
                            "code": "contains(@, email)"
                        }
                    ]
                }
            }
        }
        
        target_schema = {
            "field_requirements": {
                "email": {
                    "type": "string",
                    "description": "Email address"
                }
            }
        }
        
        result = diff_service.diff_dicts(source_schema, target_schema)
        
        rule_changes = [c for c in result.changes 
                       if c.change_type == ChangeType.VALIDATION_RULE_REMOVED]
        
        assert len(rule_changes) == 1
        assert rule_changes[0].field_name == "email"
        assert rule_changes[0].impact_level == ImpactLevel.NON_BREAKING


class TestDescriptionChanges:
    """Tests for description and metadata change detection."""
    
    def test_detect_description_change_clarification(self, diff_service, base_schema):
        """Test detection of description changes (clarification)."""
        modified_schema = {
            "requirements": {
                "field_requirements": {
                    **base_schema["requirements"]["field_requirements"],
                    "age": {
                        "type": "integer",
                        "description": "Customer age in years (must be accurate)",  # Updated description
                        "min_value": 0,
                        "max_value": 150
                    }
                }
            }
        }
        
        result = diff_service.diff_dicts(base_schema, modified_schema)
        
        desc_changes = [c for c in result.changes 
                       if c.change_type == ChangeType.DESCRIPTION_CHANGED]
        
        assert len(desc_changes) == 1
        assert desc_changes[0].field_name == "age"
        assert desc_changes[0].impact_level == ImpactLevel.CLARIFICATION
    
    def test_detect_metadata_changes(self, diff_service):
        """Test detection of other metadata changes."""
        source_schema = {
            "field_requirements": {
                "price": {
                    "type": "float",
                    "description": "Product price",
                    "default": 0.0
                }
            }
        }
        
        target_schema = {
            "field_requirements": {
                "price": {
                    "type": "float",
                    "description": "Product price",
                    "default": 10.0,  # Changed default
                    "examples": [9.99, 19.99]  # Added examples
                }
            }
        }
        
        result = diff_service.diff_dicts(source_schema, target_schema)
        
        metadata_changes = [c for c in result.changes 
                          if c.change_type == ChangeType.METADATA_CHANGED]
        
        assert len(metadata_changes) == 1
        assert metadata_changes[0].impact_level == ImpactLevel.CLARIFICATION


class TestImpactClassification:
    """Tests for impact level classification logic."""
    
    def test_classify_constraint_min_increase_breaking(self, diff_service):
        """Test that increasing min constraints is breaking."""
        impact = diff_service._classify_constraint_change_impact(
            "min_value", 0, 10
        )
        assert impact == ImpactLevel.BREAKING
    
    def test_classify_constraint_min_decrease_non_breaking(self, diff_service):
        """Test that decreasing min constraints is non-breaking."""
        impact = diff_service._classify_constraint_change_impact(
            "min_value", 10, 0
        )
        assert impact == ImpactLevel.NON_BREAKING
    
    def test_classify_constraint_max_decrease_breaking(self, diff_service):
        """Test that decreasing max constraints is breaking."""
        impact = diff_service._classify_constraint_change_impact(
            "max_value", 100, 50
        )
        assert impact == ImpactLevel.BREAKING
    
    def test_classify_constraint_max_increase_non_breaking(self, diff_service):
        """Test that increasing max constraints is non-breaking."""
        impact = diff_service._classify_constraint_change_impact(
            "max_value", 50, 100
        )
        assert impact == ImpactLevel.NON_BREAKING
    
    def test_classify_pattern_change_breaking(self, diff_service):
        """Test that pattern changes are always breaking."""
        impact = diff_service._classify_constraint_change_impact(
            "pattern", "^[a-z]+$", "^[A-Z]+$"
        )
        assert impact == ImpactLevel.BREAKING


class TestDiffReporting:
    """Tests for diff report generation."""
    
    def test_format_diff_report_text(self, diff_service, base_schema):
        """Test text format diff report generation."""
        modified_schema = {
            "requirements": {
                "field_requirements": {
                    "customer_name": base_schema["requirements"]["field_requirements"]["customer_name"],
                    "phone": {"type": "string", "description": "Phone number"}
                    # age and email removed
                }
            }
        }
        
        result = diff_service.diff_dicts(base_schema, modified_schema)
        report = format_diff_report(result)
        
        assert "ADRI Schema Diff" in report
        assert "BREAKING CHANGES" in report
        assert "NON-BREAKING CHANGES" in report
        assert "age" in report
        assert "email" in report
        assert "phone" in report
    
    def test_format_diff_markdown(self, diff_service, base_schema):
        """Test Markdown format diff report generation."""
        modified_schema = {
            "requirements": {
                "field_requirements": {
                    "customer_name": base_schema["requirements"]["field_requirements"]["customer_name"],
                    "phone": {"type": "string", "description": "Phone number"}
                }
            }
        }
        
        result = diff_service.diff_dicts(base_schema, modified_schema)
        report = format_diff_markdown(result)
        
        assert "# ADRI Schema Diff" in report
        assert "## ⚠️  Breaking Changes" in report
        assert "## ✅ Non-Breaking Changes" in report
    
    def test_format_diff_for_autotune(self, diff_service, base_schema):
        """Test autotune format diff report generation."""
        modified_schema = {
            "requirements": {
                "field_requirements": {
                    "customer_name": base_schema["requirements"]["field_requirements"]["customer_name"],
                    "phone": {"type": "string", "description": "Phone number"}
                }
            }
        }
        
        result = diff_service.diff_dicts(base_schema, modified_schema)
        report = format_diff_for_autotune(result)
        
        assert "Schema Changes" in report
        assert "Breaking:" in report or "Non-breaking:" in report
        assert result.source_version in report
        assert result.target_version in report
    
    def test_format_diff_no_changes(self, diff_service, base_schema):
        """Test diff report when no changes exist."""
        result = diff_service.diff_dicts(base_schema, base_schema)
        
        assert not result.has_changes()
        
        report = format_diff_report(result)
        assert "No changes detected" in report
        
        autotune_report = format_diff_for_autotune(result)
        assert "No schema changes" in autotune_report


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_compare_schemas_convenience_function(self, base_schema):
        """Test the compare_schemas convenience function."""
        modified_schema = {
            "requirements": {
                "field_requirements": {
                    **base_schema["requirements"]["field_requirements"],
                    "phone": {"type": "string", "description": "Phone"}
                }
            }
        }
        
        result = compare_schemas(
            base_schema,
            modified_schema,
            source_version="original",
            target_version="updated"
        )
        
        assert isinstance(result, SchemaDiffResult)
        assert result.source_version == "original"
        assert result.target_version == "updated"
        assert result.has_changes()


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_schemas(self, diff_service):
        """Test comparison of empty schemas."""
        result = diff_service.diff_dicts({}, {})
        
        assert not result.has_changes()
        assert len(result.changes) == 0
    
    def test_malformed_field_spec(self, diff_service):
        """Test handling of malformed field specifications."""
        source_schema = {
            "field_requirements": {
                "field1": None  # Malformed
            }
        }
        
        target_schema = {
            "field_requirements": {
                "field1": {"type": "string"}
            }
        }
        
        # Should not crash
        result = diff_service.diff_dicts(source_schema, target_schema)
        assert isinstance(result, SchemaDiffResult)
    
    def test_nested_field_changes(self, diff_service):
        """Test detection of changes in nested structures."""
        source_schema = {
            "field_requirements": {
                "address": {
                    "type": "array",
                    "description": "Address components",
                    "items": {
                        "type": "string"
                    }
                }
            }
        }
        
        target_schema = {
            "field_requirements": {
                "address": {
                    "type": "array",
                    "description": "Address components",
                    "items": {
                        "type": "string"
                    },
                    "min_items": 1  # Added constraint
                }
            }
        }
        
        result = diff_service.diff_dicts(source_schema, target_schema)
        
        constraint_changes = [c for c in result.changes 
                            if c.change_type == ChangeType.CONSTRAINT_CHANGED]
        assert len(constraint_changes) == 1


class TestSchemaDiffResult:
    """Tests for SchemaDiffResult data class."""
    
    def test_has_breaking_changes(self):
        """Test has_breaking_changes method."""
        result = SchemaDiffResult(
            source_version="v1",
            target_version="v2",
            changes=[],
            breaking_changes_count=1,
            non_breaking_changes_count=0,
            clarification_changes_count=0,
            summary="Test"
        )
        
        assert result.has_breaking_changes()
    
    def test_get_changes_by_impact(self):
        """Test get_changes_by_impact method."""
        changes = [
            SchemaChange(
                change_type=ChangeType.FIELD_ADDED,
                field_name="field1",
                impact_level=ImpactLevel.NON_BREAKING,
                before_value=None,
                after_value={"type": "string"},
                description="Field added"
            ),
            SchemaChange(
                change_type=ChangeType.FIELD_REMOVED,
                field_name="field2",
                impact_level=ImpactLevel.BREAKING,
                before_value={"type": "string"},
                after_value=None,
                description="Field removed"
            )
        ]
        
        result = SchemaDiffResult(
            source_version="v1",
            target_version="v2",
            changes=changes,
            breaking_changes_count=1,
            non_breaking_changes_count=1,
            clarification_changes_count=0,
            summary="Test"
        )
        
        breaking = result.get_changes_by_impact(ImpactLevel.BREAKING)
        assert len(breaking) == 1
        assert breaking[0].field_name == "field2"
        
        non_breaking = result.get_changes_by_impact(ImpactLevel.NON_BREAKING)
        assert len(non_breaking) == 1
        assert non_breaking[0].field_name == "field1"
    
    def test_to_dict_serialization(self):
        """Test to_dict serialization method."""
        changes = [
            SchemaChange(
                change_type=ChangeType.FIELD_ADDED,
                field_name="field1",
                impact_level=ImpactLevel.NON_BREAKING,
                before_value=None,
                after_value={"type": "string"},
                description="Field added",
                remediation="No action needed"
            )
        ]
        
        result = SchemaDiffResult(
            source_version="v1",
            target_version="v2",
            changes=changes,
            breaking_changes_count=0,
            non_breaking_changes_count=1,
            clarification_changes_count=0,
            summary="Test summary"
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["source_version"] == "v1"
        assert result_dict["target_version"] == "v2"
        assert result_dict["total_changes"] == 1
        assert result_dict["breaking_changes_count"] == 0
        assert result_dict["non_breaking_changes_count"] == 1
        assert len(result_dict["changes"]) == 1
        assert result_dict["changes"][0]["field_name"] == "field1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
