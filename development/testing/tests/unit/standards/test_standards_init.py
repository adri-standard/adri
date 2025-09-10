"""
Tests for the standards __init__.py module.
"""

from unittest.mock import MagicMock, patch

import pytest

from adri.standards import (
    default_loader,
    InvalidStandardError,
    list_available_standards,
    load_standard,
    standard_exists,
    StandardNotFoundError,
    StandardsLoader,
)


class TestStandardsInit:
    """Test the standards __init__.py module."""

    def test_imports_available(self):
        """Test that all expected imports are available."""
        # Test that classes are imported
        assert StandardsLoader is not None
        assert StandardNotFoundError is not None
        assert InvalidStandardError is not None

        # Test that functions are imported
        assert callable(load_standard)
        assert callable(list_available_standards)
        assert callable(standard_exists)

        # Test that default loader exists
        assert default_loader is not None
        assert isinstance(default_loader, StandardsLoader)

    def test_all_exports(self):
        """Test that __all__ contains expected exports."""
        import adri.standards

        assert hasattr(adri.standards, "__all__")
        expected_exports = [
            "StandardsLoader",
            "StandardNotFoundError",
            "InvalidStandardError",
        ]

        for export in expected_exports:
            assert export in adri.standards.__all__

    def test_module_docstring(self):
        """Test that module has proper docstring."""
        import adri.standards

        assert adri.standards.__doc__ is not None
        assert "ADRI Standards Module" in adri.standards.__doc__
        assert "offline-first" in adri.standards.__doc__

    @patch.object(StandardsLoader, "load_standard")
    def test_load_standard_convenience_function(self, mock_load):
        """Test the load_standard convenience function."""
        mock_load.return_value = {"test": "standard"}

        result = load_standard("test_standard")

        mock_load.assert_called_once_with("test_standard")
        assert result == {"test": "standard"}

    @patch.object(StandardsLoader, "load_standard")
    def test_load_standard_exception_propagation(self, mock_load):
        """Test that load_standard propagates exceptions."""
        mock_load.side_effect = StandardNotFoundError("Standard not found")

        with pytest.raises(StandardNotFoundError):
            load_standard("nonexistent_standard")

    @patch.object(StandardsLoader, "list_available_standards")
    def test_list_available_standards_convenience_function(self, mock_list):
        """Test the list_available_standards convenience function."""
        mock_list.return_value = ["standard1", "standard2", "standard3"]

        result = list_available_standards()

        mock_list.assert_called_once()
        assert result == ["standard1", "standard2", "standard3"]

    @patch.object(StandardsLoader, "standard_exists")
    def test_standard_exists_convenience_function(self, mock_exists):
        """Test the standard_exists convenience function."""
        mock_exists.return_value = True

        result = standard_exists("test_standard")

        mock_exists.assert_called_once_with("test_standard")
        assert result is True

    @patch.object(StandardsLoader, "standard_exists")
    def test_standard_exists_false_case(self, mock_exists):
        """Test the standard_exists convenience function returns False."""
        mock_exists.return_value = False

        result = standard_exists("nonexistent_standard")

        mock_exists.assert_called_once_with("nonexistent_standard")
        assert result is False

    def test_default_loader_is_standards_loader_instance(self):
        """Test that default_loader is an instance of StandardsLoader."""
        assert isinstance(default_loader, StandardsLoader)

    def test_default_loader_singleton_behavior(self):
        """Test that default_loader behaves like a singleton."""
        import adri.standards

        # Get the default loader multiple times
        loader1 = adri.standards.default_loader
        loader2 = adri.standards.default_loader

        # Should be the same instance
        assert loader1 is loader2

    def test_convenience_functions_use_default_loader(self):
        """Test that convenience functions use the default loader."""
        import adri.standards

        # Mock the default loader's methods
        with (
            patch.object(adri.standards.default_loader, "load_standard") as mock_load,
            patch.object(
                adri.standards.default_loader, "list_available_standards"
            ) as mock_list,
            patch.object(
                adri.standards.default_loader, "standard_exists"
            ) as mock_exists,
        ):
            mock_load.return_value = {"test": "data"}
            mock_list.return_value = ["test"]
            mock_exists.return_value = True

            # Call convenience functions
            load_result = load_standard("test")
            list_result = list_available_standards()
            exists_result = standard_exists("test")

            # Verify they called the default loader
            mock_load.assert_called_once_with("test")
            mock_list.assert_called_once()
            mock_exists.assert_called_once_with("test")

            assert load_result == {"test": "data"}
            assert list_result == ["test"]
            assert exists_result is True


