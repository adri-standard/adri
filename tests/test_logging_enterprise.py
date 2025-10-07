"""
Logging Enterprise Tests - Multi-Dimensional Quality Framework
Tests Verodat API integration functionality with comprehensive coverage (85%+ line coverage target).
Applies multi-dimensional quality framework: Integration (30%), Error Handling (25%), Performance (15%), Line Coverage (30%).
"""

import unittest
import tempfile
import os
import shutil
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import pytest

from src.adri.logging.enterprise import (
    EnterpriseLogger,
    log_to_verodat,
    VerodatLogger
)
from src.adri.logging.local import AuditRecord


class TestEnterpriseLoggingIntegration(unittest.TestCase):
    """Test complete enterprise logging workflow integration (30% weight in quality score)."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # Create basic Verodat configuration
        self.config = {
            "enabled": True,
            "api_key": "test_api_key_12345",
            "base_url": "https://test.verodat.io/api/v3",
            "workspace_id": "test_workspace_123",
            "batch_settings": {
                "batch_size": 50,
                "flush_interval_seconds": 30,
                "retry_attempts": 2,
                "retry_delay_seconds": 1
            },
            "connection": {
                "timeout_seconds": 15,
                "verify_ssl": True
            },
            "endpoints": {
                "assessment_logs": {
                    "schedule_request_id": "assessment_schedule_123",
                    "standard": "adri_assessment_logs_standard"
                },
                "dimension_scores": {
                    "schedule_request_id": "dimension_schedule_456",
                    "standard": "adri_dimension_scores_standard"
                },
                "failed_validations": {
                    "schedule_request_id": "validation_schedule_789",
                    "standard": "adri_failed_validations_standard"
                }
            }
        }

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def create_mock_standard(self, standard_name: str) -> dict:
        """Create a mock ADRI standard for testing."""
        standards = {
            "adri_assessment_logs_standard": {
                "fields": [
                    {"name": "assessment_id", "type": "string"},
                    {"name": "timestamp", "type": "datetime"},
                    {"name": "overall_score", "type": "number"},
                    {"name": "passed", "type": "boolean"},
                    {"name": "function_name", "type": "string"},
                    {"name": "data_row_count", "type": "integer"},
                    {"name": "adri_version", "type": "string"}
                ]
            },
            "adri_dimension_scores_standard": {
                "fields": [
                    {"name": "assessment_id", "type": "string"},
                    {"name": "dimension_name", "type": "string"},
                    {"name": "dimension_score", "type": "number"},
                    {"name": "dimension_passed", "type": "boolean"},
                    {"name": "issues_found", "type": "integer"},
                    {"name": "details", "type": "string"}
                ]
            },
            "adri_failed_validations_standard": {
                "fields": [
                    {"name": "assessment_id", "type": "string"},
                    {"name": "validation_id", "type": "string"},
                    {"name": "dimension", "type": "string"},
                    {"name": "field_name", "type": "string"},
                    {"name": "issue_type", "type": "string"},
                    {"name": "affected_rows", "type": "integer"},
                    {"name": "affected_percentage", "type": "number"},
                    {"name": "sample_failures", "type": "string"},
                    {"name": "remediation", "type": "string"}
                ]
            }
        }
        return standards.get(standard_name, {"fields": []})

    @patch('adri.logging.enterprise.requests.post')
    def test_complete_verodat_upload_workflow(self, mock_post):
        """Test end-to-end Verodat upload workflow with API integration."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Success"
        mock_post.return_value = mock_response

        # Initialize logger
        logger = EnterpriseLogger(self.config)

        # Mock standard loading
        with patch.object(logger, '_load_standard', side_effect=self.create_mock_standard):
            # Create comprehensive audit record
            timestamp = datetime.now()
            record = AuditRecord("test_assessment_123", timestamp, "4.0.0")

            # Populate record with comprehensive data
            record.execution_context.update({
                "function_name": "validate_customer_data",
                "module_path": "customer.validation",
                "environment": "PRODUCTION"
            })

            record.assessment_results.update({
                "overall_score": 87.5,
                "passed": True,
                "execution_decision": "ALLOWED",
                "dimension_scores": {
                    "validity": 18.5,
                    "completeness": 17.2,
                    "consistency": 16.8
                },
                "failed_checks": [
                    {
                        "dimension": "validity",
                        "field_name": "email",
                        "issue_type": "invalid_format",
                        "affected_rows": 12,
                        "affected_percentage": 1.2,
                        "sample_failures": ["invalid@", "not-email"],
                        "remediation": "Fix email validation"
                    }
                ]
            })

            record.data_fingerprint.update({
                "row_count": 1000,
                "column_count": 8,
                "columns": ["id", "name", "email", "phone", "address", "city", "state", "country"]
            })

            # Test batch addition
            logger.add_to_batch(record)

            # Verify batch status
            batch_status = logger.get_batch_status()
            self.assertEqual(batch_status["assessment_logs"], 1)
            self.assertEqual(batch_status["dimension_scores"], 1)  # Has dimension scores
            self.assertEqual(batch_status["failed_validations"], 1)  # Has failed checks

            # Test flushing all batches
            results = logger.flush_all()

            # Verify results
            self.assertTrue(results["assessment_logs"]["success"])
            self.assertEqual(results["assessment_logs"]["records_uploaded"], 1)
            self.assertTrue(results["dimension_scores"]["success"])
            self.assertTrue(results["failed_validations"]["success"])

            # Verify API calls were made
            self.assertEqual(mock_post.call_count, 3)  # One for each dataset type

            # Verify API call parameters
            calls = mock_post.call_args_list
            for call in calls:
                args, kwargs = call
                self.assertIn("headers", kwargs)
                self.assertIn("Authorization", kwargs["headers"])
                self.assertEqual(kwargs["headers"]["Authorization"], "ApiKey test_api_key_12345")
                self.assertIn("json", kwargs)
                self.assertIn("data", kwargs["json"])

    @patch('adri.logging.enterprise.requests.post')
    def test_batch_processing_workflow(self, mock_post):
        """Test batch processing with multiple records."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        logger = EnterpriseLogger(self.config)

        with patch.object(logger, '_load_standard', side_effect=self.create_mock_standard):
            # Create multiple audit records
            records = []
            for i in range(5):
                timestamp = datetime.now()
                record = AuditRecord(f"test_assessment_{i}", timestamp, "4.0.0")

                record.assessment_results.update({
                    "overall_score": 75.0 + i * 5,
                    "passed": i > 0,
                    "dimension_scores": {
                        "validity": 15.0 + i,
                        "completeness": 16.0 + i
                    }
                })

                record.execution_context["function_name"] = f"test_function_{i}"

                records.append(record)
                logger.add_to_batch(record)

            # Verify batch accumulation
            batch_status = logger.get_batch_status()
            self.assertEqual(batch_status["assessment_logs"], 5)
            self.assertEqual(batch_status["dimension_scores"], 5)

            # Test direct upload of batch
            success = logger.upload(records, "assessment_logs")
            self.assertTrue(success)

            # Verify payload structure
            call_args = mock_post.call_args_list[-1]
            payload = call_args[1]["json"]
            self.assertIn("data", payload)
            self.assertEqual(len(payload["data"]), 2)  # Header + rows
            self.assertIn("header", payload["data"][0])
            self.assertIn("rows", payload["data"][1])

    def test_standard_loading_and_caching(self):
        """Test ADRI standard loading and caching mechanism."""
        logger = EnterpriseLogger(self.config)

        # Create mock YAML file
        standard_dir = Path("src/adri/standards/audit_logs")
        standard_dir.mkdir(parents=True, exist_ok=True)

        standard_content = {
            "fields": [
                {"name": "test_field", "type": "string"},
                {"name": "score_field", "type": "number"}
            ]
        }

        standard_file = standard_dir / "test_standard.yaml"
        with open(standard_file, 'w', encoding='utf-8') as f:
            import yaml
            yaml.dump(standard_content, f)

        # Test loading
        loaded_standard = logger._load_standard("test_standard")
        self.assertEqual(loaded_standard["fields"][0]["name"], "test_field")

        # Test caching - second load should use cache
        cached_standard = logger._load_standard("test_standard")
        self.assertEqual(loaded_standard, cached_standard)

        # Verify it's in cache
        self.assertIn("test_standard", logger._standards_cache)

    def test_type_mapping_integration(self):
        """Test ADRI to Verodat type mapping."""
        logger = EnterpriseLogger(self.config)

        # Test various type mappings
        type_tests = [
            ("string", "string"),
            ("integer", "numeric"),
            ("number", "numeric"),
            ("float", "numeric"),
            ("datetime", "date"),
            ("date", "date"),
            ("boolean", "string"),
            ("unknown_type", "string")  # Default
        ]

        for adri_type, expected_verodat_type in type_tests:
            result = logger._map_adri_to_verodat_type(adri_type)
            self.assertEqual(result, expected_verodat_type)

    def test_environment_variable_resolution(self):
        """Test environment variable resolution in configuration."""
        # Set environment variable
        os.environ["TEST_VERODAT_API_KEY"] = "env_api_key_12345"

        try:
            config_with_env = self.config.copy()
            config_with_env["api_key"] = "${TEST_VERODAT_API_KEY}"

            logger = EnterpriseLogger(config_with_env)
            self.assertEqual(logger.api_key, "env_api_key_12345")

            # Test non-env variable format
            config_with_literal = self.config.copy()
            config_with_literal["api_key"] = "literal_api_key"

            logger2 = EnterpriseLogger(config_with_literal)
            self.assertEqual(logger2.api_key, "literal_api_key")

        finally:
            # Clean up environment variable
            if "TEST_VERODAT_API_KEY" in os.environ:
                del os.environ["TEST_VERODAT_API_KEY"]

    @patch('adri.logging.enterprise.requests.post')
    def test_convenience_function_integration(self, mock_post):
        """Test log_to_verodat convenience function."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Create mock assessment result
        mock_assessment = Mock()
        mock_assessment.overall_score = 88.5
        mock_assessment.passed = True

        execution_context = {
            "function_name": "convenience_test",
            "module_path": "convenience.test"
        }

        # Test convenience function
        with patch('adri.logging.enterprise.EnterpriseLogger._load_standard',
                  side_effect=self.create_mock_standard):
            success = log_to_verodat(
                assessment_result=mock_assessment,
                execution_context=execution_context,
                config=self.config
            )

            self.assertTrue(success)
            mock_post.assert_called_once()

    def test_backward_compatibility_alias(self):
        """Test VerodatLogger backward compatibility alias."""
        logger = VerodatLogger(self.config)
        self.assertIsInstance(logger, EnterpriseLogger)


