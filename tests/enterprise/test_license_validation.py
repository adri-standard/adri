"""
Comprehensive tests for enterprise license validation system.

Tests covering:
- API key validation with Verodat API
- License caching behavior and expiration
- Error handling for network issues and invalid keys
- Singleton pattern implementation
- Thread safety and concurrent validation
- Environment variable handling
"""

import os
import threading
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
import requests

from adri_enterprise.license import (
    LicenseValidator,
    LicenseInfo,
    LicenseValidationError,
    validate_license,
    is_license_valid,
    get_validator,
    require_license,
)


class TestLicenseValidator:
    """Test suite for core license validator functionality."""

    def test_license_validator_singleton_pattern(self, clean_license_cache):
        """Verify that LicenseValidator implements singleton pattern correctly."""
        validator1 = LicenseValidator()
        validator2 = LicenseValidator()
        validator3 = get_validator()

        # All instances should be the same object
        assert validator1 is validator2
        assert validator2 is validator3
        assert id(validator1) == id(validator2) == id(validator3)

    def test_api_key_validation_success(self, clean_license_cache, mock_verodat_api_success):
        """Test successful API key validation."""
        validator = get_validator()

        license_info = validator.validate_api_key("valid-test-key")

        # Verify successful validation
        assert license_info.is_valid is True
        assert license_info.api_key == "valid-test-key"
        assert license_info.account_id == 91
        assert license_info.username == "test@example.com"
        assert license_info.error_message is None

        # Verify API was called correctly
        mock_verodat_api_success['get'].assert_called_once()
        call_args = mock_verodat_api_success['get'].call_args
        assert "ApiKey valid-test-key" in call_args[1]["headers"]["Authorization"]

    def test_api_key_validation_failure_invalid_key(self, clean_license_cache):
        """Test API key validation with invalid key."""
        validator = get_validator()

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Invalid API key"
            mock_get.return_value = mock_response

            with pytest.raises(LicenseValidationError) as exc_info:
                validator.validate_api_key("invalid-key")

            assert "Invalid Verodat API key" in str(exc_info.value)
            assert "invalid or has expired" in exc_info.value.details

    def test_api_key_validation_failure_no_enterprise_access(self, clean_license_cache):
        """Test API key validation when user lacks enterprise access."""
        validator = get_validator()

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.text = "Forbidden"
            mock_get.return_value = mock_response

            with pytest.raises(LicenseValidationError) as exc_info:
                validator.validate_api_key("basic-access-key")

            assert "Enterprise license required" in str(exc_info.value)
            assert "does not have enterprise access" in exc_info.value.details

    def test_api_key_validation_missing_key(self, clean_license_cache):
        """Test validation when no API key is provided."""
        validator = get_validator()

        # Clear any environment variable
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(LicenseValidationError) as exc_info:
                validator.validate_api_key()

            assert "Verodat API key required" in str(exc_info.value)
            assert "VERODAT_API_KEY" in exc_info.value.details

    def test_api_key_from_environment_variable(self, clean_license_cache, mock_verodat_api_success):
        """Test that API key is read from environment variable when not provided."""
        validator = get_validator()

        with patch.dict(os.environ, {'VERODAT_API_KEY': 'env-api-key'}):
            license_info = validator.validate_api_key()

            assert license_info.is_valid is True
            assert license_info.api_key == "env-api-key"

    def test_license_cache_behavior(self, clean_license_cache, mock_verodat_api_success):
        """Test that license validation results are cached correctly."""
        validator = get_validator()

        # First validation - should call API
        license_info1 = validator.validate_api_key("cached-key")
        assert mock_verodat_api_success['get'].call_count == 1

        # Second validation with same key - should use cache
        license_info2 = validator.validate_api_key("cached-key")
        assert mock_verodat_api_success['get'].call_count == 1  # No additional call

        # Verify both results are equivalent
        assert license_info1.is_valid == license_info2.is_valid
        assert license_info1.api_key == license_info2.api_key
        assert license_info1.account_id == license_info2.account_id

    def test_license_cache_different_keys(self, clean_license_cache, mock_verodat_api_success):
        """Test that different API keys trigger separate validations."""
        validator = get_validator()

        # Validate first key
        validator.validate_api_key("key-one")
        assert mock_verodat_api_success['get'].call_count == 1

        # Validate different key - should call API again
        validator.validate_api_key("key-two")
        assert mock_verodat_api_success['get'].call_count == 2

    def test_force_revalidation(self, clean_license_cache, mock_verodat_api_success):
        """Test that force_revalidation bypasses cache."""
        validator = get_validator()

        # First validation
        validator.validate_api_key("test-key")
        assert mock_verodat_api_success['get'].call_count == 1

        # Force revalidation - should call API again
        validator.validate_api_key("test-key", force_revalidation=True)
        assert mock_verodat_api_success['get'].call_count == 2

    def test_cache_expiration(self, clean_license_cache, mock_verodat_api_success):
        """Test that cache expires after the configured duration."""
        validator = get_validator()

        # Mock cache duration to be very short for testing
        original_duration = validator._validation_cache_duration
        validator._validation_cache_duration = timedelta(milliseconds=100)

        try:
            # First validation
            validator.validate_api_key("expiring-key")
            assert mock_verodat_api_success['get'].call_count == 1

            # Wait for cache to expire
            time.sleep(0.2)

            # Second validation - should call API again due to expiration
            validator.validate_api_key("expiring-key")
            assert mock_verodat_api_success['get'].call_count == 2
        finally:
            # Restore original duration
            validator._validation_cache_duration = original_duration

    def test_network_error_handling(self, clean_license_cache, mock_verodat_api_timeout):
        """Test handling of network errors during validation."""
        validator = get_validator()

        with pytest.raises(LicenseValidationError) as exc_info:
            validator.validate_api_key("network-error-key")

        assert "License validation timeout" in str(exc_info.value)
        assert "Could not reach Verodat API" in exc_info.value.details

    def test_server_error_handling(self, clean_license_cache):
        """Test handling of server errors during validation."""
        validator = get_validator()

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 503
            mock_response.text = "Service unavailable"
            mock_get.return_value = mock_response

            with pytest.raises(LicenseValidationError) as exc_info:
                validator.validate_api_key("server-error-key")

            assert "License validation failed" in str(exc_info.value)
            assert "status 503" in exc_info.value.details

    def test_connection_error_handling(self, clean_license_cache):
        """Test handling of connection errors during validation."""
        validator = get_validator()

        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.ConnectionError("Connection failed")

            with pytest.raises(LicenseValidationError) as exc_info:
                validator.validate_api_key("connection-error-key")

            assert "License validation failed" in str(exc_info.value)
            assert "Network error" in exc_info.value.details

    def test_is_validated_property(self, clean_license_cache, mock_verodat_api_success):
        """Test the is_validated property."""
        validator = get_validator()

        # Initially not validated
        assert validator.is_validated is False

        # After successful validation
        validator.validate_api_key("test-key")
        assert validator.is_validated is True

        # After cache clear
        validator.clear_cache()
        assert validator.is_validated is False

    def test_current_license_property(self, clean_license_cache, mock_verodat_api_success):
        """Test the current_license property."""
        validator = get_validator()

        # Initially no license
        assert validator.current_license is None

        # After validation
        license_info = validator.validate_api_key("test-key")
        current = validator.current_license

        assert current is not None
        assert current.api_key == license_info.api_key
        assert current.is_valid == license_info.is_valid

    def test_clear_cache_functionality(self, clean_license_cache, mock_verodat_api_success):
        """Test that clear_cache works correctly."""
        validator = get_validator()

        # Validate and cache
        validator.validate_api_key("cached-key")
        assert validator.is_validated is True

        # Clear cache
        validator.clear_cache()
        assert validator.is_validated is False
        assert validator.current_license is None

        # Next validation should call API again
        validator.validate_api_key("cached-key")
        assert mock_verodat_api_success['get'].call_count == 2


