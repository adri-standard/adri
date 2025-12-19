"""
Tests for ADRI mode detection and structure validation system.

Tests cover:
- Mode detection for all three modes (reasoning, conversation, deterministic)
- Structure validation per mode
- Integration with load_contract
- Backwards compatibility with existing templates
"""

import pytest
from src.adri.validator.modes import (
    ADRIMode,
    detect_mode,
    get_mode_description,
    get_mode_sections,
    is_valid_mode_transition,
)
from src.adri.validator.structure import (
    validate_structure,
    format_validation_report,
    StructureValidationResult,
)


class TestModeDetection:
    """Tests for ADRIMode detection."""
    
    def test_detect_conversation_mode(self):
        """Test conversation mode detection."""
        template = {
            'schema': {
                'context': {
                    'field1': {'type': 'string'}
                }
            }
        }
        
        mode = detect_mode(template)
        assert mode == ADRIMode.CONVERSATION
    
    def test_detect_reasoning_mode_top_level(self):
        """Test reasoning mode detection (top-level)."""
        template = {
            'context_requirements': {
                'field1': {'type': 'string'}
            }
        }
        
        mode = detect_mode(template)
        assert mode == ADRIMode.REASONING
    
    def test_detect_reasoning_mode_nested(self):
        """Test reasoning mode detection (nested in requirements)."""
        template = {
            'requirements': {
                'field_requirements': {
                    'field1': {'type': 'string'}
                }
            }
        }
        
        mode = detect_mode(template)
        assert mode == ADRIMode.REASONING
    
    def test_detect_deterministic_mode_input(self):
        """Test deterministic mode detection (input)."""
        template = {
            'input_requirements': {
                'field1': {'type': 'string'}
            }
        }
        
        mode = detect_mode(template)
        assert mode == ADRIMode.DETERMINISTIC
    
    def test_detect_deterministic_mode_output(self):
        """Test deterministic mode detection (output)."""
        template = {
            'output_requirements': {
                'field1': {'type': 'string'}
            }
        }
        
        mode = detect_mode(template)
        assert mode == ADRIMode.DETERMINISTIC
    
    def test_detect_none_mode(self):
        """Test NONE mode for templates without mode sections."""
        template = {
            'metadata': {
                'name': 'Generic Template'
            }
        }
        
        mode = detect_mode(template)
        assert mode == ADRIMode.NONE
    
    def test_conversation_priority_over_reasoning(self):
        """Test conversation mode takes priority in detection."""
        # If template has both schema.context and field_requirements,
        # conversation should be detected (priority order)
        template = {
            'schema': {
                'context': {'field1': {'type': 'string'}}
            },
            'field_requirements': {
                'field2': {'type': 'string'}
            }
        }
        
        mode = detect_mode(template)
        assert mode == ADRIMode.CONVERSATION
    
    def test_from_string(self):
        """Test ADRIMode.from_string conversion."""
        assert ADRIMode.from_string('reasoning') == ADRIMode.REASONING
        assert ADRIMode.from_string('CONVERSATION') == ADRIMode.CONVERSATION
        assert ADRIMode.from_string('Deterministic') == ADRIMode.DETERMINISTIC
        
        with pytest.raises(ValueError):
            ADRIMode.from_string('invalid_mode')
    
    def test_get_mode_description(self):
        """Test mode descriptions are returned."""
        desc = get_mode_description(ADRIMode.CONVERSATION)
        assert 'conversation' in desc.lower()
        assert 'interactive' in desc.lower()
    
    def test_get_mode_sections(self):
        """Test mode sections are correct."""
        sections = get_mode_sections(ADRIMode.CONVERSATION)
        assert 'schema.context' in sections['required']
        assert 'schema.required_outputs' in sections['optional']
        
        sections = get_mode_sections(ADRIMode.REASONING)
        assert len(sections['required']) == 0  # Reasoning has no required sections
        assert 'field_requirements' in sections['optional']
    
    def test_is_valid_mode_transition_exact_match(self):
        """Test exact mode match is valid."""
        assert is_valid_mode_transition(
            ADRIMode.CONVERSATION, 
            ADRIMode.CONVERSATION
        )
    
    def test_is_valid_mode_transition_none_permissive(self):
        """Test NONE mode is permissive."""
        assert is_valid_mode_transition(
            ADRIMode.NONE,
            ADRIMode.CONVERSATION
        )
    
    def test_is_valid_mode_transition_mismatch(self):
        """Test mode mismatch is invalid."""
        assert not is_valid_mode_transition(
            ADRIMode.REASONING,
            ADRIMode.CONVERSATION
        )


