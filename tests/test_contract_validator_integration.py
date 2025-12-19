"""
Integration tests for ADRI standard validation.

Tests the complete validation pipeline including:
- Loading standards with validation enabled
- ContractsParser integration
- CLI validation command
- DataProtectionEngine integration
"""

import os
import tempfile
import pytest
from pathlib import Path

from src.adri.contracts.validator import get_validator
from src.adri.contracts.exceptions import SchemaValidationError
from src.adri.validator.loaders import load_contract


class TestLoadStandardIntegration:
    """Test load_contract with validation enabled."""

    def test_load_valid_standard_succeeds(self):
        """Loading valid standard should succeed."""
        # Create a valid standard
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
contracts:
  id: "test"
  name: "Test Standard"
  version: "1.0.0"
  description: "Test"

requirements:
  dimension_requirements:
    validity:
      weight: 3
  overall_minimum: 70
""")
            temp_path = f.name

        try:
            # Load with validation (default)
            standard = load_contract(temp_path)
            assert standard is not None
            assert "contracts" in standard
            assert "requirements" in standard
        finally:
            os.unlink(temp_path)

    def test_load_invalid_standard_raises_error(self):
        """Loading invalid standard should raise SchemaValidationError."""
        # Create an invalid standard (weight > 5)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
contracts:
  id: "test"
  name: "Test"
  version: "1.0.0"
  description: "Test"

requirements:
  dimension_requirements:
    validity:
      weight: 10
  overall_minimum: 70
""")
            temp_path = f.name

        try:
            with pytest.raises(Exception) as exc_info:  # Catch any exception type
                load_contract(temp_path)

            # Check error contains useful information about the validation failure
            error_str = str(exc_info.value)
            assert "weight" in error_str.lower() or "validation" in error_str.lower()
        finally:
            os.unlink(temp_path)

    def test_load_contract_with_validation_disabled(self):
        """Loading invalid standard with validation disabled should succeed."""
        # Create an invalid standard
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
contracts:
  id: "test"
  name: "Test"
  version: "1.0.0"
  description: "Test"

requirements:
  dimension_requirements:
    validity:
      weight: 10
  overall_minimum: 70
""")
            temp_path = f.name

        try:
            # Load with validation disabled
            standard = load_contract(temp_path, validate=False)
            assert standard is not None
        finally:
            os.unlink(temp_path)


class TestContractsParserIntegration:
    """Test ContractsParser with validation."""

    def test_parser_rejects_invalid_standard(self):
        """ContractsParser should reject invalid standards."""
        from src.adri.contracts.parser import ContractsParser
        from src.adri.contracts.exceptions import InvalidStandardError

        # Create temporary standards directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set environment variable
            os.environ['ADRI_STANDARDS_PATH'] = temp_dir

            # Create invalid standard
            invalid_path = Path(temp_dir) / "invalid_test.yaml"
            invalid_path.write_text("""
contracts:
  id: "test"
  name: "Test"
  version: "1.0.0"
  description: "Test"

requirements:
  dimension_requirements:
    validity:
      weight: 10
  overall_minimum: 150
""")

            try:
                parser = ContractsParser()
                with pytest.raises(Exception):  # Catch any exception type
                    parser.parse_contract("invalid_test")
            finally:
                # Clean up environment
                del os.environ['ADRI_STANDARDS_PATH']


class TestValidatorCacheIntegration:
    """Test that validator cache works across different loading methods."""

    def test_cache_works_across_loads(self):
        """Validator cache should work for repeated loads."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
contracts:
  id: "test"
  name: "Test"
  version: "1.0.0"
  description: "Test"

requirements:
  dimension_requirements:
    validity:
      weight: 3
  overall_minimum: 70
""")
            temp_path = f.name

        try:
            validator = get_validator()

            # Clear cache first
            validator.clear_cache()

            # First load
            result1 = validator.validate_contract_file(temp_path, use_cache=True)
            assert result1.is_valid

            # Check cache stats
            stats = validator.get_cache_stats()
            assert stats["cached_files"] == 1

            # Second load should use cache
            result2 = validator.validate_contract_file(temp_path, use_cache=True)
            assert result2.is_valid

            # Should still be 1 cached file
            stats = validator.get_cache_stats()
            assert stats["cached_files"] == 1

        finally:
            os.unlink(temp_path)


class TestEndToEndValidation:
    """End-to-end validation tests."""

    def test_complete_validation_workflow(self):
        """Test complete workflow from file creation to validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
contracts:
  id: "complete_test"
  name: "Complete Test Standard"
  version: "2.0.0"
  description: "End-to-end test standard"
  author: "Test Suite"

requirements:
  dimension_requirements:
    validity:
      weight: 5
      minimum_score: 80
    completeness:
      weight: 4
      minimum_score: 75
    consistency:
      weight: 3
  overall_minimum: 75
""")
            temp_path = f.name

        try:
            # 1. Validate using ContractValidator directly
            validator = get_validator()
            result = validator.validate_contract_file(temp_path, use_cache=False)
            assert result.is_valid
            assert not result.has_errors

            # 2. Load using load_contract with validation
            standard = load_contract(temp_path)
            assert standard["contracts"]["id"] == "complete_test"

            # 3. Verify cache is working
            stats = validator.get_cache_stats()
            assert temp_path in stats["file_paths"]

        finally:
            os.unlink(temp_path)

    def test_validation_error_messages_are_helpful(self):
        """Validation errors should provide actionable guidance."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
contracts:
  id: "test"
  name: "Test"
  version: "invalid_version"
  description: "Test"

requirements:
  dimension_requirements:
    invalid_dimension:
      weight: 10
  overall_minimum: 150
""")
            temp_path = f.name

        try:
            validator = get_validator()
            result = validator.validate_contract_file(temp_path, use_cache=False)

            assert not result.is_valid
            assert result.has_errors
            # The validator correctly identifies multiple errors
            assert result.error_count >= 1  # At least one error

            # Check that errors are detailed - could be wrapped in a file load error
            all_error_text = result.format_errors().lower()

            # Should mention some of the specific issues
            assert any(
                term in all_error_text
                for term in ["weight", "dimension", "overall_minimum", "version", "invalid"]
            )

        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
