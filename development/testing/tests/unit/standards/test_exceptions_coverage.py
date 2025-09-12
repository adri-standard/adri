"""
Tests to improve coverage for adri.standards.exceptions module.

These tests target specific uncovered lines to reach 90%+ coverage.
"""

import pytest

from adri.standards.exceptions import (
    InvalidStandardError,
    StandardNotFoundError,
    StandardsDirectoryNotFoundError,
)


class TestExceptionsCoverage:
    """Tests targeting specific uncovered lines in exceptions.py."""

    def test_standard_not_found_error(self):
        """Test StandardNotFoundError exception."""
        standard_name = "missing_standard"
        error = StandardNotFoundError(standard_name)

        assert error.standard_name == standard_name
        assert (
            str(error) == f"Standard '{standard_name}' not found in bundled standards"
        )
        assert isinstance(error, Exception)

    def test_invalid_standard_error_with_standard_name(self):
        """Test InvalidStandardError with standard_name provided."""
        message = "Invalid YAML format"
        standard_name = "bad_standard"
        error = InvalidStandardError(message, standard_name)

        assert error.standard_name == standard_name
        assert str(error) == f"Invalid standard '{standard_name}': {message}"
        assert isinstance(error, Exception)

    def test_invalid_standard_error_without_standard_name(self):
        """Test InvalidStandardError without standard_name (lines 46-47)."""
        message = "Missing required fields"
        error = InvalidStandardError(message)

        assert error.standard_name is None
        assert str(error) == f"Invalid standard: {message}"
        assert isinstance(error, Exception)

    def test_standards_directory_not_found_error(self):
        """Test StandardsDirectoryNotFoundError exception."""
        directory_path = "/path/to/missing/standards"
        error = StandardsDirectoryNotFoundError(directory_path)

        assert error.directory_path == directory_path
        assert str(error) == f"Bundled standards directory not found: {directory_path}"
        assert isinstance(error, Exception)

    def test_exceptions_inheritance(self):
        """Test that all custom exceptions inherit from Exception."""
        # Test that all exceptions are proper Exception subclasses
        assert issubclass(StandardNotFoundError, Exception)
        assert issubclass(InvalidStandardError, Exception)
        assert issubclass(StandardsDirectoryNotFoundError, Exception)

    def test_exceptions_can_be_raised_and_caught(self):
        """Test that exceptions can be properly raised and caught."""
        # Test StandardNotFoundError
        with pytest.raises(StandardNotFoundError) as exc_info:
            raise StandardNotFoundError("test_standard")
        assert exc_info.value.standard_name == "test_standard"

        # Test InvalidStandardError with standard_name
        with pytest.raises(InvalidStandardError) as exc_info:
            raise InvalidStandardError("test message", "test_standard")
        assert exc_info.value.standard_name == "test_standard"

        # Test InvalidStandardError without standard_name (target lines 46-47)
        with pytest.raises(InvalidStandardError) as exc_info:
            raise InvalidStandardError("test message")
        assert exc_info.value.standard_name is None

        # Test StandardsDirectoryNotFoundError
        with pytest.raises(StandardsDirectoryNotFoundError) as exc_info:
            raise StandardsDirectoryNotFoundError("/test/path")
        assert exc_info.value.directory_path == "/test/path"

    def test_exception_attributes_are_accessible(self):
        """Test that exception attributes are properly set and accessible."""
        # Test StandardNotFoundError attributes
        error1 = StandardNotFoundError("test_standard")
        assert hasattr(error1, "standard_name")
        assert error1.standard_name == "test_standard"

        # Test InvalidStandardError attributes with standard_name
        error2 = InvalidStandardError("test message", "test_standard")
        assert hasattr(error2, "standard_name")
        assert error2.standard_name == "test_standard"

        # Test InvalidStandardError attributes without standard_name
        error3 = InvalidStandardError("test message")
        assert hasattr(error3, "standard_name")
        assert error3.standard_name is None

        # Test StandardsDirectoryNotFoundError attributes
        error4 = StandardsDirectoryNotFoundError("/test/path")
        assert hasattr(error4, "directory_path")
        assert error4.directory_path == "/test/path"

    def test_standards_directory_not_found_error_message(self):
        """Test StandardsDirectoryNotFoundError message formatting."""
        directory_path = "/path/to/missing/standards"
        error = StandardsDirectoryNotFoundError(directory_path)
        
        expected_message = f"Bundled standards directory not found: {directory_path}"
        assert str(error) == expected_message
        assert error.directory_path == directory_path
        
        # Test with different path to ensure initialization works properly
        another_path = "/another/missing/directory"
        another_error = StandardsDirectoryNotFoundError(another_path)
        assert str(another_error) == f"Bundled standards directory not found: {another_path}"
        assert another_error.directory_path == another_path
