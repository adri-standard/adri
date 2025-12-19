"""
Test JSONL logging durability and write sequencing.

Validates the core fixes for headless/CI workflows:
1. Synchronous writes ensure assessment_id is capturable immediately
2. write_seq provides stable ordering without timestamp precision issues
3. Config precedence works with environment variables
"""

import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from adri.logging.local import LocalLogger
from adri.config.loader import ConfigurationLoader


class TestJSONLLoggingDurability:
    """Test suite for JSONL logging durability and write sequencing."""

    def test_sync_writes_ensure_immediate_read(self):
        """Verify that sync_writes=True makes logs immediately readable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Configure logger with sync writes
            config = {
                "enabled": True,
                "log_dir": tmpdir,
                "log_prefix": "test",
                "sync_writes": True,
            }

            logger = LocalLogger(config)

            # Create mock assessment result
            from adri.validator.engine import AssessmentResult, DimensionScore

            result = AssessmentResult(
                overall_score=85.5,
                passed=True,
                dimension_scores={
                    "validity": DimensionScore(18.0),
                    "completeness": DimensionScore(17.0),
                },
            )

            # Log assessment
            audit_record = logger.log_assessment(
                assessment_result=result,
                execution_context={"function_name": "test", "module_path": "test"},
                data_info={"row_count": 100, "column_count": 5, "columns": ["a", "b", "c", "d", "e"]},
                performance_metrics={"duration_ms": 250},
            )

            # Immediately read the log file
            log_file = Path(tmpdir) / "test_assessment_logs.jsonl"
            assert log_file.exists(), "Log file should exist immediately after logging"

            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            assert len(lines) == 1, "Should have exactly one log line"

            # Parse the logged record
            logged = json.loads(lines[0])

            # Verify assessment_id is present and matches
            assert "assessment_id" in logged
            assert logged["assessment_id"] == audit_record.assessment_id
            assert logged["write_seq"] == 1  # First write should be seq 1
            assert logged["overall_score"] == 85.5
            assert logged["passed"] is True

    def test_write_seq_monotonic_across_restarts(self):
        """Verify write_seq continues across logger restarts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "enabled": True,
                "log_dir": tmpdir,
                "log_prefix": "test",
                "sync_writes": True,
            }

            from adri.validator.engine import AssessmentResult, DimensionScore

            # First logger instance - write 3 records
            logger1 = LocalLogger(config)
            for i in range(3):
                result = AssessmentResult(
                    overall_score=80.0 + i,
                    passed=True,
                    dimension_scores={"validity": DimensionScore(16.0)},
                )
                logger1.log_assessment(
                    assessment_result=result,
                    execution_context={"function_name": "test", "module_path": "test"},
                    data_info={"row_count": 10, "column_count": 2, "columns": ["a", "b"]},
                )

            # Second logger instance - should continue sequence
            logger2 = LocalLogger(config)
            result = AssessmentResult(
                overall_score=90.0,
                passed=True,
                dimension_scores={"validity": DimensionScore(18.0)},
            )
            logger2.log_assessment(
                assessment_result=result,
                execution_context={"function_name": "test", "module_path": "test"},
                data_info={"row_count": 10, "column_count": 2, "columns": ["a", "b"]},
            )

            # Read all records
            log_file = Path(tmpdir) / "test_assessment_logs.jsonl"
            with open(log_file, "r", encoding="utf-8") as f:
                records = [json.loads(line) for line in f]

            assert len(records) == 4

            # Verify sequences are monotonic
            sequences = [r["write_seq"] for r in records]
            assert sequences == [1, 2, 3, 4], "write_seq should be monotonically increasing"

    def test_verodat_export_format(self):
        """Verify to_verodat_format produces correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "enabled": True,
                "log_dir": tmpdir,
                "log_prefix": "test",
                "sync_writes": True,
            }

            logger = LocalLogger(config)

            from adri.validator.engine import AssessmentResult, DimensionScore

            result = AssessmentResult(
                overall_score=85.5,
                passed=True,
                dimension_scores={"validity": DimensionScore(18.0)},
            )

            logger.log_assessment(
                assessment_result=result,
                execution_context={"function_name": "test", "module_path": "test"},
                data_info={"row_count": 100, "column_count": 5, "columns": ["a", "b", "c", "d", "e"]},
            )

            # Export to Verodat format
            verodat_data = logger.to_verodat_format("assessment_logs")

            # Verify structure
            assert "data" in verodat_data
            assert len(verodat_data["data"]) == 2

            header = verodat_data["data"][0]
            rows = verodat_data["data"][1]

            assert "header" in header
            assert "rows" in rows

            # Verify header contains required fields
            header_names = [h["name"] for h in header["header"]]
            assert "write_seq" in header_names
            assert "assessment_id" in header_names
            assert "timestamp" in header_names

            # Verify rows
            assert len(rows["rows"]) == 1
            assert len(rows["rows"][0]) == len(header["header"])


class TestConfigPrecedence:
    """Test suite for configuration precedence and environment overrides."""

    def test_adri_env_overrides_default(self):
        """Verify ADRI_ENV overrides default_environment."""
        loader = ConfigurationLoader()

        # Mock config
        config = {
            "adri": {
                "default_environment": "development",
                "environments": {
                    "development": {"paths": {"contracts": "./dev/contracts"}},
                    "production": {"paths": {"contracts": "./prod/contracts"}},
                },
            }
        }

        # Test with ADRI_ENV
        os.environ["ADRI_ENV"] = "production"
        try:
            env = loader._get_effective_environment(config, None)
            assert env == "production", "ADRI_ENV should override default"
        finally:
            del os.environ["ADRI_ENV"]

    def test_adri_standards_dir_overrides_config(self):
        """Verify ADRI_CONTRACTS_DIR overrides config paths."""
        loader = ConfigurationLoader()

        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["ADRI_CONTRACTS_DIR"] = tmpdir
            try:
                path = loader.resolve_contract_path("test_standard")
                # Normalize paths to handle Windows short path vs long path names
                normalized_tmpdir = os.path.normpath(os.path.realpath(tmpdir))
                normalized_path = os.path.normpath(os.path.realpath(path))
                assert normalized_tmpdir in normalized_path, "ADRI_CONTRACTS_DIR should override config"
                assert path.endswith("test_standard.yaml")
            finally:
                del os.environ["ADRI_CONTRACTS_DIR"]

    def test_adri_log_dir_enables_audit_logging(self):
        """Verify ADRI_LOG_DIR enables audit logging in DataQualityAssessor."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["ADRI_LOG_DIR"] = tmpdir
            try:
                from adri.validator.engine import DataQualityAssessor

                assessor = DataQualityAssessor()

                # Should have synthesized audit config
                assert "audit" in assessor.config
                assert assessor.config["audit"]["enabled"] is True
                assert assessor.config["audit"]["log_dir"] == tmpdir
                assert assessor.config["audit"]["sync_writes"] is True

                # Should have logger initialized
                assert assessor.audit_logger is not None
            finally:
                del os.environ["ADRI_LOG_DIR"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
