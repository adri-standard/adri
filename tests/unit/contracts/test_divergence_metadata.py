"""
Unit tests for divergence metadata validation.

Tests the validate_divergence_metadata function in StandardSchema.
NOTE: These tests are for a planned feature that is not yet implemented.
"""

import pytest
from adri.contracts.schema import StandardSchema


# Skip all tests in this module - validate_divergence_metadata not yet implemented
pytestmark = pytest.mark.skip(
    reason="StandardSchema.validate_divergence_metadata not yet implemented - planned for future release"
)


class TestDivergenceMetadataTypeValidation:
    """Test type validation for divergence metadata fields."""

    def test_deterministic_must_be_bool(self):
        """Test that deterministic field must be a boolean."""
        field_req = {
            "type": "string",
            "deterministic": "true",  # String instead of bool
        }
        errors = StandardSchema.validate_divergence_metadata(
            "TEST_FIELD", field_req, "test.path"
        )
        
        assert len(errors) == 1
        assert "deterministic type" in errors[0].lower()
        assert "Expected bool" in errors[0]

    def test_ai_generated_must_be_bool(self):
        """Test that ai_generated field must be a boolean."""
        field_req = {
            "type": "string",
            "ai_generated": 1,  # Integer instead of bool
        }
        errors = StandardSchema.validate_divergence_metadata(
            "TEST_FIELD", field_req, "test.path"
        )
        
        assert len(errors) == 1
        assert "ai_generated type" in errors[0].lower()
        assert "Expected bool" in errors[0]

    def test_accepts_bool_true(self):
        """Test that boolean true is accepted."""
        field_req = {
            "type": "string",
            "deterministic": True,
            "ai_generated": False,
        }
        errors = StandardSchema.validate_divergence_metadata(
            "TEST_FIELD", field_req, "test.path"
        )
        
        # Should have no type errors (but may have warnings)
        type_errors = [e for e in errors if "type" in e.lower() and "invalid" in e.lower()]
        assert len(type_errors) == 0

    def test_accepts_bool_false(self):
        """Test that boolean false is accepted."""
        field_req = {
            "type": "string",
            "deterministic": False,
            "ai_generated": False,
        }
        errors = StandardSchema.validate_divergence_metadata(
            "TEST_FIELD", field_req, "test.path"
        )
        
        # Should have no type errors
        type_errors = [e for e in errors if "type" in e.lower() and "invalid" in e.lower()]
        assert len(type_errors) == 0

    def test_accepts_none_values(self):
        """Test that None/missing values are accepted."""
        field_req = {
            "type": "string",
        }
        errors = StandardSchema.validate_divergence_metadata(
            "TEST_FIELD", field_req, "test.path"
        )
        
        assert len(errors) == 0


class TestDivergenceMetadataMutualExclusivity:
    """Test mutual exclusivity warnings for divergence metadata."""

    def test_warns_both_true(self):
        """Test warning when both deterministic and ai_generated are true."""
        field_req = {
            "type": "string",
            "deterministic": True,
            "ai_generated": True,
        }
        errors = StandardSchema.validate_divergence_metadata(
            "TEST_FIELD", field_req, "test.path"
        )
        
        # Should have warning about contradiction
        warnings = [e for e in errors if "contradictory" in e.lower()]
        assert len(warnings) == 1
        assert "deterministic=true" in warnings[0]
        assert "ai_generated=true" in warnings[0]

    def test_allows_both_false(self):
        """Test that both false is allowed without warning."""
        field_req = {
            "type": "string",
            "deterministic": False,
            "ai_generated": False,
        }
        errors = StandardSchema.validate_divergence_metadata(
            "TEST_FIELD", field_req, "test.path"
        )
        
        # No mutual exclusivity warnings
        warnings = [e for e in errors if "contradictory" in e.lower()]
        assert len(warnings) == 0

    def test_allows_deterministic_true_ai_false(self):
        """Test that deterministic=true, ai_generated=false is valid."""
        field_req = {
            "type": "string",
            "deterministic": True,
            "ai_generated": False,
        }
        errors = StandardSchema.validate_divergence_metadata(
            "TEST_FIELD", field_req, "test.path"
        )
        
        # No warnings about mutual exclusivity
        warnings = [e for e in errors if "contradictory" in e.lower()]
        assert len(warnings) == 0

    def test_allows_deterministic_false_ai_true(self):
        """Test that deterministic=false, ai_generated=true is valid."""
        field_req = {
            "type": "string",
            "deterministic": False,
            "ai_generated": True,
        }
        errors = StandardSchema.validate_divergence_metadata(
            "TEST_FIELD", field_req, "test.path"
        )
        
        # No warnings
        warnings = [e for e in errors if "contradictory" in e.lower()]
        assert len(warnings) == 0

    def test_allows_one_set_one_none(self):
        """Test that setting one and leaving the other unset is valid."""
        field_req = {
            "type": "string",
            "deterministic": True,
        }
        errors = StandardSchema.validate_divergence_metadata(
            "TEST_FIELD", field_req, "test.path"
        )
        
        assert len(errors) == 0


