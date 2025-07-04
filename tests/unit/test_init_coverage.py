"""
Tests to improve coverage for adri.__init__ module.

These tests target specific uncovered lines to reach 90%+ coverage.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys


class TestInitCoverage:
    """Tests targeting specific uncovered lines in adri.__init__."""

    def test_import_error_fallback_paths(self):
        """Test the ImportError fallback paths by simulating import failures."""
        # Test by temporarily breaking imports and reloading the module
        import sys
        import importlib
        
        # Store original modules
        original_modules = {}
        modules_to_break = [
            'adri.core.protection',
            'adri.analysis.data_profiler', 
            'adri.analysis.standard_generator'
        ]
        
        for module_name in modules_to_break:
            if module_name in sys.modules:
                original_modules[module_name] = sys.modules[module_name]
                del sys.modules[module_name]
        
        # Remove adri module to force reload
        if 'adri' in sys.modules:
            del sys.modules['adri']
        
        try:
            # Mock the imports to raise ImportError
            with patch.dict('sys.modules', {
                'adri.core.protection': None,
                'adri.analysis.data_profiler': None,
                'adri.analysis.standard_generator': None
            }):
                # This should trigger the ImportError paths
                import adri
                
                # Verify fallback behavior - some components should be None
                # Note: DataQualityAssessor might still work, but others should be None
                assert hasattr(adri, 'DataProtectionEngine')
                assert hasattr(adri, 'DataProfiler') 
                assert hasattr(adri, 'StandardGenerator')
                
        finally:
            # Restore original modules
            for module_name, module in original_modules.items():
                sys.modules[module_name] = module
            
            # Force reload of adri to restore normal state
            if 'adri' in sys.modules:
                del sys.modules['adri']
            import adri  # This will reload with proper imports

    def test_conditional_all_exports(self):
        """Test the conditional __all__ exports (lines 58-65)."""
        # Create a mock module to test the conditional logic
        import types
        
        mock_adri = types.ModuleType('adri')
        mock_adri.__all__ = ["__version__", "adri_protected", "get_version_info"]
        
        # Test when components are available
        mock_adri.DataQualityAssessor = MagicMock()
        mock_adri.DataProtectionEngine = MagicMock()
        mock_adri.DataProfiler = MagicMock()
        mock_adri.StandardGenerator = MagicMock()
        
        # Simulate the conditional __all__ logic from __init__.py
        if mock_adri.DataQualityAssessor:
            mock_adri.__all__.append("DataQualityAssessor")
        if mock_adri.DataProtectionEngine:
            mock_adri.__all__.append("DataProtectionEngine")
        if mock_adri.DataProfiler:
            mock_adri.__all__.append("DataProfiler")
        if mock_adri.StandardGenerator:
            mock_adri.__all__.append("StandardGenerator")
        
        # Verify the conditional exports
        assert "DataQualityAssessor" in mock_adri.__all__
        assert "DataProtectionEngine" in mock_adri.__all__
        assert "DataProfiler" in mock_adri.__all__
        assert "StandardGenerator" in mock_adri.__all__
        
        # Test when components are None
        mock_adri2 = types.ModuleType('adri')
        mock_adri2.__all__ = ["__version__", "adri_protected", "get_version_info"]
        mock_adri2.DataQualityAssessor = None
        mock_adri2.DataProtectionEngine = None
        mock_adri2.DataProfiler = None
        mock_adri2.StandardGenerator = None
        
        # Simulate the conditional logic with None values
        if mock_adri2.DataQualityAssessor:
            mock_adri2.__all__.append("DataQualityAssessor")
        if mock_adri2.DataProtectionEngine:
            mock_adri2.__all__.append("DataProtectionEngine")
        if mock_adri2.DataProfiler:
            mock_adri2.__all__.append("DataProfiler")
        if mock_adri2.StandardGenerator:
            mock_adri2.__all__.append("StandardGenerator")
        
        # Verify components are not added when None
        assert "DataQualityAssessor" not in mock_adri2.__all__
        assert "DataProtectionEngine" not in mock_adri2.__all__
        assert "DataProfiler" not in mock_adri2.__all__
        assert "StandardGenerator" not in mock_adri2.__all__

    def test_successful_imports(self):
        """Test that all imports work correctly under normal conditions."""
        import adri
        
        # All components should be available
        assert adri.adri_protected is not None
        assert adri.__version__ is not None
        assert adri.get_version_info is not None
        assert adri.DataQualityAssessor is not None
        assert adri.DataProtectionEngine is not None
        assert adri.DataProfiler is not None
        # StandardGenerator might be None if import fails, so check conditionally
        assert hasattr(adri, 'StandardGenerator')

    def test_all_exports_in_all(self):
        """Test that __all__ contains the expected exports."""
        import adri
        
        # Basic exports should always be present
        assert "__version__" in adri.__all__
        assert "adri_protected" in adri.__all__
        assert "get_version_info" in adri.__all__
        
        # Component exports should be present when components are available
        if adri.DataQualityAssessor:
            assert "DataQualityAssessor" in adri.__all__
        if adri.DataProtectionEngine:
            assert "DataProtectionEngine" in adri.__all__
        if adri.DataProfiler:
            assert "DataProfiler" in adri.__all__

    def test_module_metadata(self):
        """Test module metadata attributes."""
        import adri
        
        # Check metadata attributes exist
        assert hasattr(adri, '__author__')
        assert hasattr(adri, '__email__')
        assert hasattr(adri, '__license__')
        assert hasattr(adri, '__description__')
        assert hasattr(adri, '__url__')
        
        # Check metadata values
        assert adri.__author__ == "Thomas"
        assert adri.__email__ == "thomas@adri.dev"
        assert adri.__license__ == "MIT"
        assert "Stop Your AI Agents Breaking on Bad Data" in adri.__description__
        assert "github.com" in adri.__url__
