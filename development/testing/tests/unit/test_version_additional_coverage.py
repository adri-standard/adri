"""
Additional comprehensive tests for version module to achieve 85%+ coverage.
Tests all edge cases and exception paths in _get_version_from_metadata.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

import pytest

from adri import version


class TestGetVersionFromMetadataEdgeCases:
    """Test edge cases and exception paths in _get_version_from_metadata."""

    @patch.dict(os.environ, {'ADRI_VERSION': '1.2.3'}, clear=True)
    def test_get_version_from_environment_variable(self):
        """Test getting version from ADRI_VERSION environment variable."""
        result = version._get_version_from_metadata()
        assert result == '1.2.3'

    @patch.dict(os.environ, {}, clear=True)
    def test_get_version_from_pyproject_toml_manual_parse(self):
        """Test getting version from pyproject.toml with manual parsing (no tomllib)."""
        toml_content = 'version = "2.0.0"\n'
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=toml_content)):
                with patch('importlib.import_module', side_effect=ImportError("No tomllib")):
                    with patch('importlib.metadata.version', side_effect=ImportError("No metadata")):
                        result = version._get_version_from_metadata()
                        assert result == '2.0.0'

    @patch.dict(os.environ, {}, clear=True)
    def test_get_version_pyproject_not_found(self):
        """Test when pyproject.toml is not found in any parent directories."""
        # Mock exists to always return False
        with patch('os.path.exists', return_value=False):
            with patch('importlib.metadata.version', return_value='3.0.0'):
                result = version._get_version_from_metadata()
                assert result == '3.0.0'

    @patch.dict(os.environ, {}, clear=True)
    def test_get_version_pyproject_file_not_found_exception(self):
        """Test FileNotFoundError when opening pyproject.toml."""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
                with patch('importlib.metadata.version', return_value='4.0.0'):
                    result = version._get_version_from_metadata()
                    assert result == '4.0.0'

    @patch.dict(os.environ, {}, clear=True)
    @patch('os.path.exists')
    def test_get_version_pyproject_key_error(self):
        """Test KeyError when pyproject.toml doesn't have expected structure."""
        toml_data = '{"other": {"key": "value"}}'  # Missing project.version
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=toml_data)):
                # Mock tomllib to return dict without project.version
                mock_tomllib = MagicMock()
                mock_tomllib.load.return_value = {"other": {"key": "value"}}
                
                with patch.dict('sys.modules', {'tomllib': mock_tomllib}):
                    with patch('importlib.metadata.version', return_value='5.0.0'):
                        result = version._get_version_from_metadata()
                        assert result == '5.0.0'

    @patch.dict(os.environ, {}, clear=True)
    @patch('os.path.exists')
    def test_get_version_pyproject_generic_exception(self):
        """Test generic exception during pyproject.toml processing."""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', side_effect=Exception("Generic error")):
                with patch('importlib.metadata.version', return_value='6.0.0'):
                    result = version._get_version_from_metadata()
                    assert result == '6.0.0'

    @patch.dict(os.environ, {}, clear=True)
    @patch('os.path.exists', return_value=False)
    def test_get_version_importlib_metadata_import_error(self):
        """Test ImportError when importing importlib.metadata."""
        with patch('importlib.import_module', side_effect=ImportError("No importlib.metadata")):
            result = version._get_version_from_metadata()
            assert result == '0.2.0'  # Fallback version

    @patch.dict(os.environ, {}, clear=True)
    @patch('os.path.exists', return_value=False)
    def test_get_version_importlib_metadata_generic_exception(self):
        """Test generic exception when using importlib.metadata."""
        with patch('importlib.metadata.version', side_effect=Exception("Metadata error")):
            result = version._get_version_from_metadata()
            assert result == '0.2.0'  # Fallback version

    @patch.dict(os.environ, {}, clear=True)
    @patch('os.path.exists')
    def test_get_version_pyproject_manual_parse_no_version_line(self):
        """Test manual parsing when version line is not found."""
        toml_content = """
[project]
name = "adri"
# No version line
dependencies = []
"""
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=toml_content)):
                with patch('importlib.import_module', side_effect=ImportError("No tomllib")):
                    with patch('importlib.metadata.version', return_value='7.0.0'):
                        result = version._get_version_from_metadata()
                        assert result == '7.0.0'

    @patch.dict(os.environ, {}, clear=True)
    @patch('os.path.exists')
    def test_get_version_pyproject_manual_parse_malformed_version_line(self):
        """Test manual parsing with malformed version line."""
        toml_content = """
[project]
name = "adri"
version = malformed
"""
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=toml_content)):
                with patch('importlib.import_module', side_effect=ImportError("No tomllib")):
                    with patch('importlib.metadata.version', return_value='8.0.0'):
                        result = version._get_version_from_metadata()
                        assert result == '8.0.0'

    @patch.dict(os.environ, {}, clear=True)
    def test_get_version_all_methods_fail(self):
        """Test when all version detection methods fail."""
        with patch('os.path.exists', return_value=False):
            with patch('importlib.metadata.version', side_effect=Exception("All failed")):
                result = version._get_version_from_metadata()
                assert result == '0.2.0'  # Final fallback

    def test_get_version_with_tomli_fallback(self):
        """Test getting version using tomli fallback for Python < 3.11."""
        toml_content = b'[project]\nversion = "9.0.0"\n'
        
        with patch.dict(os.environ, {}, clear=True):
            with patch('os.path.exists', return_value=True):
                # Mock tomllib import to fail, but tomli to succeed
                def mock_import(name):
                    if name == 'tomllib':
                        raise ImportError("No tomllib")
                    elif name == 'tomli':
                        mock_tomli = MagicMock()
                        mock_tomli.load.return_value = {"project": {"version": "9.0.0"}}
                        return mock_tomli
                    raise ImportError(f"No module {name}")
                
                with patch('importlib.import_module', side_effect=mock_import):
                    with patch('builtins.open', mock_open(read_data=toml_content)):
                        result = version._get_version_from_metadata()
                        assert result == '9.0.0'

    def test_get_version_with_both_toml_libraries_missing(self):
        """Test when both tomllib and tomli are missing."""
        toml_content = 'version = "10.0.0"\n'
        
        with patch.dict(os.environ, {}, clear=True):
            with patch('os.path.exists', return_value=True):
                with patch('importlib.import_module', side_effect=ImportError("No TOML libraries")):
                    with patch('builtins.open', mock_open(read_data=toml_content)):
                        result = version._get_version_from_metadata()
                        assert result == '10.0.0'  # Manual parsing should work

    @patch.dict(os.environ, {}, clear=True)
    def test_get_version_pyproject_search_multiple_levels(self):
        """Test searching for pyproject.toml in parent directories."""
        def mock_exists(path):
            # Only the third level up has pyproject.toml
            return 'level3' in path
        
        def mock_dirname(path):
            if 'current' in path:
                return path.replace('current', 'level1')
            elif 'level1' in path:
                return path.replace('level1', 'level2')
            elif 'level2' in path:
                return path.replace('level2', 'level3')
            else:
                return path
        
        with patch('os.path.exists', side_effect=mock_exists):
            with patch('os.path.dirname', side_effect=mock_dirname):
                with patch('os.path.abspath', return_value='/path/to/current/adri/version.py'):
                    with patch('builtins.open', mock_open(read_data='version = "11.0.0"\n')):
                        with patch('importlib.import_module', side_effect=ImportError("No tomllib")):
                            result = version._get_version_from_metadata()
                            assert result == '11.0.0'


