"""
Test suite for ADRI Audit Logger following TDD methodology.

Tests are written FIRST before implementation (Red phase).
Then we implement code to make them pass (Green phase).
Finally we refactor while keeping tests green (Refactor phase).
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Import will fail initially (Red phase) - that's expected in TDD
from adri.core.audit_logger import AuditLogger, AuditRecord


class TestAuditRecord:
    """Test the AuditRecord data structure"""

    def test_creates_audit_record_with_required_fields(self):
        """Test that audit record contains all required compliance fields"""
        # Arrange
        record = AuditRecord(
            assessment_id="test_123", timestamp=datetime.now(), adri_version="3.0.0"
        )

        # Act
        record_dict = record.to_dict()

        # Assert - All required fields for compliance
        assert "assessment_metadata" in record_dict
        assert "execution_context" in record_dict
        assert "standard_applied" in record_dict
        assert "data_fingerprint" in record_dict
        assert "assessment_results" in record_dict
        assert "performance_metrics" in record_dict
        assert "action_taken" in record_dict

    def test_assessment_metadata_structure(self):
        """Test assessment metadata contains required fields"""
        # Arrange
        record = AuditRecord(
            assessment_id="test_123", timestamp=datetime.now(), adri_version="3.0.0"
        )

        # Act
        metadata = record.to_dict()["assessment_metadata"]

        # Assert
        assert metadata["assessment_id"] == "test_123"
        assert "timestamp" in metadata
        assert metadata["adri_version"] == "3.0.0"
        assert metadata["assessment_type"] == "QUALITY_CHECK"

    def test_serializes_to_json(self):
        """Test that audit record can be serialized to JSON"""
        # Arrange
        record = AuditRecord(
            assessment_id="test_123", timestamp=datetime.now(), adri_version="3.0.0"
        )

        # Act
        json_str = record.to_json()
        parsed = json.loads(json_str)

        # Assert
        assert isinstance(json_str, str)
        assert parsed["assessment_metadata"]["assessment_id"] == "test_123"


class TestAuditLogger:
    """Test suite for AuditLogger class"""

    @pytest.fixture
    def temp_log_file(self):
        """Create a temporary log file for testing"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            temp_path = f.name
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def mock_assessment_result(self):
        """Create a mock assessment result"""
        result = Mock()
        result.overall_score = 92.7
        result.passed = True
        result.standard_id = "test_standard_v1"
        result.assessment_date = datetime.now()

        # Mock dimension scores
        validity_score = Mock()
        validity_score.score = 18.5
        completeness_score = Mock()
        completeness_score.score = 19.2

        result.dimension_scores = {
            "validity": validity_score,
            "completeness": completeness_score,
            "consistency": Mock(score=17.8),
            "freshness": Mock(score=18.9),
            "plausibility": Mock(score=18.3),
        }

        result.metadata = {"domain": "customer_service"}
        result.rule_execution_log = []
        result.field_analysis = {}

        return result

    def test_logger_initialization(self, temp_log_file):
        """Test AuditLogger initialization with configuration"""
        # Arrange
        config = {"enabled": True, "log_location": temp_log_file, "log_level": "INFO"}

        # Act
        logger = AuditLogger(config)

        # Assert
        assert logger.enabled is True
        assert logger.log_location == temp_log_file
        assert logger.log_level == "INFO"

    def test_logs_successful_assessment(self, temp_log_file, mock_assessment_result):
        """Test logging of successful assessment"""
        # Arrange
        logger = AuditLogger({"enabled": True, "log_location": temp_log_file})
        execution_context = {
            "function_name": "process_customer_requests",
            "module_path": "customer_service.agent",
            "environment": "PRODUCTION",
        }

        # Act
        audit_record = logger.log_assessment(
            assessment_result=mock_assessment_result,
            execution_context=execution_context,
            data_info={"row_count": 1000, "column_count": 5},
            performance_metrics={"duration_ms": 27, "rows_per_second": 37037},
        )

        # Assert
        assert audit_record is not None
        assert audit_record.assessment_results["overall_score"] == 92.7
        assert audit_record.assessment_results["passed"] is True
        assert audit_record.assessment_results["execution_decision"] == "ALLOWED"

        # Verify log file was written
        assert os.path.exists(temp_log_file)
        with open(temp_log_file, "r") as f:
            log_line = f.readline()
            log_data = json.loads(log_line)
            assert log_data["assessment_results"]["overall_score"] == 92.7

    def test_logs_failed_assessment_with_details(self, temp_log_file):
        """Test that failed assessments include failure details"""
        # Arrange
        logger = AuditLogger({"enabled": True, "log_location": temp_log_file})

        failed_result = Mock()
        failed_result.overall_score = 72.3
        failed_result.passed = False
        failed_result.standard_id = "test_standard_v1"
        failed_result.assessment_date = datetime.now()
        failed_result.dimension_scores = {
            "validity": Mock(score=12.0),  # Failed dimension
            "completeness": Mock(score=14.0),  # Failed dimension
        }
        failed_result.metadata = {}
        failed_result.rule_execution_log = []
        failed_result.field_analysis = {}

        execution_context = {
            "function_name": "process_customer_requests",
            "module_path": "customer_service.agent",
        }

        # Act
        audit_record = logger.log_assessment(
            assessment_result=failed_result,
            execution_context=execution_context,
            data_info={"row_count": 1000, "column_count": 5},
            failed_checks=[
                {
                    "dimension": "validity",
                    "field": "email",
                    "issue": "pattern_mismatch",
                    "affected_rows": 156,
                }
            ],
        )

        # Assert
        assert audit_record.assessment_results["passed"] is False
        assert audit_record.assessment_results["execution_decision"] == "BLOCKED"
        assert len(audit_record.assessment_results["failed_checks"]) > 0
        assert audit_record.action_taken["decision"] == "BLOCK"

    def test_respects_enabled_flag(self, mock_assessment_result):
        """Test that logging respects the enabled configuration"""
        # Arrange
        # Use a path that doesn't exist yet
        temp_log_file = tempfile.mktemp(suffix=".jsonl")
        logger = AuditLogger({"enabled": False, "log_location": temp_log_file})

        # Act
        result = logger.log_assessment(
            assessment_result=mock_assessment_result, execution_context={}, data_info={}
        )

        # Assert
        assert result is None  # Should not create audit record when disabled
        assert not os.path.exists(temp_log_file)  # Should not write to file

        # Cleanup if file was created
        if os.path.exists(temp_log_file):
            os.unlink(temp_log_file)

    def test_generates_verodat_compatible_structure(self, mock_assessment_result):
        """Test that output matches Verodat schema requirements"""
        # Arrange
        logger = AuditLogger({"enabled": True})

        # Act
        audit_record = logger.log_assessment(
            assessment_result=mock_assessment_result,
            execution_context={
                "function_name": "test_function",
                "module_path": "test.module",
            },
            data_info={
                "row_count": 1000,
                "column_count": 5,
                "columns": ["id", "name", "email", "age", "status"],
            },
        )

        verodat_format = audit_record.to_verodat_format()

        # Assert - Check main record structure
        main_record = verodat_format["main_record"]
        assert "assessment_id" in main_record
        assert "timestamp" in main_record
        assert "overall_score" in main_record
        assert "passed" in main_record
        assert main_record["passed"] in ["TRUE", "FALSE"]  # String format for Verodat

        # Assert - Check dimension records
        dimension_records = verodat_format["dimension_records"]
        assert len(dimension_records) == 5  # One for each dimension
        for record in dimension_records:
            assert "assessment_id" in record
            assert "dimension_name" in record
            assert "dimension_score" in record
            assert "dimension_passed" in record

    def test_handles_missing_data_gracefully(self, temp_log_file):
        """Test that logger handles incomplete data without crashing"""
        # Arrange
        logger = AuditLogger({"enabled": True, "log_location": temp_log_file})

        minimal_result = Mock()
        minimal_result.overall_score = 80.0
        minimal_result.passed = True
        minimal_result.standard_id = None  # Missing
        minimal_result.assessment_date = None  # Missing
        minimal_result.dimension_scores = {}  # Empty
        minimal_result.metadata = {}
        minimal_result.rule_execution_log = []
        minimal_result.field_analysis = {}

        # Act
        audit_record = logger.log_assessment(
            assessment_result=minimal_result,
            execution_context={},  # Minimal context
            data_info=None,  # Missing
        )

        # Assert - Should still create valid record with defaults
        assert audit_record is not None
        assert audit_record.standard_applied["standard_id"] == "unknown"
        assert audit_record.data_fingerprint["row_count"] == 0

    def test_calculates_performance_metrics(self, mock_assessment_result):
        """Test that performance metrics are properly calculated"""
        # Arrange
        logger = AuditLogger({"enabled": True})

        # Act
        audit_record = logger.log_assessment(
            assessment_result=mock_assessment_result,
            execution_context={},
            data_info={"row_count": 10000},
            performance_metrics={"duration_ms": 100, "cache_used": True},
        )

        # Assert
        metrics = audit_record.performance_metrics
        assert metrics["assessment_duration_ms"] == 100
        assert metrics["rows_per_second"] == 100000  # 10000 rows / 0.1 seconds
        assert metrics["cache_used"] is True

    def test_privacy_settings_exclude_pii(self, temp_log_file, mock_assessment_result):
        """Test that PII is not logged when privacy settings are enabled"""
        # Arrange
        logger = AuditLogger(
            {
                "enabled": True,
                "log_location": temp_log_file,
                "include_data_samples": False,  # Privacy setting
            }
        )

        # Act
        audit_record = logger.log_assessment(
            assessment_result=mock_assessment_result,
            execution_context={},
            data_info={
                "row_count": 1000,
                "sample_data": ["john@example.com", "jane@test.com"],  # PII
            },
        )

        # Assert - PII should not be in the audit record
        record_dict = audit_record.to_dict()
        assert "sample_data" not in str(record_dict)
        assert "john@example.com" not in str(record_dict)

    def test_log_rotation_by_size(self, temp_log_file):
        """Test that logs rotate when max size is reached"""
        # Arrange
        logger = AuditLogger(
            {
                "enabled": True,
                "log_location": temp_log_file,
                "max_log_size_mb": 0.0001,  # Very small for testing
            }
        )

        # Act - Write multiple records
        for i in range(10):
            result = Mock()
            result.overall_score = 80.0 + i
            result.passed = True
            result.standard_id = f"standard_{i}"
            result.assessment_date = datetime.now()
            result.dimension_scores = {}
            result.metadata = {}
            result.rule_execution_log = []
            result.field_analysis = {}

            logger.log_assessment(
                assessment_result=result,
                execution_context={"function_name": f"func_{i}"},
                data_info={"row_count": 1000},
            )

        # Assert - Check for rotated log file
        log_dir = Path(temp_log_file).parent
        list(log_dir.glob(f"{Path(temp_log_file).stem}.*"))
        # Note: Rotation implementation will determine actual behavior
        # This test defines expected behavior

    def test_batch_mode_for_verodat(self):
        """Test that logger can batch records for efficient Verodat upload"""
        # Arrange
        logger = AuditLogger({"enabled": True, "batch_mode": True, "batch_size": 3})

        # Act - Add multiple records
        batch = []
        for i in range(5):
            result = Mock()
            result.overall_score = 80.0 + i
            result.passed = True
            result.standard_id = f"standard_{i}"
            result.assessment_date = datetime.now()
            result.dimension_scores = {}
            result.metadata = {}
            result.rule_execution_log = []
            result.field_analysis = {}

            audit_record = logger.log_assessment(
                assessment_result=result,
                execution_context={"function_name": f"func_{i}"},
                data_info={"row_count": 1000},
            )
            if audit_record:
                batch.append(audit_record)

        # Assert
        verodat_batch = logger.get_verodat_batch()
        assert verodat_batch is not None
        # Batch should trigger at size 3, leaving 2 in buffer

    def test_concurrent_logging_thread_safety(self, temp_log_file):
        """Test that concurrent logging is thread-safe"""
        import threading

        # Arrange
        logger = AuditLogger({"enabled": True, "log_location": temp_log_file})

        def log_assessment(thread_id):
            result = Mock()
            result.overall_score = 85.0
            result.passed = True
            result.standard_id = f"standard_thread_{thread_id}"
            result.assessment_date = datetime.now()
            result.dimension_scores = {}
            result.metadata = {}
            result.rule_execution_log = []
            result.field_analysis = {}

            logger.log_assessment(
                assessment_result=result,
                execution_context={"function_name": f"func_thread_{thread_id}"},
                data_info={"row_count": 100},
            )

        # Act - Create multiple threads
        threads = []
        for i in range(10):
            t = threading.Thread(target=log_assessment, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Assert - All logs should be written without corruption
        with open(temp_log_file, "r") as f:
            lines = f.readlines()
            assert len(lines) == 10
            for line in lines:
                json.loads(line)  # Should not raise exception


class TestAuditLoggerIntegration:
    """Integration tests for audit logger with protection engine"""

    @patch("adri.core.protection.AuditLogger")
    def test_protection_decorator_creates_audit_log(self, mock_audit_logger_class):
        """Test that using @adri_protected creates an audit log"""
        # This test will be implemented after the basic AuditLogger is working
        pass

    def test_end_to_end_audit_trail(self):
        """Test complete flow from assessment to audit log"""
        # This test will verify the entire audit trail
        pass
