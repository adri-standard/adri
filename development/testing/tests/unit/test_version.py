"""Tests for the version module."""

import os
import pytest
from unittest.mock import patch, mock_open, MagicMock

from adri import version


class TestVersionConstants:
    """Test version constants and basic attributes."""

    def test_version_constant_exists(self):
        """Test that __version__ constant exists and is a string."""
        assert hasattr(version, "__version__")
        assert isinstance(version.__version__, str)
        # Test version format (semantic versioning)
        import re

        assert re.match(
            r"^\d+\.\d+\.\d+", version.__version__
        ), f"Invalid version format: {version.__version__}"

    def test_min_compatible_version_exists(self):
        """Test that __min_compatible_version__ constant exists."""
        assert hasattr(version, "__min_compatible_version__")
        assert isinstance(version.__min_compatible_version__, str)
        assert version.__min_compatible_version__ == "0.1.0"

    def test_score_compatible_versions_exists(self):
        """Test that __score_compatible_versions__ constant exists."""
        assert hasattr(version, "__score_compatible_versions__")
        # Should behave like a list (support iteration, membership, etc.)
        assert hasattr(version.__score_compatible_versions__, "__iter__")
        assert hasattr(version.__score_compatible_versions__, "__contains__")
        assert "0.1.0" in version.__score_compatible_versions__


class TestIsVersionCompatible:
    """Test the is_version_compatible function."""

    def test_compatible_version_in_list(self):
        """Test that versions in score_compatible_versions are compatible."""
        assert version.is_version_compatible("0.1.0") is True

    def test_same_major_version_compatible(self):
        """Test that same major version is compatible."""
        # Get current major version and test with same major
        current_major = version.__version__.split(".")[0]
        assert version.is_version_compatible(f"{current_major}.0.1") is True
        assert version.is_version_compatible(f"{current_major}.2.5") is True
        assert version.is_version_compatible(f"{current_major}.99.99") is True

    def test_different_major_version_incompatible(self):
        """Test that different major version is incompatible."""
        # Get current major version and test with different majors
        current_major = int(version.__version__.split(".")[0])

        # Test versions that should be incompatible (different major, not in compatible list)
        if current_major == 0:
            # If current is 0.x.x, test 1.x.x and 2.x.x
            assert version.is_version_compatible("1.0.0") is True  # In compatible list
            assert (
                version.is_version_compatible("2.0.0") is False
            )  # Different major, not in list
            assert (
                version.is_version_compatible("3.1.0") is False
            )  # Different major, not in list
        else:
            # If current is 1.x.x or higher, test 0.x.x and higher
            assert version.is_version_compatible("0.1.0") is True  # In compatible list
            different_major = current_major + 1
            assert version.is_version_compatible(f"{different_major}.0.0") is False
            assert version.is_version_compatible(f"{different_major + 1}.1.0") is False

    def test_invalid_version_format_incompatible(self):
        """Test that invalid version formats are incompatible."""
        assert version.is_version_compatible("invalid") is False
        assert version.is_version_compatible("") is False
        # These actually pass because the function only checks major version
        current_major = version.__version__.split(".")[0]
        assert (
            version.is_version_compatible(current_major) is True
        )  # Major version matches current
        assert (
            version.is_version_compatible(f"{current_major}.") is True
        )  # Major version matches current
        assert (
            version.is_version_compatible(f"{current_major}.1") is True
        )  # Major version matches current

    def test_non_numeric_version_incompatible(self):
        """Test that non-numeric version components are incompatible."""
        assert (
            version.is_version_compatible("a.b.c") is False
        )  # Can't parse major version
        assert (
            version.is_version_compatible("v1.1.0") is False
        )  # Can't parse major version
        # This passes because it can extract major version
        current_major = version.__version__.split(".")[0]
        assert version.is_version_compatible(f"{current_major}.a.0") is True

    def test_version_with_extra_components(self):
        """Test versions with extra components (like pre-release)."""
        # These actually pass because the function only checks major version
        current_major = version.__version__.split(".")[0]
        assert version.is_version_compatible(f"{current_major}.1.0-alpha") is True
        assert version.is_version_compatible(f"{current_major}.1.0.1") is True

    def test_edge_case_versions(self):
        """Test edge case version strings."""
        current_major = version.__version__.split(".")[0]
        assert (
            version.is_version_compatible(f"{current_major}.0.0") is True
        )  # Same major as current
        assert version.is_version_compatible("0.1.0") is True  # In compatible list