class TestCompatibleVersionsEdgeCases:
    """Test edge cases in compatible versions functionality."""

    @patch.dict(os.environ, {'ADRI_COMPATIBLE_VERSIONS': ''}, clear=True)
    def test_compatible_versions_empty_environment(self):
        """Test with empty ADRI_COMPATIBLE_VERSIONS environment variable."""
        result = version._get_compatible_versions()
        # Should fall back to auto-generation
        assert version.__version__ in result
        assert "0.1.0" in result

    @patch.dict(os.environ, {'ADRI_COMPATIBLE_VERSIONS': '1.0.0,,2.0.0'}, clear=True)
    def test_compatible_versions_with_empty_values(self):
        """Test with empty values in ADRI_COMPATIBLE_VERSIONS."""
        result = version._get_compatible_versions()
        assert result == ['1.0.0', '', '2.0.0']

    @patch.dict(os.environ, {}, clear=True)
    @patch.object(version, '__version__', '1.0.0-beta.1')
    def test_compatible_versions_with_prerelease(self):
        """Test compatible versions generation with pre-release version."""
        result = version._get_compatible_versions()
        assert '1.0.0-beta.1' in result
        assert "0.1.0" in result

    @patch.dict(os.environ, {}, clear=True)
    @patch.object(version, '__version__', 'invalid.version.format')
    def test_compatible_versions_with_invalid_version(self):
        """Test compatible versions when current version is invalid format."""
        result = version._get_compatible_versions()
        # Should use fallback and include the invalid version
        assert 'invalid.version.format' in result
        assert "0.1.0" in result

    def test_compatible_versions_class_edge_cases(self):
        """Test edge cases for _CompatibleVersions class."""
        cv = version.__score_compatible_versions__
        
        # Test empty index access
        with pytest.raises(IndexError):
            _ = cv[999]  # Index that doesn't exist
        
        # Test negative indexing
        last_version = cv[-1]
        assert isinstance(last_version, str)
        
        # Test slicing (if supported)
        try:
            subset = cv[0:2]
            assert len(subset) <= 2
        except TypeError:
            # Slicing not supported, which is fine
            pass


