"""
Tests for the main adri __init__.py module.
"""

from unittest.mock import MagicMock, patch

import pytest


class TestMainInit:
    """Test the main adri __init__.py module."""

    def test_version_import(self):
        """Test that version information is properly imported."""
        from adri import __version__, get_version_info

        assert isinstance(__version__, str)
        assert __version__ == "1.0.0"

        version_info = get_version_info()
        assert isinstance(version_info, dict)
        assert version_info["version"] == "1.0.0"

    def test_adri_protected_import(self):
        """Test that adri_protected decorator is properly imported."""
        from adri import adri_protected

        # Test that it's callable
        assert callable(adri_protected)

        # Test basic decorator functionality
        @adri_protected(data_param="test_data")
        def test_function(test_data):
            return test_data

        assert callable(test_function)

    def test_optional_imports_when_available(self):
        """Test that optional components are imported when available."""
        from adri import DataProfiler, StandardGenerator

        # These should be available in the current setup
        assert DataProfiler is not None
        assert StandardGenerator is not None

        # Test they can be instantiated
        profiler = DataProfiler()
        generator = StandardGenerator()

        assert profiler is not None
        assert generator is not None

    @patch("adri.core.assessor.DataQualityAssessor", None)
    def test_missing_assessor_import(self):
        """Test graceful handling when DataQualityAssessor is missing."""
        # This test simulates the import failing
        import importlib

        import adri

        # Force reload to test import error handling
        importlib.reload(adri)

        # Should not raise an error even if component is missing
        from adri import __version__

        assert __version__ == "1.0.0"

    @patch("adri.core.protection.DataProtectionEngine", None)
    def test_missing_protection_import(self):
        """Test graceful handling when DataProtectionEngine is missing."""
        # This test simulates the import failing
        import importlib

        import adri

        # Force reload to test import error handling
        importlib.reload(adri)

        # Should not raise an error even if component is missing
        from adri import __version__

        assert __version__ == "1.0.0"

    def test_all_exports(self):
        """Test that __all__ contains expected exports."""
        import adri

        # Check that __all__ exists and contains core exports
        assert hasattr(adri, "__all__")
        assert "__version__" in adri.__all__
        assert "adri_protected" in adri.__all__
        assert "get_version_info" in adri.__all__

    def test_module_metadata(self):
        """Test that module metadata is properly set."""
        import adri

        # Test author information
        assert hasattr(adri, "__author__")
        assert adri.__author__ == "Thomas"

        # Test email
        assert hasattr(adri, "__email__")
        assert adri.__email__ == "thomas@adri.dev"

        # Test license
        assert hasattr(adri, "__license__")
        assert adri.__license__ == "MIT"

        # Test description
        assert hasattr(adri, "__description__")
        assert "Stop Your AI Agents Breaking on Bad Data" in adri.__description__

        # Test URL
        assert hasattr(adri, "__url__")
        assert "github.com" in adri.__url__

    def test_module_docstring(self):
        """Test that module has proper docstring."""
        import adri

        assert adri.__doc__ is not None
        assert "ADRI - Stop Your AI Agents Breaking on Bad Data" in adri.__doc__
        assert "Quick Start:" in adri.__doc__
        assert "CLI Usage:" in adri.__doc__

    def test_import_error_handling(self):
        """Test that import errors are handled gracefully."""
        # Mock an import error scenario
        with patch(
            "adri.analysis.data_profiler.DataProfiler",
            side_effect=ImportError("Mock import error"),
        ):
            # This should not raise an error
            import importlib

            import adri

            importlib.reload(adri)

            # Core functionality should still work
            from adri import __version__, adri_protected

            assert __version__ == "1.0.0"
            assert callable(adri_protected)

    def test_conditional_exports(self):
        """Test that exports are conditionally added to __all__."""
        import adri

        # Test that available components are in __all__
        if hasattr(adri, "DataProfiler") and adri.DataProfiler is not None:
            assert "DataProfiler" in adri.__all__

        if hasattr(adri, "StandardGenerator") and adri.StandardGenerator is not None:
            assert "StandardGenerator" in adri.__all__

    def test_fallback_behavior(self):
        """Test fallback behavior when components are missing."""
        # Test that the module can be imported even with missing components
        with patch.dict("sys.modules", {"adri.core.assessor": None}):
            import importlib

            import adri

            # Should not crash
            importlib.reload(adri)

            # Core functionality should work
            assert hasattr(adri, "__version__")
            assert hasattr(adri, "adri_protected")


class TestImportStructure:
    """Test the import structure and dependencies."""

    def test_core_imports_available(self):
        """Test that core imports are available."""
        # These should always be available
        from adri import __version__, adri_protected, get_version_info

        assert __version__ is not None
        assert adri_protected is not None
        assert get_version_info is not None

    def test_optional_imports_structure(self):
        """Test the structure of optional imports."""
        import adri

        # Test that optional components have proper fallback
        optional_components = [
            "DataQualityAssessor",
            "DataProtectionEngine",
            "DataProfiler",
            "StandardGenerator",
        ]

        for component in optional_components:
            # Component should either exist or be None
            if hasattr(adri, component):
                value = getattr(adri, component)
                assert value is None or callable(value)

    def test_import_paths(self):
        """Test that import paths are correct."""
        # Test direct imports work
        from adri.decorators.guard import adri_protected
        from adri.version import __version__, get_version_info

        assert callable(adri_protected)
        assert isinstance(__version__, str)
        assert callable(get_version_info)

    def test_circular_import_prevention(self):
        """Test that there are no circular import issues."""
        # This test ensures that importing the main module doesn't cause circular imports
        import adri
        import adri.decorators.guard
        import adri.version

        # Should be able to access all without issues
        assert adri.__version__ == adri.version.__version__
        assert adri.adri_protected == adri.decorators.guard.adri_protected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