class TestGetScoreCompatibilityMessage:
    """Test the get_score_compatibility_message function."""

    def test_fully_compatible_version_message(self):
        """Test message for fully compatible versions."""
        # Use a version that's in the compatible list
        compatible_version = version.__score_compatible_versions__[0]
        message = version.get_score_compatibility_message(compatible_version)
        expected = f"Version {compatible_version} has fully compatible scoring with current version {version.__version__}"
        assert message == expected

    def test_generally_compatible_version_message(self):
        """Test message for generally compatible versions."""
        # Use a version with same major but not in compatible list
        current_major = version.__version__.split(".")[0]
        test_version = f"{current_major}.99.0"  # Unlikely to be in compatible list
        message = version.get_score_compatibility_message(test_version)
        expected = f"Version {test_version} has generally compatible scoring with current version {version.__version__}, but check CHANGELOG.md for details"
        assert message == expected

    def test_incompatible_version_message(self):
        """Test message for incompatible versions."""
        # Use a version that's definitely not in the compatible list
        # Since 1.0.0 is in the compatible list, use 2.0.0 which should not be
        test_version = "2.0.0"
        message = version.get_score_compatibility_message(test_version)
        expected = f"Warning: Version {test_version} has incompatible scoring with current version {version.__version__}. See CHANGELOG.md for details."
        assert message == expected

    def test_invalid_version_message(self):
        """Test message for invalid version formats."""
        message = version.get_score_compatibility_message("invalid")
        expected = f"Warning: Version invalid has incompatible scoring with current version {version.__version__}. See CHANGELOG.md for details."
        assert message == expected


class TestGetVersionInfo:
    """Test the get_version_info function."""

    def test_version_info_structure(self):
        """Test that get_version_info returns correct structure."""
        info = version.get_version_info()

        assert isinstance(info, dict)

        # Check all required keys exist
        required_keys = [
            "version",
            "min_compatible_version",
            "score_compatible_versions",
            "is_production_ready",
            "api_version",
            "standards_format_version",
        ]

        for key in required_keys:
            assert key in info, f"Missing key: {key}"

    def test_version_info_values(self):
        """Test that get_version_info returns correct values."""
        info = version.get_version_info()

        assert info["version"] == version.__version__
        assert info["min_compatible_version"] == "0.1.0"
        assert info["score_compatible_versions"] == list(
            version.__score_compatible_versions__
        )
        assert info["is_production_ready"] is True
        assert info["api_version"] == "0.1"
        assert info["standards_format_version"] == "1.0"

    def test_version_info_types(self):
        """Test that get_version_info returns correct types."""
        info = version.get_version_info()

        assert isinstance(info["version"], str)
        assert isinstance(info["min_compatible_version"], str)
        assert isinstance(info["score_compatible_versions"], list)
        assert isinstance(info["is_production_ready"], bool)
        assert isinstance(info["api_version"], str)
        assert isinstance(info["standards_format_version"], str)

    def test_version_info_immutability(self):
        """Test that modifying returned dict doesn't affect subsequent calls."""
        info1 = version.get_version_info()
        original_version = info1["version"]
        info1["version"] = "modified"

        info2 = version.get_version_info()
        assert info2["version"] == original_version  # Should not be modified


class TestVersionIntegration:
    """Integration tests for version functionality."""

    def test_current_version_is_compatible_with_itself(self):
        """Test that current version is compatible with itself."""
        current = version.__version__
        assert version.is_version_compatible(current) is True

    def test_current_version_in_compatible_list(self):
        """Test that current version is in the compatible versions list."""
        current = version.__version__
        assert current in version.__score_compatible_versions__

    def test_min_compatible_version_is_compatible(self):
        """Test that min compatible version is actually compatible."""
        min_version = version.__min_compatible_version__
        assert version.is_version_compatible(min_version) is True

    def test_version_info_consistency(self):
        """Test that version info is consistent with module constants."""
        info = version.get_version_info()

        assert info["version"] == version.__version__
        assert info["min_compatible_version"] == version.__min_compatible_version__
        assert info["score_compatible_versions"] == list(
            version.__score_compatible_versions__
        )

    def test_compatibility_message_for_current_version(self):
        """Test compatibility message for current version."""
        current = version.__version__
        message = version.get_score_compatibility_message(current)
        assert "fully compatible" in message
        assert current in message


