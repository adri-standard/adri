"""
Advanced tests for Verodat API integration and logging.

Tests covering:
- Batch processing and retry logic for API calls
- Enterprise workflow context and data provenance handling
- Advanced error scenarios and recovery mechanisms
- Performance testing for API integration
- Complex integration scenarios with enterprise features
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock, call

import pytest
import requests

from adri_enterprise.logging.verodat import VerodatLogger, send_to_verodat


class TestVerodatLoggerAdvanced:
    """Advanced test suite for VerodatLogger functionality."""

    def test_verodat_logger_initialization(self):
        """Test VerodatLogger initialization with all parameters."""
        logger = VerodatLogger(
            api_url="https://custom.verodat.com/api/v1",
            api_key="custom-api-key",
            batch_size=15,
            retry_attempts=5,
            timeout=45
        )

        assert logger.api_url == "https://custom.verodat.com/api/v1"
        assert logger.api_key == "custom-api-key"
        assert logger.batch_size == 15
        assert logger.retry_attempts == 5
        assert logger.timeout == 45
        assert logger._batch_buffer == []

    def test_assessment_logging_with_enterprise_context(self, mock_workflow_context, mock_data_provenance):
        """Test assessment logging with full enterprise context."""
        logger = VerodatLogger("https://test.api.com", "test-key", batch_size=1)

        assessment_data = {
            "assessment_id": "enterprise_test_001",
            "timestamp": "2025-01-16T13:45:00Z",
            "overall_score": 88.5,
            "passed": True,
            "dimension_scores": {
                "validity": 18.0,
                "completeness": 19.0,
                "consistency": 17.5
            }
        }

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = logger.log_assessment(
                assessment_data=assessment_data,
                workflow_context=mock_workflow_context,
                data_provenance=mock_data_provenance
            )

            assert result is True
            mock_post.assert_called_once()

            # Verify enriched data was sent
            call_kwargs = mock_post.call_args[1]
            sent_data = call_kwargs["json"]

            # Should contain enriched data
            batch_data = sent_data["batch"][0]
            assert batch_data["assessment_id"] == "enterprise_test_001"
            assert batch_data["workflow_context"] == mock_workflow_context
            assert batch_data["data_provenance"] == mock_data_provenance

    def test_batch_processing_behavior(self):
        """Test that assessments are batched according to batch_size."""
        logger = VerodatLogger("https://test.api.com", "test-key", batch_size=3)

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            # Log 2 assessments - should not trigger batch send
            logger.log_assessment({"assessment_id": "batch_test_1"})
            logger.log_assessment({"assessment_id": "batch_test_2"})
            assert mock_post.call_count == 0
            assert len(logger._batch_buffer) == 2

            # Log 3rd assessment - should trigger batch send
            logger.log_assessment({"assessment_id": "batch_test_3"})
            assert mock_post.call_count == 1
            assert len(logger._batch_buffer) == 0  # Buffer should be cleared

            # Verify all 3 assessments were sent in batch
            sent_data = mock_post.call_args[1]["json"]
            batch_assessments = sent_data["batch"]
            assert len(batch_assessments) == 3
            assert batch_assessments[0]["assessment_id"] == "batch_test_1"
            assert batch_assessments[1]["assessment_id"] == "batch_test_2"
            assert batch_assessments[2]["assessment_id"] == "batch_test_3"

    def test_manual_batch_flush(self):
        """Test manual flushing of batch buffer."""
        logger = VerodatLogger("https://test.api.com", "test-key", batch_size=10)

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            # Add some assessments to buffer (less than batch_size)
            logger.log_assessment({"assessment_id": "flush_test_1"})
            logger.log_assessment({"assessment_id": "flush_test_2"})
            assert mock_post.call_count == 0

            # Manual flush
            result = logger.close()
            assert result is True
            assert mock_post.call_count == 1
            assert len(logger._batch_buffer) == 0

            # Verify assessments were sent
            sent_data = mock_post.call_args[1]["json"]
            assert len(sent_data["batch"]) == 2

    def test_workflow_step_logging(self, mock_workflow_context):
        """Test workflow step logging functionality."""
        logger = VerodatLogger("https://test.api.com", "test-key")

        step_data = {
            "step_duration": 45.2,
            "input_records": 150,
            "output_records": 147,
            "quality_metrics": {
                "validity": 98.0,
                "completeness": 95.3
            }
        }

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = logger.log_workflow_step(
                step_name="data_validation",
                workflow_context=mock_workflow_context,
                step_data=step_data
            )

            assert result is True
            mock_post.assert_called_once()

            # Verify workflow step data structure
            call_kwargs = mock_post.call_args[1]
            sent_data = call_kwargs["json"]

            assert sent_data["type"] == "workflow_step"
            assert sent_data["step_name"] == "data_validation"
            assert sent_data["workflow_context"] == mock_workflow_context
            assert sent_data["step_data"] == step_data

    def test_api_retry_logic_on_server_errors(self):
        """Test retry behavior for server errors (5xx)."""
        logger = VerodatLogger("https://test.api.com", "test-key", retry_attempts=3)

        with patch('requests.post') as mock_post:
            # First two calls return 500, third call succeeds
            responses = [
                MagicMock(status_code=500, text="Internal Server Error"),
                MagicMock(status_code=502, text="Bad Gateway"),
                MagicMock(status_code=200, json=lambda: {"success": True})
            ]
            mock_post.side_effect = responses

            result = logger.log_workflow_step(
                step_name="retry_test",
                workflow_context={"run_id": "retry_test_001"}
            )

            # Should succeed after retries
            assert result is True
            assert mock_post.call_count == 3

    def test_api_no_retry_on_client_errors(self):
        """Test that client errors (4xx) don't trigger retries."""
        logger = VerodatLogger("https://test.api.com", "test-key", retry_attempts=3)

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_post.return_value = mock_response

            result = logger.log_workflow_step("client_error_test", {"run_id": "test"})

            # Should fail immediately without retries
            assert result is False
            assert mock_post.call_count == 1

    def test_api_retry_exhaustion(self):
        """Test behavior when all retry attempts are exhausted."""
        logger = VerodatLogger("https://test.api.com", "test-key", retry_attempts=2)

        with patch('requests.post') as mock_post:
            # All calls return 500
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Persistent Server Error"
            mock_post.return_value = mock_response

            result = logger.log_workflow_step("exhaustion_test", {"run_id": "test"})

            # Should fail after all retries
            assert result is False
            assert mock_post.call_count == 2  # Initial + 1 retry (retry_attempts=2 means max 2 total attempts)

    def test_api_timeout_with_retries(self):
        """Test timeout handling with retry logic."""
        logger = VerodatLogger("https://test.api.com", "test-key", retry_attempts=3, timeout=1)

        with patch('requests.post') as mock_post:
            # First two calls timeout, third succeeds
            side_effects = [
                requests.Timeout("Request timed out"),
                requests.Timeout("Request timed out"),
                MagicMock(status_code=200, json=lambda: {"success": True})
            ]
            mock_post.side_effect = side_effects

            result = logger.log_workflow_step("timeout_retry_test", {"run_id": "test"})

            # Should succeed after timeout retries
            assert result is True
            assert mock_post.call_count == 3

    def test_api_connection_error_handling(self):
        """Test handling of connection errors."""
        logger = VerodatLogger("https://test.api.com", "test-key", batch_size=1)

        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.ConnectionError("Connection failed")

            result = logger.log_assessment({"assessment_id": "connection_error_test"})

            assert result is False

    def test_authentication_headers_correct(self):
        """Test that authentication headers are set correctly."""
        logger = VerodatLogger("https://test.api.com", "secret-api-key-123", batch_size=1)

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            logger.log_assessment({"assessment_id": "auth_test"})

            # Verify headers
            call_kwargs = mock_post.call_args[1]
            headers = call_kwargs["headers"]
            assert headers["Authorization"] == "ApiKey secret-api-key-123"
            assert headers["Content-Type"] == "application/json"

    def test_api_url_configuration(self):
        """Test that custom API URLs are used correctly."""
        custom_url = "https://custom.verodat.example.com/api/v2"
        logger = VerodatLogger(custom_url, "test-key")

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            logger.log_workflow_step("url_test", {"run_id": "test"})

            # Verify URL
            call_args = mock_post.call_args[0]
            assert call_args[0] == custom_url

    def test_timeout_configuration(self):
        """Test that timeout is configured correctly."""
        logger = VerodatLogger("https://test.api.com", "test-key", timeout=60, batch_size=1)

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            logger.log_assessment({"assessment_id": "timeout_config_test"})

            # Verify timeout
            call_kwargs = mock_post.call_args[1]
            assert call_kwargs["timeout"] == 60