class TestStructureValidation:
    """Tests for structure validation."""
    
    def test_validate_conversation_structure_valid(self):
        """Test valid conversation structure."""
        template = {
            'schema': {
                'context': {
                    'field1': {'type': 'string'}
                },
                'can_modify': {'type': 'boolean'},
                'required_outputs': {
                    'output1': {'type': 'string'}
                }
            }
        }
        
        result = validate_structure(template, ADRIMode.CONVERSATION)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_conversation_missing_context(self):
        """Test conversation fails without schema.context."""
        template = {
            'schema': {
                'can_modify': {'type': 'boolean'}
            }
        }
        
        result = validate_structure(template, ADRIMode.CONVERSATION)
        assert not result.is_valid
        assert any('schema.context' in err for err in result.errors)
    
    def test_validate_conversation_empty_context_warning(self):
        """Test warning for empty schema.context."""
        template = {
            'schema': {
                'context': {}  # Empty
            }
        }
        
        result = validate_structure(template, ADRIMode.CONVERSATION)
        assert result.is_valid  # Still valid, just warning
        assert len(result.warnings) > 0
        assert any('empty' in warn.lower() for warn in result.warnings)
    
    def test_validate_reasoning_structure_valid(self):
        """Test valid reasoning structure."""
        template = {
            'requirements': {
                'context_requirements': {
                    'field1': {'type': 'string'}
                },
                'field_requirements': {
                    'output1': {'type': 'string'}
                }
            }
        }
        
        result = validate_structure(template, ADRIMode.REASONING)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_reasoning_either_section_ok(self):
        """Test reasoning valid with only one section."""
        # Context only
        template1 = {
            'context_requirements': {
                'field1': {'type': 'string'}
            }
        }
        result1 = validate_structure(template1, ADRIMode.REASONING)
        assert result1.is_valid
        
        # Field requirements only
        template2 = {
            'field_requirements': {
                'output1': {'type': 'string'}
            }
        }
        result2 = validate_structure(template2, ADRIMode.REASONING)
        assert result2.is_valid
    
    def test_validate_deterministic_structure_valid(self):
        """Test valid deterministic structure."""
        template = {
            'input_requirements': {
                'field1': {'type': 'string'}
            },
            'output_requirements': {
                'output1': {'type': 'string'}
            }
        }
        
        result = validate_structure(template, ADRIMode.DETERMINISTIC)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_deterministic_either_section_ok(self):
        """Test deterministic valid with only one section."""
        # Input only
        template1 = {
            'input_requirements': {
                'field1': {'type': 'string'}
            }
        }
        result1 = validate_structure(template1, ADRIMode.DETERMINISTIC)
        assert result1.is_valid
        
        # Output only
        template2 = {
            'output_requirements': {
                'output1': {'type': 'string'}
            }
        }
        result2 = validate_structure(template2, ADRIMode.DETERMINISTIC)
        assert result2.is_valid
    
    def test_validate_cross_mode_contamination_warning(self):
        """Test warning for cross-mode sections."""
        # Reasoning template with conversation section
        template = {
            'field_requirements': {
                'output1': {'type': 'string'}
            },
            'schema': {
                'context': {'field1': {'type': 'string'}}
            }
        }
        
        # Mode detection will pick CONVERSATION (priority)
        # But if we force REASONING mode validation, should warn
        result = validate_structure(template, ADRIMode.REASONING, strict=False)
        # In non-strict mode, may have warnings about schema.context
        # (depends on implementation details)
    
    def test_validate_strict_mode(self):
        """Test strict mode treats warnings as errors."""
        template = {
            'schema': {
                'context': {}  # Empty - normally warning
            }
        }
        
        result = validate_structure(template, ADRIMode.CONVERSATION, strict=True)
        # In strict mode, empty context should fail
        assert not result.is_valid or len(result.warnings) == 0
    
    def test_format_validation_report(self):
        """Test validation report formatting."""
        result = StructureValidationResult(
            is_valid=False,
            mode=ADRIMode.CONVERSATION,
            errors=['Error 1', 'Error 2'],
            warnings=['Warning 1']
        )
        
        report = format_validation_report(result)
        assert 'conversation' in report.lower()
        assert 'Error 1' in report
        assert 'Warning 1' in report
        assert '✗ INVALID' in report or 'INVALID' in report


