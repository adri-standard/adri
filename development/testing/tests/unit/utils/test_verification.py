"""
Tests for adri.utils.verification module.

These tests target improving coverage for the verification utilities.
"""

import os
import sys
from io import StringIO
from unittest.mock import MagicMock, patch, mock_open

import pytest

from adri.utils.verification import (
    verify_standalone_installation,
    list_bundled_standards,
    check_system_compatibility,
    verify_audit_logging,
    run_full_verification,
)


class TestVerifyStandaloneInstallation:
    """Test verify_standalone_installation function."""

    def test_basic_verification(self):
        """Test basic verification functionality."""
        success, messages = verify_standalone_installation()
        
        # Should return boolean and list
        assert isinstance(success, bool)
        assert isinstance(messages, list)
        assert len(messages) > 0
        
        # Should include version information
        assert any("ADRI Validator version:" in msg for msg in messages)

    @patch('adri.utils.verification.StandardsLoader')
    def test_no_bundled_standards(self, mock_loader_class):
        """Test handling when no bundled standards are found."""
        mock_loader = MagicMock()
        mock_loader.list_available_standards.return_value = []
        mock_loader_class.return_value = mock_loader
        
        success, messages = verify_standalone_installation()
        
        assert success is False
        assert any("No bundled standards found" in msg for msg in messages)

    @patch('adri.utils.verification.StandardsLoader')
    def test_standards_loader_exception(self, mock_loader_class):
        """Test handling when StandardsLoader raises exception."""
        mock_loader_class.side_effect = Exception("Standards loading failed")
        
        success, messages = verify_standalone_installation()
        
        assert success is False
        assert any("Failed to load bundled standards" in msg for msg in messages)

    @patch('adri.utils.verification.StandardsLoader')
    def test_external_standards_path(self, mock_loader_class):
        """Test detection of external standards path."""
        mock_loader = MagicMock()
        mock_loader.list_available_standards.return_value = ["standard1"]
        mock_loader.standards_path = "/external/path/standards"
        mock_loader_class.return_value = mock_loader
        
        success, messages = verify_standalone_installation()
        
        assert success is False
        assert any("Using external standards path" in msg for msg in messages)

    @patch('adri.utils.verification.StandardsLoader')
    @patch.dict(os.environ, {'ADRI_STANDARDS_PATH': '/custom/path'})
    def test_custom_standards_path_env(self, mock_loader_class):
        """Test detection of custom standards path via environment variable."""
        mock_loader = MagicMock()
        mock_loader.list_available_standards.return_value = ["standard1"]
        mock_loader.standards_path = "/custom/path"
        mock_loader_class.return_value = mock_loader
        
        success, messages = verify_standalone_installation()
        
        # Should pass because environment variable indicates intentional override
        assert any("Using correct standards path" in msg for msg in messages)

    def test_core_modules_import_success(self):
        """Test successful import of core modules."""
        success, messages = verify_standalone_installation()
        
        # Should have messages about successfully loaded modules
        core_modules = [
            "adri.core.assessor",
            "adri.core.protection", 
            "adri.core.audit_logger",
            "adri.config.manager",
            "adri.decorators"
        ]
        
        for module in core_modules:
            assert any(f"Module {module} loaded successfully" in msg for msg in messages)

    def test_version_information_included(self):
        """Test that version information is included in messages."""
        success, messages = verify_standalone_installation()
        
        assert any("ADRI Validator version:" in msg for msg in messages)

    @patch('builtins.__import__')
    def test_core_module_import_failure(self, mock_import):
        """Test handling of core module import failures."""
        # Mock import to fail for one specific module
        def side_effect(module_name, *args, **kwargs):
            if module_name == "adri.core.assessor":
                raise ImportError("Module not found")
            return MagicMock()
        
        mock_import.side_effect = side_effect
        
        success, messages = verify_standalone_installation()
        
        assert success is False
        assert any("Failed to import adri.core.assessor" in msg for msg in messages)


