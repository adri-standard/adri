"""Tests for ADRI v2.0 field specification validation.

Tests validation of the optional v2.0 properties:
- field_category
- derivation
- reasoning_guidance
"""

import pytest
from adri.validator.schema_validator import (
    validate_field_spec_v2,
    validate_standard_schema_v2,
    FieldSpecValidationError,
    VALID_FIELD_CATEGORIES,
    VALID_DERIVATION_STRATEGIES
)


class TestFieldCategoryValidation:
    """Test validation of field_category property."""
    
    def test_valid_field_categories(self):
        """Valid field_category values should pass validation."""
        for category in VALID_FIELD_CATEGORIES:
            field_spec = {'field_category': category}
            errors = validate_field_spec_v2('test_field', field_spec)
            assert errors == [], f"Category '{category}' should be valid"
    
    def test_invalid_field_category(self):
        """Invalid field_category should produce error."""
        field_spec = {'field_category': 'invalid_category'}
        errors = validate_field_spec_v2('test_field', field_spec)
        assert len(errors) == 1
        assert 'invalid field_category' in errors[0]
        assert 'invalid_category' in errors[0]
    
    def test_field_category_optional(self):
        """field_category is optional - omitting it should be valid."""
        field_spec = {'type': 'string'}
        errors = validate_field_spec_v2('test_field', field_spec)
        assert errors == []


class TestDerivationValidation:
    """Test validation of derivation property."""
    
    def test_derivation_must_be_dict(self):
        """derivation must be an object/dictionary."""
        field_spec = {'derivation': "not a dict"}
        errors = validate_field_spec_v2('test_field', field_spec)
        assert len(errors) == 1
        assert 'must be an object/dictionary' in errors[0]
    
    def test_derivation_requires_strategy(self):
        """derivation must have 'strategy' property."""
        field_spec = {'derivation': {'inputs': []}}
        errors = validate_field_spec_v2('test_field', field_spec)
        assert len(errors) == 1
        assert "must have 'strategy'" in errors[0]
    
    def test_invalid_strategy(self):
        """Invalid strategy should produce error."""
        field_spec = {'derivation': {'strategy': 'invalid_strategy'}}
        errors = validate_field_spec_v2('test_field', field_spec)
        assert len(errors) >= 1
        assert any('invalid derivation strategy' in e for e in errors)
    
    def test_valid_strategies(self):
        """All valid strategies in the spec should be recognized."""
        for strategy in VALID_DERIVATION_STRATEGIES:
            # Minimal valid structure for each strategy
            if strategy == 'ordered_precedence':
                field_spec = {
                    'derivation': {
                        'strategy': strategy,
                        'inputs': ['field1'],
                        'rules': [{'condition': 'test', 'value': 'val'}]
                    }
                }
            elif strategy == 'explicit_lookup':
                field_spec = {
                    'derivation': {
                        'strategy': strategy,
                        'inputs': ['field1'],
                        'lookup_table': [{'keys': {}, 'value': 'val'}]
                    }
                }
            elif strategy == 'direct_mapping':
                field_spec = {
                    'derivation': {
                        'strategy': strategy,
                        'source_field': 'field1',
                        'mappings': {'a': 'b'}
                    }
                }
            elif strategy == 'calculated':
                field_spec = {
                    'derivation': {
                        'strategy': strategy,
                        'formula': 'A + B',
                        'variables': {'A': 1}
                    }
                }
            
            errors = validate_field_spec_v2('test_field', field_spec)
            assert errors == [], f"Strategy '{strategy}' should be valid, got errors: {errors}"
    
    def test_derivation_optional(self):
        """derivation is optional - omitting it should be valid."""
        field_spec = {'type': 'string'}
        errors = validate_field_spec_v2('test_field', field_spec)
        assert errors == []