class TestStandardsExceptions:
    """Test the standards exceptions."""

    def test_standard_not_found_error_inheritance(self):
        """Test that StandardNotFoundError inherits from Exception."""
        assert issubclass(StandardNotFoundError, Exception)

        # Test instantiation
        error = StandardNotFoundError("test_standard")
        assert str(error) == "Standard 'test_standard' not found in bundled standards"
        assert error.standard_name == "test_standard"

    def test_invalid_standard_error_inheritance(self):
        """Test that InvalidStandardError inherits from Exception."""
        assert issubclass(InvalidStandardError, Exception)

        # Test instantiation with standard name
        error = InvalidStandardError("Test message", "test_standard")
        assert str(error) == "Invalid standard 'test_standard': Test message"
        assert error.standard_name == "test_standard"

        # Test instantiation without standard name
        error2 = InvalidStandardError("Test message")
        assert str(error2) == "Invalid standard: Test message"
        assert error2.standard_name is None

    def test_exceptions_can_be_raised_and_caught(self):
        """Test that exceptions can be raised and caught properly."""
        # Test StandardNotFoundError
        with pytest.raises(StandardNotFoundError) as exc_info:
            raise StandardNotFoundError("Standard not found")
        assert "Standard not found" in str(exc_info.value)

        # Test InvalidStandardError
        with pytest.raises(InvalidStandardError) as exc_info:
            raise InvalidStandardError("Invalid standard")
        assert "Invalid standard" in str(exc_info.value)


class TestStandardsIntegration:
    """Integration tests for the standards module."""

    def test_full_import_chain(self):
        """Test that the full import chain works."""
        # Test importing from the module
        from adri.standards import load_standard, StandardsLoader
        from adri.standards.exceptions import StandardNotFoundError
        from adri.standards.loader import StandardsLoader as DirectLoader

        # Should be the same classes
        assert StandardsLoader is DirectLoader

        # Should be able to use them
        loader = StandardsLoader()
        assert isinstance(loader, StandardsLoader)

    def test_module_level_access(self):
        """Test accessing components at module level."""
        import adri.standards

        # Test accessing through module
        assert hasattr(adri.standards, "StandardsLoader")
        assert hasattr(adri.standards, "load_standard")
        assert hasattr(adri.standards, "default_loader")

        # Test they're the same as direct imports
        from adri.standards import default_loader, load_standard, StandardsLoader

        assert adri.standards.StandardsLoader is StandardsLoader
        assert adri.standards.load_standard is load_standard
        assert adri.standards.default_loader is default_loader

    @patch("adri.standards.loader.StandardsLoader.load_standard")
    def test_error_handling_integration(self, mock_load):
        """Test error handling integration across the module."""
        # Test that errors from the loader are properly propagated
        mock_load.side_effect = StandardNotFoundError("Test standard not found")

        with pytest.raises(StandardNotFoundError) as exc_info:
            load_standard("test_standard")

        assert "Test standard not found" in str(exc_info.value)
        mock_load.assert_called_once_with("test_standard")


class TestStandardsDocumentation:
    """Test documentation and metadata."""

    def test_convenience_functions_have_docstrings(self):
        """Test that convenience functions have proper docstrings."""
        functions = [load_standard, list_available_standards, standard_exists]

        for func in functions:
            assert func.__doc__ is not None
            assert len(func.__doc__.strip()) > 0
            assert "Args:" in func.__doc__ or "Returns:" in func.__doc__

    def test_module_structure_documentation(self):
        """Test that the module structure is well documented."""
        import adri.standards

        # Module should have docstring explaining its purpose
        assert adri.standards.__doc__ is not None
        assert "standards loading functionality" in adri.standards.__doc__

        # Should mention key concepts
        assert "offline-first" in adri.standards.__doc__
        assert "network dependencies" in adri.standards.__doc__


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
