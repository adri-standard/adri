"""
Integration tests for divergence metadata validation and inference.

Tests the complete flow including StandardSchema validation and ContractValidator inference.
NOTE: Several tests in this module are for planned features not yet fully implemented.
"""

import pytest
import yaml
from adri.contracts.validator import ContractValidator
from adri.contracts.schema import StandardSchema


class TestDivergenceMetadataFullValidation:
    """Test full standard validation with divergence metadata."""

    def test_valid_standard_with_divergence_metadata(self):
        """Test that a valid standard with divergence metadata passes validation."""
        standard = {
            "contracts": {
                "id": "test-standard",
                "name": "Test Standard",
                "version": "1.0.0",
                "description": "Test standard with divergence metadata",
            },
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 3,
                        "field_requirements": {
                            "CUSTOMER_ID": {
                                "type": "string",
                                "nullable": False,
                                "deterministic": True,
                            },
                            "AI_SUMMARY": {
                                "type": "string",
                                "nullable": False,
                                "ai_generated": True,
                                "deterministic": False,
                            }
                        }
                    }
                },
                "overall_minimum": 70,
            }
        }

        validator = ContractValidator()
        result = validator.validate_contract(standard, use_cache=False)
        
        assert result.is_valid
        # Should have no errors for valid divergence metadata
        assert len(result.errors) == 0

    @pytest.mark.skip(reason="Divergence metadata type validation not yet implemented")
    def test_invalid_deterministic_type_caught(self):
        """Test that invalid deterministic type is caught during validation."""
        standard = {
            "contracts": {
                "id": "test-standard",
                "name": "Test Standard",
                "version": "1.0.0",
                "description": "Test",
            },
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 3,
                        "field_requirements": {
                            "TEST_FIELD": {
                                "type": "string",
                                "deterministic": "true",  # Invalid: string instead of bool
                            }
                        }
                    }
                },
                "overall_minimum": 70,
            }
        }

        validator = ContractValidator()
        result = validator.validate_contract(standard, use_cache=False)
        
        assert not result.is_valid
        assert any("deterministic type" in e.message.lower() for e in result.errors)

    @pytest.mark.skip(reason="Contradictory divergence metadata warning not yet implemented")
    def test_contradictory_metadata_generates_warning(self):
        """Test that contradictory metadata generates warnings."""
        standard = {
            "contracts": {
                "id": "test-standard",
                "name": "Test Standard",
                "version": "1.0.0",
                "description": "Test",
            },
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 3,
                        "field_requirements": {
                            "TEST_FIELD": {
                                "type": "string",
                                "deterministic": True,
                                "ai_generated": True,  # Contradictory
                            }
                        }
                    }
                },
                "overall_minimum": 70,
            }
        }

        validator = ContractValidator()
        result = validator.validate_contract(standard, use_cache=False)
        
        # Should still be valid (warnings don't make it invalid)
        assert result.is_valid
        # But should have warnings
        assert len(result.warnings) > 0
        assert any("contradictory" in w.message.lower() for w in result.warnings)