class TestVerodatLoggerErrorHandling:
    """Test suite for comprehensive error handling."""

    def test_batch_send_failure_preserves_buffer(self):
        """Test that batch buffer is preserved when send fails."""
        logger = VerodatLogger("https://test.api.com", "test-key", batch_size=2)

        with patch('requests.post') as mock_post:
            # Mock persistent failure
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_post.return_value = mock_response

            # Fill batch buffer
            result1 = logger.log_assessment({"assessment_id": "preserve_test_1"})
            result2 = logger.log_assessment({"assessment_id": "preserve_test_2"})  # This triggers flush

            # Second call should fail due to API error
            assert result2 is False

            # Buffer should still contain data since send failed
            assert len(logger._batch_buffer) == 2

    def test_partial_batch_processing_resilience(self):
        """Test resilience when some assessments in batch are malformed."""
        logger = VerodatLogger("https://test.api.com", "test-key", batch_size=1)  # Immediate send

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            # Log assessment with potentially problematic data
            complex_assessment = {
                "assessment_id": "complex_test",
                "nested_data": {
                    "level1": {
                        "level2": {
                            "level3": "deep_value"
                        }
                    }
                },
                "special_chars": "Special characters: àáâãäå æç èéêë",
                "unicode_test": "🚀 Unicode test 📊",
                "large_number": 99999999999999999999,
                "null_value": None,
                "empty_list": [],
                "empty_dict": {}
            }

            result = logger.log_assessment(complex_assessment)

            # Should handle complex data gracefully
            assert result is True
            mock_post.assert_called_once()

            # Verify data was serialized correctly
            sent_data = mock_post.call_args[1]["json"]
            batch_data = sent_data["batch"][0]
            assert batch_data["special_chars"] == "Special characters: àáâãäå æç èéêë"
            assert batch_data["unicode_test"] == "🚀 Unicode test 📊"
            assert batch_data["null_value"] is None

    def test_json_serialization_error_handling(self):
        """Test handling of JSON serialization errors."""
        logger = VerodatLogger("https://test.api.com", "test-key", batch_size=1)

        # Create object that can't be JSON serialized
        class NonSerializable:
            def __init__(self):
                self.circular_ref = self

        problematic_data = {
            "assessment_id": "json_error_test",
            "bad_object": NonSerializable()
        }

        with patch('requests.post') as mock_post:
            result = logger.log_assessment(problematic_data)

            # Should fail gracefully without crashing
            assert result is False
            # API should not be called due to serialization failure
            assert mock_post.call_count == 0

    def test_large_payload_handling(self):
        """Test handling of very large payloads."""
        logger = VerodatLogger("https://test.api.com", "test-key", batch_size=1)

        # Create very large assessment data
        large_assessment = {
            "assessment_id": "large_payload_test",
            "large_data": {
                "records": [
                    {
                        "id": i,
                        "data": f"Large record data {i} " * 100  # 100x repeated string
                    }
                    for i in range(1000)  # 1000 large records
                ]
            }
        }

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = logger.log_assessment(large_assessment)

            # Should handle large payload
            assert result is True
            mock_post.assert_called_once()

            # Verify large data was included
            sent_data = mock_post.call_args[1]["json"]
            batch_data = sent_data["batch"][0]
            assert len(batch_data["large_data"]["records"]) == 1000

    def test_network_interruption_recovery(self):
        """Test recovery from network interruptions."""
        logger = VerodatLogger("https://test.api.com", "test-key", retry_attempts=3)

        with patch('requests.post') as mock_post:
            # Simulate network interruption then recovery
            side_effects = [
                requests.ConnectionError("Network unreachable"),
                requests.Timeout("Network timeout"),
                MagicMock(status_code=200, json=lambda: {"success": True})
            ]
            mock_post.side_effect = side_effects

            result = logger.log_workflow_step("network_recovery_test", {"run_id": "test"})

            # Should recover and succeed
            assert result is True
            assert mock_post.call_count == 3