class TestVersionCompatibilityEdgeCases:
    """Test edge cases in version compatibility functions."""

    def test_is_version_compatible_with_prerelease_versions(self):
        """Test version compatibility with pre-release versions."""
        current_major = version.__version__.split('.')[0]
        
        # Test pre-release versions
        assert version.is_version_compatible(f"{current_major}.1.0-alpha") is True
        assert version.is_version_compatible(f"{current_major}.1.0-beta.1") is True
        assert version.is_version_compatible(f"{current_major}.1.0-rc.1") is True

    def test_is_version_compatible_with_build_metadata(self):
        """Test version compatibility with build metadata."""
        current_major = version.__version__.split('.')[0]
        
        # Test versions with build metadata
        assert version.is_version_compatible(f"{current_major}.1.0+build.1") is True
        assert version.is_version_compatible(f"{current_major}.1.0-alpha+build.1") is True

    def test_is_version_compatible_empty_string(self):
        """Test version compatibility with empty string."""
        assert version.is_version_compatible("") is False

    def test_is_version_compatible_only_major_version(self):
        """Test version compatibility with only major version."""
        current_major = version.__version__.split('.')[0]
        assert version.is_version_compatible(current_major) is True

    def test_get_score_compatibility_message_edge_cases(self):
        """Test score compatibility message with edge cases."""
        # Test with empty string
        message = version.get_score_compatibility_message("")
        assert "Warning:" in message
        
        # Test with version that's in list but formatting edge case
        first_compatible = list(version.__score_compatible_versions__)[0]
        message = version.get_score_compatibility_message(first_compatible)
        assert "fully compatible" in message

    def test_version_info_with_dynamic_compatible_versions(self):
        """Test that version info returns current state of compatible versions."""
        info1 = version.get_version_info()
        
        # The compatible versions should match current state
        current_compatible = list(version.__score_compatible_versions__)
        assert info1["score_compatible_versions"] == current_compatible


class TestVersionModuleIntegration:
    """Test integration scenarios for version module."""

    def test_version_consistency_across_calls(self):
        """Test that version information is consistent across multiple calls."""
        # Multiple calls to various functions should return consistent results
        version1 = version.__version__
        version2 = version._get_version_from_metadata()
        
        # These should be the same
        assert version1 == version2
        
        # Multiple calls to get_version_info should be consistent
        info1 = version.get_version_info()
        info2 = version.get_version_info()
        assert info1 == info2

    def test_all_compatible_versions_are_valid_format(self):
        """Test that all versions in compatible list have valid format."""
        import re
        
        for v in version.__score_compatible_versions__:
            # Should be semantic version format (allowing pre-release)
            assert re.match(r'^\d+\.\d+\.\d+', v), f"Invalid version format: {v}"

    def test_current_version_compatibility_comprehensive(self):
        """Test comprehensive compatibility checks for current version."""
        current = version.__version__
        
        # Current version should be compatible with itself
        assert version.is_version_compatible(current) is True
        
        # Current version should be in compatible list
        assert current in version.__score_compatible_versions__
        
        # Compatibility message should indicate full compatibility
        message = version.get_score_compatibility_message(current)
        assert "fully compatible" in message.lower()
        
        # Version info should include current version
        info = version.get_version_info()
        assert info["version"] == current

    def test_module_constants_immutability(self):
        """Test that module constants behave as expected."""
        # These should be strings
        assert isinstance(version.__version__, str)
        assert isinstance(version.__min_compatible_version__, str)
        
        # Compatible versions should behave like a collection
        cv = version.__score_compatible_versions__
        assert hasattr(cv, '__iter__')
        assert hasattr(cv, '__contains__')
        assert hasattr(cv, '__len__')