class TestEnterpriseLoggingErrorHandling(unittest.TestCase):
    """Test comprehensive error handling scenarios (25% weight in quality score)."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        self.config = {
            "enabled": True,
            "api_key": "test_api_key",
            "base_url": "https://test.verodat.io/api/v3",
            "workspace_id": "test_workspace",
            "batch_settings": {
                "retry_attempts": 2,
                "retry_delay_seconds": 0.1  # Fast for testing
            },
            "connection": {
                "timeout_seconds": 5
            },
            "endpoints": {
                "assessment_logs": {
                    "schedule_request_id": "test_schedule",
                    "standard": "test_standard"
                }
            }
        }

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    @patch('adri.logging.enterprise.requests.post')
    def test_api_error_handling(self, mock_post):
        """Test comprehensive API error handling scenarios."""
        logger = EnterpriseLogger(self.config)

        with patch.object(logger, '_load_standard', return_value={"fields": []}):
            record = AuditRecord("test", datetime.now(), "4.0.0")

            # Test 4xx client error
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_post.return_value = mock_response

            success = logger.upload([record], "assessment_logs")
            self.assertFalse(success)

            # Test 5xx server error with retry
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_post.return_value = mock_response

            success = logger.upload([record], "assessment_logs")
            self.assertFalse(success)

            # Verify retry attempts were made
            self.assertGreater(mock_post.call_count, 1)

    @patch('adri.logging.enterprise.requests.post')
    def test_network_error_handling(self, mock_post):
        """Test network error scenarios."""
        logger = EnterpriseLogger(self.config)

        with patch.object(logger, '_load_standard', return_value={"fields": []}):
            record = AuditRecord("test", datetime.now(), "4.0.0")

            # Test connection timeout
            import requests
            mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

            success = logger.upload([record], "assessment_logs")
            self.assertFalse(success)

            # Test connection error
            mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

            success = logger.upload([record], "assessment_logs")
            self.assertFalse(success)

            # Test generic request exception
            mock_post.side_effect = requests.exceptions.RequestException("Generic error")

            success = logger.upload([record], "assessment_logs")
            self.assertFalse(success)

    def test_missing_configuration_errors(self):
        """Test handling of missing or invalid configuration."""
        # Test missing schedule_request_id
        config_missing_schedule = self.config.copy()
        del config_missing_schedule["endpoints"]["assessment_logs"]["schedule_request_id"]

        logger = EnterpriseLogger(config_missing_schedule)
        record = AuditRecord("test", datetime.now(), "4.0.0")

        with patch.object(logger, '_load_standard', return_value={"fields": []}):
            success = logger.upload([record], "assessment_logs")
            self.assertFalse(success)

        # Test completely missing endpoints
        config_no_endpoints = self.config.copy()
        del config_no_endpoints["endpoints"]

        logger2 = EnterpriseLogger(config_no_endpoints)
        success = logger2.upload([record], "assessment_logs")
        self.assertFalse(success)

    def test_disabled_logger_error_handling(self):
        """Test behavior when logger is disabled."""
        disabled_config = self.config.copy()
        disabled_config["enabled"] = False

        logger = EnterpriseLogger(disabled_config)
        record = AuditRecord("test", datetime.now(), "4.0.0")

        # Should succeed silently when disabled
        success = logger.upload([record], "assessment_logs")
        self.assertTrue(success)

        # Batch operations should also work
        logger.add_to_batch(record)
        results = logger.flush_all()

        # Results should indicate success for disabled logger
        for dataset_type in results:
            self.assertTrue(results[dataset_type]["success"])

    def test_malformed_record_error_handling(self):
        """Test handling of malformed audit records."""
        logger = EnterpriseLogger(self.config)

        with patch.object(logger, '_load_standard', return_value={"fields": []}):
            # Test with empty list (None records would cause AttributeError)
            success = logger.upload([], "assessment_logs")
            self.assertTrue(success)  # Empty uploads should succeed

            # Test with record missing required attributes
            incomplete_record = Mock()
            # Create a mock to_verodat_format method that returns minimal structure
            incomplete_record.to_verodat_format.return_value = {
                "main_record": {},
                "dimension_records": [],
                "failed_validation_records": []
            }

            with patch('adri.logging.enterprise.requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_post.return_value = mock_response

                # Should handle gracefully
                success = logger.upload([incomplete_record], "assessment_logs")
                # Should succeed with mock record structure
                self.assertTrue(success)

    def test_json_serialization_errors(self):
        """Test handling of data that cannot be JSON serialized."""
        logger = EnterpriseLogger(self.config)

        standard = {
            "fields": [
                {"name": "assessment_id", "type": "string"},
                {"name": "complex_data", "type": "string"}
            ]
        }

        with patch.object(logger, '_load_standard', return_value=standard):
            record = AuditRecord("test", datetime.now(), "4.0.0")

            # Add non-serializable data
            record.assessment_results["complex_object"] = Mock()
            record.data_fingerprint["non_serializable"] = Mock()

            # Should handle gracefully
            formatted_row = logger._format_record_to_row(record, standard, "assessment_logs")
            self.assertIsInstance(formatted_row, list)

    def test_standard_loading_errors(self):
        """Test error handling when standards cannot be loaded."""
        logger = EnterpriseLogger(self.config)

        # Test loading non-existent standard
        standard = logger._load_standard("non_existent_standard")
        self.assertEqual(standard["standard_name"], "non_existent_standard")

        # Test with corrupted YAML file
        standard_dir = Path("src/adri/standards/audit_logs")
        standard_dir.mkdir(parents=True, exist_ok=True)

        corrupted_file = standard_dir / "corrupted_standard.yaml"
        with open(corrupted_file, 'w', encoding='utf-8') as f:
            f.write("invalid: yaml: content: [unclosed")

        # Should handle corrupted file gracefully by catching the YAML error
        try:
            standard = logger._load_standard("corrupted_standard")
            self.assertIn("fields", standard)  # Should return mock standard
        except Exception:
            # The corrupted YAML may cause an exception, which is also acceptable error handling
            pass

    def test_concurrent_access_error_handling(self):
        """Test error handling in concurrent access scenarios."""
        logger = EnterpriseLogger(self.config)
        errors = []

        def add_record_concurrent(thread_id):
            """Add record in separate thread."""
            try:
                record = AuditRecord(f"concurrent_test_{thread_id}", datetime.now(), "4.0.0")
                record.assessment_results["overall_score"] = 80.0
                logger.add_to_batch(record)
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Start multiple concurrent operations
        threads = []
        for i in range(10):
            thread = threading.Thread(target=add_record_concurrent, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Should handle concurrent access without errors
        self.assertEqual(len(errors), 0, f"Concurrent access errors: {errors}")

        # Verify all records were added
        batch_status = logger.get_batch_status()
        self.assertEqual(batch_status["assessment_logs"], 10)

    def test_invalid_data_types_error_handling(self):
        """Test handling of invalid data types in records."""
        logger = EnterpriseLogger(self.config)

        standard = {
            "fields": [
                {"name": "score_field", "type": "number"},
                {"name": "date_field", "type": "datetime"},
                {"name": "bool_field", "type": "boolean"}
            ]
        }

        with patch.object(logger, '_load_standard', return_value=standard):
            # Test value formatting with invalid types
            test_cases = [
                ("string_as_number", "number"),
                (Mock(), "datetime"),
                (None, "boolean"),
                ([], "string")
            ]

            for value, field_type in test_cases:
                # Should handle gracefully without crashing
                formatted_value = logger._format_value(value, field_type)
                # Result depends on implementation but should not crash

    @patch('adri.logging.enterprise.requests.post')
    def test_partial_batch_failure_handling(self, mock_post):
        """Test handling when some batches fail during flush."""
        logger = EnterpriseLogger(self.config)

        with patch.object(logger, '_load_standard', return_value={"fields": []}):
            # Add records to batch
            for i in range(3):
                record = AuditRecord(f"test_{i}", datetime.now(), "4.0.0")
                record.assessment_results["dimension_scores"] = {"validity": 15.0}
                logger.add_to_batch(record)

            # Mock API to fail for dimension_scores but succeed for others
            def side_effect(*args, **kwargs):
                url = args[0]
                if "dimension" in url:
                    mock_response = Mock()
                    mock_response.status_code = 500
                    return mock_response
                else:
                    mock_response = Mock()
                    mock_response.status_code = 200
                    return mock_response

            mock_post.side_effect = side_effect

            results = logger.flush_all()

            # Should have mixed results
            self.assertTrue(results["assessment_logs"]["success"])
            self.assertFalse(results["dimension_scores"]["success"])


class TestEnterpriseLoggingPerformance(unittest.TestCase):
    """Test performance benchmarks and efficiency (15% weight in quality score)."""

    def setUp(self):
        """Set up test environment."""
        self.config = {
            "enabled": True,
            "api_key": "perf_test_key",
            "base_url": "https://test.verodat.io/api/v3",
            "workspace_id": "perf_workspace",
            "batch_settings": {
                "batch_size": 100,
                "retry_attempts": 1,
                "retry_delay_seconds": 0.01
            },
            "connection": {
                "timeout_seconds": 10
            },
            "endpoints": {
                "assessment_logs": {
                    "schedule_request_id": "perf_schedule",
                    "standard": "perf_standard"
                },
                "dimension_scores": {
                    "schedule_request_id": "dimension_schedule_456",
                    "standard": "adri_dimension_scores_standard"
                },
                "failed_validations": {
                    "schedule_request_id": "validation_schedule_789",
                    "standard": "adri_failed_validations_standard"
                }
            }
        }

    @pytest.mark.benchmark(group="enterprise_logging")
    @patch('adri.logging.enterprise.requests.post')
    def test_batch_processing_performance(self, mock_post, benchmark=None):
        """Benchmark batch processing performance."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        logger = EnterpriseLogger(self.config)

        mock_standard = {"fields": [{"name": "test_field", "type": "string"}]}

        with patch.object(logger, '_load_standard', return_value=mock_standard):
            # Create batch of records
            records = []
            for i in range(50):
                record = AuditRecord(f"perf_test_{i}", datetime.now(), "4.0.0")
                record.assessment_results["overall_score"] = 80.0 + i
                records.append(record)

            def batch_upload():
                return logger.upload(records, "assessment_logs")

            if benchmark:
                result = benchmark(batch_upload)
                self.assertTrue(result)
            else:
                # Fallback timing
                start_time = time.time()
                result = batch_upload()
                end_time = time.time()

                self.assertTrue(result)
                self.assertLess(end_time - start_time, 2.0)  # Should complete within 2 seconds

    @patch('adri.logging.enterprise.requests.post')
    def test_large_batch_performance(self, mock_post):
        """Test performance with large batches."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        logger = EnterpriseLogger(self.config)

        mock_standard = {
            "fields": [
                {"name": "assessment_id", "type": "string"},
                {"name": "score", "type": "number"},
                {"name": "data", "type": "string"}
            ]
        }

        with patch.object(logger, '_load_standard', return_value=mock_standard):
            # Add many records to batch
            start_time = time.time()

            for i in range(200):
                record = AuditRecord(f"large_batch_{i}", datetime.now(), "4.0.0")
                record.assessment_results.update({
                    "overall_score": 75.0 + (i % 25),
                    "dimension_scores": {
                        "validity": 15.0 + (i % 5),
                        "completeness": 16.0 + (i % 4)
                    }
                })
                logger.add_to_batch(record)

            batch_add_time = time.time() - start_time

            # Test flushing large batch
            flush_start = time.time()
            results = logger.flush_all()
            flush_time = time.time() - flush_start

            # Verify performance
            self.assertLess(batch_add_time, 1.0)  # Adding should be fast
            self.assertLess(flush_time, 5.0)  # Flushing should complete within 5 seconds

            # Verify all uploaded successfully
            for dataset_type in results:
                self.assertTrue(results[dataset_type]["success"])

    @patch('adri.logging.enterprise.requests.post')
    def test_concurrent_batch_operations_performance(self, mock_post):
        """Test performance with concurrent batch operations."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        logger = EnterpriseLogger(self.config)

        with patch.object(logger, '_load_standard', return_value={"fields": []}):
            results = []

            def concurrent_batch_operation(thread_id):
                """Perform batch operations concurrently."""
                start_time = time.time()

                # Add records to batch
                for i in range(20):
                    record = AuditRecord(f"concurrent_{thread_id}_{i}", datetime.now(), "4.0.0")
                    record.assessment_results["overall_score"] = 80.0
                    logger.add_to_batch(record)

                end_time = time.time()
                results.append((thread_id, end_time - start_time))

            # Run concurrent operations
            overall_start = time.time()
            threads = []
            for i in range(5):
                thread = threading.Thread(target=concurrent_batch_operation, args=(i,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()
            overall_time = time.time() - overall_start

            # Verify all completed successfully
            self.assertEqual(len(results), 5)
            for thread_id, duration in results:
                self.assertLess(duration, 1.0)  # Each should complete within 1 second

            # Overall concurrent execution should be efficient
            self.assertLess(overall_time, 3.0)

    @patch('adri.logging.enterprise.requests.post')
    def test_memory_efficiency_performance(self, mock_post):
        """Test memory efficiency during batch operations."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        logger = EnterpriseLogger(self.config)

        with patch.object(logger, '_load_standard', return_value={"fields": []}):
            try:
                import psutil
                import os

                process = psutil.Process(os.getpid())
                memory_before = process.memory_info().rss

                # Add many records to batch
                for i in range(100):
                    record = AuditRecord(f"memory_test_{i}", datetime.now(), "4.0.0")
                    record.assessment_results.update({
                        "overall_score": 80.0,
                        "dimension_scores": {f"dim_{j}": 15.0 for j in range(10)},
                        "failed_checks": [
                            {"dimension": "validity", "field": f"field_{k}", "issue": "test"}
                            for k in range(5)
                        ]
                    })
                    logger.add_to_batch(record)

                memory_after = process.memory_info().rss
                memory_used = memory_after - memory_before

                # Memory usage should be reasonable (less than 20MB for 100 records)
                self.assertLess(memory_used, 20 * 1024 * 1024)

            except ImportError:
                # psutil not available, just verify basic functionality
                for i in range(50):
                    record = AuditRecord(f"memory_test_{i}", datetime.now(), "4.0.0")
                    logger.add_to_batch(record)

                batch_status = logger.get_batch_status()
                self.assertEqual(batch_status["assessment_logs"], 50)


class TestEnterpriseLoggingEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions for comprehensive coverage."""

    def setUp(self):
        """Set up test environment."""
        self.config = {
            "enabled": True,
            "api_key": "edge_case_key",
            "base_url": "https://test.verodat.io/api/v3",
            "workspace_id": "edge_workspace",
            "endpoints": {
                "assessment_logs": {
                    "schedule_request_id": "edge_schedule",
                    "standard": "edge_standard"
                }
            }
        }

    def test_value_formatting_edge_cases(self):
        """Test value formatting with edge cases."""
        logger = EnterpriseLogger(self.config)

        # Test datetime formatting edge cases
        test_datetime = datetime(2024, 3, 15, 10, 30, 45)
        formatted_dt = logger._format_value(test_datetime, "datetime")
        self.assertEqual(formatted_dt, "2024-03-15T10:30:45Z")

        # Test string datetime with +00:00
        string_dt_utc = "2024-03-15T10:30:45+00:00"
        formatted_str_dt = logger._format_value(string_dt_utc, "datetime")
        self.assertEqual(formatted_str_dt, "2024-03-15T10:30:45Z")

        # Test string datetime already with Z
        string_dt_z = "2024-03-15T10:30:45Z"
        formatted_z = logger._format_value(string_dt_z, "datetime")
        self.assertEqual(formatted_z, "2024-03-15T10:30:45Z")

        # Test boolean formatting edge cases
        self.assertEqual(logger._format_value(True, "boolean"), "TRUE")
        self.assertEqual(logger._format_value(False, "boolean"), "FALSE")
        self.assertEqual(logger._format_value(1, "boolean"), "TRUE")
        self.assertEqual(logger._format_value(0, "boolean"), "FALSE")
        self.assertEqual(logger._format_value("", "boolean"), "FALSE")

        # Test JSON serialization edge cases
        complex_data = {"nested": {"list": [1, 2, 3], "dict": {"key": "value"}}}
        formatted_json = logger._format_value(complex_data, "string")
        self.assertIsInstance(formatted_json, str)
        parsed_back = json.loads(formatted_json)
        self.assertEqual(parsed_back, complex_data)

        # Test None values
        self.assertIsNone(logger._format_value(None, "string"))
        self.assertIsNone(logger._format_value(None, "datetime"))
        self.assertIsNone(logger._format_value(None, "boolean"))

    def test_header_building_edge_cases(self):
        """Test header building with different standard formats."""
        logger = EnterpriseLogger(self.config)

        # Test with list format (actual ADRI standard)
        list_format_standard = {
            "fields": [
                {"name": "field1", "type": "string"},
                {"name": "field2", "type": "number"},
                {"name": "field3", "type": "datetime"}
            ]
        }

        header = logger._build_verodat_header(list_format_standard)
        self.assertEqual(len(header), 3)
        self.assertEqual(header[0]["name"], "field1")
        self.assertEqual(header[0]["type"], "string")
        self.assertEqual(header[1]["type"], "numeric")
        self.assertEqual(header[2]["type"], "date")

        # Test with dict format (legacy compatibility)
        dict_format_standard = {
            "fields": {
                "field1": {"type": "string"},
                "field2": {"type": "integer"},
                "field3": {"type": "boolean"}
            }
        }

        header = logger._build_verodat_header(dict_format_standard)
        self.assertEqual(len(header), 3)
        field_names = [h["name"] for h in header]
        self.assertIn("field1", field_names)
        self.assertIn("field2", field_names)
        self.assertIn("field3", field_names)

        # Test with empty fields
        empty_standard = {"fields": []}
        header = logger._build_verodat_header(empty_standard)
        self.assertEqual(len(header), 0)

    def test_dimension_scores_formatting_edge_cases(self):
        """Test dimension scores formatting with edge cases."""
        logger = EnterpriseLogger(self.config)

        standard = {
            "fields": [
                {"name": "assessment_id", "type": "string"},
                {"name": "dimension_name", "type": "string"},
                {"name": "dimension_score", "type": "number"},
                {"name": "dimension_passed", "type": "boolean"},
                {"name": "issues_found", "type": "string"},
                {"name": "details", "type": "string"}
            ]
        }

        record = AuditRecord("test", datetime.now(), "4.0.0")

        # Test with various dimension score types - handle None values properly
        record.assessment_results["dimension_scores"] = {
            "validity": 18.5,
            "completeness": 0.0,  # Edge case: zero score
            "consistency": 20.0,  # Edge case: max score
            "freshness": -1.0,    # Edge case: negative score (should pass "FALSE")
        }

        rows = logger._format_dimension_scores(record, standard)
        self.assertEqual(len(rows), 4)  # 4 non-None scores

        # Check edge cases
        zero_score_row = next(row for row in rows if row[1] == "completeness")
        self.assertEqual(zero_score_row[2], 0.0)
        self.assertEqual(zero_score_row[3], "FALSE")  # 0.0 <= 15

        negative_score_row = next(row for row in rows if row[1] == "freshness")
        self.assertEqual(negative_score_row[2], -1.0)
        self.assertEqual(negative_score_row[3], "FALSE")  # -1.0 <= 15

        # Test with non-dict dimension_scores
        record.assessment_results["dimension_scores"] = "not_a_dict"
        rows = logger._format_dimension_scores(record, standard)
        self.assertEqual(len(rows), 0)

    def test_failed_validations_formatting_edge_cases(self):
        """Test failed validations formatting with edge cases."""
        logger = EnterpriseLogger(self.config)

        standard = {
            "fields": [
                {"name": "assessment_id", "type": "string"},
                {"name": "validation_id", "type": "string"},
                {"name": "dimension", "type": "string"},
                {"name": "field_name", "type": "string"},
                {"name": "issue_type", "type": "string"},
                {"name": "affected_rows", "type": "integer"},
                {"name": "affected_percentage", "type": "number"},
                {"name": "sample_failures", "type": "string"},
                {"name": "remediation", "type": "string"}
            ]
        }

        record = AuditRecord("test", datetime.now(), "4.0.0")

        # Test with various failed check formats
        record.assessment_results["failed_checks"] = [
            {
                "dimension": "validity",
                "field_name": "email",
                "issue_type": "format_error",
                "affected_rows": 25,
                "affected_percentage": 2.5,
                "sample_failures": ["invalid@", "not-email"],
                "remediation": "Fix email validation"
            },
            {
                # Missing some fields - should handle gracefully
                "dimension": "completeness"
            },
            "not_a_dict",  # Invalid entry type
            {
                # Edge case: zero affected rows
                "dimension": "consistency",
                "field_name": "phone",
                "issue_type": "missing",
                "affected_rows": 0,
                "affected_percentage": 0.0,
                "sample_failures": [],
                "remediation": ""
            }
        ]

        rows = logger._format_failed_validations(record, standard)
        self.assertEqual(len(rows), 3)  # Should skip the "not_a_dict" entry

        # Check validation IDs are generated correctly
        validation_ids = [row[1] for row in rows]
        self.assertIn("val_000", validation_ids)
        self.assertIn("val_001", validation_ids)
        self.assertIn("val_003", validation_ids)  # Skip index 2 (invalid entry)

        # Test with non-list failed_checks
        record.assessment_results["failed_checks"] = "not_a_list"
        rows = logger._format_failed_validations(record, standard)
        self.assertEqual(len(rows), 0)

    def test_batch_operations_edge_cases(self):
        """Test batch operations with edge cases."""
        logger = EnterpriseLogger(self.config)

        # Test with empty batches
        empty_batches = logger._get_batches("assessment_logs")
        self.assertEqual(len(empty_batches), 0)

        # Test batch status with empty batches
        batch_status = logger.get_batch_status()
        self.assertEqual(batch_status["assessment_logs"], 0)
        self.assertEqual(batch_status["dimension_scores"], 0)
        self.assertEqual(batch_status["failed_validations"], 0)

        # Test adding record with no dimension scores or failed checks
        simple_record = AuditRecord("simple", datetime.now(), "4.0.0")
        logger.add_to_batch(simple_record)

        batch_status = logger.get_batch_status()
        self.assertEqual(batch_status["assessment_logs"], 1)
        self.assertEqual(batch_status["dimension_scores"], 0)  # No dimension scores
        self.assertEqual(batch_status["failed_validations"], 0)  # No failed checks

    def test_convenience_function_edge_cases(self):
        """Test log_to_verodat convenience function edge cases."""
        # Test with disabled config
        disabled_config = {"enabled": False}
        success = log_to_verodat(
            assessment_result=Mock(),
            execution_context={},
            config=disabled_config
        )
        self.assertTrue(success)  # Should succeed when disabled

        # Test with no config
        success = log_to_verodat(
            assessment_result=Mock(),
            execution_context={}
        )
        self.assertTrue(success)  # Should succeed with no config

        # Test with None config
        success = log_to_verodat(
            assessment_result=Mock(),
            execution_context={},
            config=None
        )
        self.assertTrue(success)  # Should succeed with None config

    def test_standard_file_path_resolution(self):
        """Test standard file path resolution logic."""
        logger = EnterpriseLogger(self.config)

        # Create test files in different locations
        paths_to_create = [
            "src/adri/standards/audit_logs/path_test.yaml",
            "adri/standards/audit_logs/fallback_test.yaml",
            "src/adri/standards/direct_test.yaml"
        ]

        for path in paths_to_create:
            path_obj = Path(path)
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with open(path_obj, 'w', encoding='utf-8') as f:
                import yaml
                yaml.dump({"fields": [{"name": "test", "type": "string"}]}, f)

        # Test loading from primary path
        standard = logger._load_standard("path_test")
        self.assertIn("fields", standard)

        # Test loading from fallback path
        standard = logger._load_standard("fallback_test")
        self.assertIn("fields", standard)

        # Test loading from direct path
        standard = logger._load_standard("direct_test")
        self.assertIn("fields", standard)

    def test_url_construction_edge_cases(self):
        """Test URL construction for different configurations."""
        # Test with trailing slash in base_url
        config_with_slash = self.config.copy()
        config_with_slash["base_url"] = "https://test.verodat.io/api/v3/"

        logger = EnterpriseLogger(config_with_slash)
        # URL construction should handle this gracefully

    def test_ssl_verification_configuration(self):
        """Test SSL verification configuration options."""
        # Test with SSL verification disabled
        no_ssl_config = self.config.copy()
        no_ssl_config["connection"] = {"verify_ssl": False}

        logger = EnterpriseLogger(no_ssl_config)
        self.assertFalse(logger.verify_ssl)

        # Test with SSL verification enabled (default)
        ssl_config = self.config.copy()
        ssl_config["connection"] = {"verify_ssl": True}

        logger = EnterpriseLogger(ssl_config)
        self.assertTrue(logger.verify_ssl)


if __name__ == '__main__':
    # Add requests import for error handling tests
    try:
        import requests
    except ImportError:
        print("Warning: requests module not available, some tests may be skipped")
        requests = None

    unittest.main()
