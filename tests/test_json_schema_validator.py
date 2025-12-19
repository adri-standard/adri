"""Tests for JSON Schema validation functionality.

This test suite verifies the JSON Schema validator's ability to validate data
against JSON Schema specifications, including all Draft 7 validator types.
"""

import pytest
from adri.utils.json_schema_validator import validate_json_against_schema


class TestBasicValidation:
    """Test basic validation scenarios."""
    
    def test_valid_object_passes(self):
        """Test that valid object data passes validation."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        data = {"name": "Alice", "age": 30}
        
        is_valid, violations = validate_json_against_schema(data, schema)
        
        assert is_valid is True
        assert violations == []
    
    def test_valid_array_passes(self):
        """Test that valid array data passes validation."""
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"}
                }
            }
        }
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
        
        is_valid, violations = validate_json_against_schema(data, schema)
        
        assert is_valid is True
        assert violations == []
    
    def test_empty_schema_passes(self):
        """Test that empty schema allows any data."""
        data = {"anything": "goes", "nested": {"data": [1, 2, 3]}}
        
        is_valid, violations = validate_json_against_schema(data, {})
        
        assert is_valid is True
        assert violations == []
    
    def test_none_schema_passes(self):
        """Test that None schema skips validation."""
        data = {"test": "data"}
        
        is_valid, violations = validate_json_against_schema(data, None)
        
        assert is_valid is True
        assert violations == []


class TestRequiredFields:
    """Test required field validation."""
    
    def test_missing_required_field(self):
        """Test detection of missing required field."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"}
            },
            "required": ["name", "email"]
        }
        data = {"name": "Alice"}
        
        is_valid, violations = validate_json_against_schema(data, schema)
        
        assert is_valid is False
        assert len(violations) == 1
        assert "Missing required field 'email'" in violations[0]
    
    def test_multiple_missing_required_fields(self):
        """Test detection of multiple missing required fields."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name", "email", "age"]
        }
        data = {}
        
        is_valid, violations = validate_json_against_schema(data, schema)
        
        assert is_valid is False
        assert len(violations) == 3
        # Check that all required fields are mentioned
        violation_str = " ".join(violations)
        assert "name" in violation_str
        assert "email" in violation_str
        assert "age" in violation_str


class TestTypeValidation:
    """Test data type validation."""
    
    def test_wrong_type_string_instead_of_integer(self):
        """Test detection of string when integer expected."""
        schema = {
            "type": "object",
            "properties": {
                "age": {"type": "integer"}
            }
        }
        data = {"age": "thirty"}
        
        is_valid, violations = validate_json_against_schema(data, schema)
        
        assert is_valid is False
        assert len(violations) == 1
        assert "age" in violations[0]
        assert "integer" in violations[0].lower() or "type" in violations[0].lower()
    
    def test_wrong_type_string_instead_of_array(self):
        """Test detection of string when array expected."""
        schema = {
            "type": "object",
            "properties": {
                "tags": {"type": "array", "items": {"type": "string"}}
            }
        }
        data = {"tags": "tag1, tag2, tag3"}
        
        is_valid, violations = validate_json_against_schema(data, schema)
        
        assert is_valid is False
        assert len(violations) == 1
        assert "tags" in violations[0]
        assert "array" in violations[0].lower() or "type" in violations[0].lower()
    
    def test_wrong_type_object_instead_of_string(self):
        """Test detection of object when string expected."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            }
        }
        data = {"name": {"first": "Alice", "last": "Smith"}}
        
        is_valid, violations = validate_json_against_schema(data, schema)
        
        assert is_valid is False
        assert len(violations) >= 1
        assert "name" in violations[0]


class TestEnumValidation:
    """Test enum/allowed values validation."""
    
    def test_enum_violation(self):
        """Test detection of value not in allowed enum."""
        schema = {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["active", "inactive", "pending"]
                }
            }
        }
        data = {"status": "deleted"}
        
        is_valid, violations = validate_json_against_schema(data, schema)
        
        assert is_valid is False
        assert len(violations) == 1
        assert "status" in violations[0]
        assert "active" in violations[0] or "enum" in violations[0].lower()
    
    def test_enum_passes_with_valid_value(self):
        """Test that valid enum value passes."""
        schema = {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["active", "inactive", "pending"]
                }
            }
        }
        data = {"status": "active"}
        
        is_valid, violations = validate_json_against_schema(data, schema)
        
        assert is_valid is True
        assert violations == []


class TestPatternValidation:
    """Test regex pattern validation."""
    
    def test_pattern_mismatch(self):
        """Test detection of value not matching pattern."""
        schema = {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "pattern": r"^\d{4}-\d{2}-\d{2}$"
                }
            }
        }
        data = {"date": "2024/01/15"}
        
        is_valid, violations = validate_json_against_schema(data, schema)
        
        assert is_valid is False
        assert len(violations) == 1
        assert "date" in violations[0]
        assert "pattern" in violations[0].lower()
    
    def test_pattern_passes_with_valid_value(self):
        """Test that value matching pattern passes."""
        schema = {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "pattern": r"^\d{4}-\d{2}-\d{2}$"
                }
            }
        }
        data = {"date": "2024-01-15"}
        
        is_valid, violations = validate_json_against_schema(data, schema)
        
        assert is_valid is True
        assert violations == []