class TestOrderedPrecedenceValidation:
    """Test validation of ordered_precedence strategy."""
    
    def test_requires_inputs(self):
        """ordered_precedence requires 'inputs' array."""
        field_spec = {
            'derivation': {
                'strategy': 'ordered_precedence',
                'rules': []
            }
        }
        errors = validate_field_spec_v2('test_field', field_spec)
        assert any("requires 'inputs' array" in e for e in errors)
    
    def test_inputs_must_be_array(self):
        """'inputs' must be an array."""
        field_spec = {
            'derivation': {
                'strategy': 'ordered_precedence',
                'inputs': 'not_array',
                'rules': []
            }
        }
        errors = validate_field_spec_v2('test_field', field_spec)
        assert any("'inputs' must be an array" in e for e in errors)
    
    def test_requires_rules(self):
        """ordered_precedence requires 'rules' array."""
        field_spec = {
            'derivation': {
                'strategy': 'ordered_precedence',
                'inputs': []
            }
        }
        errors = validate_field_spec_v2('test_field', field_spec)
        assert any("requires 'rules' array" in e for e in errors)
    
    def test_rules_must_be_array(self):
        """'rules' must be an array."""
        field_spec = {
            'derivation': {
                'strategy': 'ordered_precedence',
                'inputs': [],
                'rules': 'not_array'
            }
        }
        errors = validate_field_spec_v2('test_field', field_spec)
        assert any("'rules' must be an array" in e for e in errors)
    
    def test_rules_cannot_be_empty(self):
        """'rules' array cannot be empty."""
        field_spec = {
            'derivation': {
                'strategy': 'ordered_precedence',
                'inputs': [],
                'rules': []
            }
        }
        errors = validate_field_spec_v2('test_field', field_spec)
        assert any("'rules' array cannot be empty" in e for e in errors)
    
    def test_valid_ordered_precedence(self):
        """Valid ordered_precedence should pass."""
        field_spec = {
            'derivation': {
                'strategy': 'ordered_precedence',
                'inputs': ['priority', 'status'],
                'rules': [
                    {'precedence': 1, 'condition': 'priority = 1', 'value': 'High'},
                    {'precedence': 2, 'is_default': True, 'value': 'Low'}
                ]
            }
        }
        errors = validate_field_spec_v2('RISK_LEVEL', field_spec)
        assert errors == []


class TestExplicitLookupValidation:
    """Test validation of explicit_lookup strategy."""
    
    def test_requires_inputs(self):
        """explicit_lookup requires 'inputs' array."""
        field_spec = {
            'derivation': {
                'strategy': 'explicit_lookup',
                'lookup_table': []
            }
        }
        errors = validate_field_spec_v2('test_field', field_spec)
        assert any("requires 'inputs' array" in e for e in errors)
    
    def test_requires_lookup_table(self):
        """explicit_lookup requires 'lookup_table' array."""
        field_spec = {
            'derivation': {
                'strategy': 'explicit_lookup',
                'inputs': []
            }
        }
        errors = validate_field_spec_v2('test_field', field_spec)
        assert any("requires 'lookup_table' array" in e for e in errors)
    
    def test_lookup_table_cannot_be_empty(self):
        """'lookup_table' array cannot be empty."""
        field_spec = {
            'derivation': {
                'strategy': 'explicit_lookup',
                'inputs': [],
                'lookup_table': []
            }
        }
        errors = validate_field_spec_v2('test_field', field_spec)
        assert any("'lookup_table' array cannot be empty" in e for e in errors)
    
    def test_valid_explicit_lookup(self):
        """Valid explicit_lookup should pass."""
        field_spec = {
            'derivation': {
                'strategy': 'explicit_lookup',
                'inputs': ['TIMELINE_STATUS', 'priority'],
                'lookup_table': [
                    {'keys': {'TIMELINE_STATUS': 'On Track', 'priority': 1}, 'value': 100},
                    {'is_default': True, 'value': 50}
                ]
            }
        }
        errors = validate_field_spec_v2('HEALTH_SCORE', field_spec)
        assert errors == []


