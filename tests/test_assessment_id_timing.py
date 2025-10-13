"""
Test assessment ID timing fix.

Verify that assessment IDs are generated at AssessmentResult creation time
and are consistently used across workflow, audit, and reasoning logging.
"""

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from adri.validator.engine import AssessmentResult, DataQualityAssessor


class TestAssessmentIdTiming:
    """Test assessment ID timing and consistency."""

    def test_assessment_result_has_id_on_creation(self):
        """Verify AssessmentResult has assessment_id immediately after creation."""
        result = AssessmentResult(
            overall_score=85.0,
            passed=True,
            dimension_scores={
                "validity": 18.0,
                "completeness": 17.0,
                "consistency": 20.0,
                "freshness": 20.0,
                "plausibility": 20.0,
            },
        )

        # Assessment ID should exist immediately
        assert hasattr(result, "assessment_id")
        assert result.assessment_id is not None
        assert isinstance(result.assessment_id, str)
        assert result.assessment_id.startswith("adri_")
        assert len(result.assessment_id) > 10  # Should have timestamp and random hex

    def test_assessment_id_format(self):
        """Verify assessment_id follows expected format pattern."""
        result = AssessmentResult(
            overall_score=85.0,
            passed=True,
            dimension_scores={},
        )

        # Format should be: adri_{YYYYMMDD}_{HHMMSS}_{random_hex}
        parts = result.assessment_id.split("_")
        assert len(parts) == 4
        assert parts[0] == "adri"
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 6  # HHMMSS
        assert len(parts[3]) == 6  # 3-byte hex = 6 characters

    def test_assessment_id_uniqueness(self):
        """Verify each AssessmentResult gets a unique ID."""
        result1 = AssessmentResult(
            overall_score=85.0,
            passed=True,
            dimension_scores={},
        )
        result2 = AssessmentResult(
            overall_score=90.0,
            passed=True,
            dimension_scores={},
        )

        # IDs should be different
        assert result1.assessment_id != result2.assessment_id

    def test_assessment_id_used_in_audit_logging(self):
        """Verify assessment_id from result is used in audit logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create assessor with audit logging enabled
            config = {
                "audit": {
                    "enabled": True,
                    "log_dir": temp_dir,
                    "log_prefix": "test",
                    "sync_writes": True,
                }
            }
            assessor = DataQualityAssessor(config=config)

            # Create test data
            data = pd.DataFrame(
                {
                    "name": ["Alice", "Bob"],
                    "age": [25, 30],
                    "email": ["alice@example.com", "bob@example.com"],
                }
            )

            # Perform assessment
            result = assessor.assess(data)

            # Verify assessment_id exists
            assert hasattr(result, "assessment_id")
            assert result.assessment_id.startswith("adri_")

            # Check audit log file contains the assessment_id
            audit_log_path = Path(temp_dir) / "test_assessment_logs.jsonl"
            assert audit_log_path.exists()

            import json

            with open(audit_log_path, "r", encoding="utf-8") as f:
                log_content = f.read()
                log_record = json.loads(log_content.strip())

                # The assessment_id in the log should match the result
                assert log_record["assessment_id"] == result.assessment_id

    def test_assessment_id_consistency_across_logs(self):
        """Verify same assessment_id is used across all log files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create assessor with audit logging enabled
            config = {
                "audit": {
                    "enabled": True,
                    "log_dir": temp_dir,
                    "log_prefix": "test",
                    "sync_writes": True,
                }
            }
            assessor = DataQualityAssessor(config=config)

            # Create test data
            data = pd.DataFrame(
                {
                    "name": ["Alice", "Bob"],
                    "age": [25, 30],
                    "email": ["alice@example.com", "bob@example.com"],
                }
            )

            # Perform assessment
            result = assessor.assess(data)
            expected_id = result.assessment_id

            # Check assessment logs
            import json

            assessment_log_path = Path(temp_dir) / "test_assessment_logs.jsonl"
            if assessment_log_path.exists():
                with open(assessment_log_path, "r", encoding="utf-8") as f:
                    log_record = json.loads(f.read().strip())
                    assert log_record["assessment_id"] == expected_id

            # Check dimension scores
            dimension_log_path = Path(temp_dir) / "test_dimension_scores.jsonl"
            if dimension_log_path.exists():
                with open(dimension_log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            log_record = json.loads(line.strip())
                            assert log_record["assessment_id"] == expected_id

    def test_assessment_id_not_unknown(self):
        """Verify assessment_id is never 'unknown' in workflow logging context."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create assessor with audit logging enabled
            config = {
                "audit": {
                    "enabled": True,
                    "log_dir": temp_dir,
                    "log_prefix": "test",
                    "sync_writes": True,
                }
            }
            assessor = DataQualityAssessor(config=config)

            # Create test data
            data = pd.DataFrame(
                {
                    "name": ["Alice"],
                    "age": [25],
                }
            )

            # Perform assessment
            result = assessor.assess(data)

            # Verify assessment_id is not "unknown"
            assert result.assessment_id != "unknown"
            assert "unknown" not in result.assessment_id.lower()

    def test_custom_assessment_id(self):
        """Verify custom assessment_id can be provided if needed."""
        custom_id = "adri_test_custom_123456"
        result = AssessmentResult(
            overall_score=85.0,
            passed=True,
            dimension_scores={},
            assessment_id=custom_id,
        )

        # Custom ID should be used
        assert result.assessment_id == custom_id