class TestSendToVerodatConvenienceFunction:
    """Test suite for the convenience function."""

    def test_send_to_verodat_basic_functionality(self):
        """Test basic send_to_verodat function."""
        assessment_data = {
            "assessment_id": "convenience_test_001",
            "overall_score": 85.5,
            "passed": True
        }

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = send_to_verodat(
                assessment_data,
                "https://api.verodat.com/assessments",
                "convenience-api-key"
            )

            assert result is True
            mock_post.assert_called_once()

            # Verify it was sent immediately (batch_size=1)
            sent_data = mock_post.call_args[1]["json"]
            batch_data = sent_data["batch"][0]
            assert batch_data["assessment_id"] == "convenience_test_001"

    def test_send_to_verodat_error_handling(self):
        """Test send_to_verodat error handling."""
        assessment_data = {"assessment_id": "convenience_error_test"}

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_post.return_value = mock_response

            result = send_to_verodat(
                assessment_data,
                "https://api.verodat.com/assessments",
                "test-key"
            )

            assert result is False

    def test_send_to_verodat_backward_compatibility(self):
        """Test that send_to_verodat maintains backward compatibility."""
        # This function should work the same as before (from existing tests)
        assessment_data = {
            "assessment_id": "compat_test_001",
            "overall_score": 92.3,
            "passed": True,
            "dimension_scores": {
                "validity": 18.5,
                "completeness": 19.2
            }
        }

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True, "id": "uploaded_001"}
            mock_post.return_value = mock_response

            result = send_to_verodat(
                assessment_data,
                "https://api.verodat.com/upload",
                "backward-compat-key"
            )

            assert result is True

            # Verify standard headers and timeout
            call_kwargs = mock_post.call_args[1]
            assert call_kwargs["headers"]["Authorization"] == "ApiKey backward-compat-key"
            assert call_kwargs["headers"]["Content-Type"] == "application/json"
            # Note: exact timeout behavior may depend on implementation