class TestDirectMappingValidation:
    """Test validation of direct_mapping strategy."""
    
    def test_requires_source_field(self):
        """direct_mapping requires 'source_field' string."""
        field_spec = {
            'derivation': {
                'strategy': 'direct_mapping',
                'mappings': {}
            }
        }
        errors = validate_field_spec_v2('test_field', field_spec)
        assert any("requires 'source_field' string" in e for e in errors)
    
    def test_source_field_must_be_string(self):
        """'source_field' must be a string."""
        field_spec = {
            'derivation': {
                'strategy': 'direct_mapping',
                'source_field': 123,
                'mappings': {}
            }
        }
        errors = validate_field_spec_v2('test_field', field_spec)
        assert any("'source_field' must be a string" in e for e in errors)
    
    def test_requires_mappings(self):
        """direct_mapping requires 'mappings' object."""
        field_spec = {
            'derivation': {
                'strategy': 'direct_mapping',
                'source_field': 'status'
            }
        }
        errors = validate_field_spec_v2('test_field', field_spec)
        assert any("requires 'mappings' object" in e for e in errors)
    
    def test_mappings_must_be_dict(self):
        """'mappings' must be an object/dictionary."""
        field_spec = {
            'derivation': {
                'strategy': 'direct_mapping',
                'source_field': 'status',
                'mappings': 'not_dict'
            }
        }
        errors = validate_field_spec_v2('test_field', field_spec)
        assert any("'mappings' must be an object/dictionary" in e for e in errors)
    
    def test_mappings_cannot_be_empty(self):
        """'mappings' object cannot be empty."""
        field_spec = {
            'derivation': {
                'strategy': 'direct_mapping',
                'source_field': 'status',
                'mappings': {}
            }
        }
        errors = validate_field_spec_v2('test_field', field_spec)
        assert any("'mappings' object cannot be empty" in e for e in errors)
    
    def test_valid_direct_mapping(self):
        """Valid direct_mapping should pass."""
        field_spec = {
            'derivation': {
                'strategy': 'direct_mapping',
                'source_field': 'project_status',
                'mappings': {
                    'At Risk': 'At Risk',
                    '*': 'On Track'
                }
            }
        }
        errors = validate_field_spec_v2('TIMELINE_STATUS', field_spec)
        assert errors == []


class TestCalculatedValidation:
    """Test validation of calculated strategy."""
    
    def test_requires_formula(self):
        """calculated requires 'formula' string."""
        field_spec = {
            'derivation': {
                'strategy': 'calculated',
                'variables': {}
            }
        }
        errors = validate_field_spec_v2('test_field', field_spec)
        assert any("requires 'formula' string" in e for e in errors)
    
    def test_formula_must_be_string(self):
        """'formula' must be a string."""
        field_spec = {
            'derivation': {
                'strategy': 'calculated',
                'formula': 123,
                'variables': {}
            }
        }
        errors = validate_field_spec_v2('test_field', field_spec)
        assert any("'formula' must be a string" in e for e in errors)
    
    def test_requires_variables(self):
        """calculated requires 'variables' object."""
        field_spec = {
            'derivation': {
                'strategy': 'calculated',
                'formula': 'A + B'
            }
        }
        errors = validate_field_spec_v2('test_field', field_spec)
        assert any("requires 'variables' object" in e for e in errors)
    
    def test_variables_must_be_dict(self):
        """'variables' must be an object/dictionary."""
        field_spec = {
            'derivation': {
                'strategy': 'calculated',
                'formula': 'A + B',
                'variables': 'not_dict'
            }
        }
        errors = validate_field_spec_v2('test_field', field_spec)
        assert any("'variables' must be an object/dictionary" in e for e in errors)
    
    def test_valid_calculated(self):
        """Valid calculated should pass."""
        field_spec = {
            'derivation': {
                'strategy': 'calculated',
                'formula': 'BASE + FACTOR',
                'variables': {
                    'BASE': 50,
                    'FACTOR': {
                        'lookup': 'status',
                        'values': {'On Track': 10, 'At Risk': -10}
                    }
                },
                'constraints': {'min': 0, 'max': 100}
            }
        }
        errors = validate_field_spec_v2('HEALTH_SCORE', field_spec)
        assert errors == []


class TestReasoningGuidanceValidation:
    """Test validation of reasoning_guidance property."""
    
    def test_must_be_string(self):
        """reasoning_guidance must be a string."""
        field_spec = {'reasoning_guidance': 123}
        errors = validate_field_spec_v2('test_field', field_spec)
        assert len(errors) == 1
        assert 'must be a string' in errors[0]
    
    def test_valid_reasoning_guidance(self):
        """Valid reasoning_guidance should pass."""
        field_spec = {
            'reasoning_guidance': 'Explain the risk factors...'
        }
        errors = validate_field_spec_v2('RISK_RATIONALE', field_spec)
        assert errors == []
    
    def test_multiline_reasoning_guidance(self):
        """Multi-line reasoning_guidance should pass."""
        field_spec = {
            'reasoning_guidance': """Explain risk factors.
            
Consider:
- Priority level
- Timeline status"""
        }
        errors = validate_field_spec_v2('RISK_RATIONALE', field_spec)
        assert errors == []
    
    def test_reasoning_guidance_optional(self):
        """reasoning_guidance is optional."""
        field_spec = {'type': 'string'}
        errors = validate_field_spec_v2('test_field', field_spec)
        assert errors == []


