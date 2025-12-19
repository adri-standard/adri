"""Tests for ADRI Schema Consistency Validator."""

import pytest
from adri.utils.schema_consistency_validator import (
    SchemaConsistencyValidator,
    validate_schema_consistency,
    ConsistencyIssueType,
    ConsistencyIssueSeverity,
    SQL_RESERVED_WORDS
)


class TestSchemaConsistencyValidator:
    """Test suite for ADRI schema consistency validation."""
    
    def test_valid_schema_no_issues(self):
        """Test that valid schema passes without issues."""
        adri_spec = {
            "field_requirements": {
                "customer_name": {
                    "type": "string",
                    "description": "Customer full name"
                },
                "age": {
                    "type": "integer",
                    "min_value": 0,
                    "max_value": 120,
                    "description": "Customer age in years"
                }
            }
        }
        
        validator = SchemaConsistencyValidator()
        report = validator.validate(adri_spec)
        
        assert report.is_valid
        assert report.total_fields == 2
        assert report.issues_found == 0
        assert not report.has_critical_issues()
        assert not report.has_errors()
    
    def test_type_description_conflict_array(self):
        """Test detection of type/description conflict (string vs array)."""
        adri_spec = {
            "field_requirements": {
                "risk_factors": {
                    "type": "string",
                    "description": "JSON array of risk factors"
                }
            }
        }
        
        validator = SchemaConsistencyValidator()
        report = validator.validate(adri_spec)
        
        assert not report.is_valid or report.has_errors()
        assert report.issues_found > 0
        
        # Find the type conflict issue
        type_conflicts = [
            i for i in report.issues 
            if i.type == ConsistencyIssueType.TYPE_DESCRIPTION_CONFLICT
        ]
        assert len(type_conflicts) == 1
        assert type_conflicts[0].severity == ConsistencyIssueSeverity.ERROR
        assert "array" in type_conflicts[0].message.lower()
    
    def test_type_description_conflict_integer(self):
        """Test detection of type/description conflict (string vs integer)."""
        adri_spec = {
            "field_requirements": {
                "count_value": {
                    "type": "string",
                    "description": "Count of items (integer value)"
                }
            }
        }
        
        validator = SchemaConsistencyValidator()
        report = validator.validate(adri_spec)
        
        type_conflicts = [
            i for i in report.issues
            if i.type == ConsistencyIssueType.TYPE_DESCRIPTION_CONFLICT
        ]
        assert len(type_conflicts) > 0
        assert "integer" in type_conflicts[0].message.lower()
    
    def test_sql_reserved_word_warning(self):
        """Test detection of SQL reserved word in field name."""
        adri_spec = {
            "field_requirements": {
                "SELECT": {
                    "type": "string",
                    "description": "Selection criteria"
                }
            }
        }
        
        validator = SchemaConsistencyValidator(strict_mode=False)
        report = validator.validate(adri_spec)
        
        sql_issues = [
            i for i in report.issues
            if i.type == ConsistencyIssueType.SQL_RESERVED_WORD
        ]
        assert len(sql_issues) == 1
        assert sql_issues[0].severity == ConsistencyIssueSeverity.WARNING
        assert "SQL reserved word" in sql_issues[0].message
    
    def test_sql_reserved_word_error_strict_mode(self):
        """Test SQL reserved word escalated to ERROR in strict mode."""
        adri_spec = {
            "field_requirements": {
                "ORDER": {
                    "type": "string",
                    "description": "Order details"
                }
            }
        }
        
        validator = SchemaConsistencyValidator(strict_mode=True)
        report = validator.validate(adri_spec)
        
        sql_issues = [
            i for i in report.issues
            if i.type == ConsistencyIssueType.SQL_RESERVED_WORD
        ]
        assert len(sql_issues) == 1
        assert sql_issues[0].severity == ConsistencyIssueSeverity.ERROR
    
    def test_sql_reserved_word_case_insensitive(self):
        """Test SQL reserved word detection is case-insensitive."""
        adri_spec = {
            "field_requirements": {
                "select": {
                    "type": "string",
                    "description": "Selection"
                },
                "Select": {
                    "type": "string",
                    "description": "Selection"
                }
            }
        }
        
        validator = SchemaConsistencyValidator()
        report = validator.validate(adri_spec)
        
        sql_issues = [
            i for i in report.issues
            if i.type == ConsistencyIssueType.SQL_RESERVED_WORD
        ]
        assert len(sql_issues) == 2  # Both variants detected
    
    def test_missing_type_critical(self):
        """Test that missing type is CRITICAL severity."""
        adri_spec = {
            "field_requirements": {
                "bad_field": {
                    "description": "Missing type attribute"
                }
            }
        }
        
        validator = SchemaConsistencyValidator()
        report = validator.validate(adri_spec)
        
        assert report.has_critical_issues()
        
        missing_type = [
            i for i in report.issues
            if i.type == ConsistencyIssueType.MISSING_TYPE
        ]
        assert len(missing_type) == 1
        assert missing_type[0].severity == ConsistencyIssueSeverity.CRITICAL
    
    def test_invalid_type_critical(self):
        """Test that invalid type is CRITICAL severity."""
        adri_spec = {
            "field_requirements": {
                "bad_field": {
                    "type": "invalid_type",
                    "description": "Has invalid type"
                }
            }
        }
        
        validator = SchemaConsistencyValidator()
        report = validator.validate(adri_spec)
        
        assert report.has_critical_issues()
        
        invalid_type = [
            i for i in report.issues
            if i.type == ConsistencyIssueType.INVALID_TYPE
        ]
        assert len(invalid_type) == 1
        assert invalid_type[0].severity == ConsistencyIssueSeverity.CRITICAL
    
    def test_array_without_items_warning(self):
        """Test array without items specification."""
        adri_spec = {
            "field_requirements": {
                "tags": {
                    "type": "array",
                    "description": "List of tags"
                }
            }
        }
        
        validator = SchemaConsistencyValidator(strict_mode=False)
        report = validator.validate(adri_spec)
        
        array_issues = [
            i for i in report.issues
            if i.type == ConsistencyIssueType.INCOMPLETE_ARRAY_SPEC
        ]
        assert len(array_issues) > 0
        assert any("items" in i.message.lower() for i in array_issues)
    
    def test_array_without_items_error_strict_mode(self):
        """Test array without items is ERROR in strict mode."""
        adri_spec = {
            "field_requirements": {
                "tags": {
                    "type": "array",
                    "description": "List of tags"
                }
            }
        }
        
        validator = SchemaConsistencyValidator(strict_mode=True)
        report = validator.validate(adri_spec)
        
        array_issues = [
            i for i in report.issues
            if i.type == ConsistencyIssueType.INCOMPLETE_ARRAY_SPEC
            and "items" in i.message.lower()
        ]
        assert len(array_issues) > 0
        assert array_issues[0].severity == ConsistencyIssueSeverity.ERROR
    
    def test_array_items_without_type(self):
        """Test array items specification missing type."""
        adri_spec = {
            "field_requirements": {
                "tags": {
                    "type": "array",
                    "items": {
                        "min_length": 1
                    },
                    "description": "List of tags"
                }
            }
        }
        
        validator = SchemaConsistencyValidator()
        report = validator.validate(adri_spec)
        
        array_issues = [
            i for i in report.issues
            if i.type == ConsistencyIssueType.INCOMPLETE_ARRAY_SPEC
        ]
        assert len(array_issues) > 0
    
    def test_array_without_bounds_warning(self):
        """Test array without min_items/max_items gets warning."""
        adri_spec = {
            "field_requirements": {
                "tags": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "List of tags"
                }
            }
        }
        
        validator = SchemaConsistencyValidator()
        report = validator.validate(adri_spec)
        
        bound_warnings = [
            i for i in report.issues
            if i.type == ConsistencyIssueType.INCOMPLETE_ARRAY_SPEC
            and "size constraints" in i.message.lower()
        ]
        assert len(bound_warnings) == 1
        assert bound_warnings[0].severity == ConsistencyIssueSeverity.WARNING
    
    def test_conflicting_numeric_constraints(self):
        """Test min_value > max_value conflict."""
        adri_spec = {
            "field_requirements": {
                "bad_range": {
                    "type": "integer",
                    "min_value": 100,
                    "max_value": 50,
                    "description": "Invalid range"
                }
            }
        }
        
        validator = SchemaConsistencyValidator()
        report = validator.validate(adri_spec)
        
        conflicts = [
            i for i in report.issues
            if i.type == ConsistencyIssueType.CONFLICTING_CONSTRAINTS
        ]
        assert len(conflicts) == 1
        assert conflicts[0].severity == ConsistencyIssueSeverity.ERROR
        assert "min_value" in conflicts[0].message
        assert "max_value" in conflicts[0].message
    
    def test_conflicting_string_length_constraints(self):
        """Test min_length > max_length conflict."""
        adri_spec = {
            "field_requirements": {
                "bad_length": {
                    "type": "string",
                    "min_length": 50,
                    "max_length": 10,
                    "description": "Invalid length constraints"
                }
            }
        }
        
        validator = SchemaConsistencyValidator()
        report = validator.validate(adri_spec)
        
        conflicts = [
            i for i in report.issues
            if i.type == ConsistencyIssueType.CONFLICTING_CONSTRAINTS
        ]
        assert len(conflicts) == 1
        assert "min_length" in conflicts[0].message
        assert "max_length" in conflicts[0].message
    
    def test_conflicting_array_items_constraints(self):
        """Test min_items > max_items conflict."""
        adri_spec = {
            "field_requirements": {
                "bad_array": {
                    "type": "array",
                    "items": {"type": "string"},
                    "min_items": 10,
                    "max_items": 5,
                    "description": "Invalid array size"
                }
            }
        }
        
        validator = SchemaConsistencyValidator()
        report = validator.validate(adri_spec)
        
        conflicts = [
            i for i in report.issues
            if i.type == ConsistencyIssueType.CONFLICTING_CONSTRAINTS
        ]
        assert len(conflicts) == 1
        assert "min_items" in conflicts[0].message
        assert "max_items" in conflicts[0].message
    
    def test_invalid_constraint_value_type(self):
        """Test non-numeric constraint value."""
        adri_spec = {
            "field_requirements": {
                "bad_constraint": {
                    "type": "integer",
                    "min_value": "not_a_number",
                    "description": "Invalid constraint type"
                }
            }
        }
        
        validator = SchemaConsistencyValidator()
        report = validator.validate(adri_spec)
        
        invalid_vals = [
            i for i in report.issues
            if i.type == ConsistencyIssueType.INVALID_CONSTRAINT_VALUE
        ]
        assert len(invalid_vals) == 1
        assert invalid_vals[0].severity == ConsistencyIssueSeverity.ERROR
    
    def test_negative_min_value_warning(self):
        """Test negative min_value generates warning."""
        adri_spec = {
            "field_requirements": {
                "negative_min": {
                    "type": "integer",
                    "min_value": -10,
                    "description": "Allows negative values"
                }
            }
        }
        
        validator = SchemaConsistencyValidator()
        report = validator.validate(adri_spec)
        
        # Should have warning about negative min_value
        negative_warnings = [
            i for i in report.issues
            if i.type == ConsistencyIssueType.INVALID_CONSTRAINT_VALUE
            and "negative" in i.message.lower()
        ]
        assert len(negative_warnings) == 1
        assert negative_warnings[0].severity == ConsistencyIssueSeverity.WARNING
    
    def test_multiple_issues_same_field(self):
        """Test field with multiple issues."""
        adri_spec = {
            "field_requirements": {
                "SELECT": {  # SQL reserved word
                    "type": "string",
                    "min_length": 100,  # Conflicting constraints
                    "max_length": 10,
                    "description": "JSON array of values"  # Type/description conflict
                }
            }
        }
        
        validator = SchemaConsistencyValidator()
        report = validator.validate(adri_spec)
        
        # Should detect multiple issues for this field
        assert report.issues_found >= 3
        select_issues = [i for i in report.issues if i.field_name == "SELECT"]
        assert len(select_issues) >= 3
    
    def test_report_to_dict(self):
        """Test SchemaConsistencyReport to_dict method."""
        adri_spec = {
            "field_requirements": {
                "test_field": {
                    "type": "string",
                    "description": "Test field"
                }
            }
        }
        
        validator = SchemaConsistencyValidator()
        report = validator.validate(adri_spec)
        
        report_dict = report.to_dict()
        
        assert "is_valid" in report_dict
        assert "total_fields" in report_dict
        assert "issues_found" in report_dict
        assert "has_critical_issues" in report_dict
        assert "has_errors" in report_dict
        assert "issues" in report_dict
        assert isinstance(report_dict["issues"], list)
    
    def test_get_issues_by_severity(self):
        """Test filtering issues by severity."""
        adri_spec = {
            "field_requirements": {
                "SELECT": {  # WARNING
                    "type": "string",
                    "description": "JSON array"  # ERROR
                },
                "no_type": {  # CRITICAL
                    "description": "Missing type"
                }
            }
        }
        
        validator = SchemaConsistencyValidator()
        report = validator.validate(adri_spec)
        
        criticals = report.get_issues_by_severity(ConsistencyIssueSeverity.CRITICAL)
        errors = report.get_issues_by_severity(ConsistencyIssueSeverity.ERROR)
        warnings = report.get_issues_by_severity(ConsistencyIssueSeverity.WARNING)
        
        assert len(criticals) > 0
        assert len(errors) > 0
        assert len(warnings) > 0
    
    def test_empty_field_requirements(self):
        """Test handling of empty field_requirements."""
        adri_spec = {"field_requirements": {}}
        
        validator = SchemaConsistencyValidator()
        report = validator.validate(adri_spec)
        
        assert report.total_fields == 0
        assert report.issues_found == 0
    
    def test_missing_field_requirements_section(self):
        """Test handling of missing field_requirements section."""
        adri_spec = {"contracts": {"id": "test"}}
        
        validator = SchemaConsistencyValidator()
        report = validator.validate(adri_spec)
        
        assert not report.is_valid
        assert report.total_fields == 0
    
    def test_convenience_function(self):
        """Test convenience function validate_schema_consistency."""
        adri_spec = {
            "field_requirements": {
                "test_field": {
                    "type": "string",
                    "description": "Test field"
                }
            }
        }
        
        report = validate_schema_consistency(adri_spec)
        
        assert report.is_valid
        assert report.total_fields == 1
    
    def test_real_world_phase1_issue_detection(self):
        """Test detection of the Phase 1 type/description conflict issue."""
        # This is the BEFORE state that caused issues in Phase 1
        adri_spec = {
            "field_requirements": {
                "AI_RISK_FACTORS": {
                    "type": "string",  # WRONG
                    "description": "JSON array of identified project risks"
                }
            }
        }
        
        validator = SchemaConsistencyValidator()
        report = validator.validate(adri_spec)
        
        # Should detect type/description conflict
        assert report.has_errors()
        type_conflicts = [
            i for i in report.issues
            if i.type == ConsistencyIssueType.TYPE_DESCRIPTION_CONFLICT
        ]
        assert len(type_conflicts) == 1
        assert "array" in type_conflicts[0].message.lower()
        assert "string" in type_conflicts[0].message.lower()
        
        # Should suggest changing to array type
        assert "array" in type_conflicts[0].remediation.lower()
    
    def test_real_world_phase1_fixed_schema(self):
        """Test that Phase 1 fixed schema passes validation."""
        # This is the AFTER state that fixed the Phase 1 issue
        adri_spec = {
            "field_requirements": {
                "AI_RISK_FACTORS": {
                    "type": "array",  # CORRECT
                    "min_items": 1,
                    "max_items": 20,
                    "items": {
                        "type": "string",
                        "min_length": 10,
                        "max_length": 200
                    },
                    "description": "JSON array of identified project risks"
                }
            }
        }
        
        validator = SchemaConsistencyValidator()
        report = validator.validate(adri_spec)
        
        # Should pass without type/description conflicts
        assert report.is_valid
        type_conflicts = [
            i for i in report.issues
            if i.type == ConsistencyIssueType.TYPE_DESCRIPTION_CONFLICT
        ]
        assert len(type_conflicts) == 0
    
    def test_type_description_patterns(self):
        """Test various type indicator patterns in descriptions."""
        test_cases = [
            ("string", "This is a list of items", "array"),
            ("string", "Collection of values", "array"),
            ("string", "Comma-separated list", "array"),
            ("string", "Age count", "integer"),
            ("string", "The score percentage", "float"),
            ("string", "Boolean flag indicating status", "boolean"),
            ("string", "Timestamp in ISO 8601 format", "date"),
        ]
        
        for field_type, description, expected_suggestion in test_cases:
            adri_spec = {
                "field_requirements": {
                    "test_field": {
                        "type": field_type,
                        "description": description
                    }
                }
            }
            
            validator = SchemaConsistencyValidator()
            report = validator.validate(adri_spec)
            
            if field_type != expected_suggestion:
                type_conflicts = [
                    i for i in report.issues
                    if i.type == ConsistencyIssueType.TYPE_DESCRIPTION_CONFLICT
                ]
                assert len(type_conflicts) > 0, \
                    f"Failed to detect conflict for: {description}"
                assert expected_suggestion in type_conflicts[0].message.lower(), \
                    f"Expected suggestion '{expected_suggestion}' not found in: {type_conflicts[0].message}"


class TestSQLReservedWordsConstant:
    """Test SQL reserved words constant."""
    
    def test_sql_reserved_words_exists(self):
        """Test that SQL_RESERVED_WORDS set exists."""
        assert isinstance(SQL_RESERVED_WORDS, set)
        assert len(SQL_RESERVED_WORDS) > 0
    
    def test_common_sql_keywords_present(self):
        """Test that common SQL keywords are in the set."""
        common_keywords = [
            "SELECT", "FROM", "WHERE", "ORDER", "GROUP", "BY",
            "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"
        ]
        for keyword in common_keywords:
            assert keyword in SQL_RESERVED_WORDS, f"Missing keyword: {keyword}"
