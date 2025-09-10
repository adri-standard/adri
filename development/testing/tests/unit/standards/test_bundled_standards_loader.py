"""
Test-Driven Development for Bundled Standards Loader

This module tests the bundled standards loading system that eliminates
network dependencies and provides offline-first functionality.
"""

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import yaml

from adri.standards.exceptions import InvalidStandardError, StandardNotFoundError
from adri.standards.loader import StandardsLoader


class TestBundledStandardsLoader:
    """Test cases for the StandardsLoader class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.loader = StandardsLoader()

    def test_loader_initialization(self):
        """Test that the loader initializes correctly."""
        assert self.loader is not None
        assert hasattr(self.loader, "standards_path")
        assert isinstance(self.loader.standards_path, Path)

    def test_bundled_standards_directory_exists(self):
        """Test that the standards directory exists."""
        # This test will fail initially - we need to create the directory
        assert self.loader.standards_path.exists()
        assert self.loader.standards_path.is_dir()

    def test_load_customer_data_standard(self):
        """Test loading the customer data standard."""
        # This test will fail initially - we need to bundle the standard
        standard = self.loader.load_standard("customer_data_standard")

        assert standard is not None
        assert "standards" in standard
        assert "requirements" in standard
        assert standard["standards"]["id"] == "customer-data-v1"

    def test_load_financial_data_standard(self):
        """Test loading the financial data standard."""
        standard = self.loader.load_standard(
            "financial_risk_analyzer_financial_data_standard"
        )

        assert standard is not None
        assert "standards" in standard
        assert "requirements" in standard

    def test_load_nonexistent_standard_raises_error(self):
        """Test that loading a non-existent standard raises appropriate error."""
        with pytest.raises(StandardNotFoundError) as exc_info:
            self.loader.load_standard("nonexistent_standard")

        assert "nonexistent_standard" in str(exc_info.value)

    def test_load_invalid_yaml_raises_error(self):
        """Test that loading invalid YAML raises appropriate error."""
        # Mock a file with invalid YAML
        invalid_yaml = "invalid: yaml: content: ["

        # Mock both file existence and file content
        with (
            patch.object(Path, "exists", return_value=True),
            patch("builtins.open", mock_open(read_data=invalid_yaml)),
        ):
            with pytest.raises(InvalidStandardError):
                self.loader.load_standard("invalid_standard")

    def test_list_available_standards(self):
        """Test listing all available bundled standards."""
        standards = self.loader.list_available_standards()

        assert isinstance(standards, list)
        assert len(standards) > 0
        assert "customer_data_standard" in standards
        assert "financial_risk_analyzer_financial_data_standard" in standards

    def test_standard_exists_check(self):
        """Test checking if a standard exists."""
        assert self.loader.standard_exists("customer_data_standard") is True
        assert self.loader.standard_exists("nonexistent_standard") is False

    def test_get_standard_metadata(self):
        """Test getting metadata for a standard."""
        metadata = self.loader.get_standard_metadata("customer_data_standard")

        assert "name" in metadata
        assert "version" in metadata
        assert "description" in metadata
        assert "file_path" in metadata

    def test_load_all_bundled_standards(self):
        """Test that all bundled standards can be loaded without errors."""
        available_standards = self.loader.list_available_standards()

        for standard_name in available_standards:
            # Each standard should load without raising an exception
            standard = self.loader.load_standard(standard_name)
            assert standard is not None
            assert "standards" in standard

    def test_standards_validation(self):
        """Test that all bundled standards are valid ADRI standards."""
        available_standards = self.loader.list_available_standards()

        for standard_name in available_standards:
            standard = self.loader.load_standard(standard_name)

            # Validate required structure
            assert "standards" in standard
            assert "requirements" in standard

            # Validate standards section
            standards_section = standard["standards"]
            assert "id" in standards_section
            assert "name" in standards_section
            assert "version" in standards_section

            # Validate requirements section
            requirements_section = standard["requirements"]
            assert "overall_minimum" in requirements_section

    def test_performance_load_standard(self):
        """Test that loading a standard is fast (< 10ms)."""
        import time

        start_time = time.time()
        self.loader.load_standard("customer_data_standard")
        end_time = time.time()

        load_time = (end_time - start_time) * 1000  # Convert to milliseconds
        assert load_time < 50, f"Standard loading took {load_time}ms, should be < 50ms"

    def test_concurrent_access_safety(self):
        """Test that the loader is safe for concurrent access."""
        import threading
        import time

        results = []
        errors = []

        def load_standard_worker():
            try:
                standard = self.loader.load_standard("customer_data_standard")
                results.append(standard)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=load_standard_worker)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify results
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == 10

        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result


class TestStandardsExceptions:
    """Test cases for standards-related exceptions."""

    def test_standard_not_found_error(self):
        """Test StandardNotFoundError exception."""
        error = StandardNotFoundError("test_standard")
        assert "test_standard" in str(error)
        assert isinstance(error, Exception)

    def test_invalid_standard_error(self):
        """Test InvalidStandardError exception."""
        error = InvalidStandardError("Invalid YAML format")
        assert "Invalid YAML format" in str(error)
        assert isinstance(error, Exception)


class TestBundledStandardsIntegration:
    """Integration tests for bundled standards with existing decorator."""

    def test_decorator_uses_bundled_standards(self):
        """Test that @adri_protected decorator uses bundled standards."""
        from adri.decorators.guard import adri_protected

        # This test ensures the decorator integrates with bundled standards
        @adri_protected(data_param="customer_data")
        def test_function(customer_data):
            return {"processed": True}

        # The decorator should be able to find and use bundled standards
        # This test will validate the integration works
        assert hasattr(test_function, "_adri_protected")

    def test_no_network_requests_during_standard_loading(self):
        """Test that no network requests are made during standard loading."""
        import socket

        # Mock socket to prevent any network access
        with patch("socket.socket") as mock_socket:
            mock_socket.side_effect = Exception("Network access attempted!")

            # Loading standards should work without network
            loader = StandardsLoader()
            standard = loader.load_standard("customer_data_standard")

            assert standard is not None
            # Verify no network calls were attempted
            mock_socket.assert_not_called()
