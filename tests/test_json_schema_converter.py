"""Tests for ADRI to JSON Schema converter utility."""

import pytest
from adri.utils.json_schema_converter import (
    ADRIToJSONSchemaConverter,
    convert_adri_to_json_schema,
    SQL_RESERVED_WORDS
)


class TestADRIToJSONSchemaConverter:
    """Test suite for ADRI to JSON Schema conversion."""
    
    def test_basic_string_field(self):
        """Test conversion of basic string field."""
        adri_spec = {
            "field_requirements": {
                "customer_name": {
                    "type": "string",
                    "description": "Customer full name"
                }
            }
        }
        
        converter = ADRIToJSONSchemaConverter()
        result = converter.convert(adri_spec)
        
        assert result["type"] == "object"
        assert "customer_name" in result["properties"]
        assert result["properties"]["customer_name"]["type"] == "string"
        assert "customer_name" in result["required"]
    
    def test_nullable_field(self):
        """Test conversion of nullable field."""
        adri_spec = {
            "field_requirements": {
                "middle_name": {
                    "type": "string",
                    "nullable": True,
                    "description": "Customer middle name (optional)"
                }
            }
        }
        
        converter = ADRIToJSONSchemaConverter()
        result = converter.convert(adri_spec)
        
        # Nullable fields should use anyOf with null type
        assert "anyOf" in result["properties"]["middle_name"]
        assert {"type": "null"} in result["properties"]["middle_name"]["anyOf"]
        # Should not be in required list
        assert "middle_name" not in result["required"]
    
    def test_integer_with_bounds(self):
        """Test conversion of integer field with min/max values."""
        adri_spec = {
            "field_requirements": {
                "age": {
                    "type": "integer",
                    "min_value": 0,
                    "max_value": 120,
                    "description": "Customer age"
                }
            }
        }
        
        converter = ADRIToJSONSchemaConverter()
        result = converter.convert(adri_spec)
        
        age_prop = result["properties"]["age"]
        assert age_prop["type"] == "integer"
        assert age_prop["minimum"] == 0
        assert age_prop["maximum"] == 120
    
    def test_float_type_mapping(self):
        """Test conversion of float to number type."""
        adri_spec = {
            "field_requirements": {
                "score": {
                    "type": "float",
                    "min_value": 0.0,
                    "max_value": 100.0,
                    "description": "Quality score"
                }
            }
        }
        
        converter = ADRIToJSONSchemaConverter()
        result = converter.convert(adri_spec)
        
        score_prop = result["properties"]["score"]
        assert score_prop["type"] == "number"  # float maps to number
        assert score_prop["minimum"] == 0.0
        assert score_prop["maximum"] == 100.0
    
    def test_boolean_field(self):
        """Test conversion of boolean field."""
        adri_spec = {
            "field_requirements": {
                "is_active": {
                    "type": "boolean",
                    "description": "Whether account is active"
                }
            }
        }
        
        converter = ADRIToJSONSchemaConverter()
        result = converter.convert(adri_spec)
        
        assert result["properties"]["is_active"]["type"] == "boolean"
    
    def test_date_field(self):
        """Test conversion of date field (maps to string)."""
        adri_spec = {
            "field_requirements": {
                "created_date": {
                    "type": "date",
                    "description": "Account creation date"
                }
            }
        }
        
        converter = ADRIToJSONSchemaConverter()
        result = converter.convert(adri_spec)
        
        # Date maps to string in JSON Schema
        assert result["properties"]["created_date"]["type"] == "string"
    
    def test_string_with_pattern(self):
        """Test conversion of string field with regex pattern."""
        adri_spec = {
            "field_requirements": {
                "email": {
                    "type": "string",
                    "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
                    "description": "Email address"
                }
            }
        }
        
        converter = ADRIToJSONSchemaConverter()
        result = converter.convert(adri_spec)
        
        email_prop = result["properties"]["email"]
        assert email_prop["type"] == "string"
        assert "pattern" in email_prop
        assert email_prop["pattern"] == "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
    
    def test_string_with_length_constraints(self):
        """Test conversion of string with min/max length."""
        adri_spec = {
            "field_requirements": {
                "username": {
                    "type": "string",
                    "min_length": 3,
                    "max_length": 20,
                    "description": "Username"
                }
            }
        }
        
        converter = ADRIToJSONSchemaConverter()
        result = converter.convert(adri_spec)
        
        username_prop = result["properties"]["username"]
        assert username_prop["minLength"] == 3
        assert username_prop["maxLength"] == 20
    
    def test_string_with_enum(self):
        """Test conversion of string field with valid_values (enum)."""
        adri_spec = {
            "field_requirements": {
                "status": {
                    "type": "string",
                    "valid_values": ["ACTIVE", "INACTIVE", "PENDING"],
                    "description": "Account status"
                }
            }
        }
        
        converter = ADRIToJSONSchemaConverter()
        result = converter.convert(adri_spec)
        
        status_prop = result["properties"]["status"]
        assert "enum" in status_prop
        assert set(status_prop["enum"]) == {"ACTIVE", "INACTIVE", "PENDING"}
    
    def test_array_with_items_spec(self):
        """Test conversion of array field with items specification."""
        adri_spec = {
            "field_requirements": {
                "tags": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "min_length": 1,
                        "max_length": 50
                    },
                    "min_items": 1,
                    "max_items": 10,
                    "description": "Tag list"
                }
            }
        }
        
        converter = ADRIToJSONSchemaConverter()
        result = converter.convert(adri_spec)
        
        tags_prop = result["properties"]["tags"]
        assert tags_prop["type"] == "array"
        assert tags_prop["minItems"] == 1
        assert tags_prop["maxItems"] == 10
        assert "items" in tags_prop
        assert tags_prop["items"]["type"] == "string"
        assert tags_prop["items"]["minLength"] == 1
        assert tags_prop["items"]["maxLength"] == 50
    
    def test_array_without_items_spec_strict_mode(self):
        """Test array without items spec generates warning in strict mode."""
        adri_spec = {
            "field_requirements": {
                "tags": {
                    "type": "array",
                    "description": "Tag list"
                }
            }
        }
        
        converter = ADRIToJSONSchemaConverter(strict_arrays=True)
        result = converter.convert(adri_spec)
        
        warnings = converter.get_warnings()
        assert len(warnings) > 0
        assert any("items" in w.lower() for w in warnings)
    
    def test_array_without_items_spec_non_strict_mode(self):
        """Test array without items spec in non-strict mode."""
        adri_spec = {
            "field_requirements": {
                "tags": {
                    "type": "array",
                    "description": "Tag list"
                }
            }
        }
        
        converter = ADRIToJSONSchemaConverter(strict_arrays=False)
        result = converter.convert(adri_spec)
        
        # Should still create valid schema
        assert result["properties"]["tags"]["type"] == "array"
    
    def test_array_with_numeric_items(self):
        """Test array of numeric items."""
        adri_spec = {
            "field_requirements": {
                "scores": {
                    "type": "array",
                    "items": {
                        "type": "float",
                        "min_value": 0.0,
                        "max_value": 100.0
                    },
                    "description": "Score array"
                }
            }
        }
        
        converter = ADRIToJSONSchemaConverter()
        result = converter.convert(adri_spec)
        
        scores_prop = result["properties"]["scores"]
        assert scores_prop["items"]["type"] == "number"  # float -> number
        assert scores_prop["items"]["minimum"] == 0.0
        assert scores_prop["items"]["maximum"] == 100.0
    
    def test_multiple_fields(self):
        """Test conversion with multiple fields."""
        adri_spec = {
            "field_requirements": {
                "customer_id": {
                    "type": "string",
                    "description": "Unique identifier"
                },
                "customer_name": {
                    "type": "string",
                    "description": "Full name"
                },
                "age": {
                    "type": "integer",
                    "min_value": 0,
                    "description": "Age in years"
                },
                "is_active": {
                    "type": "boolean",
                    "description": "Active status"
                }
            }
        }
        
        converter = ADRIToJSONSchemaConverter()
        result = converter.convert(adri_spec)
        
        assert len(result["properties"]) == 4
        assert all(field in result["properties"] for field in [
            "customer_id", "customer_name", "age", "is_active"
        ])
        assert len(result["required"]) == 4
    
    def test_empty_spec_raises_error(self):
        """Test that empty spec raises ValueError."""
        converter = ADRIToJSONSchemaConverter()
        
        with pytest.raises(ValueError, match="cannot be empty"):
            converter.convert({})
    
    def test_missing_field_requirements_raises_error(self):
        """Test that missing field_requirements raises ValueError."""
        adri_spec = {"contracts": {"id": "test"}}
        converter = ADRIToJSONSchemaConverter()
        
        with pytest.raises(ValueError, match="field_requirements"):
            converter.convert(adri_spec)
    
    def test_invalid_type_raises_error(self):
        """Test that invalid ADRI type logs warning and excludes field.
        
        Note: When ALL fields have invalid types, a ValueError is raised.
        Here we include a valid field to ensure the warning is logged.
        """
        adri_spec = {
            "field_requirements": {
                "good_field": {
                    "type": "string",
                    "description": "Valid field"
                },
                "bad_field": {
                    "type": "invalid_type",
                    "description": "Bad type"
                }
            }
        }
        
        converter = ADRIToJSONSchemaConverter()
        result = converter.convert(adri_spec)
        
        # Should log warning and exclude bad_field
        warnings = converter.get_warnings()
        assert len(warnings) > 0
        # good_field should be present, bad_field should not
        assert "good_field" in result["properties"]
        assert "bad_field" not in result["properties"]
    
    def test_missing_type_attribute(self):
        """Test field without type attribute logs warning.
        
        Note: When ALL fields are missing type, a ValueError is raised.
        Here we include a valid field to ensure the warning is logged.
        """
        adri_spec = {
            "field_requirements": {
                "good_field": {
                    "type": "string",
                    "description": "Valid field"
                },
                "no_type_field": {
                    "description": "Missing type"
                }
            }
        }
        
        converter = ADRIToJSONSchemaConverter()
        result = converter.convert(adri_spec)
        
        # Should log warning
        warnings = converter.get_warnings()
        assert len(warnings) > 0
        # good_field should be present, no_type_field should not
        assert "good_field" in result["properties"]
        assert "no_type_field" not in result["properties"]
    
    def test_additional_properties_false(self):
        """Test that additionalProperties is set to false."""
        adri_spec = {
            "field_requirements": {
                "field1": {
                    "type": "string",
                    "description": "Test field"
                }
            }
        }
        
        converter = ADRIToJSONSchemaConverter()
        result = converter.convert(adri_spec)
        
        assert result["additionalProperties"] is False
    
    def test_description_preservation(self):
        """Test that field descriptions are preserved."""
        description_text = "This is a detailed description of the field"
        adri_spec = {
            "field_requirements": {
                "field1": {
                    "type": "string",
                    "description": description_text
                }
            }
        }
        
        converter = ADRIToJSONSchemaConverter()
        result = converter.convert(adri_spec)
        
        assert result["properties"]["field1"]["description"] == description_text
    
    def test_convenience_function(self):
        """Test convenience function convert_adri_to_json_schema."""
        adri_spec = {
            "field_requirements": {
                "test_field": {
                    "type": "string",
                    "description": "Test"
                }
            }
        }
        
        result = convert_adri_to_json_schema(adri_spec)
        
        assert result["type"] == "object"
        assert "test_field" in result["properties"]
    
    def test_real_world_scenario_from_phase1(self):
        """Test conversion of the AI_RISK_FACTORS field that caused Phase 1 issue."""
        adri_spec = {
            "field_requirements": {
                "AI_RISK_FACTORS": {
                    "type": "array",
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
        
        converter = ADRIToJSONSchemaConverter()
        result = converter.convert(adri_spec)
        
        risk_prop = result["properties"]["AI_RISK_FACTORS"]
        assert risk_prop["type"] == "array"
        assert risk_prop["minItems"] == 1
        assert risk_prop["maxItems"] == 20
        assert risk_prop["items"]["type"] == "string"
        assert risk_prop["items"]["minLength"] == 10
        assert risk_prop["items"]["maxLength"] == 200
        
        # Should not have warnings since it's properly specified
        warnings = converter.get_warnings()
        array_warnings = [w for w in warnings if "AI_RISK_FACTORS" in w]
        assert len(array_warnings) == 0


class TestSQLReservedWords:
    """Test SQL reserved words constant."""
    
    def test_sql_reserved_words_exists(self):
        """Test that SQL_RESERVED_WORDS set exists and has common words."""
        assert "SELECT" in SQL_RESERVED_WORDS
        assert "FROM" in SQL_RESERVED_WORDS
        assert "WHERE" in SQL_RESERVED_WORDS
        assert "ORDER" in SQL_RESERVED_WORDS
        assert "GROUP" in SQL_RESERVED_WORDS
        assert "INSERT" in SQL_RESERVED_WORDS
        assert "UPDATE" in SQL_RESERVED_WORDS
        assert "DELETE" in SQL_RESERVED_WORDS