class TestCombinedProperties:
    """Test combinations of v2.0 properties."""
    
    def test_all_properties_valid(self):
        """All v2.0 properties together should validate correctly."""
        field_spec = {
            'field_category': 'ai_decision',
            'derivation': {
                'strategy': 'ordered_precedence',
                'inputs': ['priority'],
                'rules': [{'value': 'High'}]
            },
            'type': 'string'
        }
        errors = validate_field_spec_v2('RISK_LEVEL', field_spec)
        assert errors == []
    
    def test_narrative_with_guidance(self):
        """Narrative field with reasoning_guidance should validate."""
        field_spec = {
            'field_category': 'ai_narrative',
            'reasoning_guidance': 'Explain the rationale...',
            'type': 'string'
        }
        errors = validate_field_spec_v2('RISK_RATIONALE', field_spec)
        assert errors == []
    
    def test_multiple_errors_collected(self):
        """Multiple validation errors should all be collected."""
        field_spec = {
            'field_category': 'invalid_category',
            'derivation': 'not_dict',
            'reasoning_guidance': 123
        }
        errors = validate_field_spec_v2('test_field', field_spec)
        assert len(errors) == 3  # One for each invalid property


class TestStandardValidation:
    """Test validation of complete standards."""
    
    def test_empty_standard(self):
        """Empty field_requirements should be valid."""
        errors = validate_standard_schema_v2({})
        assert errors == {}
    
    def test_valid_standard(self):
        """Valid standard with multiple fields should pass."""
        field_requirements = {
            'RISK_LEVEL': {
                'field_category': 'ai_decision',
                'derivation': {
                    'strategy': 'ordered_precedence',
                    'inputs': ['priority'],
                    'rules': [{'value': 'High'}]
                }
            },
            'RISK_RATIONALE': {
                'field_category': 'ai_narrative',
                'reasoning_guidance': 'Explain...'
            },
            'project_id': {
                'type': 'integer'
            }
        }
        errors = validate_standard_schema_v2(field_requirements)
        assert errors == {}
    
    def test_standard_with_errors(self):
        """Standard with multiple field errors should collect all errors."""
        field_requirements = {
            'field1': {
                'field_category': 'invalid'
            },
            'field2': {
                'derivation': {'strategy': 'invalid'}
            },
            'field3': {
                'type': 'string'  # Valid field
            }
        }
        errors = validate_standard_schema_v2(field_requirements)
        assert len(errors) == 2
        assert 'field1' in errors
        assert 'field2' in errors
        assert 'field3' not in errors
    
    def test_field_spec_not_dict(self):
        """Field spec that isn't a dictionary should error."""
        field_requirements = {
            'bad_field': 'not a dict'
        }
        errors = validate_standard_schema_v2(field_requirements)
        assert 'bad_field' in errors
        assert 'must be an object/dictionary' in errors['bad_field'][0]


class TestBackwardCompatibility:
    """Test that existing standards without v2.0 properties still work."""
    
    def test_standard_without_v2_properties(self):
        """Standard without any v2.0 properties should be valid."""
        field_requirements = {
            'project_id': {
                'type': 'integer',
                'constraints': [
                    {'type': 'min_value', 'value': 0}
                ]
            },
            'project_name': {
                'type': 'string',
                'constraints': [
                    {'type': 'min_length', 'value': 1}
                ]
            }
        }
        errors = validate_standard_schema_v2(field_requirements)
        assert errors == {}
    
    def test_mixed_v1_and_v2_fields(self):
        """Standard with mix of v1 and v2 fields should be valid."""
        field_requirements = {
            'project_id': {
                'type': 'integer'  # v1 field
            },
            'RISK_LEVEL': {
                'field_category': 'ai_decision',  # v2 field
                'derivation': {
                    'strategy': 'ordered_precedence',
                    'inputs': ['status'],
                    'rules': [{'value': 'High'}]
                }
            }
        }
        errors = validate_standard_schema_v2(field_requirements)
        assert errors == {}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