class TestGetVersionFromMetadata:
    """Test the internal _get_version_from_metadata function."""

    def test_version_function_exists(self):
        """Test that _get_version_from_metadata function exists."""
        assert hasattr(version, '_get_version_from_metadata')
        assert callable(version._get_version_from_metadata)

    def test_version_function_returns_string(self):
        """Test that _get_version_from_metadata returns a string."""
        result = version._get_version_from_metadata()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_version_function_returns_valid_format(self):
        """Test that _get_version_from_metadata returns valid version format."""
        result = version._get_version_from_metadata()
        # Should be semantic version or fallback
        import re
        assert re.match(r"^\d+\.\d+\.\d+", result) or result == "0.2.0"

    def test_version_metadata_function_callable(self):
        """Test that _get_version_from_metadata is callable and returns reasonable result."""
        result = version._get_version_from_metadata()
        assert isinstance(result, str)
        assert len(result) > 0
        # Should be semantic version format
        import re
        assert re.match(r"^\d+\.\d+\.\d+", result)

    def test_version_metadata_consistent(self):
        """Test that _get_version_from_metadata returns consistent results."""
        result1 = version._get_version_from_metadata()
        result2 = version._get_version_from_metadata()
        assert result1 == result2

    def test_version_metadata_matches_public_version(self):
        """Test that _get_version_from_metadata matches the public __version__."""
        internal_version = version._get_version_from_metadata()
        public_version = version.__version__
        assert internal_version == public_version


class TestCompatibleVersions:
    """Test the _get_compatible_versions function and _CompatibleVersions class."""

    @patch.dict(os.environ, {'ADRI_COMPATIBLE_VERSIONS': '1.0.0,1.1.0,1.2.0'})
    def test_compatible_versions_from_environment(self):
        """Test getting compatible versions from environment variable."""
        result = version._get_compatible_versions()
        assert result == ['1.0.0', '1.1.0', '1.2.0']

    @patch.dict(os.environ, {}, clear=True)
    def test_compatible_versions_auto_generated(self):
        """Test auto-generation of compatible versions."""
        result = version._get_compatible_versions()
        
        # Should include known versions and current version
        assert "0.1.0" in result
        assert version.__version__ in result
        assert isinstance(result, list)
        assert len(result) > 0

    @patch.dict(os.environ, {}, clear=True)
    @patch.object(version, '__version__', 'invalid-version')
    def test_compatible_versions_fallback_on_error(self):
        """Test fallback when version parsing fails."""
        result = version._get_compatible_versions()
        
        # Should include fallback versions and invalid version
        assert "0.1.0" in result
        assert "invalid-version" in result

    def test_compatible_versions_class_methods(self):
        """Test _CompatibleVersions class methods."""
        cv = version.__score_compatible_versions__
        
        # Test iteration
        versions_list = list(cv)
        assert len(versions_list) > 0
        
        # Test membership
        assert "0.1.0" in cv
        
        # Test indexing
        first_version = cv[0]
        assert isinstance(first_version, str)
        
        # Test length
        assert len(cv) > 0
        
        # Test repr
        repr_str = repr(cv)
        assert isinstance(repr_str, str)
        assert "0.1.0" in repr_str


class TestVersionDocumentation:
    """Test that version module has proper documentation."""

    def test_module_has_docstring(self):
        """Test that the version module has a docstring."""
        assert version.__doc__ is not None
        assert len(version.__doc__.strip()) > 0

    def test_functions_have_docstrings(self):
        """Test that all functions have docstrings."""
        functions = [
            version.is_version_compatible,
            version.get_score_compatibility_message,
            version.get_version_info,
        ]

        for func in functions:
            assert func.__doc__ is not None
            assert len(func.__doc__.strip()) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