class TestDivergenceMetadataConsistencyChecks:
    """Test consistency checks with other field properties."""

    def test_warns_derived_but_not_deterministic(self):
        """Test warning when is_derived=true but deterministic=false."""
        field_req = {
            "type": "string",
            "is_derived": True,
            "deterministic": False,
        }
        errors = StandardSchema.validate_divergence_metadata(
            "TEST_FIELD", field_req, "test.path"
        )
        
        # Should warn about inconsistency
        warnings = [e for e in errors if "is_derived=true" in e.lower() and "deterministic=false" in e.lower()]
        assert len(warnings) == 1

    def test_no_warning_derived_and_deterministic(self):
        """Test no warning when is_derived=true and deterministic=true."""
        field_req = {
            "type": "string",
            "is_derived": True,
            "deterministic": True,
        }
        errors = StandardSchema.validate_divergence_metadata(
            "TEST_FIELD", field_req, "test.path"
        )
        
        # No warnings about consistency
        warnings = [e for e in errors if "is_derived" in e.lower()]
        assert len(warnings) == 0

    def test_no_warning_not_derived(self):
        """Test no warning when is_derived=false."""
        field_req = {
            "type": "string",
            "is_derived": False,
            "deterministic": False,
        }
        errors = StandardSchema.validate_divergence_metadata(
            "TEST_FIELD", field_req, "test.path"
        )
        
        # No warnings
        warnings = [e for e in errors if "is_derived" in e.lower()]
        assert len(warnings) == 0

    def test_no_warning_derived_missing_deterministic(self):
        """Test no warning when is_derived=true but deterministic not set."""
        field_req = {
            "type": "string",
            "is_derived": True,
        }
        errors = StandardSchema.validate_divergence_metadata(
            "TEST_FIELD", field_req, "test.path"
        )
        
        # No warnings (deterministic not specified is fine)
        warnings = [e for e in errors if "is_derived" in e.lower()]
        assert len(warnings) == 0


class TestDivergenceMetadataIntegration:
    """Test integration with validate_field_requirement."""

    def test_field_requirement_calls_divergence_validation(self):
        """Test that validate_field_requirement includes divergence checks."""
        field_req = {
            "type": "string",
            "deterministic": "not_a_bool",  # Invalid type
        }
        errors = StandardSchema.validate_field_requirement(
            "TEST_FIELD", field_req, "test.path"
        )
        
        # Should include divergence validation error
        assert any("deterministic type" in e.lower() for e in errors)

    def test_multiple_divergence_errors_collected(self):
        """Test that multiple divergence errors are collected."""
        field_req = {
            "type": "string",
            "deterministic": "invalid",
            "ai_generated": 123,
        }
        errors = StandardSchema.validate_field_requirement(
            "TEST_FIELD", field_req, "test.path"
        )
        
        # Should have both type errors
        assert sum(1 for e in errors if "type" in e.lower() and "invalid" in e.lower()) == 2

    def test_valid_divergence_metadata_no_errors(self):
        """Test that valid divergence metadata produces no errors."""
        field_req = {
            "type": "string",
            "nullable": False,
            "deterministic": True,
            "ai_generated": False,
        }
        errors = StandardSchema.validate_field_requirement(
            "TEST_FIELD", field_req, "test.path"
        )
        
        assert len(errors) == 0


class TestDivergenceMetadataEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_field_requirement(self):
        """Test handling of empty field requirement dict."""
        field_req = {}
        errors = StandardSchema.validate_divergence_metadata(
            "TEST_FIELD", field_req, "test.path"
        )
        
        assert len(errors) == 0

    def test_field_with_all_metadata(self):
        """Test field with all possible metadata."""
        field_req = {
            "type": "string",
            "nullable": False,
            "is_derived": True,
            "deterministic": True,
            "ai_generated": False,
            "allowed_values": {
                "type": "categorical",
                "categories": {
                    "A": {"description": "Category A"},
                    "B": {"description": "Category B"},
                }
            }
        }
        errors = StandardSchema.validate_divergence_metadata(
            "TEST_FIELD", field_req, "test.path"
        )
        
        # Should be valid
        assert len(errors) == 0

    def test_error_message_includes_field_name(self):
        """Test that error messages include the field name."""
        field_req = {
            "deterministic": "invalid",
        }
        errors = StandardSchema.validate_divergence_metadata(
            "MY_FIELD", field_req, "my.path"
        )
        
        assert any("MY_FIELD" in e for e in errors)
        assert any("my.path" in e for e in errors)

    def test_case_with_multiple_warnings(self):
        """Test case that generates multiple warnings."""
        field_req = {
            "is_derived": True,
            "deterministic": True,
            "ai_generated": True,  # Both true - contradictory
        }
        errors = StandardSchema.validate_divergence_metadata(
            "TEST_FIELD", field_req, "test.path"
        )
        
        # Should have warning about contradiction
        warnings = [e for e in errors if "contradictory" in e.lower()]
        assert len(warnings) == 1