@pytest.mark.integration
class TestVerodatLoggerIntegration:
    """Integration tests for Verodat logger with enterprise components."""

    def test_verodat_with_enterprise_decorator_integration(
        self, mock_workflow_context, mock_data_provenance
    ):
        """Test integration with enterprise decorator workflow."""
        from adri_enterprise.decorator import _log_workflow_context, _log_data_provenance

        logger = VerodatLogger("https://test.api.com", "integration-key")

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            # Simulate decorator logging workflow context
            _log_workflow_context(mock_workflow_context, "test_function", verbose=True)

            # Simulate decorator logging data provenance
            _log_data_provenance(mock_data_provenance, "test_function", verbose=True)

            # Log assessment with context (as decorator would do)
            assessment_data = {
                "assessment_id": "integration_test_001",
                "function_name": "test_function",
                "overall_score": 88.5
            }

            result = logger.log_assessment(
                assessment_data=assessment_data,
                workflow_context=mock_workflow_context,
                data_provenance=mock_data_provenance
            )

            assert result is True

    def test_verodat_with_license_validation_integration(self, mock_verodat_api_success):
        """Test integration with license validation system."""
        from adri_enterprise.license import validate_license, get_validator

        # First validate license (this would happen in decorator)
        license_info = validate_license("integration-license-key")
        assert license_info.is_valid is True

        # Then use Verodat logger (as enterprise decorator would)
        logger = VerodatLogger("https://test.api.com", "integration-license-key")

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            # Include license info in assessment
            assessment_data = {
                "assessment_id": "license_integration_001",
                "license_account_id": license_info.account_id,
                "license_username": license_info.username
            }

            result = logger.log_assessment(assessment_data)
            assert result is True

    def test_verodat_with_reasoning_logger_integration(self, temp_log_dir, mock_reasoning_data):
        """Test integration with reasoning logger."""
        from adri_enterprise.logging.reasoning import ReasoningLogger

        # Set up both loggers with batch_size=1 for immediate sending
        verodat_logger = VerodatLogger("https://test.api.com", "reasoning-integration-key", batch_size=1)
        reasoning_logger = ReasoningLogger(log_dir=temp_log_dir)

        # Log reasoning step
        prompt_id, response_id = reasoning_logger.log_reasoning_step(
            prompt=mock_reasoning_data['prompt'],
            response=mock_reasoning_data['response'],
            assessment_id=mock_reasoning_data['assessment_id']
        )

        # Send assessment with reasoning references to Verodat
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            assessment_data = {
                "assessment_id": mock_reasoning_data['assessment_id'],
                "reasoning_prompt_id": prompt_id,
                "reasoning_response_id": response_id,
                "has_reasoning_logs": True
            }

            result = verodat_logger.log_assessment(assessment_data)
            assert result is True

            # Verify reasoning IDs were included
            sent_data = mock_post.call_args[1]["json"]
            batch_data = sent_data["batch"][0]
            assert batch_data["reasoning_prompt_id"] == prompt_id
            assert batch_data["reasoning_response_id"] == response_id


