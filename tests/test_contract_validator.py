"""
Comprehensive unit tests for ADRI standard validation.

This test suite validates the ContractValidator implementation including:
- Structure validation
- Type validation
- Range validation
- Caching behavior
- Error message formatting
- Thread safety
"""

import os
import pytest
import tempfile
import time
import threading
from pathlib import Path
from typing import Dict, Any

from src.adri.contracts.validator import ContractValidator, get_validator
from src.adri.contracts.exceptions import (
    ValidationResult,
    ValidationError,
    ValidationSeverity,
    SchemaValidationError
)
from src.adri.contracts.schema import StandardSchema


# Fixture paths
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "contracts"
VALID_FIXTURES_DIR = FIXTURES_DIR / "valid"
INVALID_FIXTURES_DIR = FIXTURES_DIR / "invalid"


class TestValidationResult:
    """Test ValidationResult dataclass functionality."""

    def test_empty_result_is_valid(self):
        """Empty result should be valid by default."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid
        assert not result.has_errors
        assert not result.has_warnings
        assert result.error_count == 0
        assert result.warning_count == 0

    def test_add_error_marks_invalid(self):
        """Adding error should mark result as invalid."""
        result = ValidationResult(is_valid=True)
        result.add_error("Test error", "test.path")

        assert not result.is_valid
        assert result.has_errors
        assert result.error_count == 1
        assert not result.has_warnings

    def test_add_warning_keeps_valid(self):
        """Adding warning should not affect validity."""
        result = ValidationResult(is_valid=True)
        result.add_warning("Test warning", "test.path")

        assert result.is_valid
        assert not result.has_errors
        assert result.has_warnings
        assert result.warning_count == 1

    def test_error_formatting(self):
        """Test error message formatting."""
        result = ValidationResult(is_valid=True)
        result.add_error(
            "Invalid value",
            "test.field",
            expected="number",
            actual="string",
            suggestion="Use a numeric value"
        )

        formatted = result.format_errors()
        assert "Invalid value" in formatted
        assert "test.field" in formatted
        assert "Expected: number" in formatted
        assert "Actual: string" in formatted
        assert "Use a numeric value" in formatted

    def test_summary_formatting(self):
        """Test summary formatting."""
        result = ValidationResult(is_valid=False, standard_path="/path/to/standard.yaml")
        result.add_error("Error 1", "path1")
        result.add_warning("Warning 1", "path2")

        summary = result.format_summary()
        assert "/path/to/standard.yaml" in summary
        assert "INVALID" in summary
        assert "Errors: 1" in summary
        assert "Warnings: 1" in summary


class TestStandardSchema:
    """Test StandardSchema validation methods."""

    def test_validate_top_level_structure_valid(self):
        """Valid top-level structure should pass."""
        standard = {
            "contracts": {},
            "requirements": {}
        }
        errors = StandardSchema.validate_top_level_structure(standard)
        assert len(errors) == 0

    def test_validate_top_level_structure_missing_contracts(self):
        """Missing 'contracts' section should fail."""
        standard = {
            "requirements": {}
        }
        errors = StandardSchema.validate_top_level_structure(standard)
        assert len(errors) == 1
        assert "contracts" in errors[0].lower()

    def test_validate_top_level_structure_missing_requirements(self):
        """Missing 'requirements' section should fail."""
        standard = {
            "contracts": {}
        }
        errors = StandardSchema.validate_top_level_structure(standard)
        assert len(errors) == 1
        assert "requirements" in errors[0].lower()

    def test_validate_top_level_structure_unexpected_section(self):
        """Unexpected top-level section should fail."""
        standard = {
            "contracts": {},
            "requirements": {},
            "unexpected": {}
        }
        errors = StandardSchema.validate_top_level_structure(standard)
        assert len(errors) == 1
        assert "unexpected" in errors[0].lower()

    def test_validate_field_type_correct(self):
        """Correct field type should pass."""
        error = StandardSchema.validate_field_type("test", str, "test.field")
        assert error is None

    def test_validate_field_type_incorrect(self):
        """Incorrect field type should fail."""
        error = StandardSchema.validate_field_type(123, str, "test.field")
        assert error is not None
        assert "test.field" in error
        assert "str" in error
        assert "int" in error

    def test_validate_field_type_multiple_types(self):
        """Multiple valid types should work."""
        error1 = StandardSchema.validate_field_type(123, (int, float), "test.field")
        error2 = StandardSchema.validate_field_type(123.5, (int, float), "test.field")
        assert error1 is None
        assert error2 is None

        error3 = StandardSchema.validate_field_type("string", (int, float), "test.field")
        assert error3 is not None

    def test_validate_numeric_range_valid(self):
        """Value within range should pass."""
        error = StandardSchema.validate_numeric_range(3, 0, 5, "test.weight")
        assert error is None

    def test_validate_numeric_range_below_minimum(self):
        """Value below minimum should fail."""
        error = StandardSchema.validate_numeric_range(-1, 0, 5, "test.weight")
        assert error is not None
        assert "below minimum" in error.lower()

    def test_validate_numeric_range_above_maximum(self):
        """Value above maximum should fail."""
        error = StandardSchema.validate_numeric_range(10, 0, 5, "test.weight")
        assert error is not None
        assert "exceeds maximum" in error.lower()

    def test_validate_version_string_valid(self):
        """Valid version strings should pass."""
        assert StandardSchema.validate_version_string("1.0.0") is None
        assert StandardSchema.validate_version_string("2.1.3") is None
        assert StandardSchema.validate_version_string("10.20.30") is None

    def test_validate_version_string_invalid(self):
        """Invalid version strings should fail."""
        error1 = StandardSchema.validate_version_string("1")
        error2 = StandardSchema.validate_version_string("")
        error3 = StandardSchema.validate_version_string("invalid")

        assert error1 is not None
        assert error2 is not None
        assert error3 is not None

    def test_validate_overall_minimum_valid(self):
        """Valid overall_minimum values should pass."""
        assert StandardSchema.validate_overall_minimum(0) is None
        assert StandardSchema.validate_overall_minimum(50) is None
        assert StandardSchema.validate_overall_minimum(100) is None
        assert StandardSchema.validate_overall_minimum(75.5) is None

    def test_validate_overall_minimum_invalid_type(self):
        """Non-numeric overall_minimum should fail."""
        error = StandardSchema.validate_overall_minimum("75")
        assert error is not None
        assert "number" in error.lower()

    def test_validate_overall_minimum_out_of_range(self):
        """Out of range overall_minimum should fail."""
        error1 = StandardSchema.validate_overall_minimum(-10)
        error2 = StandardSchema.validate_overall_minimum(150)

        assert error1 is not None
        assert error2 is not None


class TestContractValidatorBasics:
    """Test basic ContractValidator functionality."""

    def test_validator_initialization(self):
        """Validator should initialize with empty cache."""
        validator = ContractValidator()
        stats = validator.get_cache_stats()
        assert stats["cached_files"] == 0

    def test_get_validator_singleton(self):
        """get_validator should return singleton instance."""
        validator1 = get_validator()
        validator2 = get_validator()
        assert validator1 is validator2

    def test_validate_valid_minimal_standard(self):
        """Minimal valid standard should pass validation."""
        standard = {
            "contracts": {
                "id": "test",
                "name": "Test",
                "version": "1.0.0",
                "description": "Test standard"
            },
            "requirements": {
                "dimension_requirements": {
                    "validity": {"weight": 3}
                },
                "overall_minimum": 70
            }
        }

        validator = ContractValidator()
        result = validator.validate_contract(standard, use_cache=False)

        assert result.is_valid
        assert not result.has_errors
        assert result.error_count == 0

    def test_validate_invalid_missing_contracts_section(self):
        """Missing 'contracts' section should fail."""
        standard = {
            "requirements": {
                "dimension_requirements": {
                    "validity": {"weight": 3}
                },
                "overall_minimum": 70
            }
        }

        validator = ContractValidator()
        result = validator.validate_contract(standard, use_cache=False)

        assert not result.is_valid
        assert result.has_errors
        assert any("contracts" in err.message.lower() for err in result.errors)

    def test_validate_invalid_weight_range(self):
        """Weight outside valid range should fail."""
        standard = {
            "contracts": {
                "id": "test",
                "name": "Test",
                "version": "1.0.0",
                "description": "Test"
            },
            "requirements": {
                "dimension_requirements": {
                    "validity": {"weight": 10}  # Invalid: > 5
                },
                "overall_minimum": 70
            }
        }

        validator = ContractValidator()
        result = validator.validate_contract(standard, use_cache=False)

        assert not result.is_valid
        assert result.has_errors
        assert any("weight" in err.path.lower() for err in result.errors)

    def test_validate_invalid_overall_minimum(self):
        """overall_minimum outside valid range should fail."""
        standard = {
            "contracts": {
                "id": "test",
                "name": "Test",
                "version": "1.0.0",
                "description": "Test"
            },
            "requirements": {
                "dimension_requirements": {
                    "validity": {"weight": 3}
                },
                "overall_minimum": 150  # Invalid: > 100
            }
        }

        validator = ContractValidator()
        result = validator.validate_contract(standard, use_cache=False)

        assert not result.is_valid
        assert result.has_errors
        assert any("overall_minimum" in err.path.lower() for err in result.errors)

    def test_validate_invalid_dimension_name(self):
        """Invalid dimension name should fail."""
        standard = {
            "contracts": {
                "id": "test",
                "name": "Test",
                "version": "1.0.0",
                "description": "Test"
            },
            "requirements": {
                "dimension_requirements": {
                    "invalid_dimension": {"weight": 3}
                },
                "overall_minimum": 70
            }
        }

        validator = ContractValidator()
        result = validator.validate_contract(standard, use_cache=False)

        assert not result.is_valid
        assert result.has_errors
        assert any("invalid_dimension" in err.message.lower() for err in result.errors)


class TestContractValidatorFixtures:
    """Test validator against fixture files."""

    def test_validate_minimal_valid_fixture(self):
        """Minimal valid fixture should pass."""
        fixture_path = VALID_FIXTURES_DIR / "minimal_valid_standard.yaml"
        if not fixture_path.exists():
            pytest.skip("Fixture file not found")

        validator = ContractValidator()
        result = validator.validate_contract_file(str(fixture_path), use_cache=False)

        assert result.is_valid, f"Errors: {result.format_errors()}"
        assert not result.has_errors

    def test_validate_comprehensive_valid_fixture(self):
        """Comprehensive valid fixture should pass."""
        fixture_path = VALID_FIXTURES_DIR / "comprehensive_valid_standard.yaml"
        if not fixture_path.exists():
            pytest.skip("Fixture file not found")

        validator = ContractValidator()
        result = validator.validate_contract_file(str(fixture_path), use_cache=False)

        assert result.is_valid, f"Errors: {result.format_errors()}"
        assert not result.has_errors

    def test_validate_missing_contracts_section_fixture(self):
        """Missing standards section fixture should fail."""
        fixture_path = INVALID_FIXTURES_DIR / "missing_standards_section.yaml"
        if not fixture_path.exists():
            pytest.skip("Fixture file not found")

        validator = ContractValidator()
        result = validator.validate_contract_file(str(fixture_path), use_cache=False)

        assert not result.is_valid
        assert result.has_errors

    def test_validate_invalid_weight_range_fixture(self):
        """Invalid weight range fixture should fail."""
        fixture_path = INVALID_FIXTURES_DIR / "invalid_weight_range.yaml"
        if not fixture_path.exists():
            pytest.skip("Fixture file not found")

        validator = ContractValidator()
        result = validator.validate_contract_file(str(fixture_path), use_cache=False)

        assert not result.is_valid
        assert result.has_errors

    def test_validate_invalid_overall_minimum_fixture(self):
        """Invalid overall_minimum fixture should fail."""
        fixture_path = INVALID_FIXTURES_DIR / "invalid_overall_minimum.yaml"
        if not fixture_path.exists():
            pytest.skip("Fixture file not found")

        validator = ContractValidator()
        result = validator.validate_contract_file(str(fixture_path), use_cache=False)

        assert not result.is_valid
        assert result.has_errors

    def test_validate_invalid_dimension_name_fixture(self):
        """Invalid dimension name fixture should fail."""
        fixture_path = INVALID_FIXTURES_DIR / "invalid_dimension_name.yaml"
        if not fixture_path.exists():
            pytest.skip("Fixture file not found")

        validator = ContractValidator()
        result = validator.validate_contract_file(str(fixture_path), use_cache=False)

        assert not result.is_valid
        assert result.has_errors


class TestValidatorCaching:
    """Test validator caching behavior."""

    def test_cache_stores_result(self):
        """Validation result should be cached."""
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
            validator = ContractValidator()

            # First validation
            result1 = validator.validate_contract_file(temp_path, use_cache=True)
            assert result1.is_valid

            stats = validator.get_cache_stats()
            assert stats["cached_files"] == 1
            assert temp_path in stats["file_paths"]

            # Second validation should use cache
            result2 = validator.validate_contract_file(temp_path, use_cache=True)
            assert result2.is_valid

        finally:
            os.unlink(temp_path)

    def test_cache_invalidation_on_file_modification(self):
        """Cache should invalidate when file is modified."""
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
            validator = ContractValidator()

            # First validation
            result1 = validator.validate_contract_file(temp_path, use_cache=True)
            assert result1.is_valid

            # Wait a bit to ensure mtime changes
            time.sleep(0.1)

            # Modify file
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write("""
contracts:
  id: "test2"
  name: "Test2"
  version: "2.0.0"
  description: "Test2"