class TestLicenseValidatorSingleton:
    """Test suite for singleton behavior and thread safety."""

    def test_multiple_concurrent_validations(self, clean_license_cache, mock_verodat_api_success):
        """Test that concurrent validations work correctly with singleton pattern."""
        def validate_in_thread(api_key):
            validator = get_validator()
            return validator.validate_api_key(api_key)

        # Run multiple validations concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i in range(10):
                future = executor.submit(validate_in_thread, "concurrent-key")
                futures.append(future)

            # Collect results
            results = []
            for future in as_completed(futures):
                results.append(future.result())

        # All results should be successful and identical
        assert len(results) == 10
        for result in results:
            assert result.is_valid is True
            assert result.api_key == "concurrent-key"

        # API should only be called once due to caching
        assert mock_verodat_api_success['get'].call_count == 1

    def test_thread_safety_singleton_creation(self, clean_license_cache):
        """Test that singleton creation is thread-safe."""
        validators = []
        creation_times = []
        lock = threading.Lock()

        def create_validator():
            validator = LicenseValidator()
            timestamp = datetime.now()
            with lock:
                validators.append(validator)
                creation_times.append(timestamp)

        # Create validators concurrently
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_validator)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All validators should be the same instance
        first_validator = validators[0]
        for validator in validators:
            assert validator is first_validator

        # Verify creation was properly synchronized
        assert len(validators) == 10
        assert len(creation_times) == 10


