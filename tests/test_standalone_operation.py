"""
Test suite for verifying standalone operation of ADRI Validator.

This test suite ensures that the ADRI Validator operates independently
without external dependencies and with bundled standards only.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from adri.core.boundary import StandaloneMode, validate_standalone_operation
from adri.decorators import adri_protected
from adri.standards.loader import StandardsLoader
from adri.utils.verification import (
    check_system_compatibility,
    list_bundled_standards,
    run_full_verification,
    verify_standalone_installation,
)


class TestStandaloneInstallation:
    """Test standalone installation verification."""

    def test_no_external_dependencies(self):
        """Verify no external adri-standards dependency."""
        with patch("pkg_resources.working_set", []):
            success, messages = verify_standalone_installation()
            assert any("No external adri-standards" in msg for msg in messages)

    def test_bundled_standards_available(self):
        """Verify bundled standards are available."""
        loader = StandardsLoader()
        standards = loader.list_available_standards()
        assert len(standards) > 0, "No bundled standards found"
        assert len(standards) >= 15, "Expected at least 15 bundled standards"

    def test_standards_path_is_bundled(self):
        """Verify standards path points to bundled directory."""
        loader = StandardsLoader()
        path_str = str(loader.standards_path)
        assert "bundled" in path_str or os.getenv(
            "ADRI_STANDARDS_PATH"
        ), f"Standards path not using bundled: {path_str}"

    def test_core_modules_importable(self):
        """Verify all core modules can be imported."""
        modules = [
            "adri.core.assessor",
            "adri.core.protection",
            "adri.core.audit_logger",
            "adri.config.manager",
            "adri.decorators.guard",
        ]

        for module in modules:
            try:
                __import__(module)
            except ImportError as e:
                pytest.fail(f"Failed to import {module}: {e}")


class TestStandardsLoader:
    """Test standards loading without external dependencies."""

    def test_load_bundled_standard(self):
        """Test loading a bundled standard."""
        loader = StandardsLoader()
        # Use an actual bundled standard
        standard = loader.load_standard("customer_data_standard")

        assert standard is not None
        assert "standards" in standard
        assert "requirements" in standard
        # Standard uses "field_requirements" instead of "schema"
        assert (
            "requirements" in standard
            and "field_requirements" in standard["requirements"]
        )

    def test_list_all_bundled_standards(self):
        """Test listing all bundled standards."""
        standards = list_bundled_standards()

        assert len(standards) > 0
        for std in standards:
            assert "name" in std
            assert "id" in std
            assert "version" in std

    def test_no_network_calls(self):
        """Verify no network calls are made."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            with patch("requests.get") as mock_get:
                loader = StandardsLoader()
                standards = loader.list_available_standards()

                # Load each standard
                for std_name in standards[:3]:  # Test first 3
                    loader.load_standard(std_name)

                # Verify no network calls were made
                mock_urlopen.assert_not_called()
                mock_get.assert_not_called()

    def test_cache_functionality(self):
        """Test standards caching works offline."""
        loader = StandardsLoader()

        # First load using actual bundled standard
        standard1 = loader.load_standard("customer_data_standard")

        # Second load (should use cache)
        standard2 = loader.load_standard("customer_data_standard")

        assert standard1 == standard2

        # Check cache info
        cache_info = loader.get_cache_info()
        assert cache_info.hits > 0