class TestNumericConstraints:
    """Test numeric constraint validation (minimum, maximum)."""
    
    def test_minimum_violation(self):
        """Test detection of value below minimum."""
        schema = {
            "type": "object",
            "properties": {
                "age": {
                    "type": "integer",
                    "minimum": 0
                }
            }
        }
        data = {"age": -5}
        
        is_valid, violations = validate_json_against_schema(data, schema)
        
        assert is_valid is False
        assert len(violations) == 1
        assert "age" in violations[0]
    
    def test_maximum_violation(self):
        """Test detection of value above maximum."""
        schema = {
            "type": "object",
            "properties": {
                "age": {
                    "type": "integer",
                    "maximum": 120
                }
            }
        }
        data = {"age": 150}
        
        is_valid, violations = validate_json_against_schema(data, schema)
        
        assert is_valid is False
        assert len(violations) == 1
        assert "age" in violations[0]
    
    def test_numeric_constraints_pass(self):
        """Test that values within range pass."""
        schema = {
            "type": "object",
            "properties": {
                "age": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 120
                }
            }
        }
        data = {"age": 30}
        
        is_valid, violations = validate_json_against_schema(data, schema)
        
        assert is_valid is True
        assert violations == []


class TestStringConstraints:
    """Test string length constraint validation."""
    
    def test_min_length_violation(self):
        """Test detection of string shorter than minimum."""
        schema = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "minLength": 3
                }
            }
        }
        data = {"name": "Al"}
        
        is_valid, violations = validate_json_against_schema(data, schema)
        
        assert is_valid is False
        assert len(violations) == 1
        assert "name" in violations[0]
    
    def test_max_length_violation(self):
        """Test detection of string longer than maximum."""
        schema = {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "maxLength": 10
                }
            }
        }
        data = {"code": "VERYLONGCODE123"}
        
        is_valid, violations = validate_json_against_schema(data, schema)
        
        assert is_valid is False
        assert len(violations) == 1
        assert "code" in violations[0]
    
    def test_string_constraints_pass(self):
        """Test that string within length range passes."""
        schema = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "minLength": 2,
                    "maxLength": 50
                }
            }
        }
        data = {"name": "Alice"}
        
        is_valid, violations = validate_json_against_schema(data, schema)
        
        assert is_valid is True
        assert violations == []


class TestNestedStructures:
    """Test validation of nested objects and arrays."""
    
    def test_nested_object_validation(self):
        """Test validation of nested object structures."""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"}
                    },
                    "required": ["email"]
                }
            }
        }
        data = {"user": {"name": "Alice"}}
        
        is_valid, violations = validate_json_against_schema(data, schema)
        
        assert is_valid is False
        assert len(violations) == 1
        assert "email" in violations[0]
        assert "user" in violations[0]
    
    def test_array_of_objects_validation(self):
        """Test validation of array items."""
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"}
                },
                "required": ["id", "name"]
            }
        }
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2}  # Missing name
        ]
        
        is_valid, violations = validate_json_against_schema(data, schema)
        
        assert is_valid is False
        assert len(violations) >= 1
        assert "name" in violations[0]
        assert "[1]" in violations[0]  # Second item (index 1)


class TestPathFormatting:
    """Test violation message path formatting."""
    
    def test_path_format_for_nested_field(self):
        """Test that path correctly identifies nested field location."""
        schema = {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "integer"}
                    }
                }
            }
        }
        data = {"data": {"value": "not_an_integer"}}
        
        is_valid, violations = validate_json_against_schema(data, schema)
        
        assert is_valid is False
        assert len(violations) == 1
        # Should include path to nested field
        assert "data" in violations[0]
        assert "value" in violations[0]
    
    def test_path_format_for_array_item(self):
        """Test that path correctly identifies array item location."""
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"}
                },
                "required": ["name"]
            }
        }
        data = [
            {"name": "Alice"},
            {},  # Missing name
            {"name": "Charlie"}
        ]
        
        is_valid, violations = validate_json_against_schema(data, schema)
        
        assert is_valid is False
        assert len(violations) == 1
        # Should indicate second item (index 1)
        assert "[1]" in violations[0]
        assert "name" in violations[0]


class TestMultipleViolations:
    """Test handling of multiple validation errors."""
    
    def test_multiple_violations_reported(self):
        """Test that all violations are reported."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0},
                "email": {"type": "string"}
            },
            "required": ["name", "email"]
        }
        data = {
            "age": -5  # Missing name and email, wrong age
        }
        
        is_valid, violations = validate_json_against_schema(data, schema)
        
        assert is_valid is False
        # Should have at least 2 violations (missing fields)
        assert len(violations) >= 2
        violation_str = " ".join(violations)
        assert "name" in violation_str
        assert "email" in violation_str


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_schema_handled_gracefully(self):
        """Test that invalid schema doesn't crash validation."""
        # Schema with invalid format
        schema = {"type": "invalid_type"}
        data = {"test": "data"}
        
        # Should not raise exception
        is_valid, violations = validate_json_against_schema(data, schema)
        
        # May pass (graceful handling) or fail with error message
        assert isinstance(is_valid, bool)
        assert isinstance(violations, list)
    
    def test_none_data_handled(self):
        """Test validation of None data."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}}
        }
        data = None
        
        is_valid, violations = validate_json_against_schema(data, schema)
        
        # Should detect type mismatch
        assert is_valid is False
        assert len(violations) >= 1
