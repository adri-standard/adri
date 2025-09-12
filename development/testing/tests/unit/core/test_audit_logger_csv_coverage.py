"""
Comprehensive test coverage for adri.core.audit_logger_csv module.
Tests all classes, methods and edge cases to achieve 85%+ coverage.
"""

import csv
import json
import os
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest

from adri.core.audit_logger_csv import AuditRecord, CSVAuditLogger


class TestAuditRecord:
    """Test cases for AuditRecord class."""

    def test_init_with_basic_params(self):
        """Test AuditRecord initialization with basic parameters."""
        timestamp = datetime.now()
        record = AuditRecord("test_id", timestamp, "1.0.0")
        
        assert record.assessment_id == "test_id"
        assert record.timestamp == timestamp
        assert record.adri_version == "1.0.0"
        
        # Check that all sections are initialized
        assert "assessment_id" in record.assessment_metadata
        assert "function_name" in record.execution_context
        assert "standard_id" in record.standard_applied
        assert "row_count" in record.data_fingerprint
        assert "overall_score" in record.assessment_results
        assert "assessment_duration_ms" in record.performance_metrics
        assert "decision" in record.action_taken

    def test_init_with_none_timestamp(self):
        """Test initialization handles None timestamp gracefully."""
        with patch('adri.core.audit_logger_csv.datetime') as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = mock_now
            
            record = AuditRecord("test_id", None, "1.0.0")
            
            # Should use current datetime when None is passed
            assert record.assessment_metadata["timestamp"] == mock_now.isoformat()

    def test_to_dict(self):
        """Test conversion to dictionary format."""
        record = AuditRecord("test_id", datetime.now(), "1.0.0")
        result = record.to_dict()
        
        assert isinstance(result, dict)
        assert "assessment_metadata" in result
        assert "execution_context" in result
        assert "standard_applied" in result
        assert "data_fingerprint" in result
        assert "assessment_results" in result
        assert "performance_metrics" in result
        assert "action_taken" in result

    def test_count_dimension_issues_with_valid_checks(self):
        """Test counting dimension issues with valid failed checks."""
        record = AuditRecord("test_id", datetime.now(), "1.0.0")
        record.assessment_results["failed_checks"] = [
            {"dimension": "completeness", "issue": "missing_values"},
            {"dimension": "completeness", "issue": "null_values"},
            {"dimension": "accuracy", "issue": "invalid_format"},
        ]
        
        assert record._count_dimension_issues("completeness") == 2
        assert record._count_dimension_issues("accuracy") == 1
        assert record._count_dimension_issues("consistency") == 0

    def test_count_dimension_issues_with_invalid_checks(self):
        """Test counting dimension issues with invalid failed checks."""
        record = AuditRecord("test_id", datetime.now(), "1.0.0")
        
        # Test with non-list failed_checks
        record.assessment_results["failed_checks"] = "invalid"
        assert record._count_dimension_issues("completeness") == 0
        
        # Test with list containing non-dict items
        record.assessment_results["failed_checks"] = ["invalid", 123]
        assert record._count_dimension_issues("completeness") == 0
        
        # Test with dicts missing dimension key
        record.assessment_results["failed_checks"] = [{"issue": "missing_values"}]
        assert record._count_dimension_issues("completeness") == 0

    def test_to_json(self):
        """Test conversion to JSON string."""
        record = AuditRecord("test_id", datetime.now(), "1.0.0")
        json_str = record.to_json()
        
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert "assessment_metadata" in parsed
        assert parsed["assessment_metadata"]["assessment_id"] == "test_id"

    def test_to_verodat_format_basic(self):
        """Test conversion to Verodat format with basic data."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        record = AuditRecord("test_id", timestamp, "1.0.0")
        
        result = record.to_verodat_format()
        
        assert "main_record" in result
        assert "dimension_records" in result
        assert "failed_validation_records" in result
        
        # Check main record structure
        main = result["main_record"]
        assert main["assessment_id"] == "test_id"
        assert main["adri_version"] == "1.0.0"
        assert main["passed"] == "FALSE"
        assert main["function_executed"] == "FALSE"

    def test_to_verodat_format_with_dimension_scores(self):
        """Test Verodat format conversion with dimension scores."""
        record = AuditRecord("test_id", datetime.now(), "1.0.0")
        record.assessment_results["dimension_scores"] = {
            "completeness": 18.5,
            "accuracy": 12.0,
            "consistency": 20.0
        }
        
        result = record.to_verodat_format()
        dim_records = result["dimension_records"]
        
        assert len(dim_records) == 3
        
        # Find completeness record
        completeness_record = next(
            r for r in dim_records if r["dimension_name"] == "completeness"
        )
        assert completeness_record["dimension_score"] == 18.5
        assert completeness_record["dimension_passed"] == "TRUE"  # > 15
        
        # Find accuracy record
        accuracy_record = next(
            r for r in dim_records if r["dimension_name"] == "accuracy"
        )
        assert accuracy_record["dimension_score"] == 12.0
        assert accuracy_record["dimension_passed"] == "FALSE"  # <= 15

    def test_to_verodat_format_with_failed_validations(self):
        """Test Verodat format conversion with failed validations."""
        record = AuditRecord("test_id", datetime.now(), "1.0.0")
        record.assessment_results["failed_checks"] = [
            {
                "dimension": "completeness",
                "field": "email",
                "issue": "missing_values",
                "affected_rows": 150,
                "affected_percentage": 15.0,
                "samples": ["", None, "missing"],
                "remediation": "Fill missing email values"
            },
            {
                "dimension": "accuracy",
                "field": "age",
                "issue": "invalid_range",
                "affected_rows": 25,
                "affected_percentage": 2.5,
                "samples": [-5, 200, 999],
                "remediation": "Validate age range"
            }
        ]
        
        result = record.to_verodat_format()
        failed_records = result["failed_validation_records"]
        
        assert len(failed_records) == 2
        
        # Check first record
        first_record = failed_records[0]
        assert first_record["assessment_id"] == "test_id"
        assert first_record["validation_id"] == "val_000"
        assert first_record["dimension"] == "completeness"
        assert first_record["field_name"] == "email"
        assert first_record["issue_type"] == "missing_values"
        assert first_record["affected_rows"] == 150
        assert first_record["affected_percentage"] == 15.0
        
        # Check that samples are JSON encoded
        samples = json.loads(first_record["sample_failures"])
        assert samples == ["", None, "missing"]

    def test_to_verodat_format_with_non_dict_dimension_scores(self):
        """Test Verodat format when dimension_scores is not a dict."""
        record = AuditRecord("test_id", datetime.now(), "1.0.0")
        record.assessment_results["dimension_scores"] = "invalid"
        
        result = record.to_verodat_format()
        assert result["dimension_records"] == []

    def test_to_verodat_format_with_non_list_failed_checks(self):
        """Test Verodat format when failed_checks is not a list."""
        record = AuditRecord("test_id", datetime.now(), "1.0.0")
        record.assessment_results["failed_checks"] = "invalid"
        
        result = record.to_verodat_format()
        assert result["failed_validation_records"] == []


class TestCSVAuditLogger:
    """Test cases for CSVAuditLogger class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        logger = CSVAuditLogger()
        
        assert logger.enabled is False
        assert logger.log_dir == Path("./logs")
        assert logger.log_prefix == "adri"
        assert logger.log_level == "INFO"
        assert logger.include_data_samples is True
        assert logger.max_log_size_mb == 100
        assert logger.verodat_logger is None

    def test_init_with_custom_config(self):
        """Test initialization with custom configuration."""
        config = {
            "enabled": True,
            "log_dir": str(self.temp_path),
            "log_prefix": "test",
            "log_level": "DEBUG",
            "include_data_samples": False,
            "max_log_size_mb": 50
        }
        
        logger = CSVAuditLogger(config)
        
        assert logger.enabled is True
        assert logger.log_dir == self.temp_path
        assert logger.log_prefix == "test"
        assert logger.log_level == "DEBUG"
        assert logger.include_data_samples is False
        assert logger.max_log_size_mb == 50

    def test_init_enabled_creates_csv_files(self):
        """Test that enabled logger creates CSV files."""
        config = {
            "enabled": True,
            "log_dir": str(self.temp_path)
        }
        
        logger = CSVAuditLogger(config)
        
        # Check that CSV files are created
        assert logger.assessment_log_path.exists()
        assert logger.dimension_score_path.exists()
        assert logger.failed_validation_path.exists()
        
        # Check that files have headers
        with open(logger.assessment_log_path, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert "assessment_id" in headers
            assert "timestamp" in headers

    def test_initialize_csv_files_thread_safety(self):
        """Test that CSV file initialization is thread-safe."""
        config = {
            "enabled": True,
            "log_dir": str(self.temp_path)
        }
        
        logger = CSVAuditLogger(config)
        
        # Test that multiple calls don't cause issues
        logger._initialize_csv_files()
        logger._initialize_csv_files()
        
        # Files should still exist and be valid
        assert logger.assessment_log_path.exists()

    def test_log_assessment_disabled(self):
        """Test logging when disabled returns None."""
        logger = CSVAuditLogger({"enabled": False})
        
        result = logger.log_assessment(
            MagicMock(),
            {"function_name": "test_func"},
            {"row_count": 100},
            {"duration_ms": 500}
        )
        
        assert result is None

    @patch('adri.core.audit_logger_csv.datetime')
    @patch('adri.core.audit_logger_csv.os.urandom')
    def test_log_assessment_enabled(self, mock_urandom, mock_datetime):
        """Test logging when enabled creates audit record."""
        # Mock datetime and urandom for predictable IDs
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_urandom.return_value = b'\x12\x34\x56'
        
        config = {
            "enabled": True,
            "log_dir": str(self.temp_path)
        }
        logger = CSVAuditLogger(config)
        
        # Mock assessment result
        assessment_result = MagicMock()
        assessment_result.standard_id = "test_standard"
        assessment_result.overall_score = 85.0
        assessment_result.passed = True
        assessment_result.dimension_scores = {
            "completeness": MagicMock(score=18.0),
            "accuracy": MagicMock(score=16.5)
        }
        
        result = logger.log_assessment(
            assessment_result,
            {"function_name": "test_func", "module_path": "test.module"},
            {"row_count": 1000, "column_count": 5, "columns": ["a", "b", "c"]},
            {"duration_ms": 1500},
            [{"dimension": "completeness", "issue": "test_issue"}]
        )
        
        assert result is not None
        assert isinstance(result, AuditRecord)
        assert result.assessment_id.startswith("adri_20230101_120000_")
        assert result.execution_context["function_name"] == "test_func"
        assert result.standard_applied["standard_id"] == "test_standard"
        assert result.assessment_results["overall_score"] == 85.0
        assert result.assessment_results["passed"] is True

    def test_log_assessment_with_environment_variable(self):
        """Test that environment is set from ADRI_ENV variable."""
        config = {
            "enabled": True,
            "log_dir": str(self.temp_path)
        }
        logger = CSVAuditLogger(config)
        
        with patch.dict(os.environ, {"ADRI_ENV": "TEST"}):
            result = logger.log_assessment(
                MagicMock(),
                {"function_name": "test_func"},
                {"row_count": 100}
            )
            
            assert result.execution_context["environment"] == "TEST"

    def test_log_assessment_calculates_data_checksum(self):
        """Test that data checksum is calculated when missing."""
        config = {
            "enabled": True,
            "log_dir": str(self.temp_path)
        }
        logger = CSVAuditLogger(config)
        
        result = logger.log_assessment(
            MagicMock(),
            {"function_name": "test_func"},
            {"row_count": 100, "column_count": 5}  # No checksum provided
        )
        
        assert result.data_fingerprint["data_checksum"] != ""
        assert len(result.data_fingerprint["data_checksum"]) == 16

    def test_log_assessment_calculates_rows_per_second(self):
        """Test that rows per second is calculated."""
        config = {
            "enabled": True,
            "log_dir": str(self.temp_path)
        }
        logger = CSVAuditLogger(config)
        
        result = logger.log_assessment(
            MagicMock(),
            {"function_name": "test_func"},
            {"row_count": 1000},
            {"duration_ms": 2000}  # 2 seconds
        )
        
        assert result.performance_metrics["rows_per_second"] == 500.0

    def test_log_assessment_handles_duration_ms_key(self):
        """Test that duration_ms key is mapped correctly."""
        config = {
            "enabled": True,
            "log_dir": str(self.temp_path)
        }
        logger = CSVAuditLogger(config)
        
        result = logger.log_assessment(
            MagicMock(),
            {"function_name": "test_func"},
            {"row_count": 100},
            {"duration_ms": 1500}
        )
        
        assert result.performance_metrics["assessment_duration_ms"] == 1500

    def test_write_to_csv_files(self):
        """Test writing audit record to CSV files."""
        config = {
            "enabled": True,
            "log_dir": str(self.temp_path)
        }
        logger = CSVAuditLogger(config)
        
        # Create a sample record
        record = AuditRecord("test_id", datetime.now(), "1.0.0")
        record.assessment_results["dimension_scores"] = {"completeness": 18.0}
        record.assessment_results["failed_checks"] = [
            {"dimension": "accuracy", "field": "email", "issue": "invalid"}
        ]
        
        logger._write_to_csv_files(record)
        
        # Check that data was written to files
        with open(logger.assessment_log_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["assessment_id"] == "test_id"
        
        with open(logger.dimension_score_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["dimension_name"] == "completeness"
        
        with open(logger.failed_validation_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["dimension"] == "accuracy"

    def test_check_rotation_small_files(self):
        """Test that small files are not rotated."""
        config = {
            "enabled": True,
            "log_dir": str(self.temp_path),
            "max_log_size_mb": 100
        }
        logger = CSVAuditLogger(config)
        
        # Files should exist but be small
        original_path = logger.assessment_log_path
        logger._check_rotation()
        
        # File should still exist at original path
        assert original_path.exists()

    def test_check_rotation_large_files(self):
        """Test file rotation when files exceed size limit."""
        config = {
            "enabled": True,
            "log_dir": str(self.temp_path),
            "max_log_size_mb": 0.001  # Very small limit for testing
        }
        logger = CSVAuditLogger(config)
        
        # Write enough data to exceed the limit
        with open(logger.assessment_log_path, 'a') as f:
            f.write("x" * 2048)  # Write 2KB of data
        
        original_size = logger.assessment_log_path.stat().st_size
        
        with patch('adri.core.audit_logger_csv.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20230101_120000"
            logger._check_rotation()
        
        # Original file should be smaller now (just headers)
        new_size = logger.assessment_log_path.stat().st_size
        assert new_size < original_size
        
        # Rotated file should exist
        rotated_files = list(self.temp_path.glob("*20230101_120000.csv"))
        assert len(rotated_files) > 0

    def test_check_rotation_nonexistent_files(self):
        """Test rotation check with nonexistent files."""
        config = {
            "enabled": True,
            "log_dir": str(self.temp_path)
        }
        logger = CSVAuditLogger(config)
        
        # Delete the files
        logger.assessment_log_path.unlink()
        logger.dimension_score_path.unlink()
        logger.failed_validation_path.unlink()
        
        # Should not raise an error
        logger._check_rotation()

    def test_get_log_files(self):
        """Test getting log file paths."""
        config = {
            "enabled": True,
            "log_dir": str(self.temp_path),
            "log_prefix": "custom"
        }
        logger = CSVAuditLogger(config)
        
        files = logger.get_log_files()
        
        assert "assessment_logs" in files
        assert "dimension_scores" in files
        assert "failed_validations" in files
        assert files["assessment_logs"].name == "custom_assessment_logs.csv"

    def test_clear_logs_disabled(self):
        """Test clearing logs when disabled does nothing."""
        logger = CSVAuditLogger({"enabled": False})
        
        # Should not raise an error
        logger.clear_logs()

    def test_clear_logs_enabled(self):
        """Test clearing logs removes and recreates files."""
        config = {
            "enabled": True,
            "log_dir": str(self.temp_path)
        }
        logger = CSVAuditLogger(config)
        
        # Write some data
        with open(logger.assessment_log_path, 'a') as f:
            f.write("test data\n")
        
        original_size = logger.assessment_log_path.stat().st_size
        
        logger.clear_logs()
        
        # Files should exist but be smaller (just headers)
        assert logger.assessment_log_path.exists()
        new_size = logger.assessment_log_path.stat().st_size
        assert new_size < original_size

    def test_clear_logs_handles_missing_files(self):
        """Test clearing logs when files don't exist."""
        config = {
            "enabled": True,
            "log_dir": str(self.temp_path)
        }
        logger = CSVAuditLogger(config)
        
        # Delete files
        logger.assessment_log_path.unlink()
        logger.dimension_score_path.unlink()
        logger.failed_validation_path.unlink()
        
        # Should recreate files
        logger.clear_logs()
        
        assert logger.assessment_log_path.exists()
        assert logger.dimension_score_path.exists()
        assert logger.failed_validation_path.exists()

    def test_thread_safety_multiple_logs(self):
        """Test thread safety with multiple concurrent log operations."""
        config = {
            "enabled": True,
            "log_dir": str(self.temp_path)
        }
        logger = CSVAuditLogger(config)
        
        # Function to log from multiple threads
        def log_worker(worker_id):
            for i in range(10):
                result = logger.log_assessment(
                    MagicMock(),
                    {"function_name": f"worker_{worker_id}_func_{i}"},
                    {"row_count": 100 + i}
                )
                assert result is not None
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=log_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that all records were written
        with open(logger.assessment_log_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 50  # 5 threads * 10 logs each

    def test_audit_logger_csv_alias(self):
        """Test that AuditLoggerCSV alias works."""
        from adri.core.audit_logger_csv import AuditLoggerCSV
        
        logger = AuditLoggerCSV({"enabled": False})
        assert isinstance(logger, CSVAuditLogger)


class TestIntegration:
    """Integration tests for the audit logger components."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_audit_workflow(self):
        """Test complete audit workflow from record creation to CSV output."""
        config = {
            "enabled": True,
            "log_dir": str(self.temp_path),
            "log_prefix": "integration_test"
        }
        logger = CSVAuditLogger(config)
        
        # Create mock assessment result
        assessment_result = MagicMock()
        assessment_result.standard_id = "customer_data_v1"
        assessment_result.overall_score = 92.5
        assessment_result.passed = True
        assessment_result.dimension_scores = {
            "completeness": MagicMock(score=19.0),
            "accuracy": MagicMock(score=18.5),
            "consistency": MagicMock(score=17.0)
        }
        
        # Log the assessment
        record = logger.log_assessment(
            assessment_result,
            {
                "function_name": "process_customer_data",
                "module_path": "customer.processor",
                "environment": "PRODUCTION"
            },
            {
                "row_count": 10000,
                "column_count": 15,
                "columns": ["id", "name", "email", "age", "city"],
                "data_checksum": "abc123def456"
            },
            {
                "duration_ms": 2500,
                "cache_used": True
            },
            [
                {
                    "dimension": "consistency",
                    "field": "city",
                    "issue": "inconsistent_format",
                    "affected_rows": 250,
                    "affected_percentage": 2.5,
                    "samples": ["New York", "new york", "NEW YORK"],
                    "remediation": "Standardize city name format"
                }
            ]
        )
        
        # Verify the record was created correctly
        assert record is not None
        assert record.execution_context["function_name"] == "process_customer_data"
        assert record.standard_applied["standard_id"] == "customer_data_v1"
        assert record.assessment_results["overall_score"] == 92.5
        assert record.performance_metrics["cache_used"] is True
        
        # Verify CSV files were created and contain expected data
        assert logger.assessment_log_path.exists()
        assert logger.dimension_score_path.exists()
        assert logger.failed_validation_path.exists()
        
        # Check assessment log
        with open(logger.assessment_log_path, 'r') as f:
            reader = csv.DictReader(f)
            assessment_rows = list(reader)
            assert len(assessment_rows) == 1
            assert assessment_rows[0]["function_name"] == "process_customer_data"
            assert assessment_rows[0]["overall_score"] == "92.5"
            assert assessment_rows[0]["passed"] == "TRUE"
        
        # Check dimension scores
        with open(logger.dimension_score_path, 'r') as f:
            reader = csv.DictReader(f)
            dimension_rows = list(reader)
            assert len(dimension_rows) == 3
            
            completeness_row = next(
                r for r in dimension_rows if r["dimension_name"] == "completeness"
            )
            assert completeness_row["dimension_score"] == "19.0"
            assert completeness_row["dimension_passed"] == "TRUE"
        
        # Check failed validations
        with open(logger.failed_validation_path, 'r') as f:
            reader = csv.DictReader(f)
            validation_rows = list(reader)
            assert len(validation_rows) == 1
            assert validation_rows[0]["dimension"] == "consistency"
            assert validation_rows[0]["field_name"] == "city"
            assert validation_rows[0]["affected_rows"] == "250"
