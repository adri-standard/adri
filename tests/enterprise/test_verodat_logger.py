"""
Test suite for Verodat logger functionality.

Tests the integration with Verodat API for centralized audit logging,
using ADRI standards as the schema definition.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

import pytest
import yaml

from adri.core.audit_logger import AuditRecord


class TestVerodatLogger:
    """Test suite for VerodatLogger class."""

    @pytest.fixture
    def sample_audit_record(self):
        """Create a sample audit record for testing."""
        record = AuditRecord(
            assessment_id="adri_20250111_223000_abc123",
            timestamp=datetime(2025, 1, 11, 22, 30, 0),
            adri_version="0.1.0",
        )

        # Populate record with test data
        record.execution_context.update(
            {
                "function_name": "process_data",
                "module_path": "app.processors",
                "environment": "PRODUCTION",
            }
        )

        record.standard_applied.update(
            {
                "standard_id": "customer_data_standard",
                "standard_version": "1.0.0",
                "standard_checksum": "abc123def456",
            }
        )

        record.data_fingerprint.update(
            {
                "row_count": 1000,
                "column_count": 10,
                "columns": ["id", "name", "email", "created_at"],
                "data_checksum": "sha256_sample",
            }
        )

        record.assessment_results.update(
            {
                "overall_score": 85.5,
                "required_score": 75.0,
                "passed": True,
                "execution_decision": "ALLOWED",
                "dimension_scores": {
                    "completeness": 90.0,
                    "validity": 85.0,
                    "consistency": 80.0,
                    "uniqueness": 87.0,
                },
                "failed_checks": [
                    {
                        "dimension": "validity",
                        "field": "email",
                        "issue": "invalid_format",
                        "affected_rows": 5,
                        "affected_percentage": 0.5,
                        "samples": ["bad@", "test@"],
                        "remediation": "Fix email format",
                    }
                ],
            }
        )

        record.performance_metrics.update(
            {
                "assessment_duration_ms": 1500,
                "rows_per_second": 666.67,
                "cache_used": False,
            }
        )

        return record

    @pytest.fixture
    def mock_assessment_logs_standard(self):
        """Mock ADRI standard for assessment logs."""
        return {
            "standard_name": "adri_assessment_logs_standard",
            "version": "1.0.0",
            "fields": {
                "assessment_id": {
                    "type": "string",
                    "required": True,
                    "description": "Unique assessment identifier",
                },
                "timestamp": {
                    "type": "datetime",
                    "required": True,
                    "description": "Assessment timestamp",
                },
                "adri_version": {"type": "string", "required": True},
                "function_name": {"type": "string", "required": True},
                "overall_score": {"type": "number", "required": True},
                "passed": {"type": "boolean", "required": True},
                "row_count": {"type": "integer", "required": False},
            },
        }

    @pytest.fixture
    def mock_dimension_scores_standard(self):
        """Mock ADRI standard for dimension scores."""
        return {
            "standard_name": "adri_dimension_scores_standard",
            "version": "1.0.0",
            "fields": {
                "assessment_id": {"type": "string", "required": True},
                "dimension_name": {"type": "string", "required": True},
                "dimension_score": {"type": "number", "required": True},
                "dimension_passed": {"type": "boolean", "required": True},
            },
        }

    @pytest.fixture
    def verodat_config(self):
        """Create test Verodat configuration."""
        return {
            "enabled": True,
            "api_key": "test_api_key_123",
            "base_url": "https://verodat.io/api/v3",
            "workspace_id": 236,
            "endpoints": {
                "assessment_logs": {
                    "schedule_request_id": 588,
                    "standard": "adri_assessment_logs_standard",
                },
                "dimension_scores": {
                    "schedule_request_id": 589,
                    "standard": "adri_dimension_scores_standard",
                },
                "failed_validations": {
                    "schedule_request_id": 590,
                    "standard": "adri_failed_validations_standard",
                },
            },
            "batch_settings": {
                "batch_size": 100,
                "flush_interval_seconds": 60,
                "retry_attempts": 3,
                "retry_delay_seconds": 5,
            },
            "connection": {"timeout_seconds": 30, "verify_ssl": True},
        }

    def test_verodat_logger_initialization(self, verodat_config):
        """Test VerodatLogger initialization with config."""
        from adri.core.verodat_logger import VerodatLogger

        logger = VerodatLogger(verodat_config)

        assert logger.config == verodat_config
        assert logger.api_key == "test_api_key_123"
        assert logger.base_url == "https://verodat.io/api/v3"
        assert logger.workspace_id == 236

    def test_load_standard(self, verodat_config, mock_assessment_logs_standard):
        """Test loading ADRI standard for schema mapping."""
        from adri.core.verodat_logger import VerodatLogger

        with patch("adri.core.verodat_logger.yaml.safe_load") as mock_yaml:
            mock_yaml.return_value = mock_assessment_logs_standard

            logger = VerodatLogger(verodat_config)
            standard = logger._load_standard("adri_assessment_logs_standard")

            assert standard == mock_assessment_logs_standard
            assert "fields" in standard

    def test_build_verodat_header_from_standard(
        self, verodat_config, mock_assessment_logs_standard
    ):
        """Test generating Verodat header from ADRI standard."""
        from adri.core.verodat_logger import VerodatLogger

        logger = VerodatLogger(verodat_config)
        header = logger._build_verodat_header(mock_assessment_logs_standard)

        # Check header structure
        assert isinstance(header, list)
        assert len(header) == len(mock_assessment_logs_standard["fields"])

        # Check field mapping
        expected_fields = {
            "assessment_id": "string",
            "timestamp": "date",
            "adri_version": "string",
            "function_name": "string",
            "overall_score": "numeric",
            "passed": "string",  # Boolean as string for Verodat
            "row_count": "numeric",
        }

        for field in header:
            assert "name" in field
            assert "type" in field
            assert field["type"] == expected_fields[field["name"]]

    def test_map_adri_to_verodat_type(self, verodat_config):
        """Test ADRI to Verodat type mapping."""
        from adri.core.verodat_logger import VerodatLogger

        logger = VerodatLogger(verodat_config)

        # Test type mappings
        assert logger._map_adri_to_verodat_type("string") == "string"
        assert logger._map_adri_to_verodat_type("integer") == "numeric"
        assert logger._map_adri_to_verodat_type("number") == "numeric"
        assert logger._map_adri_to_verodat_type("datetime") == "date"
        assert logger._map_adri_to_verodat_type("boolean") == "string"
        assert logger._map_adri_to_verodat_type("unknown") == "string"  # Default

    def test_format_audit_record_to_verodat_row(
        self, verodat_config, sample_audit_record, mock_assessment_logs_standard
    ):
        """Test formatting audit record to Verodat row format."""
        from adri.core.verodat_logger import VerodatLogger

        logger = VerodatLogger(verodat_config)

        # Format record for assessment logs
        row = logger._format_record_to_row(
            sample_audit_record, mock_assessment_logs_standard, "assessment_logs"
        )

        assert isinstance(row, list)
        # Row should have values in same order as fields in standard
        assert len(row) == len(mock_assessment_logs_standard["fields"])

        # Check specific values
        assert row[0] == "adri_20250111_223000_abc123"  # assessment_id
        assert row[1] == "2025-01-11T22:30:00Z"  # timestamp in ISO format
        assert row[2] == "0.1.0"  # adri_version
        assert row[3] == "process_data"  # function_name
        assert row[4] == 85.5  # overall_score
        assert row[5] == "TRUE"  # passed as string
        assert row[6] == 1000  # row_count

    def test_format_dimension_scores(
        self, verodat_config, sample_audit_record, mock_dimension_scores_standard
    ):
        """Test formatting dimension scores for Verodat."""
        from adri.core.verodat_logger import VerodatLogger

        logger = VerodatLogger(verodat_config)

        # Format dimension scores
        rows = logger._format_dimension_scores(
            sample_audit_record, mock_dimension_scores_standard
        )

        assert isinstance(rows, list)
        assert len(rows) == 4  # 4 dimensions in sample

        # Check first dimension row
        first_row = rows[0]
        assert first_row[0] == "adri_20250111_223000_abc123"  # assessment_id
        assert first_row[1] in [
            "completeness",
            "validity",
            "consistency",
            "uniqueness",
        ]  # dimension_name
        assert isinstance(first_row[2], float)  # dimension_score
        assert first_row[3] in ["TRUE", "FALSE"]  # dimension_passed

    def test_prepare_verodat_payload(
        self, verodat_config, sample_audit_record, mock_assessment_logs_standard
    ):
        """Test preparing complete Verodat API payload."""
        from adri.core.verodat_logger import VerodatLogger

        with patch.object(VerodatLogger, "_load_standard") as mock_load:
            mock_load.return_value = mock_assessment_logs_standard

            logger = VerodatLogger(verodat_config)
            payload = logger._prepare_payload([sample_audit_record], "assessment_logs")

            assert isinstance(payload, list)
            assert len(payload) == 2  # Header and rows

            # Check header
            header_obj = payload[0]
            assert "header" in header_obj
            assert isinstance(header_obj["header"], list)

            # Check rows
            rows_obj = payload[1]
            assert "rows" in rows_obj
            assert isinstance(rows_obj["rows"], list)
            assert len(rows_obj["rows"]) == 1  # One record

    @patch("requests.post")
    def test_upload_to_verodat_success(
        self, mock_post, verodat_config, sample_audit_record
    ):
        """Test successful upload to Verodat API."""
        from adri.core.verodat_logger import VerodatLogger

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "records_processed": 1}
        mock_post.return_value = mock_response

        logger = VerodatLogger(verodat_config)
        result = logger.upload([sample_audit_record], "assessment_logs")

        assert result is True
        mock_post.assert_called_once()

        # Check request details
        call_args = mock_post.call_args
        assert call_args[1]["headers"]["Authorization"] == "ApiKey test_api_key_123"
        assert "verodat.io" in call_args[0][0]

    @patch("requests.post")
    def test_upload_to_verodat_failure_with_retry(
        self, mock_post, verodat_config, sample_audit_record
    ):
        """Test upload failure with retry logic."""
        from adri.core.verodat_logger import VerodatLogger

        # Mock failed responses then success
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.text = "Server error"

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"status": "success"}

        mock_post.side_effect = [
            mock_response_fail,
            mock_response_fail,
            mock_response_success,
        ]

        logger = VerodatLogger(verodat_config)
        logger.config["batch_settings"]["retry_delay_seconds"] = 0.1  # Speed up test

        result = logger.upload([sample_audit_record], "assessment_logs")

        assert result is True
        assert mock_post.call_count == 3  # Initial + 2 retries

    @patch("requests.post")
    def test_upload_failure_after_max_retries(
        self, mock_post, verodat_config, sample_audit_record
    ):
        """Test upload failure after exhausting retries."""
        from adri.core.verodat_logger import VerodatLogger

        # Mock all failed responses
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_post.return_value = mock_response

        logger = VerodatLogger(verodat_config)
        logger.config["batch_settings"]["retry_delay_seconds"] = 0.1

        result = logger.upload([sample_audit_record], "assessment_logs")

        assert result is False
        assert mock_post.call_count == 4  # Initial + 3 retries

    def test_batch_processing(self, verodat_config):
        """Test batching of records."""
        from adri.core.audit_logger import AuditRecord
        from adri.core.verodat_logger import VerodatLogger

        logger = VerodatLogger(verodat_config)
        # Set batch_size directly on the logger instance
        logger.batch_size = 2

        # Add records to batch - create unique records
        for i in range(5):
            record = AuditRecord(
                assessment_id=f"adri_20250111_223000_abc{i:03d}",
                timestamp=datetime(2025, 1, 11, 22, 30, i),
                adri_version="0.1.0",
            )
            logger.add_to_batch(record)

        # Check batch state
        assert len(logger._assessment_logs_batch) == 5

        # Get batches
        batches = logger._get_batches("assessment_logs")
        assert len(batches) == 3  # 2 full batches + 1 partial
        assert len(batches[0]) == 2
        assert len(batches[1]) == 2
        assert len(batches[2]) == 1

    @patch("requests.post")
    def test_flush_batches(self, mock_post, verodat_config, sample_audit_record):
        """Test flushing batched records to Verodat."""
        from adri.core.verodat_logger import VerodatLogger

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_post.return_value = mock_response

        logger = VerodatLogger(verodat_config)

        # Add records
        for _ in range(3):
            logger.add_to_batch(sample_audit_record)

        # Flush all batches
        result = logger.flush_all()

        assert result["assessment_logs"]["success"] is True
        assert result["assessment_logs"]["records_uploaded"] == 3

    def test_environment_variable_substitution(self):
        """Test API key from environment variable."""
        from adri.core.verodat_logger import VerodatLogger

        config = {
            "enabled": True,
            "api_key": "${VERODAT_API_KEY}",
            "base_url": "https://verodat.io/api/v3",
            "workspace_id": 236,
        }

        with patch.dict(os.environ, {"VERODAT_API_KEY": "env_test_key"}):
            logger = VerodatLogger(config)
            assert logger.api_key == "env_test_key"

    def test_disabled_verodat_logger(self, verodat_config):
        """Test that disabled logger doesn't upload."""
        from adri.core.verodat_logger import VerodatLogger

        verodat_config["enabled"] = False
        logger = VerodatLogger(verodat_config)

        result = logger.upload([], "assessment_logs")
        assert result is True  # Returns True but doesn't actually upload