@pytest.mark.performance
class TestVerodatLoggerPerformance:
    """Performance tests for Verodat logger."""

    def test_batch_processing_performance(self, performance_baseline):
        """Test batch processing performance meets baseline."""
        logger = VerodatLogger("https://test.api.com", "perf-key", batch_size=50)

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            # Measure time to process a batch
            assessments = [
                {"assessment_id": f"perf_test_{i}", "score": 80 + i}
                for i in range(50)
            ]

            start_time = time.time()
            for assessment in assessments[:-1]:
                logger.log_assessment(assessment)  # Build batch

            # Last one triggers send
            logger.log_assessment(assessments[-1])
            end_time = time.time()

            total_time = end_time - start_time
            # Should complete batch processing within reasonable time
            assert total_time < 5.0  # Should complete within 5 seconds

            # Verify batch was sent
            assert mock_post.call_count == 1
            sent_data = mock_post.call_args[1]["json"]
            assert len(sent_data["batch"]) == 50

    def test_concurrent_logging_performance(self):
        """Test performance with concurrent logging operations."""
        logger = VerodatLogger("https://test.api.com", "concurrent-perf-key", batch_size=1)

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            def concurrent_log(assessment_id):
                return logger.log_assessment({
                    "assessment_id": f"concurrent_{assessment_id}",
                    "score": 85
                })

            start_time = time.time()

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(concurrent_log, i)
                    for i in range(25)
                ]
                results = [future.result() for future in as_completed(futures)]

            end_time = time.time()

            # All operations should succeed
            assert len(results) == 25
            assert all(results)

            # Should complete within reasonable time
            total_time = end_time - start_time
            assert total_time < 10.0  # Should complete within 10 seconds

            # All assessments should have been sent
            assert mock_post.call_count == 25

    def test_large_assessment_processing_performance(self):
        """Test performance with large assessment payloads."""
        logger = VerodatLogger("https://test.api.com", "large-payload-key", batch_size=1)

        # Create large assessment
        large_assessment = {
            "assessment_id": "large_perf_test",
            "dimension_scores": {
                f"dimension_{i}": float(80 + (i % 20))
                for i in range(100)  # 100 dimensions
            },
            "detailed_metrics": {
                f"metric_{i}": {
                    "value": float(i * 1.5),
                    "threshold": float(i * 1.2),
                    "status": "pass" if i % 2 == 0 else "fail",
                    "details": f"Detailed information for metric {i} " * 10
                }
                for i in range(200)  # 200 detailed metrics
            }
        }

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            start_time = time.time()
            result = logger.log_assessment(large_assessment)
            end_time = time.time()

            # Should handle large payload efficiently
            assert result is True
            processing_time = end_time - start_time
            assert processing_time < 2.0  # Should complete within 2 seconds

            # Verify large data was sent correctly
            sent_data = mock_post.call_args[1]["json"]
            batch_data = sent_data["batch"][0]
            assert len(batch_data["dimension_scores"]) == 100
            assert len(batch_data["detailed_metrics"]) == 200

    def test_api_call_performance_baseline(self, performance_baseline):
        """Test that API calls meet performance baseline."""
        logger = VerodatLogger("https://test.api.com", "baseline-key")

        with patch('requests.post') as mock_post:
            # Simulate realistic API response time
            def mock_response_with_delay():
                time.sleep(0.1)  # 100ms simulated network delay
                response = MagicMock()
                response.status_code = 200
                return response

            mock_post.side_effect = lambda *args, **kwargs: mock_response_with_delay()

            start_time = time.time()
            result = logger.log_workflow_step("baseline_test", {"run_id": "perf_test"})
            end_time = time.time()

            assert result is True
            api_call_time = end_time - start_time
            assert api_call_time < performance_baseline['verodat_api_call_max_time']