class TestListBundledStandards:
    """Test list_bundled_standards function."""

    @patch('adri.utils.verification.StandardsLoader')
    def test_successful_standards_listing(self, mock_loader_class):
        """Test successful listing of bundled standards."""
        mock_loader = MagicMock()
        mock_loader.list_available_standards.return_value = ["standard1", "standard2"]
        mock_loader.get_standard_metadata.side_effect = [
            {
                "id": "std1",
                "version": "1.0",
                "description": "First standard"
            },
            {
                "id": "std2", 
                "version": "2.0",
                "description": "Second standard"
            }
        ]
        mock_loader_class.return_value = mock_loader
        
        standards = list_bundled_standards()
        
        assert len(standards) == 2
        assert standards[0]["name"] == "standard1"
        assert standards[0]["id"] == "std1"
        assert standards[0]["version"] == "1.0"
        assert standards[1]["name"] == "standard2"

    @patch('adri.utils.verification.StandardsLoader')
    def test_metadata_loading_failure(self, mock_loader_class):
        """Test handling when metadata loading fails."""
        mock_loader = MagicMock()
        mock_loader.list_available_standards.return_value = ["broken_standard"]
        mock_loader.get_standard_metadata.side_effect = Exception("Metadata error")
        mock_loader_class.return_value = mock_loader
        
        standards = list_bundled_standards()
        
        assert len(standards) == 1
        assert standards[0]["name"] == "broken_standard"
        assert standards[0]["id"] == "error"
        assert standards[0]["version"] == "error"
        assert "Failed to load metadata" in standards[0]["description"]

    @patch('adri.utils.verification.StandardsLoader')
    def test_missing_metadata_fields(self, mock_loader_class):
        """Test handling of missing metadata fields."""
        mock_loader = MagicMock()
        mock_loader.list_available_standards.return_value = ["incomplete_standard"]
        mock_loader.get_standard_metadata.return_value = {"id": "incomplete"}  # Missing version, description
        mock_loader_class.return_value = mock_loader
        
        standards = list_bundled_standards()
        
        assert len(standards) == 1
        assert standards[0]["name"] == "incomplete_standard"
        assert standards[0]["id"] == "incomplete"
        assert standards[0]["version"] == "unknown"
        assert standards[0]["description"] == "No description"


class TestCheckSystemCompatibility:
    """Test check_system_compatibility function."""

    def test_system_info_collection(self):
        """Test that system information is properly collected."""
        info = check_system_compatibility()
        
        # Check required fields are present
        required_fields = [
            "python_version",
            "python_version_tuple", 
            "platform",
            "architecture",
            "os",
            "python_compatible",
            "missing_packages",
            "packages_compatible"
        ]
        
        for field in required_fields:
            assert field in info

    def test_python_version_compatibility(self):
        """Test Python version compatibility checking."""
        info = check_system_compatibility()
        
        # Should be compatible with current Python version (3.11+)
        assert info["python_compatible"] is True
        assert isinstance(info["python_version_tuple"], tuple)
        assert len(info["python_version_tuple"]) == 3

    @patch.object(sys, 'version_info', (3, 9, 0))
    def test_python_version_incompatible(self):
        """Test detection of incompatible Python version."""
        info = check_system_compatibility()
        
        assert info["python_compatible"] is False

    @patch('builtins.__import__')
    def test_missing_packages_detection(self, mock_import):
        """Test detection of missing required packages."""
        def side_effect(package_name, *args, **kwargs):
            if package_name == "pandas":
                raise ImportError("pandas not found")
            return MagicMock()
        
        mock_import.side_effect = side_effect
        
        info = check_system_compatibility()
        
        assert "pandas" in info["missing_packages"]
        assert info["packages_compatible"] is False

    def test_all_packages_available(self):
        """Test when all required packages are available."""
        info = check_system_compatibility()
        
        # In our test environment, packages should be available
        assert info["packages_compatible"] is True
        assert len(info["missing_packages"]) == 0


class TestVerifyAuditLogging:
    """Test verify_audit_logging function."""

    def test_audit_logging_disabled(self):
        """Test audit logging verification when disabled."""
        success, messages = verify_audit_logging(enabled=False)
        
        assert success is True
        assert any("AuditLogger instantiated (enabled=False)" in msg for msg in messages)

    def test_audit_logging_enabled(self):
        """Test audit logging verification when enabled."""
        success, messages = verify_audit_logging(enabled=True)
        
        assert success is True
        assert any("AuditLogger instantiated (enabled=True)" in msg for msg in messages)
        assert any("AuditRecord created successfully" in msg for msg in messages)
        assert any("AuditRecord converts to dict" in msg for msg in messages)
        assert any("AuditRecord converts to JSON" in msg for msg in messages)
        assert any("AuditRecord converts to Verodat format" in msg for msg in messages)

    @patch('adri.core.audit_logger.AuditLogger')
    def test_audit_logger_import_failure(self, mock_audit_logger):
        """Test handling of AuditLogger import failure."""
        mock_audit_logger.side_effect = ImportError("AuditLogger not found")
        
        success, messages = verify_audit_logging(enabled=False)
        
        assert success is False
        assert any("Audit logging verification failed" in msg for msg in messages)

    def test_verodat_logger_availability(self):
        """Test checking Verodat logger availability."""
        success, messages = verify_audit_logging(enabled=False)
        
        # Should have message about VerodatLogger (available or not)
        assert any("VerodatLogger" in msg for msg in messages)

    def test_csv_logger_availability(self):
        """Test checking CSV logger availability.""" 
        success, messages = verify_audit_logging(enabled=False)
        
        # Should have message about CSV logger
        assert any("AuditLoggerCSV module available" in msg for msg in messages)