class TestConvenienceFunctions:
    """Test suite for convenience functions."""

    def test_validate_license_function(self, clean_license_cache, mock_verodat_api_success):
        """Test the validate_license convenience function."""
        license_info = validate_license("function-test-key")

        assert license_info.is_valid is True
        assert license_info.api_key == "function-test-key"

        # Should use the same validator instance
        validator = get_validator()
        assert validator.current_license.api_key == "function-test-key"

    def test_validate_license_function_with_env_var(self, clean_license_cache, mock_verodat_api_success):
        """Test validate_license function reading from environment."""
        with patch.dict(os.environ, {'VERODAT_API_KEY': 'env-function-key'}):
            license_info = validate_license()

            assert license_info.is_valid is True
            assert license_info.api_key == "env-function-key"

    def test_is_license_valid_function(self, clean_license_cache, mock_verodat_api_success):
        """Test the is_license_valid convenience function."""
        # Initially not valid
        assert is_license_valid() is False

        # After validation
        validate_license("valid-function-key")
        assert is_license_valid() is True

        # After cache clear
        validator = get_validator()
        validator.clear_cache()
        assert is_license_valid() is False

    def test_require_license_decorator(self, clean_license_cache, mock_verodat_api_success):
        """Test the require_license decorator."""
        # Set up environment with valid key
        with patch.dict(os.environ, {'VERODAT_API_KEY': 'decorator-test-key'}):

            @require_license
            def protected_function():
                return "success"

            result = protected_function()
            assert result == "success"

            # Verify license was validated
            validator = get_validator()
            assert validator.is_validated is True
            assert validator.current_license.api_key == "decorator-test-key"

    def test_require_license_decorator_failure(self, clean_license_cache):
        """Test require_license decorator with invalid license."""
        # Clear environment
        with patch.dict(os.environ, {}, clear=True):

            @require_license
            def protected_function():
                return "should not reach here"

            with pytest.raises(LicenseValidationError):
                protected_function()


class TestLicenseValidationCaching:
    """Test suite for caching behavior and performance."""

    def test_cache_hit_performance(self, clean_license_cache, mock_verodat_api_success, performance_baseline):
        """Test that cache hits are fast."""
        validator = get_validator()

        # First validation (cache miss)
        validator.validate_api_key("performance-test-key")

        # Multiple cache hits - should be very fast
        start_time = time.time()
        for _ in range(10):
            validator.validate_api_key("performance-test-key")
        end_time = time.time()

        # All cache hits should be much faster than baseline
        cache_time = (end_time - start_time) / 10
        assert cache_time < performance_baseline['license_cache_hit_max_time']

        # API should only be called once
        assert mock_verodat_api_success['get'].call_count == 1

    def test_cache_memory_efficiency(self, clean_license_cache, mock_verodat_api_success):
        """Test that cache doesn't grow indefinitely with different keys."""
        validator = get_validator()

        # Validate multiple different keys
        for i in range(5):
            validator.validate_api_key(f"memory-test-key-{i}")

        # With current implementation, only the last validation is cached
        # (since we only store one license at a time)
        assert validator.current_license.api_key == "memory-test-key-4"

        # Verify all validations were made
        assert mock_verodat_api_success['get'].call_count == 5

    def test_invalid_license_caching(self, clean_license_cache):
        """Test that invalid licenses are NOT cached (by design).
        
        Invalid licenses should not be cached to allow immediate retry
        when the user fixes their API key. Each validation attempt with
        an invalid key should make a new API call.
        """
        validator = get_validator()

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_get.return_value = mock_response

            # First validation - should fail and store (but not cache) the failure
            with pytest.raises(LicenseValidationError):
                validator.validate_api_key("invalid-cached-key")

            # Invalid license should be stored for reference
            assert validator.current_license is not None
            assert validator.current_license.is_valid is False
            assert validator.current_license.api_key == "invalid-cached-key"

            # Second validation with same key should NOT use cache
            # Invalid licenses are not cached by design, so this makes another API call
            with pytest.raises(LicenseValidationError):
                validator.validate_api_key("invalid-cached-key")

            # Both attempts should make API calls (invalid licenses not cached)
            assert mock_get.call_count == 2  # Two API calls - no caching for invalid


