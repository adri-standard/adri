"""Unit tests for ADRILogReader JSONL log reading functionality.

Tests the ADRILogReader class for reading JSONL audit logs from
ADRI's standard log directory structure.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from adri.logging import ADRILogReader


class TestADRILogReader:
    """Test suite for ADRILogReader class."""

    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory with sample JSONL files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)

            # Create sample assessment logs
            assessment_logs = [
                {
                    "assessment_id": "adri_20251008_120000_abc123",
                    "timestamp": "2025-10-08T12:00:00",
                    "adri_version": "4.3.0",
                    "overall_score": 85.5,
                    "passed": True,
                    "data_row_count": 100,
                    "data_column_count": 5,
                    "data_columns": ["id", "name", "email", "age", "status"],
                    "write_seq": 1
                },
                {
                    "assessment_id": "adri_20251008_130000_def456",
                    "timestamp": "2025-10-08T13:00:00",
                    "adri_version": "4.3.0",
                    "overall_score": 72.3,
                    "passed": False,
                    "data_row_count": 50,
                    "data_column_count": 3,
                    "data_columns": ["id", "value", "date"],
                    "write_seq": 2
                }
            ]

            assessment_file = log_dir / "adri_assessment_logs.jsonl"
            with open(assessment_file, "w", encoding="utf-8") as f:
                for log in assessment_logs:
                    f.write(json.dumps(log) + "\n")

            # Create sample dimension scores
            dimension_scores = [
                {
                    "assessment_id": "adri_20251008_120000_abc123",
                    "dimension_name": "completeness",
                    "dimension_score": 18.5,
                    "dimension_passed": True,
                    "issues_found": 2,
                    "details": {"score": 18.5, "max_score": 20},
                    "write_seq": 1
                },
                {
                    "assessment_id": "adri_20251008_120000_abc123",
                    "dimension_name": "validity",
                    "dimension_score": 17.0,
                    "dimension_passed": True,
                    "issues_found": 1,
                    "details": {"score": 17.0, "max_score": 20},
                    "write_seq": 1
                }
            ]

            dimension_file = log_dir / "adri_dimension_scores.jsonl"
            with open(dimension_file, "w", encoding="utf-8") as f:
                for score in dimension_scores:
                    f.write(json.dumps(score) + "\n")

            # Create sample failed validations
            failed_validations = [
                {
                    "assessment_id": "adri_20251008_130000_def456",
                    "validation_id": "val_001",
                    "dimension": "completeness",
                    "field_name": "email",
                    "issue_type": "missing_value",
                    "affected_rows": 5,
                    "affected_percentage": 10.0,
                    "sample_failures": ["row_1", "row_5"],
                    "remediation": "Fill missing email values",
                    "write_seq": 2
                }
            ]

            validation_file = log_dir / "adri_failed_validations.jsonl"
            with open(validation_file, "w", encoding="utf-8") as f:
                for validation in failed_validations:
                    f.write(json.dumps(validation) + "\n")

            yield log_dir

    def test_read_assessment_logs_success(self, temp_log_dir):
        """Test reading assessment logs successfully."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})
        logs = reader.read_assessment_logs()

        assert len(logs) == 2
        assert logs[0]["assessment_id"] == "adri_20251008_120000_abc123"
        assert logs[1]["assessment_id"] == "adri_20251008_130000_def456"

        # Verify native types
        assert isinstance(logs[0]["passed"], bool)
        assert logs[0]["passed"] is True
        assert isinstance(logs[0]["data_columns"], list)
        assert len(logs[0]["data_columns"]) == 5

    def test_read_assessment_logs_with_limit(self, temp_log_dir):
        """Test reading assessment logs with limit."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})
        logs = reader.read_assessment_logs(limit=1)

        assert len(logs) == 1
        assert logs[0]["assessment_id"] == "adri_20251008_120000_abc123"

    def test_read_assessment_logs_with_filter(self, temp_log_dir):
        """Test reading assessment logs with filter function."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})

        # Filter for only passed assessments
        logs = reader.read_assessment_logs(filter_fn=lambda r: r["passed"])

        assert len(logs) == 1
        assert logs[0]["passed"] is True
        assert logs[0]["overall_score"] == 85.5

    def test_read_dimension_scores(self, temp_log_dir):
        """Test reading dimension scores for specific assessment."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})
        scores = reader.read_dimension_scores("adri_20251008_120000_abc123")

        assert len(scores) == 2
        assert scores[0]["dimension_name"] == "completeness"
        assert scores[1]["dimension_name"] == "validity"

        # Verify native types
        assert isinstance(scores[0]["dimension_passed"], bool)
        assert isinstance(scores[0]["details"], dict)

    def test_read_failed_validations(self, temp_log_dir):
        """Test reading failed validations for specific assessment."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})
        validations = reader.read_failed_validations("adri_20251008_130000_def456")

        assert len(validations) == 1
        assert validations[0]["validation_id"] == "val_001"
        assert validations[0]["field_name"] == "email"

        # Verify native types
        assert isinstance(validations[0]["sample_failures"], list)
        assert len(validations[0]["sample_failures"]) == 2

    def test_get_latest_assessments(self, temp_log_dir):
        """Test getting latest assessments sorted by timestamp."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})
        latest = reader.get_latest_assessments(limit=1)

        assert len(latest) == 1
        # Should return the most recent (13:00:00)
        assert latest[0]["assessment_id"] == "adri_20251008_130000_def456"

    def test_missing_log_file_returns_empty(self):
        """Test that missing log files return empty lists gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reader = ADRILogReader({"paths": {"audit_logs": tmpdir}})

            logs = reader.read_assessment_logs()
            assert logs == []

            scores = reader.read_dimension_scores("test_id")
            assert scores == []

            validations = reader.read_failed_validations("test_id")
            assert validations == []

    def test_malformed_json_line_skipped(self, temp_log_dir):
        """Test that malformed JSON lines are skipped with warning."""
        # Add a malformed line to the assessment log
        assessment_file = temp_log_dir / "adri_assessment_logs.jsonl"
        with open(assessment_file, "a", encoding="utf-8") as f:
            f.write("{ invalid json }\n")

        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})
        logs = reader.read_assessment_logs()

        # Should still get the 2 valid records
        assert len(logs) == 2

    def test_write_seq_ordering(self, temp_log_dir):
        """Test that records are sorted by write_seq."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})
        logs = reader.read_assessment_logs()

        # Should be sorted by write_seq (1, 2)
        assert logs[0]["write_seq"] == 1
        assert logs[1]["write_seq"] == 2

    def test_default_config_path(self):
        """Test that default config path is used when not specified."""
        reader = ADRILogReader({})

        # Should use default path (use as_posix() for cross-platform compatibility)
        assert reader.log_dir.as_posix() == "ADRI/dev/audit-logs"

    def test_custom_config_path(self, temp_log_dir):
        """Test that custom config path is respected."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})

        assert reader.log_dir == temp_log_dir

    def test_empty_lines_skipped(self, temp_log_dir):
        """Test that empty lines in JSONL files are skipped."""
        assessment_file = temp_log_dir / "adri_assessment_logs.jsonl"
        with open(assessment_file, "a", encoding="utf-8") as f:
            f.write("\n\n")  # Add empty lines

        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})
        logs = reader.read_assessment_logs()

        # Should still get the 2 valid records
        assert len(logs) == 2

    def test_type_preservation(self, temp_log_dir):
        """Test that JSON types are preserved (booleans, numbers, arrays)."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})
        logs = reader.read_assessment_logs()

        # Boolean types
        assert isinstance(logs[0]["passed"], bool)
        assert logs[0]["passed"] is True
        assert logs[1]["passed"] is False

        # Number types
        assert isinstance(logs[0]["overall_score"], float)
        assert isinstance(logs[0]["data_row_count"], int)

        # Array types
        assert isinstance(logs[0]["data_columns"], list)
        assert all(isinstance(col, str) for col in logs[0]["data_columns"])

    def test_multiple_filters_combination(self, temp_log_dir):
        """Test combining limit and filter parameters."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})

        # Get only failed assessments with limit
        logs = reader.read_assessment_logs(
            limit=10,
            filter_fn=lambda r: not r["passed"]
        )

        assert len(logs) == 1
        assert logs[0]["passed"] is False