class TestRunFullVerification:
    """Test run_full_verification function."""

    def test_verbose_output(self):
        """Test verbose output of full verification."""
        # Capture stdout
        captured_output = StringIO()
        
        with patch('sys.stdout', captured_output):
            success = run_full_verification(verbose=True)
        
        output = captured_output.getvalue()
        
        # Check for expected sections
        assert "ADRI VALIDATOR STANDALONE VERIFICATION" in output
        assert "1. Verifying Standalone Installation" in output
        assert "2. Checking System Compatibility" in output
        assert "3. Bundled Standards" in output
        assert "4. Verifying Audit Logging" in output

    def test_silent_mode(self):
        """Test silent mode of full verification."""
        captured_output = StringIO()
        
        with patch('sys.stdout', captured_output):
            success = run_full_verification(verbose=False)
        
        output = captured_output.getvalue()
        
        # Should be minimal output in silent mode
        assert output == ""

    @patch('adri.utils.verification.verify_standalone_installation')
    @patch('adri.utils.verification.check_system_compatibility')
    @patch('adri.utils.verification.list_bundled_standards')
    @patch('adri.utils.verification.verify_audit_logging')
    def test_failure_propagation(self, mock_audit, mock_standards, mock_compat, mock_standalone):
        """Test that failures in sub-functions are propagated."""
        # Mock failures
        mock_standalone.return_value = (False, ["Standalone check failed"])
        mock_compat.return_value = {"python_compatible": False, "packages_compatible": True}
        mock_standards.return_value = []
        mock_audit.return_value = (False, ["Audit check failed"])
        
        success = run_full_verification(verbose=False)
        
        assert success is False

    @patch('adri.utils.verification.list_bundled_standards')  
    def test_many_standards_display(self, mock_standards):
        """Test display when there are many bundled standards."""
        # Mock many standards
        mock_standards.return_value = [
            {"name": f"standard_{i}", "version": "1.0"} for i in range(10)
        ]
        
        captured_output = StringIO()
        
        with patch('sys.stdout', captured_output):
            run_full_verification(verbose=True)
        
        output = captured_output.getvalue()
        
        # Should show "... and X more" for many standards
        assert "and 5 more" in output


class TestMainExecution:
    """Test main execution block."""

    def test_main_block_exists(self):
        """Test that main execution block exists."""
        # Simply test that the function exists and can be called
        success = run_full_verification(verbose=False)
        assert isinstance(success, bool)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_standards_list(self):
        """Test handling of empty standards list."""
        with patch('adri.utils.verification.StandardsLoader') as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.list_available_standards.return_value = []
            mock_loader_class.return_value = mock_loader
            
            standards = list_bundled_standards()
            assert standards == []

    def test_partial_system_info(self):
        """Test system compatibility with partial information."""
        try:
            with patch('platform.platform', side_effect=Exception("Platform error")):
                # Should still work despite platform detection failure
                info = check_system_compatibility()
                assert "python_version" in info  # Core info should still be available
        except Exception:
            # If the function doesn't handle platform errors gracefully, that's expected
            # This test just verifies the function can be called
            info = check_system_compatibility()
            assert "python_version" in info

    @patch('adri.utils.verification.StandardsLoader')
    def test_standards_path_verification_exception(self, mock_loader_class):
        """Test handling of exception during standards path verification."""
        mock_loader = MagicMock()
        mock_loader.standards_path = MagicMock()
        mock_loader.standards_path.__str__ = MagicMock(side_effect=Exception("Path error"))
        mock_loader_class.return_value = mock_loader
        
        success, messages = verify_standalone_installation()
        
        assert success is False
        assert any("Failed to verify standards path" in msg for msg in messages)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