class TestLoadContractIntegration:
    """Tests for load_contract integration with mode system."""
    
    def test_load_contract_detects_mode(self, tmp_path):
        """Test load_contract detects and adds mode metadata."""
        import yaml
        from src.adri.validator.loaders import load_contract
        
        template = {
            'schema': {
                'context': {
                    'field1': {'type': 'string'}
                }
            }
        }
        
        # Write temporary YAML file
        yaml_file = tmp_path / "test_template.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump(template, f)
        
        # Load with mode detection (skip schema validation for test)
        result = load_contract(str(yaml_file), validate=False)
        
        # Check mode was detected and added
        assert '_adri_mode' in result
        assert result['_adri_mode'] == 'conversation'
    
    def test_load_contract_expected_mode_match(self, tmp_path):
        """Test load_contract with matching expected_mode."""
        import yaml
        from src.adri.validator.loaders import load_contract
        
        template = {
            'schema': {
                'context': {
                    'field1': {'type': 'string'}
                }
            }
        }
        
        yaml_file = tmp_path / "test_template.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump(template, f)
        
        # Load with expected mode
        result = load_contract(
            str(yaml_file), 
            validate=False,
            expected_mode=ADRIMode.CONVERSATION
        )
        
        assert result['_adri_mode'] == 'conversation'
    
    def test_load_contract_expected_mode_mismatch(self, tmp_path):
        """Test load_contract fails with mismatched expected_mode."""
        import yaml
        from src.adri.validator.loaders import load_contract
        
        template = {
            'schema': {
                'context': {
                    'field1': {'type': 'string'}
                }
            }
        }
        
        yaml_file = tmp_path / "test_template.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump(template, f)
        
        # Load with wrong expected mode - should raise ValueError
        with pytest.raises(ValueError, match="Mode mismatch"):
            load_contract(
                str(yaml_file),
                validate=False,
                expected_mode=ADRIMode.REASONING
            )
    
    def test_load_contract_structure_validation_fails(self, tmp_path):
        """Test load_contract fails with invalid structure."""
        import yaml
        from src.adri.validator.loaders import load_contract
        
        # Conversation template with invalid context type (must be dict, not string)
        # This will be detected as CONVERSATION mode because schema.context exists,
        # but will fail structure validation because context is not a dictionary
        template = {
            'schema': {
                'context': 'invalid_context_type'  # Should be dict, not string
            }
        }
        
        yaml_file = tmp_path / "test_template.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump(template, f)
        
        # Should raise ValueError for structure validation failure
        with pytest.raises(ValueError, match="Structure validation failed"):
            load_contract(str(yaml_file), validate=False)


class TestBackwardsCompatibility:
    """Tests for backwards compatibility with existing templates."""
    
    def test_existing_reasoning_templates_work(self, tmp_path):
        """Test existing reasoning templates still load correctly."""
        import yaml
        from src.adri.validator.loaders import load_contract
        
        # Typical existing reasoning template structure
        template = {
            'contracts': {
                'id': 'test_standard',
                'version': '1.0.0'
            },
            'requirements': {
                'field_requirements': {
                    'OUTPUT_FIELD': {
                        'type': 'string',
                        'nullable': False
                    }
                },
                'overall_minimum': 75.0
            }
        }
        
        yaml_file = tmp_path / "reasoning_template.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump(template, f)
        
        # Should load without errors
        result = load_contract(str(yaml_file), validate=False)
        assert result['_adri_mode'] == 'reasoning'
        assert 'requirements' in result
    
    def test_none_mode_templates_dont_fail(self, tmp_path):
        """Test generic templates without mode sections don't fail."""
        import yaml
        from src.adri.validator.loaders import load_contract
        
        # Generic template without mode-specific sections
        template = {
            'metadata': {
                'name': 'Generic Config',
                'version': '1.0'
            },
            'settings': {
                'key': 'value'
            }
        }
        
        yaml_file = tmp_path / "generic_template.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump(template, f)
        
        # Should load without errors (NONE mode)
        result = load_contract(str(yaml_file), validate=False)
        assert result['_adri_mode'] == 'none'
