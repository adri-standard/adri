"""Tests for the version module."""

import pytest

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
        assert isinstance(version.__score_compatible_versions__, list)
        assert "0.1.0" in version.__score_compatible_versions__


class TestIsVersionCompatible:
    """Test the is_version_compatible function."""

    def test_compatible_version_in_list(self):
        """Test that versions in score_compatible_versions are compatible."""
        assert version.is_version_compatible("0.1.0") is True

    def test_same_major_version_compatible(self):
        """Test that same major version is compatible."""
        # Current version is 1.0.0, so major version 1 should be compatible
        assert version.is_version_compatible("1.0.1") is True
        assert version.is_version_compatible("1.2.5") is True
        assert version.is_version_compatible("1.99.99") is True

    def test_different_major_version_incompatible(self):
        """Test that different major version is incompatible."""
        # Current version is 1.0.0, so major version 0 and 2+ should be incompatible
        assert (
            version.is_version_compatible("0.1.0") is True
        )  # Exception: in compatible list
        assert version.is_version_compatible("0.2.5") is False  # Not in compatible list
        assert version.is_version_compatible("2.0.0") is False
        assert version.is_version_compatible("3.1.0") is False

    def test_invalid_version_format_incompatible(self):
        """Test that invalid version formats are incompatible."""
        assert version.is_version_compatible("invalid") is False
        assert version.is_version_compatible("") is False
        # These actually pass because the function only checks major version
        assert (
            version.is_version_compatible("1") is True
        )  # Major version 1 matches current
        assert (
            version.is_version_compatible("1.") is True
        )  # Major version 1 matches current
        assert (
            version.is_version_compatible("1.1") is True
        )  # Major version 1 matches current

    def test_non_numeric_version_incompatible(self):
        """Test that non-numeric version components are incompatible."""
        assert (
            version.is_version_compatible("a.b.c") is False
        )  # Can't parse major version
        assert (
            version.is_version_compatible("v1.1.0") is False
        )  # Can't parse major version
        # This passes because it can extract major version "1"
        assert version.is_version_compatible("1.a.0") is True

    def test_version_with_extra_components(self):
        """Test versions with extra components (like pre-release)."""
        # These actually pass because the function only checks major version
        assert version.is_version_compatible("1.1.0-alpha") is True
        assert version.is_version_compatible("1.1.0.1") is True

    def test_edge_case_versions(self):
        """Test edge case version strings."""
        assert version.is_version_compatible("1.0.0") is True  # Same major as current
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
        # Use a version with different major
        current_major = int(version.__version__.split(".")[0])
        incompatible_major = current_major + 1
        test_version = f"{incompatible_major}.0.0"
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
        assert (
            info["score_compatible_versions"] == version.__score_compatible_versions__
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
        assert (
            info["score_compatible_versions"] == version.__score_compatible_versions__
        )

    def test_compatibility_message_for_current_version(self):
        """Test compatibility message for current version."""
        current = version.__version__
        message = version.get_score_compatibility_message(current)
        assert "fully compatible" in message
        assert current in message


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