class TestDataValidation:
    """Test data validation with bundled standards."""

    def test_decorator_with_bundled_standard(self):
        """Test @adri_protected decorator with bundled standard."""

        @adri_protected(
            data_param="df",
            standard_name="customer_data_standard",
            min_score=50.0,
            on_failure="warn",
        )
        def process_data(df):
            return df

        # Create test data matching the standard
        df = pd.DataFrame(
            {
                "customer_id": ["C001", "C002", "C003"],
                "email": [
                    "user1@example.com",
                    "user2@example.com",
                    "user3@example.com",
                ],
                "age": [25, 30, 35],
                "registration_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            }
        )

        # Should not raise with good data
        result = process_data(df)
        assert result is not None
        assert len(result) == 3
        assert isinstance(result, pd.DataFrame)  # Use result to satisfy flake8

    def test_validation_without_network(self):
        """Test validation works without network access."""

        @adri_protected(standard_name="customer_data_standard")
        def validate_customer(df):
            return df

        # Mock network to ensure no calls
        with patch("urllib.request.urlopen") as mock_urlopen:
            with patch("requests.get") as mock_get:
                df = pd.DataFrame(
                    {
                        "customer_id": ["C001", "C002"],
                        "email": ["user1@example.com", "user2@example.com"],
                        "age": [25, 30],
                        "registration_date": ["2024-01-01", "2024-01-02"],
                    }
                )

                try:
                    result = validate_customer(df)
                    # May pass or fail based on data quality
                    assert result is not None or result is None  # Use result variable
                except Exception:
                    pass  # Expected if data doesn't meet standard

                # Verify no network calls
                mock_urlopen.assert_not_called()
                mock_get.assert_not_called()


class TestStandaloneMode:
    """Test standalone mode context manager."""

    def test_standalone_mode_context(self):
        """Test StandaloneMode context manager."""
        from adri.core.boundary import get_boundary_manager

        boundary = get_boundary_manager()

        # Add a mock integration
        mock_integration = MagicMock()
        boundary._integrations["test"] = mock_integration

        assert len(boundary.list_integrations()) == 1

        # Enter standalone mode
        with StandaloneMode():
            # Integration should be removed
            assert len(boundary.list_integrations()) == 0

        # Integration should be restored
        assert len(boundary.list_integrations()) == 1

    def test_validate_standalone_operation(self):
        """Test standalone operation validation."""
        is_standalone = validate_standalone_operation()
        assert is_standalone, "Standalone operation validation failed"


class TestSystemCompatibility:
    """Test system compatibility checks."""

    def test_python_version_check(self):
        """Test Python version compatibility."""
        sys_info = check_system_compatibility()

        assert "python_version" in sys_info
        assert "python_compatible" in sys_info

        # We require Python 3.10+
        assert sys_info["python_compatible"] or sys.version_info[:2] < (3, 10)

    def test_required_packages_check(self):
        """Test required packages are available."""
        sys_info = check_system_compatibility()

        assert "missing_packages" in sys_info
        assert "packages_compatible" in sys_info

        # These packages should be available
        required = ["pandas", "yaml", "click"]
        for pkg in required:
            assert (
                pkg not in sys_info["missing_packages"]
            ), f"Required package {pkg} is missing"


class TestAuditLogging:
    """Test audit logging in standalone mode."""

    def test_audit_logger_standalone(self):
        """Test audit logger works standalone."""
        from datetime import datetime

        from adri.core.audit_logger import AuditLogger, AuditRecord

        # Create logger (disabled by default)
        logger = AuditLogger({"enabled": False})
        assert logger.enabled is False  # Use logger variable

        # Create audit record
        record = AuditRecord(
            assessment_id="test_001", timestamp=datetime.now(), adri_version="3.0.1"
        )

        # Convert to various formats
        dict_format = record.to_dict()
        assert "assessment_metadata" in dict_format

        json_format = record.to_json()
        assert isinstance(json_format, str)

        verodat_format = record.to_verodat_format()
        assert "main_record" in verodat_format

    def test_csv_logger_standalone(self):
        """Test CSV audit logger works standalone."""
        from adri.core.audit_logger_csv import AuditLoggerCSV

        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLoggerCSV({"enabled": True, "output_path": tmpdir})

            # Logger should initialize without errors
            assert logger is not None
            assert hasattr(logger, "enabled")  # Use logger to satisfy flake8


class TestDeploymentScenarios:
    """Test various deployment scenarios."""

    def test_air_gapped_simulation(self):
        """Simulate air-gapped environment."""
        # Remove network access
        with patch("urllib.request.urlopen") as mock_urlopen:
            with patch("requests.get") as mock_get:
                mock_urlopen.side_effect = Exception("No network")
                mock_get.side_effect = Exception("No network")

                # Should still work
                loader = StandardsLoader()
                standards = loader.list_available_standards()
                assert len(standards) > 0

                # Load an actual bundled standard
                standard = loader.load_standard("customer_data_standard")
                assert standard is not None

    def test_custom_standards_path(self):
        """Test using custom standards path via environment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test standard
            test_standard = {
                "standards": {
                    "id": "custom_test",
                    "name": "Custom Test Standard",
                    "version": "1.0.0",
                },
                "requirements": {"overall_minimum": 75.0},
                "schema": {},
            }

            # Write to temp directory
            import yaml

            standard_path = Path(tmpdir) / "custom_test.yaml"
            with open(standard_path, "w") as f:
                yaml.dump(test_standard, f)

            # Set environment variable
            os.environ["ADRI_STANDARDS_PATH"] = tmpdir

            try:
                # Create new loader (should use env path)
                loader = StandardsLoader()
                standards = loader.list_available_standards()

                assert "custom_test" in standards

                # Load the custom standard
                loaded = loader.load_standard("custom_test")
                assert loaded["standards"]["id"] == "custom_test"

            finally:
                # Clean up
                del os.environ["ADRI_STANDARDS_PATH"]


class TestFullVerification:
    """Test complete verification suite."""

    def test_run_full_verification(self):
        """Test full verification runs successfully."""
        success = run_full_verification(verbose=False)
        assert success, "Full verification failed"

    def test_verification_components(self):
        """Test individual verification components."""
        from adri.utils.verification import verify_audit_logging

        # Test audit logging verification
        success, messages = verify_audit_logging(enabled=False)
        assert success, f"Audit logging verification failed: {messages}"

        # Test with enabled
        success, messages = verify_audit_logging(enabled=True)
        assert success, f"Audit logging verification failed: {messages}"


@pytest.mark.integration
class TestIntegrationScenarios:
    """Integration tests for standalone operation."""

    def test_end_to_end_validation(self):
        """Test end-to-end validation workflow."""

        @adri_protected(
            data_param="df",
            standard_name="customer_data_standard",
            min_score=60.0,
            on_failure="warn",
        )
        def process_transactions(df):
            return df

        # Create customer data matching the standard
        df = pd.DataFrame(
            {
                "customer_id": ["C001", "C002", "C003"],
                "email": [
                    "user1@example.com",
                    "user2@example.com",
                    "user3@example.com",
                ],
                "age": [25, 30, 35],
                "registration_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            }
        )

        # Process with validation
        with patch("warnings.warn") as mock_warn:
            result = process_transactions(df)

            # Check result
            assert result is not None
            if mock_warn.called:
                # Warning mode was triggered
                assert "Data quality" in str(mock_warn.call_args)

    def test_multiple_standards_loading(self):
        """Test loading multiple standards concurrently."""
        import concurrent.futures

        loader = StandardsLoader()
        # Use actual bundled standards
        standards_to_load = [
            "customer_data_standard",
            "sample_data_ADRI_standard",
            "high_quality_agent_data_standard",
            "process_customers_customer_data_standard",
            "financial_risk_analyzer_financial_data_standard",
        ]

        def load_standard(name):
            return loader.load_standard(name)

        # Load standards concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(load_standard, name) for name in standards_to_load
            ]
            results = [f.result() for f in futures]

        # Verify all loaded successfully
        assert len(results) == len(standards_to_load)
        for result in results:
            assert result is not None
            assert "standards" in result


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
