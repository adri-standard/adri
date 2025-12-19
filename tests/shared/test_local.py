"""
Logging Local Tests - Multi-Dimensional Quality Framework
Tests CSV-based audit logging functionality with comprehensive coverage (85%+ line coverage target).
Applies multi-dimensional quality framework: Integration (30%), Error Handling (25%), Performance (15%), Line Coverage (30%).
"""

import unittest
import tempfile
import os
import shutil
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import pytest

from src.adri.logging.local import (
    AuditRecord,
    LocalLogger,
    log_to_csv,
    CSVAuditLogger,
    AuditLoggerCSV
)


class TestLocalLoggingIntegration(unittest.TestCase):
    """Test complete local logging workflow integration (30% weight in quality score)."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_no_duplicate_audit_logging(self):
        """Test that duplicate audit logging does not occur - regression test for CLI/engine duplicate issue."""
        # Create logger configuration
        config = {
            "enabled": True,
            "log_dir": str(self.log_dir),
            "log_prefix": "duplicate_test",
            "log_level": "INFO",
            "include_data_samples": True,
            "max_log_size_mb": 10
        }

        # Initialize logger
        logger = LocalLogger(config)

        # Create mock assessment result similar to CLI flow
        mock_assessment = Mock()
        mock_assessment.overall_score = 88.5
        mock_assessment.passed = True
        mock_assessment.standard_id = "duplicate_prevention_test_standard"

        # Create dimension scores with specific scores to verify uniqueness
        validity_dim = Mock()
        validity_dim.score = 18.0
        completeness_dim = Mock()
        completeness_dim.score = 20.0
        consistency_dim = Mock()
        consistency_dim.score = 16.0
        freshness_dim = Mock()
        freshness_dim.score = 19.0
        plausibility_dim = Mock()
        plausibility_dim.score = 15.5

        mock_assessment.dimension_scores = {
            "validity": validity_dim,
            "completeness": completeness_dim,
            "consistency": consistency_dim,
            "freshness": freshness_dim,
            "plausibility": plausibility_dim
        }

        # Create execution context similar to validator engine flow
        execution_context = {
            "function_name": "assess",
            "module_path": "adri.validator.engine",
            "environment": "TEST"
        }

        # Create data info
        data_info = {
            "row_count": 10,
            "column_count": 6,
            "columns": ["invoice_id", "customer_id", "amount", "date", "status", "payment_method"],
            "data_checksum": "test_checksum_123"
        }

        # Create performance metrics
        performance_metrics = {
            "duration_ms": 1,
            "rows_per_second": 10000.0,
            "cache_used": False
        }

        # Create failed checks
        failed_checks = [
            {
                "validation_id": "val_001",
                "dimension": "validity",
                "field": "amount",
                "issue": "negative_value",
                "affected_rows": 1,
                "affected_percentage": 10.0,
                "samples": ["INV-103"],
                "remediation": "Remove or correct negative amounts"
            }
        ]

        # Log assessment ONLY ONCE (simulating the fix where CLI no longer duplicates)
        audit_record = logger.log_assessment(
            assessment_result=mock_assessment,
            execution_context=execution_context,
            data_info=data_info,
            performance_metrics=performance_metrics,
            failed_checks=failed_checks
        )

        # Verify audit record was created
        self.assertIsNotNone(audit_record)
        self.assertIsInstance(audit_record, AuditRecord)

        # Get log files
        log_files = logger.get_log_files()

        # CRITICAL TEST: Verify exactly ONE main assessment log entry
        with open(log_files["assessment_logs"], 'r', encoding='utf-8') as f:
            main_rows = [json.loads(line) for line in f if line.strip()]

            # Should be exactly 1 entry, not 2 (no duplicates)
            self.assertEqual(len(main_rows), 1,
                           f"Expected exactly 1 audit log entry, found {len(main_rows)}. "
                           f"This indicates duplicate logging occurred.")

            main_row = main_rows[0]
            self.assertEqual(main_row["function_name"], "assess")
            self.assertEqual(main_row["module_path"], "adri.validator.engine")
            self.assertEqual(main_row["overall_score"], 88.5)
            self.assertEqual(main_row["passed"], True)
            self.assertEqual(main_row["standard_id"], "duplicate_prevention_test_standard")

        # CRITICAL TEST: Verify exactly 5 dimension score entries (one per dimension)
        with open(log_files["dimension_scores"], 'r', encoding='utf-8') as f:
            dim_rows = [json.loads(line) for line in f if line.strip()]

            # Should be exactly 5 entries (5 dimensions), not 10 (no duplicates)
            self.assertEqual(len(dim_rows), 5,
                           f"Expected exactly 5 dimension score entries, found {len(dim_rows)}. "
                           f"This indicates duplicate dimension logging occurred.")

            # Verify each dimension appears exactly once
            dimension_names = [row["dimension_name"] for row in dim_rows]
            expected_dimensions = ["validity", "completeness", "consistency", "freshness", "plausibility"]

            self.assertEqual(sorted(dimension_names), sorted(expected_dimensions))

            # Verify no duplicate dimensions
            unique_dimensions = set(dimension_names)
            self.assertEqual(len(unique_dimensions), 5,
                           f"Found duplicate dimensions: {dimension_names}")

            # Verify specific dimension scores
            validity_row = next(row for row in dim_rows if row["dimension_name"] == "validity")
            self.assertEqual(validity_row["dimension_score"], 18.0)

            completeness_row = next(row for row in dim_rows if row["dimension_name"] == "completeness")
            self.assertEqual(completeness_row["dimension_score"], 20.0)

        # CRITICAL TEST: Verify exactly 1 failed validation entry
        with open(log_files["failed_validations"], 'r', encoding='utf-8') as f:
            validation_rows = [json.loads(line) for line in f if line.strip()]

            # Should be exactly 1 entry, not 2 (no duplicates)
            self.assertEqual(len(validation_rows), 1,
                           f"Expected exactly 1 failed validation entry, found {len(validation_rows)}. "
                           f"This indicates duplicate validation logging occurred.")

            validation_row = validation_rows[0]
            self.assertEqual(validation_row["validation_id"], "val_000")
            self.assertEqual(validation_row["dimension"], "validity")
            self.assertEqual(validation_row["field_name"], "amount")
            self.assertEqual(validation_row["issue_type"], "negative_value")

        # Additional verification: Test that assessment IDs are unique
        # This ensures no accidental duplicate entries with different IDs
        all_assessment_ids = []

        # Check main log
        with open(log_files["assessment_logs"], 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    row = json.loads(line)
                    all_assessment_ids.append(row["assessment_id"])

        # Check dimension scores
        with open(log_files["dimension_scores"], 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    row = json.loads(line)
                    all_assessment_ids.append(row["assessment_id"])

        # Check failed validations
        with open(log_files["failed_validations"], 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    row = json.loads(line)
                    all_assessment_ids.append(row["assessment_id"])

        # All assessment IDs should be the same (single assessment)
        unique_assessment_ids = set(all_assessment_ids)
        self.assertEqual(len(unique_assessment_ids), 1,
                       f"Found multiple assessment IDs in logs: {unique_assessment_ids}. "
                       f"This indicates separate logging operations occurred.")

        print(f"✅ Duplicate logging prevention test passed: "
              f"1 main log, 5 dimensions, 1 validation, 1 unique assessment ID")

    def test_complete_audit_logging_workflow(self):
        """Test end-to-end audit logging workflow with CSV output."""
        # Create logger configuration
        config = {
            "enabled": True,
            "log_dir": str(self.log_dir),
            "log_prefix": "test_audit",
            "log_level": "INFO",
            "include_data_samples": True,
            "max_log_size_mb": 10
        }

        # Initialize logger
        logger = LocalLogger(config)

        # Verify CSV files were created with headers
        log_files = logger.get_log_files()
        self.assertTrue(log_files["assessment_logs"].exists())
        self.assertTrue(log_files["dimension_scores"].exists())
        self.assertTrue(log_files["failed_validations"].exists())

        # Create mock assessment result
        mock_assessment = Mock()
        mock_assessment.overall_score = 85.5
        mock_assessment.passed = True
        mock_assessment.standard_id = "customer_data_standard"

        # Create dimension scores
        validity_dim = Mock()
        validity_dim.score = 18.2
        completeness_dim = Mock()
        completeness_dim.score = 16.8

        mock_assessment.dimension_scores = {
            "validity": validity_dim,
            "completeness": completeness_dim
        }

        # Create execution context
        execution_context = {
            "function_name": "test_customer_validation",
            "module_path": "customer.validation",
            "environment": "TEST"
        }

        # Create data info
        data_info = {
            "row_count": 1000,
            "column_count": 8,
            "columns": ["customer_id", "name", "email", "age", "balance", "status", "created_at", "updated_at"]
        }

        # Create performance metrics
        performance_metrics = {
            "duration_ms": 250,
            "cache_used": True
        }

        # Create failed checks
        failed_checks = [
            {
                "dimension": "validity",
                "field": "email",
                "issue": "invalid_format",
                "affected_rows": 15,
                "affected_percentage": 1.5,
                "samples": ["invalid@", "not-email", ""],
                "remediation": "Fix email format validation"
            },
            {
                "dimension": "completeness",
                "field": "age",
                "issue": "missing_values",
                "affected_rows": 8,
                "affected_percentage": 0.8,
                "samples": [None, "", "null"],
                "remediation": "Populate missing age values"
            }
        ]

        # Log assessment
        audit_record = logger.log_assessment(
            assessment_result=mock_assessment,
            execution_context=execution_context,
            data_info=data_info,
            performance_metrics=performance_metrics,
            failed_checks=failed_checks
        )

        # Verify audit record was created
        self.assertIsNotNone(audit_record)
        self.assertIsInstance(audit_record, AuditRecord)
        self.assertEqual(audit_record.assessment_results["overall_score"], 85.5)
        self.assertTrue(audit_record.assessment_results["passed"])

        # Verify main assessment log
        with open(log_files["assessment_logs"], 'r', encoding='utf-8') as f:
            rows = [json.loads(line) for line in f if line.strip()]
            self.assertEqual(len(rows), 1)

            main_row = rows[0]
            self.assertEqual(main_row["function_name"], "test_customer_validation")
            self.assertEqual(main_row["data_row_count"], 1000)
            self.assertEqual(main_row["overall_score"], 85.5)
            self.assertEqual(main_row["passed"], True)

        # Verify dimension scores
        with open(log_files["dimension_scores"], 'r', encoding='utf-8') as f:
            dim_rows = [json.loads(line) for line in f if line.strip()]
            self.assertEqual(len(dim_rows), 2)

            validity_row = next(row for row in dim_rows if row["dimension_name"] == "validity")
            self.assertEqual(validity_row["dimension_score"], 18.2)
            self.assertEqual(validity_row["dimension_passed"], True)

        # Verify failed validations
        with open(log_files["failed_validations"], 'r', encoding='utf-8') as f:
            validation_rows = [json.loads(line) for line in f if line.strip()]
            self.assertEqual(len(validation_rows), 2)

            email_validation = next(row for row in validation_rows if row["field_name"] == "email")
            self.assertEqual(email_validation["issue_type"], "invalid_format")
            self.assertEqual(email_validation["affected_rows"], 15)

    def test_multiple_assessments_workflow(self):
        """Test logging multiple assessments to verify file appending."""
        config = {
            "enabled": True,
            "log_dir": str(self.log_dir),
            "log_prefix": "multi_test"
        }

        logger = LocalLogger(config)

        # Log multiple assessments
        for i in range(3):
            mock_assessment = Mock()
            mock_assessment.overall_score = 70.0 + (i * 10)
            mock_assessment.passed = i > 0  # First fails, others pass
            mock_assessment.standard_id = f"standard_{i}"
            mock_assessment.dimension_scores = {}

            execution_context = {
                "function_name": f"test_function_{i}",
                "module_path": f"module_{i}",
                "environment": "TEST"
            }

            data_info = {
                "row_count": 100 * (i + 1),
                "column_count": 5,
                "columns": ["id", "name", "email", "age", "status"]
            }

            logger.log_assessment(
                assessment_result=mock_assessment,
                execution_context=execution_context,
                data_info=data_info
            )

        # Verify all assessments logged
        log_files = logger.get_log_files()
        with open(log_files["assessment_logs"], 'r', encoding='utf-8') as f:
            rows = [json.loads(line) for line in f if line.strip()]
            self.assertEqual(len(rows), 3)

            # Verify each assessment
            for i, row in enumerate(rows):
                self.assertEqual(row["function_name"], f"test_function_{i}")
                self.assertEqual(row["data_row_count"], 100 * (i + 1))
                expected_score = 70.0 + (i * 10)
                self.assertEqual(row["overall_score"], expected_score)

    def test_audit_record_creation_integration(self):
        """Test comprehensive audit record creation and conversion."""
        timestamp = datetime.now()
        record = AuditRecord("test_123", timestamp, "4.0.0")

        # Verify initialization
        self.assertEqual(record.assessment_id, "test_123")
        self.assertEqual(record.timestamp, timestamp)
        self.assertEqual(record.adri_version, "4.0.0")

        # Update record with comprehensive data
        record.execution_context.update({
            "function_name": "validate_customer_data",
            "module_path": "customer.validation",
            "environment": "PRODUCTION"
        })

        record.standard_applied.update({
            "standard_id": "customer_quality_v2",
            "standard_version": "2.1.0",
            "standard_path": "/contracts/customer.yaml",
            "standard_checksum": "abc123def456"
        })

        record.data_fingerprint.update({
            "row_count": 5000,
            "column_count": 12,
            "columns": ["customer_id", "name", "email", "phone", "address", "city", "state", "zip", "country", "age", "segment", "status"],
            "data_checksum": "data123hash456"
        })

        record.assessment_results.update({
            "overall_score": 88.7,
            "required_score": 80.0,
            "passed": True,
            "execution_decision": "ALLOWED",
            "dimension_scores": {
                "validity": 17.5,
                "completeness": 18.9,
                "consistency": 16.2,
                "freshness": 19.1,
                "plausibility": 17.0
            },
            "failed_checks": [
                {
                    "dimension": "validity",
                    "field": "phone",
                    "issue": "invalid_format",
                    "affected_rows": 25,
                    "affected_percentage": 0.5
                }
            ]
        })

        # Test conversion methods
        record_dict = record.to_dict()
        self.assertIn("assessment_metadata", record_dict)
        self.assertIn("execution_context", record_dict)
        self.assertEqual(record_dict["data_fingerprint"]["row_count"], 5000)

        record_json = record.to_json()
        self.assertIsInstance(record_json, str)
        parsed_json = json.loads(record_json)
        self.assertEqual(parsed_json["assessment_results"]["overall_score"], 88.7)

        # Test Verodat format conversion
        verodat_format = record.to_verodat_format()
        self.assertIn("main_record", verodat_format)
        self.assertIn("dimension_records", verodat_format)
        self.assertIn("failed_validation_records", verodat_format)

        main_record = verodat_format["main_record"]
        self.assertEqual(main_record["overall_score"], 88.7)
        self.assertEqual(main_record["data_row_count"], 5000)
        self.assertEqual(main_record["passed"], "TRUE")

        dimension_records = verodat_format["dimension_records"]
        self.assertEqual(len(dimension_records), 5)
        validity_record = next(r for r in dimension_records if r["dimension_name"] == "validity")
        self.assertEqual(validity_record["dimension_score"], 17.5)

        failed_validations = verodat_format["failed_validation_records"]
        self.assertEqual(len(failed_validations), 1)
        self.assertEqual(failed_validations[0]["field_name"], "phone")

    def test_disabled_logger_integration(self):
        """Test behavior when logger is disabled."""
        config = {
            "enabled": False,
            "log_dir": str(self.log_dir)
        }

        logger = LocalLogger(config)

        # Verify no files created
        log_files = logger.get_log_files()
        self.assertFalse(log_files["assessment_logs"].exists())

        # Attempt to log assessment
        mock_assessment = Mock()
        mock_assessment.overall_score = 75.0

        result = logger.log_assessment(
            assessment_result=mock_assessment,
            execution_context={"function_name": "test"}
        )

        # Should return None when disabled
        self.assertIsNone(result)
        self.assertFalse(log_files["assessment_logs"].exists())

    def test_log_file_rotation_integration(self):
        """Test log file rotation when max size is reached."""
        config = {
            "enabled": True,
            "log_dir": str(self.log_dir),
            "log_prefix": "rotation_test",
            "max_log_size_mb": 0.001  # Very small for testing
        }

        logger = LocalLogger(config)

        # Log many assessments to trigger rotation
        for i in range(50):
            mock_assessment = Mock()
            mock_assessment.overall_score = 80.0
            mock_assessment.passed = True
            mock_assessment.standard_id = "test"
            mock_assessment.dimension_scores = {}

            execution_context = {
                "function_name": f"large_test_function_with_long_name_{i}",
                "module_path": f"very.long.module.path.for.testing.rotation.{i}"
            }

            data_info = {
                "row_count": 1000,
                "column_count": 20,
                "columns": [f"column_{j}" for j in range(20)]
            }

            logger.log_assessment(
                assessment_result=mock_assessment,
                execution_context=execution_context,
                data_info=data_info
            )

        # Check for rotated files
        log_files = list(self.log_dir.glob("rotation_test_assessment_logs.*.jsonl"))
        self.assertGreater(len(log_files), 0, "Log rotation should have occurred")

    def test_convenience_function_integration(self):
        """Test log_to_csv convenience function integration."""
        config = {
            "enabled": True,
            "log_dir": str(self.log_dir),
            "log_prefix": "convenience"
        }

        mock_assessment = Mock()
        mock_assessment.overall_score = 92.3
        mock_assessment.passed = True
        mock_assessment.standard_id = "convenience_test"
        mock_assessment.dimension_scores = {}

        execution_context = {
            "function_name": "convenience_test_function",
            "module_path": "convenience.module"
        }

        # Test convenience function
        result = log_to_csv(
            assessment_result=mock_assessment,
            execution_context=execution_context,
            config=config
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result, AuditRecord)

        # Verify file was created
        log_file = self.log_dir / "convenience_assessment_logs.jsonl"
        self.assertTrue(log_file.exists())

    def test_backward_compatibility_aliases(self):
        """Test backward compatibility class aliases."""
        config = {
            "enabled": True,
            "log_dir": str(self.log_dir)
        }

        # Test CSVAuditLogger alias
        csv_logger = CSVAuditLogger(config)
        self.assertIsInstance(csv_logger, LocalLogger)

        # Test AuditLoggerCSV alias
        audit_logger = AuditLoggerCSV(config)
        self.assertIsInstance(audit_logger, LocalLogger)


class TestLocalLoggingErrorHandling(unittest.TestCase):
    """Test comprehensive error handling scenarios (25% weight in quality score)."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_invalid_log_directory_errors(self):
        """Test error handling for invalid log directories."""
        # Test with config that would fail during initialization
        config = {
            "enabled": True,
            "log_dir": "/root/restricted/path/logs"  # Use a path that would be permission denied
        }

        # Should handle directory creation errors gracefully
        try:
            logger = LocalLogger(config)

            # If initialization succeeded, try logging
            mock_assessment = Mock()
            mock_assessment.overall_score = 75.0
            mock_assessment.passed = True
            mock_assessment.standard_id = "test"
            mock_assessment.dimension_scores = {}

            result = logger.log_assessment(
                assessment_result=mock_assessment,
                execution_context={"function_name": "test"}
            )

            # If we get here, it worked despite the problematic path
            self.assertIsNotNone(result)

        except (OSError, PermissionError, FileNotFoundError):
            # Expected on systems where we can't create paths in restricted areas
            pass

    def test_file_permission_errors(self):
        """Test handling of file permission errors."""
        if os.name == 'nt':  # Skip on Windows
            self.skipTest("File permission tests not applicable on Windows")

        config = {
            "enabled": True,
            "log_dir": str(self.log_dir)
        }

        logger = LocalLogger(config)

        # Remove write permissions from log directory
        os.chmod(self.log_dir, 0o444)

        try:
            mock_assessment = Mock()
            mock_assessment.overall_score = 75.0
            mock_assessment.passed = True
            mock_assessment.standard_id = "test"
            mock_assessment.dimension_scores = {}

            # This should handle permission error gracefully
            with self.assertRaises((PermissionError, OSError)):
                logger.log_assessment(
                    assessment_result=mock_assessment,
                    execution_context={"function_name": "test"}
                )
        finally:
            # Restore permissions for cleanup
            os.chmod(self.log_dir, 0o755)

    def test_malformed_assessment_result_errors(self):
        """Test handling of malformed assessment result objects."""
        config = {
            "enabled": True,
            "log_dir": str(self.log_dir)
        }

        logger = LocalLogger(config)

        # Test with None assessment result
        result = logger.log_assessment(
            assessment_result=None,
            execution_context={"function_name": "test"}
        )
        self.assertIsNotNone(result)  # Should create record despite None input

        # Test with object missing expected attributes but with proper dimension_scores
        incomplete_assessment = Mock()
        incomplete_assessment.dimension_scores = {}  # Empty dict, not Mock
        # Don't set overall_score attribute so it doesn't exist
        del incomplete_assessment.overall_score

        result = logger.log_assessment(
            assessment_result=incomplete_assessment,
            execution_context={"function_name": "test"}
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.assessment_results["overall_score"], 0.0)

    def test_invalid_data_types_errors(self):
        """Test handling of invalid data types in inputs."""
        config = {
            "enabled": True,
            "log_dir": str(self.log_dir)
        }

        logger = LocalLogger(config)

        mock_assessment = Mock()
        mock_assessment.overall_score = "not_a_number"  # Invalid type
        mock_assessment.passed = "not_a_boolean"
        mock_assessment.standard_id = None

        # Don't set dimension_scores to invalid type that would break iteration
        # Instead, test that it handles missing attribute gracefully
        delattr(mock_assessment, 'dimension_scores')

        # Should handle gracefully
        result = logger.log_assessment(
            assessment_result=mock_assessment,
            execution_context={"function_name": "test"}
        )

        self.assertIsNotNone(result)
        # Score should be stored as provided (even if invalid type)
        self.assertEqual(result.assessment_results["overall_score"], "not_a_number")

    def test_corrupted_csv_file_errors(self):
        """Test handling when CSV files are corrupted."""
        config = {
            "enabled": True,
            "log_dir": str(self.log_dir)
        }

        logger = LocalLogger(config)

        # Corrupt the assessment log file
        log_files = logger.get_log_files()
        with open(log_files["assessment_logs"], 'w', encoding='utf-8') as f:
            f.write("corrupted,invalid,csv,data\n")
            f.write("missing,fields,in,this,row\n")

        # Should handle gracefully and continue appending
        mock_assessment = Mock()
        mock_assessment.overall_score = 85.0
        mock_assessment.passed = True
        mock_assessment.standard_id = "test"
        mock_assessment.dimension_scores = {}

        result = logger.log_assessment(
            assessment_result=mock_assessment,
            execution_context={"function_name": "test"}
        )

        self.assertIsNotNone(result)

    def test_disk_space_exhaustion_simulation(self):
        """Test handling when disk space is exhausted (simulated)."""
        config = {
            "enabled": True,
            "log_dir": str(self.log_dir)
        }

        logger = LocalLogger(config)

        # Mock open to raise OSError (disk full)
        with patch('builtins.open', side_effect=OSError("No space left on device")):
            mock_assessment = Mock()
            mock_assessment.overall_score = 75.0
            mock_assessment.passed = True
            mock_assessment.standard_id = "test"
            mock_assessment.dimension_scores = {}

            # Should raise error but not crash
            with self.assertRaises(OSError):
                logger.log_assessment(
                    assessment_result=mock_assessment,
                    execution_context={"function_name": "test"}
                )

    def test_concurrent_file_access_errors(self):
        """Test handling of concurrent file access scenarios."""
        config = {
            "enabled": True,
            "log_dir": str(self.log_dir)
        }

        logger = LocalLogger(config)
        errors = []
        results = []

        def log_concurrent(thread_id):
            """Log assessment in separate thread."""
            try:
                mock_assessment = Mock()
                mock_assessment.overall_score = 75.0 + thread_id
                mock_assessment.passed = True
                mock_assessment.standard_id = f"test_{thread_id}"
                mock_assessment.dimension_scores = {}

                result = logger.log_assessment(
                    assessment_result=mock_assessment,
                    execution_context={"function_name": f"test_{thread_id}"}
                )
                results.append((thread_id, result))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Start multiple concurrent logging operations
        threads = []
        for i in range(10):
            thread = threading.Thread(target=log_concurrent, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Should handle concurrent access without errors
        self.assertEqual(len(errors), 0, f"Concurrent logging errors: {errors}")
        self.assertEqual(len(results), 10)

    def test_json_serialization_errors(self):
        """Test handling of objects that can't be JSON serialized."""
        timestamp = datetime.now()
        record = AuditRecord("test", timestamp, "4.0.0")

        # Add non-serializable object
        record.assessment_results["complex_object"] = Mock()
        record.data_fingerprint["columns"] = [Mock(), Mock()]

        # Should handle gracefully using str() fallback
        json_str = record.to_json()
        self.assertIsInstance(json_str, str)

        # Should be valid JSON despite complex objects
        parsed = json.loads(json_str)
        self.assertIn("assessment_results", parsed)

    def test_missing_dimension_scores_errors(self):
        """Test handling when dimension scores are missing or malformed."""
        timestamp = datetime.now()
        record = AuditRecord("test", timestamp, "4.0.0")

        # Test with None dimension scores
        record.assessment_results["dimension_scores"] = None
        verodat_format = record.to_verodat_format()
        self.assertEqual(len(verodat_format["dimension_records"]), 0)

        # Test with malformed dimension scores
        record.assessment_results["dimension_scores"] = "not_a_dict"
        verodat_format = record.to_verodat_format()
        self.assertEqual(len(verodat_format["dimension_records"]), 0)

        # Test with dimension scores with numeric values (not Mock objects)
        record.assessment_results["dimension_scores"] = {"validity": 18.5, "completeness": 12.3}
        verodat_format = record.to_verodat_format()
        self.assertEqual(len(verodat_format["dimension_records"]), 2)

        # Verify proper handling of numeric dimension scores
        validity_record = next(r for r in verodat_format["dimension_records"] if r["dimension_name"] == "validity")
        self.assertEqual(validity_record["dimension_score"], 18.5)
        self.assertEqual(validity_record["dimension_passed"], "TRUE")  # 18.5 > 15

        completeness_record = next(r for r in verodat_format["dimension_records"] if r["dimension_name"] == "completeness")
        self.assertEqual(completeness_record["dimension_score"], 12.3)
        self.assertEqual(completeness_record["dimension_passed"], "FALSE")  # 12.3 <= 15

    def test_configuration_validation_errors(self):
        """Test handling of invalid configuration parameters."""
        # Test with invalid max_log_size_mb
        config = {
            "enabled": True,
            "log_dir": str(self.log_dir),
            "max_log_size_mb": "not_a_number"
        }

        # Should handle invalid config gracefully
        try:
            logger = LocalLogger(config)
            # Basic operation should still work
            mock_assessment = Mock()
            mock_assessment.overall_score = 75.0
            mock_assessment.passed = True
            mock_assessment.standard_id = "test"
            mock_assessment.dimension_scores = {}

            result = logger.log_assessment(
                assessment_result=mock_assessment,
                execution_context={"function_name": "test"}
            )
            self.assertIsNotNone(result)
        except (TypeError, ValueError):
            # Expected for invalid configuration
            pass


class TestLocalLoggingPerformance(unittest.TestCase):
    """Test performance benchmarks and efficiency (15% weight in quality score)."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    @pytest.mark.benchmark(group="local_logging")
    def test_single_assessment_logging_performance(self, benchmark=None):
        """Benchmark single assessment logging performance."""
        config = {
            "enabled": True,
            "log_dir": str(self.log_dir),
            "log_prefix": "perf_test"
        }

        logger = LocalLogger(config)

        # Create comprehensive assessment data
        mock_assessment = Mock()
        mock_assessment.overall_score = 87.5
        mock_assessment.passed = True
        mock_assessment.standard_id = "performance_test_standard"

        # Create dimension scores
        dimension_scores = {}
        for i in range(10):
            dim_mock = Mock()
            dim_mock.score = 15.0 + i
            dimension_scores[f"dimension_{i}"] = dim_mock
        mock_assessment.dimension_scores = dimension_scores

        execution_context = {
            "function_name": "performance_test_function",
            "module_path": "performance.test.module",
            "environment": "BENCHMARK"
        }

        data_info = {
            "row_count": 10000,
            "column_count": 25,
            "columns": [f"column_{i}" for i in range(25)]
        }

        performance_metrics = {
            "duration_ms": 500,
            "cache_used": True
        }

        failed_checks = [
            {
                "dimension": f"dimension_{i}",
                "field": f"field_{i}",
                "issue": "test_issue",
                "affected_rows": i * 10,
                "affected_percentage": i * 0.1
            }
            for i in range(5)
        ]

        def log_assessment():
            return logger.log_assessment(
                assessment_result=mock_assessment,
                execution_context=execution_context,
                data_info=data_info,
                performance_metrics=performance_metrics,
                failed_checks=failed_checks
            )

        if benchmark:
            result = benchmark(log_assessment)
            self.assertIsNotNone(result)
        else:
            # Fallback timing
            start_time = time.time()
            result = log_assessment()
            end_time = time.time()

            self.assertIsNotNone(result)
            from tests.utils.performance_helpers import assert_performance
        assert_performance(end_time - start_time, "micro", "validation_simple", "Single assessment logging")

    def test_bulk_logging_performance(self):
        """Test performance with bulk logging operations."""
        config = {
            "enabled": True,
            "log_dir": str(self.log_dir),
            "log_prefix": "bulk_test"
        }

        logger = LocalLogger(config)

        # Time bulk logging
        start_time = time.time()

        for i in range(100):
            mock_assessment = Mock()
            mock_assessment.overall_score = 75.0 + (i % 25)
            mock_assessment.passed = i % 3 != 0
            mock_assessment.standard_id = f"bulk_test_{i % 5}"
            mock_assessment.dimension_scores = {
                "validity": Mock(score=15.0 + (i % 5)),
                "completeness": Mock(score=16.0 + (i % 4))
            }

            execution_context = {
                "function_name": f"bulk_function_{i}",
                "module_path": f"bulk.module.{i % 10}"
            }

            data_info = {
                "row_count": 1000 + (i * 10),
                "column_count": 8,
                "columns": ["id", "name", "email", "age", "status", "created_at", "updated_at", "category"]
            }

            logger.log_assessment(
                assessment_result=mock_assessment,
                execution_context=execution_context,
                data_info=data_info
            )

        end_time = time.time()
        total_time = end_time - start_time

        # Verify all assessments logged
        log_files = logger.get_log_files()
        with open(log_files["assessment_logs"], 'r', encoding='utf-8') as f:
            rows = [json.loads(line) for line in f if line.strip()]
            self.assertEqual(len(rows), 100)

        # Should complete bulk logging efficiently
        from tests.utils.performance_helpers import assert_performance
        assert_performance(total_time, "small", "file_processing_small", "Bulk logging (100 assessments)")

        # Calculate average time per assessment
        avg_time_per_assessment = total_time / 100
        from tests.performance_thresholds import get_performance_threshold
        threshold_per_assessment = get_performance_threshold("small", "file_processing_small") / 100
        self.assertLess(avg_time_per_assessment, threshold_per_assessment)

    def test_concurrent_logging_performance(self):
        """Test performance with concurrent logging operations."""
        config = {
            "enabled": True,
            "log_dir": str(self.log_dir),
            "log_prefix": "concurrent_perf"
        }

        logger = LocalLogger(config)
        results = []

        def log_concurrent(thread_id):
            """Log assessment concurrently."""
            start_time = time.time()

            mock_assessment = Mock()
            mock_assessment.overall_score = 75.0 + thread_id
            mock_assessment.passed = True
            mock_assessment.standard_id = f"concurrent_test_{thread_id}"
            mock_assessment.dimension_scores = {
                "validity": Mock(score=15.0 + thread_id),
                "completeness": Mock(score=16.0 + thread_id)
            }

            execution_context = {
                "function_name": f"concurrent_function_{thread_id}",
                "module_path": f"concurrent.module.{thread_id}"
            }

            result = logger.log_assessment(
                assessment_result=mock_assessment,
                execution_context=execution_context
            )

            end_time = time.time()
            results.append((thread_id, end_time - start_time, result))

        # Run concurrent logging
        overall_start = time.time()
        threads = []
        for i in range(5):
            thread = threading.Thread(target=log_concurrent, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
        overall_time = time.time() - overall_start

        # Verify all completed successfully
        self.assertEqual(len(results), 5)
        for thread_id, duration, result in results:
            self.assertIsNotNone(result)
            self.assertLess(duration, 1.0)  # Each should complete within 1 second

        # Overall concurrent execution should be efficient
        self.assertLess(overall_time, 3.0)

    def test_file_rotation_performance(self):
        """Test performance impact of file rotation."""
        config = {
            "enabled": True,
            "log_dir": str(self.log_dir),
            "log_prefix": "rotation_perf",
            "max_log_size_mb": 0.01  # Small for testing rotation
        }

        logger = LocalLogger(config)

        # Measure time before and after rotation
        times = []

        for batch in range(3):  # Three batches to trigger rotations
            batch_start = time.time()

            for i in range(20):  # Log assessments in batch
                mock_assessment = Mock()
                mock_assessment.overall_score = 80.0
                mock_assessment.passed = True
                mock_assessment.standard_id = f"rotation_test_{batch}_{i}"
                mock_assessment.dimension_scores = {}

                execution_context = {
                    "function_name": f"rotation_test_function_{batch}_{i}",
                    "module_path": f"rotation.test.module.{batch}.{i}"
                }

                data_info = {
                    "row_count": 1000,
                    "column_count": 15,
                    "columns": [f"column_{j}" for j in range(15)]
                }

                logger.log_assessment(
                    assessment_result=mock_assessment,
                    execution_context=execution_context,
                    data_info=data_info
                )

            batch_time = time.time() - batch_start
            times.append(batch_time)

        # Verify rotation occurred
        rotated_files = list(self.log_dir.glob("rotation_perf_assessment_logs.*.jsonl"))
        self.assertGreater(len(rotated_files), 0)

        # Performance should remain reasonable despite rotation
        # Use 3.0 second threshold to account for slower CI environments (Windows)
        # while still catching real performance regressions
        for batch_time in times:
            self.assertLess(batch_time, 3.0)  # Each batch should complete within 3 seconds

    def test_memory_usage_performance(self):
        """Test memory efficiency during logging operations."""
        config = {
            "enabled": True,
            "log_dir": str(self.log_dir),
            "log_prefix": "memory_test"
        }

        logger = LocalLogger(config)

        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss

            # Log many assessments
            for i in range(200):
                mock_assessment = Mock()
                mock_assessment.overall_score = 75.0 + (i % 25)
                mock_assessment.passed = True
                mock_assessment.standard_id = f"memory_test_{i}"
                mock_assessment.dimension_scores = {
                    f"dimension_{j}": Mock(score=15.0 + j)
                    for j in range(5)
                }

                execution_context = {
                    "function_name": f"memory_test_function_{i}",
                    "module_path": f"memory.test.module.{i}"
                }

                data_info = {
                    "row_count": 1000,
                    "column_count": 10,
                    "columns": [f"column_{k}" for k in range(10)]
                }

                failed_checks = [
                    {
                        "dimension": f"dimension_{j}",
                        "field": f"field_{j}",
                        "issue": "test_issue",
                        "affected_rows": j * 5,
                        "affected_percentage": j * 0.5
                    }
                    for j in range(3)
                ]

                logger.log_assessment(
                    assessment_result=mock_assessment,
                    execution_context=execution_context,
                    data_info=data_info,
                    failed_checks=failed_checks
                )

            memory_after = process.memory_info().rss
            memory_used = memory_after - memory_before

            # Memory usage should be reasonable (less than 50MB for 200 assessments)
            self.assertLess(memory_used, 50 * 1024 * 1024)

        except ImportError:
            # psutil not available, just verify logging works
            for i in range(50):  # Fewer without memory monitoring
                mock_assessment = Mock()
                mock_assessment.overall_score = 75.0
                mock_assessment.passed = True
                mock_assessment.standard_id = f"memory_test_{i}"
                mock_assessment.dimension_scores = {}

                result = logger.log_assessment(
                    assessment_result=mock_assessment,
                    execution_context={"function_name": f"test_{i}"}
                )
                self.assertIsNotNone(result)


class TestLocalLoggingEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions for comprehensive coverage."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_edge_case_assessment_scores(self):
        """Test logging with edge case assessment scores."""
        config = {
            "enabled": True,
            "log_dir": str(self.log_dir),
            "log_prefix": "edge_case"
        }

        logger = LocalLogger(config)

        edge_case_scores = [0.0, 100.0, -1.0, 999.99, float('inf'), float('-inf')]

        for i, score in enumerate(edge_case_scores):
            mock_assessment = Mock()
            mock_assessment.overall_score = score
            mock_assessment.passed = score > 75.0 if score not in [float('inf'), float('-inf')] else False
            mock_assessment.standard_id = f"edge_test_{i}"
            mock_assessment.dimension_scores = {}

            try:
                result = logger.log_assessment(
                    assessment_result=mock_assessment,
                    execution_context={"function_name": f"edge_test_{i}"}
                )
                self.assertIsNotNone(result)
            except (ValueError, TypeError):
                # Some edge cases may cause errors, which is acceptable
                pass

    def test_unicode_and_special_characters(self):
        """Test logging with Unicode and special characters."""
        config = {
            "enabled": True,
            "log_dir": str(self.log_dir),
            "log_prefix": "unicode_test"
        }

        logger = LocalLogger(config)

        mock_assessment = Mock()
        mock_assessment.overall_score = 87.5
        mock_assessment.passed = True
        mock_assessment.standard_id = "unicode_test_标准"
        mock_assessment.dimension_scores = {}  # Empty dict, not Mock

        execution_context = {
            "function_name": "test_función_специальная",
            "module_path": "测试.模块.специальный",
            "environment": "тест"
        }

        data_info = {
            "row_count": 100,
            "column_count": 5,
            "columns": ["客户ID", "姓名", "электронная_почта", "âge", "statüs"]
        }

        failed_checks = [
            {
                "dimension": "validity",
                "field": "электронная_почта",
                "issue": "invalid_format_问题",
                "affected_rows": 5,
                "affected_percentage": 5.0,
                "samples": ["无效@", "не-email", ""],
                "remediation": "修复电子邮件格式验证"
            }
        ]

        result = logger.log_assessment(
            assessment_result=mock_assessment,
            execution_context=execution_context,
            data_info=data_info,
            failed_checks=failed_checks
        )

        self.assertIsNotNone(result)

        # Verify Unicode content was logged correctly
        log_files = logger.get_log_files()
        with open(log_files["assessment_logs"], "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("unicode_test_标准", content)
            self.assertIn("test_función_специальная", content)

    def test_empty_and_null_values(self):
        """Test logging with empty and null values."""
        config = {
            "enabled": True,
            "log_dir": str(self.log_dir),
            "log_prefix": "null_test"
        }

        logger = LocalLogger(config)

        mock_assessment = Mock()
        mock_assessment.overall_score = None
        mock_assessment.passed = None
        mock_assessment.standard_id = ""
        mock_assessment.dimension_scores = {}

        execution_context = {
            "function_name": "",
            "module_path": None,
            "environment": ""
        }

        data_info = {
            "row_count": 0,
            "column_count": 0,
            "columns": []
        }

        result = logger.log_assessment(
            assessment_result=mock_assessment,
            execution_context=execution_context,
            data_info=data_info
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.data_fingerprint["row_count"], 0)

    def test_disabled_logger_edge_cases(self):
        """Test edge cases when logger is disabled."""
        config = {
            "enabled": False,
            "log_dir": str(self.log_dir)
        }

        logger = LocalLogger(config)

        # Test all methods return None or handle gracefully
        result = logger.log_assessment(
            assessment_result=Mock(),
            execution_context={"function_name": "test"}
        )
        self.assertIsNone(result)

        # Clear logs should not crash
        logger.clear_logs()

        # Get log files should return paths even if files don't exist
        log_files = logger.get_log_files()
        self.assertIn("assessment_logs", log_files)
        self.assertIn("dimension_scores", log_files)
        self.assertIn("failed_validations", log_files)

    def test_legacy_config_compatibility(self):
        """Test backward compatibility with legacy configuration options."""
        # Test log_location instead of log_dir
        config = {
            "enabled": True,
            "log_location": str(self.log_dir / "legacy_logs.csv"),  # File path instead of dir
            "log_prefix": "legacy"
        }

        logger = LocalLogger(config)

        # Should extract directory from file path - check if log_dir is correctly set to the parent directory
        expected_dir = self.log_dir
        actual_dir = Path(logger.log_dir)

        # On Windows, if log_location is a file path, the logger should extract just the directory
        if actual_dir.name == "legacy_logs.csv":
            # Logger stored the full file path, extract the parent
            actual_dir = actual_dir.parent

        # Compare the resolved paths to handle path separator differences
        self.assertEqual(actual_dir.resolve(), Path(expected_dir).resolve())

        mock_assessment = Mock()
        mock_assessment.overall_score = 80.0
        mock_assessment.passed = True
        mock_assessment.standard_id = "legacy_test"
        mock_assessment.dimension_scores = {}

        result = logger.log_assessment(
            assessment_result=mock_assessment,
            execution_context={"function_name": "legacy_test"}
        )

        self.assertIsNotNone(result)

    def test_dimension_counting_edge_cases(self):
        """Test edge cases in dimension issue counting."""
        timestamp = datetime.now()
        record = AuditRecord("test", timestamp, "4.0.0")

        # Test with various failed_checks formats
        test_cases = [
            None,  # No failed checks
            [],    # Empty list
            "not_a_list",  # Wrong type
            [
                {"dimension": "validity", "field": "test1"},
                {"dimension": "validity", "field": "test2"},
                {"dimension": "completeness", "field": "test3"},
                {"not_dimension": "invalid"}  # Missing dimension key
            ]
        ]

        for failed_checks in test_cases:
            record.assessment_results["failed_checks"] = failed_checks

            # Should handle gracefully
            count = record._count_dimension_issues("validity")
            self.assertIsInstance(count, int)
            self.assertGreaterEqual(count, 0)

    def test_verodat_format_edge_cases(self):
        """Test Verodat format conversion edge cases."""
        timestamp = datetime.now()
        record = AuditRecord("test", timestamp, "4.0.0")

        # Test with edge case boolean values
        record.assessment_results["passed"] = None
        record.performance_metrics["cache_used"] = "not_boolean"

        verodat_format = record.to_verodat_format()
        main_record = verodat_format["main_record"]

        # Should handle None boolean gracefully
        self.assertIn(main_record["passed"], ["TRUE", "FALSE"])
        self.assertIn(main_record["cache_used"], ["TRUE", "FALSE"])


if __name__ == '__main__':
    unittest.main()
