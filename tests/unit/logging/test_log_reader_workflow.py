"""Unit tests for ADRILogReader workflow orchestration methods.

Tests the workflow orchestration capabilities added to ADRILogReader
for integration with workflow engines like WorkflowEngine.
"""

import json
import tempfile
from pathlib import Path

import pytest

from adri.logging import ADRILogReader


class TestWorkflowOrchestrationMethods:
    """Test suite for workflow orchestration methods in ADRILogReader."""

    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory with sample JSONL files for workflow tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)

            # Create sample assessment logs with various timestamps
            assessment_logs = [
                {
                    "assessment_id": "adri_20251008_100000_aaa111",
                    "timestamp": "2025-10-08T10:00:00",
                    "adri_version": "4.3.0",
                    "overall_score": 75.0,
                    "passed": True,
                    "data_row_count": 50,
                    "data_column_count": 3,
                    "data_columns": ["id", "name", "value"],
                    "write_seq": 1
                },
                {
                    "assessment_id": "adri_20251008_120000_bbb222",
                    "timestamp": "2025-10-08T12:00:00",
                    "adri_version": "4.3.0",
                    "overall_score": 85.5,
                    "passed": True,
                    "data_row_count": 100,
                    "data_column_count": 5,
                    "data_columns": ["id", "name", "email", "age", "status"],
                    "write_seq": 2
                },
                {
                    "assessment_id": "adri_20251008_140000_ccc333",
                    "timestamp": "2025-10-08T14:00:00",
                    "adri_version": "4.3.0",
                    "overall_score": 92.3,
                    "passed": True,
                    "data_row_count": 75,
                    "data_column_count": 4,
                    "data_columns": ["id", "customer", "amount", "date"],
                    "write_seq": 3
                },
                {
                    "assessment_id": "adri_20251008_160000_ddd444",
                    "timestamp": "2025-10-08T16:00:00",
                    "adri_version": "4.3.0",
                    "overall_score": 65.2,
                    "passed": False,
                    "data_row_count": 25,
                    "data_column_count": 2,
                    "data_columns": ["id", "status"],
                    "write_seq": 4
                }
            ]

            assessment_file = log_dir / "adri_assessment_logs.jsonl"
            with open(assessment_file, "w", encoding="utf-8") as f:
                for log in assessment_logs:
                    f.write(json.dumps(log) + "\n")

            # Create sample dimension scores
            dimension_scores = [
                {
                    "assessment_id": "adri_20251008_120000_bbb222",
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

            # Create sample failed validations
            failed_validations = [
                {
                    "assessment_id": "adri_20251008_160000_ddd444",
                    "validation_id": "val_001",
                    "dimension": "completeness",
                    "field_name": "email",
                    "issue_type": "missing_value",
                    "affected_rows": 5,
                    "affected_percentage": 20.0,
                    "sample_failures": ["row_1", "row_5"],
                    "remediation": "Fill missing values",
                    "write_seq": 1
                }
            ]

            validation_file = log_dir / "adri_failed_validations.jsonl"
            with open(validation_file, "w", encoding="utf-8") as f:
                for validation in failed_validations:
                    f.write(json.dumps(validation) + "\n")

            yield log_dir

    # Tests for get_latest_assessment_id()

    def test_get_latest_assessment_id_success(self, temp_log_dir):
        """Test get_latest_assessment_id returns the most recent assessment ID."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})

        latest_id = reader.get_latest_assessment_id()

        # Should return the most recent assessment (16:00:00)
        assert latest_id == "adri_20251008_160000_ddd444"
        assert isinstance(latest_id, str)

    def test_get_latest_assessment_id_empty(self):
        """Test get_latest_assessment_id returns None when no logs exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reader = ADRILogReader({"paths": {"audit_logs": tmpdir}})

            latest_id = reader.get_latest_assessment_id()

            assert latest_id is None

    def test_get_latest_assessment_id_uses_timestamp_sorting(self, temp_log_dir):
        """Test that get_latest_assessment_id correctly sorts by timestamp."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})

        # Get all assessments to verify sorting
        all_assessments = reader.get_latest_assessments(limit=4)

        # Verify they're sorted by timestamp descending
        assert all_assessments[0]["timestamp"] == "2025-10-08T16:00:00"
        assert all_assessments[1]["timestamp"] == "2025-10-08T14:00:00"
        assert all_assessments[2]["timestamp"] == "2025-10-08T12:00:00"
        assert all_assessments[3]["timestamp"] == "2025-10-08T10:00:00"

        # Latest ID should match the first one
        latest_id = reader.get_latest_assessment_id()
        assert latest_id == all_assessments[0]["assessment_id"]

    # Tests for get_assessments_since(timestamp)

    def test_get_assessments_since_filters_correctly(self, temp_log_dir):
        """Test get_assessments_since returns assessments after given timestamp."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})

        # Get assessments since 12:00:00 (should return 14:00:00 and 16:00:00)
        assessments = reader.get_assessments_since("2025-10-08T12:00:00")

        assert len(assessments) == 2
        # Should be sorted by write_seq
        assert assessments[0]["assessment_id"] == "adri_20251008_140000_ccc333"
        assert assessments[1]["assessment_id"] == "adri_20251008_160000_ddd444"

        # All timestamps should be after the filter timestamp
        for assessment in assessments:
            assert assessment["timestamp"] > "2025-10-08T12:00:00"

    def test_get_assessments_since_empty(self, temp_log_dir):
        """Test get_assessments_since returns empty list when no matches."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})

        # Get assessments after the latest timestamp
        assessments = reader.get_assessments_since("2025-10-08T20:00:00")

        assert assessments == []
        assert isinstance(assessments, list)

    def test_get_assessments_since_boundary_case(self, temp_log_dir):
        """Test get_assessments_since excludes exact timestamp match."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})

        # Get assessments since exactly 14:00:00
        # Should only return 16:00:00 (not 14:00:00 itself, since we use >)
        assessments = reader.get_assessments_since("2025-10-08T14:00:00")

        assert len(assessments) == 1
        assert assessments[0]["assessment_id"] == "adri_20251008_160000_ddd444"

    def test_get_assessments_since_all_match(self, temp_log_dir):
        """Test get_assessments_since returns all when timestamp is before all."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})

        # Get assessments since before all logs
        assessments = reader.get_assessments_since("2025-10-08T09:00:00")

        assert len(assessments) == 4
        # Should be sorted by write_seq
        assert assessments[0]["write_seq"] == 1
        assert assessments[3]["write_seq"] == 4

    def test_get_assessments_since_with_no_logs(self):
        """Test get_assessments_since with empty log directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reader = ADRILogReader({"paths": {"audit_logs": tmpdir}})

            assessments = reader.get_assessments_since("2025-10-08T12:00:00")

            assert assessments == []

    # Tests for read_assessment_by_id(assessment_id)

    def test_read_assessment_by_id_found(self, temp_log_dir):
        """Test read_assessment_by_id returns correct record when found."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})

        assessment = reader.read_assessment_by_id("adri_20251008_120000_bbb222")

        assert assessment is not None
        assert assessment["assessment_id"] == "adri_20251008_120000_bbb222"
        assert assessment["timestamp"] == "2025-10-08T12:00:00"
        assert assessment["overall_score"] == 85.5
        assert assessment["passed"] is True

        # Verify all expected fields are present
        assert "data_row_count" in assessment
        assert "data_columns" in assessment

    def test_read_assessment_by_id_not_found(self, temp_log_dir):
        """Test read_assessment_by_id returns None when ID not found."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})

        assessment = reader.read_assessment_by_id("adri_nonexistent_id")

        assert assessment is None

    def test_read_assessment_by_id_returns_first_match(self, temp_log_dir):
        """Test read_assessment_by_id returns only the first match."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})

        # Test with a valid ID - should return exactly one result
        assessment = reader.read_assessment_by_id("adri_20251008_140000_ccc333")

        assert assessment is not None
        assert isinstance(assessment, dict)
        # Not a list
        assert not isinstance(assessment, list)

    def test_read_assessment_by_id_with_empty_logs(self):
        """Test read_assessment_by_id with empty log directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reader = ADRILogReader({"paths": {"audit_logs": tmpdir}})

            assessment = reader.read_assessment_by_id("some_id")

            assert assessment is None

    def test_read_assessment_by_id_case_sensitive(self, temp_log_dir):
        """Test that read_assessment_by_id is case-sensitive."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})

        # Try with wrong case - should not find it
        assessment = reader.read_assessment_by_id("ADRI_20251008_120000_BBB222")

        assert assessment is None

    # Tests for Property Aliases

    def test_property_aliases_work(self, temp_log_dir):
        """Test that all three property aliases return correct paths."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})

        # Test assessment_logs_path alias
        assert reader.assessment_logs_path == reader.assessment_log_path
        assert reader.assessment_logs_path == Path(temp_log_dir) / "adri_assessment_logs.jsonl"

        # Test dimension_scores_path alias
        assert reader.dimension_scores_path == reader.dimension_score_path
        assert reader.dimension_scores_path == Path(temp_log_dir) / "adri_dimension_scores.jsonl"

        # Test failed_validations_path alias
        assert reader.failed_validations_path == reader.failed_validation_path
        assert reader.failed_validations_path == Path(temp_log_dir) / "adri_failed_validations.jsonl"

    def test_property_aliases_return_path_objects(self, temp_log_dir):
        """Test that property aliases return Path objects."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})

        assert isinstance(reader.assessment_logs_path, Path)
        assert isinstance(reader.dimension_scores_path, Path)
        assert isinstance(reader.failed_validations_path, Path)

    def test_property_aliases_backward_compatibility(self, temp_log_dir):
        """Test that both singular and plural property names work."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})

        # Both should work and return the same values
        assert reader.assessment_log_path.name == "adri_assessment_logs.jsonl"
        assert reader.assessment_logs_path.name == "adri_assessment_logs.jsonl"

        assert reader.dimension_score_path.name == "adri_dimension_scores.jsonl"
        assert reader.dimension_scores_path.name == "adri_dimension_scores.jsonl"

        assert reader.failed_validation_path.name == "adri_failed_validations.jsonl"
        assert reader.failed_validations_path.name == "adri_failed_validations.jsonl"


class TestWorkflowOrchestrationIntegration:
    """Integration tests for workflow orchestration methods."""

    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory with comprehensive test data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)

            # Create multiple assessment logs for comprehensive testing
            assessment_logs = [
                {
                    "assessment_id": f"adri_20251008_{hour:02d}0000_id{idx}",
                    "timestamp": f"2025-10-08T{hour:02d}:00:00",
                    "adri_version": "4.3.0",
                    "overall_score": 70.0 + (idx * 5),
                    "passed": idx % 2 == 0,  # Alternate passed/failed
                    "data_row_count": 50 + (idx * 10),
                    "data_column_count": 3 + idx,
                    "data_columns": [f"col{i}" for i in range(3 + idx)],
                    "write_seq": idx + 1
                }
                for idx, hour in enumerate([10, 11, 12, 13, 14])
            ]

            assessment_file = log_dir / "adri_assessment_logs.jsonl"
            with open(assessment_file, "w", encoding="utf-8") as f:
                for log in assessment_logs:
                    f.write(json.dumps(log) + "\n")

            # Create dimension scores for all assessments
            dimension_scores = []
            for log in assessment_logs:
                dimension_scores.append({
                    "assessment_id": log["assessment_id"],
                    "dimension_name": "completeness",
                    "dimension_score": 18.0,
                    "dimension_passed": True,
                    "issues_found": 1,
                    "details": {"score": 18.0},
                    "write_seq": log["write_seq"]
                })

            dimension_file = log_dir / "adri_dimension_scores.jsonl"
            with open(dimension_file, "w", encoding="utf-8") as f:
                for score in dimension_scores:
                    f.write(json.dumps(score) + "\n")

            # Create failed validations for failed assessments
            failed_validations = []
            for log in assessment_logs:
                if not log["passed"]:
                    failed_validations.append({
                        "assessment_id": log["assessment_id"],
                        "validation_id": f"val_{log['assessment_id']}",
                        "dimension": "completeness",
                        "field_name": "test_field",
                        "issue_type": "missing_value",
                        "affected_rows": 5,
                        "affected_percentage": 10.0,
                        "sample_failures": ["row_1"],
                        "remediation": "Fix values",
                        "write_seq": log["write_seq"]
                    })

            validation_file = log_dir / "adri_failed_validations.jsonl"
            with open(validation_file, "w", encoding="utf-8") as f:
                for validation in failed_validations:
                    f.write(json.dumps(validation) + "\n")

            yield log_dir

    def test_workflow_sequence_latest_to_details(self, temp_log_dir):
        """Test typical workflow sequence: get latest, then get details."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})

        # Step 1: Get latest assessment ID
        latest_id = reader.get_latest_assessment_id()
        assert latest_id is not None

        # Step 2: Get full assessment details
        assessment = reader.read_assessment_by_id(latest_id)
        assert assessment is not None
        assert assessment["assessment_id"] == latest_id

        # Step 3: Get related dimension scores
        scores = reader.read_dimension_scores(latest_id)
        assert len(scores) > 0
        assert scores[0]["assessment_id"] == latest_id

    def test_workflow_incremental_processing(self, temp_log_dir):
        """Test workflow pattern for incremental processing."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})

        # Simulate processing up to 12:00:00
        last_processed_timestamp = "2025-10-08T12:00:00"

        # Get new assessments since last processing
        new_assessments = reader.get_assessments_since(last_processed_timestamp)

        # Should get assessments at 13:00:00 and 14:00:00
        assert len(new_assessments) == 2
        assert all(a["timestamp"] > last_processed_timestamp for a in new_assessments)

        # Process each new assessment
        for assessment in new_assessments:
            # Can get details, scores, validations for each
            scores = reader.read_dimension_scores(assessment["assessment_id"])
            assert isinstance(scores, list)

    def test_workflow_filtering_by_status(self, temp_log_dir):
        """Test workflow pattern for filtering by pass/fail status."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})

        # Get recent assessments since a timestamp
        recent = reader.get_assessments_since("2025-10-08T10:00:00")

        # Filter for failed assessments
        failed_assessments = [a for a in recent if not a["passed"]]

        # For each failed assessment, get validation details
        for assessment in failed_assessments:
            validations = reader.read_failed_validations(assessment["assessment_id"])
            # Failed assessments should have validations
            assert len(validations) > 0

    def test_workflow_monitoring_pattern(self, temp_log_dir):
        """Test workflow pattern for continuous monitoring."""
        reader = ADRILogReader({"paths": {"audit_logs": str(temp_log_dir)}})

        # Get latest assessment for monitoring
        latest_id = reader.get_latest_assessment_id()
        latest = reader.read_assessment_by_id(latest_id)

        assert latest is not None

        # Check status
        if not latest["passed"]:
            # If failed, investigate details
            validations = reader.read_failed_validations(latest_id)
            scores = reader.read_dimension_scores(latest_id)

            # Should have data to analyze the failure
            assert len(validations) > 0 or len(scores) > 0
