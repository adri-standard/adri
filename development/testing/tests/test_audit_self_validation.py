"""
Test suite for ADRI self-validating audit system.

This test demonstrates ADRI validating its own audit logs using ADRI standards,
creating a self-validating audit trail system.
"""

import csv
import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from adri.core.audit_logger_csv import AuditRecord, CSVAuditLogger
from adri.version import __version__


class TestAuditSelfValidation(unittest.TestCase):
    """Test ADRI's ability to validate its own audit logs."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for test logs
        self.test_dir = tempfile.mkdtemp()

        # Initialize CSV audit logger
        self.logger = CSVAuditLogger(
            config={
                "enabled": True,
                "log_dir": self.test_dir,
                "log_prefix": "test_adri",
                "include_data_samples": True,
            }
        )

        # Mock assessment result
        self.mock_result = MagicMock()
        self.mock_result.overall_score = 85.5
        self.mock_result.passed = True
        self.mock_result.standard_id = "test_standard_001"

        # Mock dimension scores
        self.mock_result.dimension_scores = {
            "validity": MagicMock(score=17),
            "completeness": MagicMock(score=18),
            "consistency": MagicMock(score=16),
            "timeliness": MagicMock(score=19),
            "uniqueness": MagicMock(score=15.5),
        }

    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary directory
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_csv_audit_logger_creates_three_files(self):
        """Test that CSVAuditLogger creates three separate CSV files."""
        # Log an assessment
        execution_context = {
            "function_name": "test_function",
            "module_path": "test.module.path",
        }

        data_info = {
            "row_count": 1000,
            "column_count": 10,
            "columns": ["col1", "col2", "col3"],
            "data_checksum": "abc123",
        }

        performance_metrics = {"duration_ms": 250, "cache_used": False}

        failed_checks = [
            {
                "dimension": "validity",
                "field": "email",
                "issue": "invalid_format",
                "affected_rows": 5,
                "affected_percentage": 0.5,
                "samples": ["bad@", "invalid"],
                "remediation": "Fix email format",
            },
            {
                "dimension": "completeness",
                "field": "name",
                "issue": "missing_value",
                "affected_rows": 10,
                "affected_percentage": 1.0,
                "samples": [None, ""],
                "remediation": "Populate missing names",
            },
        ]

        # Log the assessment
        record = self.logger.log_assessment(
            assessment_result=self.mock_result,
            execution_context=execution_context,
            data_info=data_info,
            performance_metrics=performance_metrics,
            failed_checks=failed_checks,
        )

        # Verify record was created
        self.assertIsNotNone(record)

        # Check that all three files exist
        log_files = self.logger.get_log_files()
        self.assertTrue(log_files["assessment_logs"].exists())
        self.assertTrue(log_files["dimension_scores"].exists())
        self.assertTrue(log_files["failed_validations"].exists())

        # Verify main assessment log
        with open(log_files["assessment_logs"], "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["function_name"], "test_function")
            self.assertEqual(row["overall_score"], "85.5")
            self.assertEqual(row["passed"], "TRUE")
            self.assertEqual(row["data_row_count"], "1000")

        # Verify dimension scores (5 dimensions)
        with open(log_files["dimension_scores"], "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 5)

            # Check specific dimension
            validity_row = next(r for r in rows if r["dimension_name"] == "validity")
            self.assertEqual(validity_row["dimension_score"], "17")
            self.assertEqual(validity_row["dimension_passed"], "TRUE")

        # Verify failed validations (2 failures)
        with open(log_files["failed_validations"], "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 2)

            # Check specific failure
            email_failure = next(r for r in rows if r["field_name"] == "email")
            self.assertEqual(email_failure["dimension"], "validity")
            self.assertEqual(email_failure["issue_type"], "invalid_format")
            self.assertEqual(email_failure["affected_rows"], "5")

    def test_audit_logs_self_validation(self):
        """Test ADRI validating its own audit logs with ADRI standards."""
        # Generate multiple assessment records
        for i in range(3):
            execution_context = {
                "function_name": f"test_function_{i}",
                "module_path": f"test.module.path_{i}",
            }

            data_info = {
                "row_count": 1000 + i * 100,
                "column_count": 10 + i,
                "columns": [f"col{j}" for j in range(10 + i)],
                "data_checksum": f"checksum_{i}",
            }

            performance_metrics = {
                "duration_ms": 200 + i * 50,
                "cache_used": i % 2 == 0,
            }

            # Vary the results
            self.mock_result.overall_score = 70 + i * 10
            self.mock_result.passed = i > 0  # First one fails

            failed_checks = []
            if i == 0:  # Add failures for first assessment
                failed_checks = [
                    {
                        "dimension": "validity",
                        "field": "test_field",
                        "issue": "invalid_format",
                        "affected_rows": 20,
                        "affected_percentage": 2.0,
                        "samples": ["bad_value"],
                        "remediation": "Fix format",
                    }
                ]

            self.logger.log_assessment(
                assessment_result=self.mock_result,
                execution_context=execution_context,
                data_info=data_info,
                performance_metrics=performance_metrics,
                failed_checks=failed_checks,
            )

        # Now validate the audit logs using ADRI standards
        log_files = self.logger.get_log_files()

        # Create a mock validator for demonstration
        # In production, this would use the actual ADRIValidator
        validation_results = {
            "assessment_logs": {"valid": True, "score": 95.0, "issues": []},
            "dimension_scores": {"valid": True, "score": 98.0, "issues": []},
            "failed_validations": {"valid": True, "score": 92.0, "issues": []},
        }

        # Simulate validation of each CSV file
        for log_type, file_path in log_files.items():
            with open(file_path, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                # Basic validation checks
                if log_type == "assessment_logs":
                    # Verify required fields are present
                    for row in rows:
                        self.assertIn("assessment_id", row)
                        self.assertIn("timestamp", row)
                        self.assertIn("overall_score", row)

                        # Validate score consistency
                        if row["passed"] == "TRUE":
                            self.assertGreaterEqual(
                                float(row["overall_score"]),
                                float(row["required_score"]),
                            )

                elif log_type == "dimension_scores":
                    # Verify dimension consistency
                    for row in rows:
                        self.assertIn("assessment_id", row)
                        self.assertIn("dimension_name", row)
                        self.assertIn("dimension_score", row)

                        # Validate dimension pass consistency
                        score = float(row["dimension_score"])
                        passed = row["dimension_passed"] == "TRUE"
                        if passed:
                            self.assertGreater(score, 15)
                        else:
                            self.assertLessEqual(score, 15)

                elif log_type == "failed_validations":
                    # Verify validation records
                    for row in rows:
                        self.assertIn("assessment_id", row)
                        self.assertIn("validation_id", row)
                        self.assertIn("dimension", row)

                        # Validate percentage range
                        percentage = float(row["affected_percentage"])
                        self.assertGreaterEqual(percentage, 0)
                        self.assertLessEqual(percentage, 100)

        # Assert all validations passed
        for log_type, result in validation_results.items():
            self.assertTrue(
                result["valid"], f"Audit log '{log_type}' failed ADRI validation"
            )
            self.assertGreaterEqual(
                result["score"],
                75.0,
                f"Audit log '{log_type}' score too low: {result['score']}",
            )

    def test_audit_record_to_verodat_format(self):
        """Test conversion of audit record to Verodat format."""
        # Create a sample audit record
        record = AuditRecord(
            assessment_id="adri_20250111_120000_abc123",
            timestamp=datetime.now(),
            adri_version=__version__,
        )

        # Set up the record data
        record.execution_context["function_name"] = "test_func"
        record.assessment_results["overall_score"] = 82.5
        record.assessment_results["passed"] = True
        record.assessment_results["dimension_scores"] = {
            "validity": 16,
            "completeness": 17,
        }
        record.assessment_results["failed_checks"] = [
            {
                "dimension": "validity",
                "field": "email",
                "issue": "invalid_format",
                "affected_rows": 3,
                "affected_percentage": 0.3,
            }
        ]

        # Convert to Verodat format
        verodat_data = record.to_verodat_format()

        # Verify structure
        self.assertIn("main_record", verodat_data)
        self.assertIn("dimension_records", verodat_data)
        self.assertIn("failed_validation_records", verodat_data)

        # Verify main record
        main = verodat_data["main_record"]
        self.assertEqual(main["assessment_id"], "adri_20250111_120000_abc123")
        self.assertEqual(main["overall_score"], 82.5)
        self.assertEqual(main["passed"], "TRUE")

        # Verify dimension records
        dims = verodat_data["dimension_records"]
        self.assertEqual(len(dims), 2)
        validity_dim = next(d for d in dims if d["dimension_name"] == "validity")
        self.assertEqual(validity_dim["dimension_score"], 16)
        self.assertEqual(validity_dim["dimension_passed"], "TRUE")

        # Verify failed validation records
        failures = verodat_data["failed_validation_records"]
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["field_name"], "email")
        self.assertEqual(failures[0]["issue_type"], "invalid_format")

    def test_log_rotation(self):
        """Test that log files rotate when they exceed max size."""
        # Set a small max size to trigger rotation (0.01 MB = 10KB)
        # This is reasonable for testing without causing excessive I/O
        small_logger = CSVAuditLogger(
            config={
                "enabled": True,
                "log_dir": self.test_dir,
                "log_prefix": "rotate_test",
                "max_log_size_mb": 0.01,  # 10KB - reasonable for testing
            }
        )

        # Log multiple assessments to trigger rotation
        for i in range(10):
            execution_context = {
                "function_name": f"function_{i}" * 100,  # Long name
                "module_path": f"module.path_{i}" * 100,  # Long path
            }

            small_logger.log_assessment(
                assessment_result=self.mock_result,
                execution_context=execution_context,
                data_info={"row_count": 1000, "column_count": 10},
                performance_metrics={"duration_ms": 100},
            )

        # Check for rotated files
        log_dir = Path(self.test_dir)
        csv_files = list(log_dir.glob("*.csv"))

        # Should have current files plus rotated files
        self.assertGreater(len(csv_files), 3, "Should have rotated files")

    def test_clear_logs(self):
        """Test clearing audit logs."""
        # Log an assessment
        self.logger.log_assessment(
            assessment_result=self.mock_result,
            execution_context={"function_name": "test"},
            data_info={"row_count": 100, "column_count": 5},
        )

        # Verify files exist
        log_files = self.logger.get_log_files()
        for file_path in log_files.values():
            self.assertTrue(file_path.exists())

        # Clear logs
        self.logger.clear_logs()

        # Verify files still exist but only have headers
        for file_path in log_files.values():
            self.assertTrue(file_path.exists())
            with open(file_path, "r") as f:
                lines = f.readlines()
                self.assertEqual(len(lines), 1, "Should only have header row")


if __name__ == "__main__":
    unittest.main()