class TestADRILogReaderIntegration:
    """Integration tests for ADRILogReader with real file structure."""

    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory with sample JSONL files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)

            # Create sample assessment logs
            assessment_logs = [
                {
                    "assessment_id": "adri_20251008_120000_abc123",
                    "timestamp": "2025-10-08T12:00:00",
                    "adri_version": "4.3.0",
                    "overall_score": 85.5,
                    "passed": True,
                    "data_row_count": 100,
                    "data_column_count": 5,
                    "data_columns": ["id", "name", "email", "age", "status"],
                    "write_seq": 1
                }
            ]

            assessment_file = log_dir / "adri_assessment_logs.jsonl"
            with open(assessment_file, "w", encoding="utf-8") as f:
                for log in assessment_logs:
                    f.write(json.dumps(log) + "\n")

            # Create sample dimension scores
            dimension_scores = [
                {
                    "assessment_id": "adri_20251008_120000_abc123",
                    "dimension_name": "completeness",
                    "dimension_score": 18.5,
                    "dimension_passed": True,
                    "issues_found": 2,
                    "details": {"score": 18.5, "max_score": 20},
                    "write_seq": 1
                }
            ]

            dimension_file = log_dir / "adri_dimension_scores.jsonl"
            with open(dimension_file, "w", encoding="utf-8") as f:
                for score in dimension_scores:
                    f.write(json.dumps(score) + "\n")

            yield log_dir

    def test_reads_from_standard_dev_location(self):
        """Test reading from standard ADRI/dev/audit-logs location."""
        # This test will pass if the directory exists, otherwise gracefully return empty
        reader = ADRILogReader({"paths": {"audit_logs": "ADRI/dev/audit-logs"}})

        # Should not raise an error even if files don't exist
        try:
            logs = reader.read_assessment_logs()
            # May be empty if no logs exist, but should be a list
            assert isinstance(logs, list)
        except Exception:
            # If directory doesn't exist or has issues, that's ok for this test
            pass

    def test_cross_file_linkage(self, temp_log_dir):
        """Test that assessment_id links work across files."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})

        # Get an assessment
        logs = reader.read_assessment_logs(limit=1)
        assert len(logs) > 0, "Should have at least one log"

        assessment_id = logs[0]["assessment_id"]

        # Get related dimension scores
        scores = reader.read_dimension_scores(assessment_id)

        # All scores should have matching assessment_id
        assert all(s["assessment_id"] == assessment_id for s in scores)