class TestLicenseValidationErrors:
    """Test suite for comprehensive error scenarios."""

    def test_license_validation_error_creation(self):
        """Test LicenseValidationError creation and attributes."""
        error = LicenseValidationError("Test message", "Test details")

        assert str(error) == "Test message"
        assert error.message == "Test message"
        assert error.details == "Test details"

    def test_license_validation_error_without_details(self):
        """Test LicenseValidationError without details."""
        error = LicenseValidationError("Test message")

        assert str(error) == "Test message"
        assert error.message == "Test message"
        assert error.details is None

    def test_api_timeout_with_retries(self, clean_license_cache):
        """Test API timeout behavior (no retries in current implementation)."""
        validator = get_validator()

        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.Timeout("Timeout after 30 seconds")

            with pytest.raises(LicenseValidationError) as exc_info:
                validator.validate_api_key("timeout-key")

            assert "timeout" in str(exc_info.value).lower()
            # Current implementation doesn't retry, so only one call
            assert mock_get.call_count == 1

    def test_malformed_api_response(self, clean_license_cache):
        """Test handling of malformed API responses."""
        validator = get_validator()

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_get.return_value = mock_response

            # Should handle JSON parsing error gracefully
            license_info = validator.validate_api_key("malformed-response-key")

            # Should still create license info, but with missing optional fields
            assert license_info.is_valid is True
            assert license_info.api_key == "malformed-response-key"
            assert license_info.account_id is None  # Missing from malformed response
            assert license_info.username is None  # Missing from malformed response

    def test_empty_api_response(self, clean_license_cache):
        """Test handling of empty API responses."""
        validator = get_validator()

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}
            mock_get.return_value = mock_response

            license_info = validator.validate_api_key("empty-response-key")

            # Should handle empty response gracefully
            assert license_info.is_valid is True
            assert license_info.api_key == "empty-response-key"
            assert license_info.account_id is None
            assert license_info.username is None

    def test_custom_api_url_configuration(self, clean_license_cache, mock_verodat_api_success):
        """Test using custom API URL from environment."""
        validator = get_validator()

        original_url = validator._api_url
        custom_url = "https://custom-api.example.com/api/v1"

        try:
            # Set custom URL
            with patch.dict(os.environ, {'VERODAT_API_URL': custom_url}):
                # Create new validator instance to pick up env var
                validator = LicenseValidator._instance = None
                validator = LicenseValidator()

                assert validator._api_url == custom_url

                # Validation should use custom URL
                validator.validate_api_key("custom-url-key")

                # Verify API was called with custom URL
                call_args = mock_verodat_api_success['get'].call_args[0]
                assert custom_url in call_args[0]
        finally:
            # Reset for other tests
            LicenseValidator._instance = None


@pytest.mark.integration
class TestLicenseValidationIntegration:
    """Integration tests for license validation with other enterprise components."""

    def test_license_validation_with_enterprise_decorator(self, clean_license_cache, mock_verodat_api_success):
        """Test that enterprise decorator validates license correctly."""
        from adri_enterprise.decorator import adri_protected
        import pandas as pd

        test_data = pd.DataFrame({
            "id": [1, 2, 3],
            "value": [10, 20, 30]
        })

        with patch.dict(os.environ, {'VERODAT_API_KEY': 'decorator-integration-key'}):
            @adri_protected(contract="test_license_integration")
            def test_function(data):
                return len(data)

            # Function should execute successfully (license validated)
            result = test_function(test_data)
            assert result == 3

            # Verify license was validated
            validator = get_validator()
            assert validator.is_validated is True
            assert validator.current_license.api_key == "decorator-integration-key"

    def test_license_validation_failure_blocks_decorator(self, clean_license_cache):
        """Test that license validation failure prevents decorator execution."""
        from adri_enterprise.decorator import adri_protected
        import pandas as pd

        test_data = pd.DataFrame({"id": [1, 2, 3]})

        # No API key provided
        with patch.dict(os.environ, {}, clear=True):
            @adri_protected(contract="test_license_failure")
            def test_function(data):
                return "should not execute"

            # Should raise license validation error
            with pytest.raises(LicenseValidationError):
                test_function(test_data)


@pytest.mark.performance
class TestLicenseValidationPerformance:
    """Performance tests for license validation system."""

    def test_validation_performance_baseline(self, clean_license_cache, mock_verodat_api_success, performance_baseline):
        """Test that license validation meets performance baseline."""
        validator = get_validator()

        start_time = time.time()
        validator.validate_api_key("performance-baseline-key")
        end_time = time.time()

        validation_time = end_time - start_time
        assert validation_time < performance_baseline['license_validation_max_time']

    def test_concurrent_validation_performance(self, clean_license_cache, mock_verodat_api_success):
        """Test performance with concurrent validations."""
        def concurrent_validation():
            validator = get_validator()
            return validator.validate_api_key("concurrent-perf-key")

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(concurrent_validation) for _ in range(20)]
            results = [future.result() for future in as_completed(futures)]

        end_time = time.time()

        # All validations should succeed
        assert len(results) == 20
        for result in results:
            assert result.is_valid is True

        # Total time should be reasonable (benefit from caching)
        total_time = end_time - start_time
        assert total_time < 5.0  # Should complete in under 5 seconds

        # API should only be called once due to singleton + caching
        assert mock_verodat_api_success['get'].call_count == 1