requirements:
  dimension_requirements:
    validity:
      weight: 4
  overall_minimum: 80
""")

            # Validation should detect file change
            result2 = validator.validate_contract_file(temp_path, use_cache=True)
            assert result2.is_valid

        finally:
            os.unlink(temp_path)

    def test_clear_cache_all(self):
        """clear_cache() should clear all cached results."""
        validator = ContractValidator()

        # Add some cached results
        validator._cache["path1"] = (ValidationResult(is_valid=True), 12345.0)
        validator._cache["path2"] = (ValidationResult(is_valid=True), 12346.0)

        assert len(validator._cache) == 2

        validator.clear_cache()

        assert len(validator._cache) == 0

    def test_clear_cache_specific_file(self):
        """clear_cache(path) should clear only that file."""
        validator = ContractValidator()

        # Add some cached results
        validator._cache["path1"] = (ValidationResult(is_valid=True), 12345.0)
        validator._cache["path2"] = (ValidationResult(is_valid=True), 12346.0)

        validator.clear_cache("path1")

        assert "path1" not in validator._cache
        assert "path2" in validator._cache


class TestValidatorThreadSafety:
    """Test validator thread safety."""

    def test_concurrent_validation(self):
        """Validator should handle concurrent validation safely."""
        validator = ContractValidator()
        results = []
        errors = []

        standard = {
            "contracts": {
                "id": "test",
                "name": "Test",
                "version": "1.0.0",
                "description": "Test"
            },
            "requirements": {
                "dimension_requirements": {
                    "validity": {"weight": 3}
                },
                "overall_minimum": 70
            }
        }

        def validate_standard():
            try:
                result = validator.validate_contract(standard, use_cache=False)
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Run 10 concurrent validations
        threads = [threading.Thread(target=validate_standard) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10
        assert all(r.is_valid for r in results)


class TestValidatorErrorMessages:
    """Test validator error message quality."""

    def test_error_messages_include_path(self):
        """Error messages should include field path."""
        standard = {
            "contracts": {
                "id": "test",
                "name": "Test",
                "version": "1.0.0",
                "description": "Test"
            },
            "requirements": {
                "dimension_requirements": {
                    "validity": {"weight": "invalid"}  # Wrong type
                },
                "overall_minimum": 70
            }
        }

        validator = ContractValidator()
        result = validator.validate_contract(standard, use_cache=False)

        assert not result.is_valid
        assert result.has_errors
        # Check that error path includes the field location
        error_paths = [err.path for err in result.errors]
        assert any("weight" in path.lower() for path in error_paths)

    def test_error_messages_include_suggestions(self):
        """Error messages should include helpful suggestions."""
        standard = {
            "contracts": {
                "id": "test",
                "name": "Test",
                "version": "1",  # Invalid format
                "description": "Test"
            },
            "requirements": {
                "dimension_requirements": {
                    "validity": {"weight": 3}
                },
                "overall_minimum": 70
            }
        }

        validator = ContractValidator()
        result = validator.validate_contract(standard, use_cache=False)

        assert not result.is_valid
        # Check that at least one error has a suggestion
        has_suggestion = any(err.suggestion for err in result.errors)
        assert has_suggestion


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