class TestDivergenceMetadataInference:
    """Test inference suggestions for divergence metadata."""

    @pytest.mark.skip(reason="Divergence metadata inference suggestions not yet implemented")
    def test_suggests_deterministic_for_derived_fields(self):
        """Test that validator suggests deterministic=true for derived fields with allowed_values."""
        standard = {
            "contracts": {
                "id": "test-standard",
                "name": "Test Standard",
                "version": "1.0.0",
                "description": "Test",
            },
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 3,
                        "field_requirements": {
                            "STATUS_CODE": {
                                "type": "string",
                                "is_derived": True,
                                "allowed_values": ["ACTIVE", "INACTIVE"],  #  Simple format
                                # Missing deterministic metadata - should get suggestion
                            }
                        }
                    }
                },
                "overall_minimum": 70,
            }
        }

        validator = ContractValidator()
        result = validator.validate_contract(standard, use_cache=False)
        
        # May fail enhanced allowed_values validation but that's not what we're testing
        # Just check that inference suggestion is present
        assert len(result.warnings) > 0
        assert any(
            "is_derived=true" in w.message and "deterministic=true" in w.message.lower()
            for w in result.warnings
        )

    @pytest.mark.skip(reason="Divergence metadata inference suggestions not yet implemented")
    def test_suggests_ai_generated_for_ai_fields(self):
        """Test that validator suggests ai_generated=true for AI-named fields."""
        standard = {
            "contracts": {
                "id": "test-standard",
                "name": "Test Standard",
                "version": "1.0.0",
                "description": "Test",
            },
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 3,
                        "field_requirements": {
                            "AI_SUMMARY": {  # AI-related name
                                "type": "string",
                                # Missing ai_generated metadata
                            }
                        }
                    }
                },
                "overall_minimum": 70,
            }
        }

        validator = ContractValidator()
        result = validator.validate_contract(standard, use_cache=False)
        
        assert result.is_valid
        # Should have inference suggestion
        assert len(result.warnings) > 0
        assert any(
            "ai-generated" in w.message.lower() and "ai_generated=true" in w.message.lower()
            for w in result.warnings
        )

    def test_no_suggestion_when_metadata_present(self):
        """Test that no suggestions are made when metadata is already present."""
        standard = {
            "contracts": {
                "id": "test-standard",
                "name": "Test Standard",
                "version": "1.0.0",
                "description": "Test",
            },
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 3,
                        "field_requirements": {
                            "STATUS_CODE": {
                                "type": "string",
                                "is_derived": True,
                                "deterministic": True,  # Already specified - no suggestion needed
                                "allowed_values": ["ACTIVE", "INACTIVE"],
                            }
                        }
                    }
                },
                "overall_minimum": 70,
            }
        }

        validator = ContractValidator()
        result = validator.validate_contract(standard, use_cache=False)
        
        # Should have no divergence inference warnings (metadata already present)
        divergence_warnings = [
            w for w in result.warnings
            if ("deterministic" in w.message.lower() or "ai_generated" in w.message.lower())
            and "consider adding" in w.message.lower()
        ]
        assert len(divergence_warnings) == 0

    @pytest.mark.skip(reason="Divergence metadata inference suggestions not yet implemented")
    def test_multiple_fields_with_different_suggestions(self):
        """Test inference for multiple fields with different needs."""
        standard = {
            "contracts": {
                "id": "test-standard",
                "name": "Test Standard",
                "version": "1.0.0",
                "description": "Test",
            },
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 3,
                        "field_requirements": {
                            "RISK_LEVEL": {
                                "type": "string",
                                "is_derived": True,
                                "allowed_values": ["LOW", "HIGH"],
                            },
                            "GPT_RECOMMENDATION": {
                                "type": "string",
                            },
                            "CUSTOMER_NAME": {
                                "type": "string",
                            }
                        }
                    }
                },
                "overall_minimum": 70,
            }
        }

        validator = ContractValidator()
        result = validator.validate_contract(standard, use_cache=False)
        
        # Should have suggestions for RISK_LEVEL and GPT_RECOMMENDATION
        warnings_text = " ".join(w.message for w in result.warnings)
        assert "RISK_LEVEL" in warnings_text
        assert "GPT_RECOMMENDATION" in warnings_text


class TestBackwardCompatibility:
    """Test backward compatibility with existing standards."""

    def test_standards_without_divergence_metadata_still_valid(self):
        """Test that existing standards without divergence metadata remain valid."""
        standard = {
            "contracts": {
                "id": "legacy-standard",
                "name": "Legacy Standard",
                "version": "1.0.0",
                "description": "Standard without divergence metadata",
            },
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 3,
                        "field_requirements": {
                            "CUSTOMER_ID": {
                                "type": "string",
                                "nullable": False,
                            }
                        }
                    }
                },
                "overall_minimum": 70,
            }
        }

        validator = ContractValidator()
        result = validator.validate_contract(standard, use_cache=False)
        
        assert result.is_valid
        assert len(result.errors) == 0

    def test_mixed_fields_some_with_some_without_metadata(self):
        """Test standards with mixed fields (some with metadata, some without)."""
        standard = {
            "contracts": {
                "id": "mixed-standard",
                "name": "Mixed Standard",
                "version": "1.0.0",
                "description": "Mixed metadata",
            },
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 3,
                        "field_requirements": {
                            "FIELD_WITH_METADATA": {
                                "type": "string",
                                "deterministic": True,
                            },
                            "FIELD_WITHOUT_METADATA": {
                                "type": "string",
                            }
                        }
                    }
                },
                "overall_minimum": 70,
            }
        }

        validator = ContractValidator()
        result = validator.validate_contract(standard, use_cache=False)
        
        assert result.is_valid
        assert len(result.errors) == 0


class TestRealWorldScenarios:
    """Test real-world scenarios with divergence metadata."""

    def test_roadmap_style_standard(self):
        """Test a roadmap-style standard with mixed deterministic and AI fields."""
        standard = {
            "contracts": {
                "id": "roadmap-standard",
                "name": "Roadmap Standard",
                "version": "1.0.0",
                "description": "Roadmap with divergence metadata",
            },
            "requirements": {
                "dimension_requirements": {
                    "validity": {
                        "weight": 5,
                        "field_requirements": {
                            "ITEM_ID": {
                                "type": "string",
                                "nullable": False,
                            },
                            "HEALTH_SCORE": {
                                "type": "integer",
                                "nullable": False,
                                "deterministic": True,
                            },
                            "AI_STATUS_SUMMARY": {
                                "type": "string",
                                "nullable": False,
                                "ai_generated": True,
                                "deterministic": False,
                            },
                            "AI_RISK_RATIONALE": {
                                "type": "string",
                                "nullable": True,
                                "ai_generated": True,
                                "deterministic": False,
                            }
                        }
                    }
                },
                "overall_minimum": 70,
            }
        }

        validator = ContractValidator()
        result = validator.validate_contract(standard, use_cache=False)
        
        assert result.is_valid
        assert len(result.errors) == 0
