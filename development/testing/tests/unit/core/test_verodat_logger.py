"""
Comprehensive test suite for adri.core.verodat_logger module.

Tests enterprise Verodat API integration to achieve 85%+ coverage.
Covers API configuration, batch processing, schema mapping, error handling, and thread safety.
"""

import json
import os
import tempfile
import threading
import time
import unittest
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import requests
import yaml

from adri.core.audit_logger_csv import AuditRecord
from adri.core.verodat_logger import VerodatLogger


class TestVerodatLoggerInitialization(unittest.TestCase):
    """Test VerodatLogger initialization and configuration."""

    def setUp(self):
        """Set up test fixtures."""
        self.base_config = {
            "enabled": True,
            "api_key": "test_api_key_123",
            "base_url": "https://verodat.io/api/v3",
            "workspace_id": 236,
            "endpoints": {
                "assessment_logs": {
                    "schedule_request_id": 588,
                    "standard": "adri_assessment_logs_standard"
                },
                "dimension_scores": {
                    "schedule_request_id": 589, 
                    "standard": "adri_dimension_scores_standard"
                },
                "failed_validations": {
                    "schedule_request_id": 590,
                    "standard": "adri_failed_validations_standard"
                }
            },
            "batch_settings": {
                "batch_size": 100,
                "flush_interval_seconds": 60,
                "retry_attempts": 3,
                "retry_delay_seconds": 5
            },
            "connection": {
                "timeout_seconds": 30,
                "verify_ssl": True
            }
        }

    def test_verodat_logger_initialization_complete_config(self):
        """Test VerodatLogger initialization with complete configuration."""
        logger = VerodatLogger(self.base_config)
        
        self.assertEqual(logger.config, self.base_config)
        self.assertTrue(logger.enabled)
        self.assertEqual(logger.api_key, "test_api_key_123")
        self.assertEqual(logger.base_url, "https://verodat.io/api/v3")
        self.assertEqual(logger.workspace_id, 236)
        
        # Test batch settings
        self.assertEqual(logger.batch_size, 100)
        self.assertEqual(logger.flush_interval, 60)
        self.assertEqual(logger.retry_attempts, 3)
        self.assertEqual(logger.retry_delay, 5)
        
        # Test connection settings
        self.assertEqual(logger.timeout, 30)
        self.assertTrue(logger.verify_ssl)
        
        # Test batch initialization
        self.assertIsInstance(logger._assessment_logs_batch, list)
        self.assertIsInstance(logger._dimension_scores_batch, list)
        self.assertIsInstance(logger._failed_validations_batch, list)
        self.assertEqual(len(logger._assessment_logs_batch), 0)

    def test_verodat_logger_initialization_minimal_config(self):
        """Test VerodatLogger initialization with minimal configuration."""
        minimal_config = {
            "enabled": True,
            "api_key": "minimal_key"
        }
        
        logger = VerodatLogger(minimal_config)
        
        self.assertTrue(logger.enabled)
        self.assertEqual(logger.api_key, "minimal_key")
        self.assertEqual(logger.base_url, "https://verodat.io/api/v3")
        self.assertIsNone(logger.workspace_id)
        
        # Test defaults
        self.assertEqual(logger.batch_size, 100)
        self.assertEqual(logger.flush_interval, 60)
        self.assertEqual(logger.retry_attempts, 3)
        self.assertEqual(logger.retry_delay, 5)
        self.assertEqual(logger.timeout, 30)
        self.assertTrue(logger.verify_ssl)

    def test_verodat_logger_initialization_disabled(self):
        """Test VerodatLogger initialization when disabled."""
        config = {"enabled": False}
        logger = VerodatLogger(config)
        
        self.assertFalse(logger.enabled)
        self.assertEqual(logger.api_key, "")

    def test_resolve_env_var_with_environment_variable(self):
        """Test environment variable resolution."""
        config = {
            "enabled": True,
            "api_key": "${VERODAT_API_KEY}"
        }
        
        with patch.dict(os.environ, {"VERODAT_API_KEY": "env_test_key"}):
            logger = VerodatLogger(config)
            self.assertEqual(logger.api_key, "env_test_key")

    def test_resolve_env_var_without_environment_variable(self):
        """Test environment variable resolution when env var doesn't exist."""
        config = {
            "enabled": True,
            "api_key": "${NONEXISTENT_VAR}"
        }
        
        with patch.dict(os.environ, {}, clear=True):
            logger = VerodatLogger(config)
            self.assertEqual(logger.api_key, "${NONEXISTENT_VAR}")

    def test_resolve_env_var_with_regular_string(self):
        """Test that regular strings are not modified."""
        config = {
            "enabled": True,
            "api_key": "regular_api_key"
        }
        
        logger = VerodatLogger(config)
        self.assertEqual(logger.api_key, "regular_api_key")


class TestVerodatLoggerStandardsLoading(unittest.TestCase):
    """Test ADRI standards loading and caching."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "enabled": True,
            "api_key": "test_key"
        }
        self.logger = VerodatLogger(self.config)

    def test_load_standard_from_cache(self):
        """Test loading standard from cache."""
        # Pre-populate cache
        cached_standard = {"standard_name": "cached", "fields": {"test": {"type": "string"}}}
        self.logger._standards_cache["test_standard"] = cached_standard
        
        result = self.logger._load_standard("test_standard")
        self.assertEqual(result, cached_standard)

    def test_load_standard_from_file_first_path(self):
        """Test loading standard from first file path."""
        mock_standard = {"standard_name": "loaded", "fields": {"field1": {"type": "string"}}}
        
        with patch('os.path.exists') as mock_exists, \
             patch('builtins.open', create=True) as mock_open, \
             patch('yaml.safe_load') as mock_yaml:
            
            # Mock first path exists
            mock_exists.side_effect = lambda path: "audit_logs" in path
            mock_yaml.return_value = mock_standard
            
            result = self.logger._load_standard("test_standard")
            
            self.assertEqual(result, mock_standard)
            self.assertIn("test_standard", self.logger._standards_cache)

    def test_load_standard_from_file_second_path(self):
        """Test loading standard from second file path."""
        mock_standard = {"standard_name": "loaded", "fields": {"field1": {"type": "string"}}}
        
        with patch('os.path.exists') as mock_exists, \
             patch('builtins.open', create=True) as mock_open, \
             patch('yaml.safe_load') as mock_yaml:
            
            # Mock second path exists
            mock_exists.side_effect = lambda path: path.endswith("adri/standards/test_standard.yaml")
            mock_yaml.return_value = mock_standard
            
            result = self.logger._load_standard("test_standard")
            
            self.assertEqual(result, mock_standard)

    def test_load_standard_from_file_third_path(self):
        """Test loading standard from third file path."""
        mock_standard = {"standard_name": "loaded", "fields": {"field1": {"type": "string"}}}
        
        with patch('os.path.exists') as mock_exists, \
             patch('builtins.open', create=True) as mock_open, \
             patch('yaml.safe_load') as mock_yaml:
            
            # Mock third path exists
            mock_exists.side_effect = lambda path: path == "test_standard.yaml"
            mock_yaml.return_value = mock_standard
            
            result = self.logger._load_standard("test_standard")
            
            self.assertEqual(result, mock_standard)

    def test_load_standard_file_not_found(self):
        """Test loading standard when no file exists."""
        with patch('os.path.exists', return_value=False):
            result = self.logger._load_standard("nonexistent_standard")
            
            # Should return mock standard
            self.assertEqual(result["standard_name"], "nonexistent_standard")
            self.assertIn("fields", result)

    def test_load_standard_yaml_load_returns_none(self):
        """Test loading standard when yaml.safe_load returns None."""
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', create=True), \
             patch('yaml.safe_load', return_value=None):
            
            result = self.logger._load_standard("test_standard")
            
            self.assertEqual(result, {})


class TestVerodatLoggerTypeMapping(unittest.TestCase):
    """Test ADRI to Verodat type mapping."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = VerodatLogger({"enabled": True})

    def test_map_adri_to_verodat_type_string(self):
        """Test string type mapping."""
        self.assertEqual(self.logger._map_adri_to_verodat_type("string"), "string")

    def test_map_adri_to_verodat_type_numeric_types(self):
        """Test numeric type mappings."""
        self.assertEqual(self.logger._map_adri_to_verodat_type("integer"), "numeric")
        self.assertEqual(self.logger._map_adri_to_verodat_type("number"), "numeric")
        self.assertEqual(self.logger._map_adri_to_verodat_type("float"), "numeric")

    def test_map_adri_to_verodat_type_date_types(self):
        """Test date type mappings."""
        self.assertEqual(self.logger._map_adri_to_verodat_type("datetime"), "date")
        self.assertEqual(self.logger._map_adri_to_verodat_type("date"), "date")

    def test_map_adri_to_verodat_type_boolean(self):
        """Test boolean type mapping."""
        self.assertEqual(self.logger._map_adri_to_verodat_type("boolean"), "string")

    def test_map_adri_to_verodat_type_unknown(self):
        """Test unknown type defaults to string."""
        self.assertEqual(self.logger._map_adri_to_verodat_type("unknown_type"), "string")

    def test_map_adri_to_verodat_type_case_insensitive(self):
        """Test case insensitive type mapping."""
        self.assertEqual(self.logger._map_adri_to_verodat_type("STRING"), "string")
        self.assertEqual(self.logger._map_adri_to_verodat_type("INTEGER"), "numeric")


class TestVerodatLoggerHeaderBuilding(unittest.TestCase):
    """Test Verodat header building from ADRI standards."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = VerodatLogger({"enabled": True})

    def test_build_verodat_header_list_format(self):
        """Test building header from list format standard."""
        standard = {
            "fields": [
                {"name": "assessment_id", "type": "string"},
                {"name": "timestamp", "type": "datetime"},
                {"name": "score", "type": "number"}
            ]
        }
        
        header = self.logger._build_verodat_header(standard)
        
        self.assertEqual(len(header), 3)
        self.assertEqual(header[0], {"name": "assessment_id", "type": "string"})
        self.assertEqual(header[1], {"name": "timestamp", "type": "date"})
        self.assertEqual(header[2], {"name": "score", "type": "numeric"})

    def test_build_verodat_header_dict_format(self):
        """Test building header from dict format standard."""
        standard = {
            "fields": {
                "assessment_id": {"type": "string"},
                "timestamp": {"type": "datetime"},
                "score": {"type": "number"}
            }
        }
        
        header = self.logger._build_verodat_header(standard)
        
        self.assertEqual(len(header), 3)
        
        # Convert to dict for easier checking
        header_dict = {field["name"]: field["type"] for field in header}
        self.assertEqual(header_dict["assessment_id"], "string")
        self.assertEqual(header_dict["timestamp"], "date")
        self.assertEqual(header_dict["score"], "numeric")

    def test_build_verodat_header_empty_standard(self):
        """Test building header from empty standard."""
        standard = {"fields": []}
        header = self.logger._build_verodat_header(standard)
        self.assertEqual(len(header), 0)

    def test_build_verodat_header_missing_fields(self):
        """Test building header when fields key is missing."""
        standard = {}
        header = self.logger._build_verodat_header(standard)
        self.assertEqual(len(header), 0)


class TestVerodatLoggerValueFormatting(unittest.TestCase):
    """Test value formatting for Verodat API."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = VerodatLogger({"enabled": True})

    def test_format_value_none(self):
        """Test formatting None values."""
        result = self.logger._format_value(None, "string")
        self.assertIsNone(result)

    def test_format_value_datetime_object(self):
        """Test formatting datetime objects."""
        dt = datetime(2025, 4, 5, 10, 30, 0)
        result = self.logger._format_value(dt, "datetime")
        self.assertEqual(result, "2025-04-05T10:30:00Z")

    def test_format_value_datetime_string_with_timezone(self):
        """Test formatting datetime string with timezone."""
        result = self.logger._format_value("2025-04-05T10:30:00+00:00", "datetime")
        self.assertEqual(result, "2025-04-05T10:30:00Z")

    def test_format_value_datetime_string_without_z(self):
        """Test formatting datetime string without Z."""
        result = self.logger._format_value("2025-04-05T10:30:00", "datetime")
        self.assertEqual(result, "2025-04-05T10:30:00")

    def test_format_value_datetime_string_with_z(self):
        """Test formatting datetime string already with Z."""
        result = self.logger._format_value("2025-04-05T10:30:00Z", "datetime")
        self.assertEqual(result, "2025-04-05T10:30:00Z")

    def test_format_value_boolean_true(self):
        """Test formatting boolean True."""
        result = self.logger._format_value(True, "boolean")
        self.assertEqual(result, "TRUE")

    def test_format_value_boolean_false(self):
        """Test formatting boolean False."""
        result = self.logger._format_value(False, "boolean")
        self.assertEqual(result, "FALSE")

    def test_format_value_list_to_json(self):
        """Test formatting list values to JSON."""
        test_list = ["item1", "item2", "item3"]
        result = self.logger._format_value(test_list, "string")
        self.assertEqual(result, json.dumps(test_list))

    def test_format_value_dict_to_json(self):
        """Test formatting dict values to JSON."""
        test_dict = {"key1": "value1", "key2": "value2"}
        result = self.logger._format_value(test_dict, "string")
        self.assertEqual(result, json.dumps(test_dict))

    def test_format_value_regular_string(self):
        """Test formatting regular string values."""
        result = self.logger._format_value("test_string", "string")
        self.assertEqual(result, "test_string")

    def test_format_value_numeric(self):
        """Test formatting numeric values."""
        result = self.logger._format_value(123.45, "number")
        self.assertEqual(result, 123.45)


class TestVerodatLoggerFieldValueExtraction(unittest.TestCase):
    """Test field value extraction from audit records."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = VerodatLogger({"enabled": True})
        self.record = AuditRecord("test_001", datetime.now(), "3.1.0")
        self.record.execution_context.update({
            "function_name": "test_func",
            "module_path": "test.module",
            "environment": "TEST",
            "hostname": "test-host",
            "process_id": 12345,
            "failure_mode": "log"
        })
        self.main_record = {"fallback_field": "fallback_value"}

    def test_get_core_metadata_fields(self):
        """Test extracting core metadata fields."""
        self.assertEqual(
            self.logger._get_core_metadata_field("assessment_id", self.record),
            "test_001"
        )
        self.assertEqual(
            self.logger._get_core_metadata_field("adri_version", self.record),
            "3.1.0"
        )
        self.assertEqual(
            self.logger._get_core_metadata_field("assessment_type", self.record),
            "QUALITY_CHECK"
        )
        self.assertIsNone(
            self.logger._get_core_metadata_field("unknown_field", self.record)
        )

    def test_get_execution_context_fields(self):
        """Test extracting execution context fields."""
        self.assertEqual(
            self.logger._get_execution_context_field("function_name", self.record),
            "test_func"
        )
        self.assertEqual(
            self.logger._get_execution_context_field("module_path", self.record),
            "test.module"
        )
        self.assertEqual(
            self.logger._get_execution_context_field("environment", self.record),
            "TEST"
        )

    def test_get_execution_context_fields_with_os_fallback(self):
        """Test execution context fields with OS fallback."""
        # Clear hostname and process_id to test fallbacks
        self.record.execution_context["hostname"] = None
        self.record.execution_context["process_id"] = None
        
        with patch('os.uname') as mock_uname, \
             patch('os.getpid', return_value=99999):
            mock_uname.return_value.nodename = "fallback-host"
            
            hostname = self.logger._get_execution_context_field("hostname", self.record)
            pid = self.logger._get_execution_context_field("process_id", self.record)
            
            self.assertEqual(hostname, "fallback-host")
            self.assertEqual(pid, 99999)

    def test_get_standard_metadata_fields(self):
        """Test extracting standard metadata fields."""
        self.record.standard_applied.update({
            "standard_id": "test_standard",
            "standard_version": "1.0.0",
            "standard_checksum": "abc123"
        })
        
        self.assertEqual(
            self.logger._get_standard_metadata_field("standard_id", self.record),
            "test_standard"
        )
        self.assertEqual(
            self.logger._get_standard_metadata_field("standard_version", self.record),
            "1.0.0"
        )
        self.assertEqual(
            self.logger._get_standard_metadata_field("standard_checksum", self.record),
            "abc123"
        )

    def test_get_data_fingerprint_fields(self):
        """Test extracting data fingerprint fields."""
        self.record.data_fingerprint.update({
            "row_count": 1000,
            "column_count": 5,
            "columns": ["col1", "col2", "col3"],
            "checksum": "data_hash"
        })
        
        self.assertEqual(
            self.logger._get_data_fingerprint_field("data_row_count", self.record),
            1000
        )
        self.assertEqual(
            self.logger._get_data_fingerprint_field("data_column_count", self.record),
            5
        )
        
        columns_json = self.logger._get_data_fingerprint_field("data_columns", self.record)
        self.assertEqual(columns_json, '["col1", "col2", "col3"]')
        
        self.assertEqual(
            self.logger._get_data_fingerprint_field("data_checksum", self.record),
            "data_hash"
        )

    def test_get_data_fingerprint_fields_empty_columns(self):
        """Test data fingerprint fields with empty columns."""
        self.record.data_fingerprint["columns"] = []
        
        columns_json = self.logger._get_data_fingerprint_field("data_columns", self.record)
        self.assertEqual(columns_json, "[]")

    def test_get_assessment_result_fields(self):
        """Test extracting assessment result fields."""
        self.record.assessment_results.update({
            "overall_score": 85.5,
            "required_score": 70.0,
            "passed": True,
            "function_executed": False
        })
        
        self.assertEqual(
            self.logger._get_assessment_result_field("overall_score", self.record),
            85.5
        )
        self.assertEqual(
            self.logger._get_assessment_result_field("required_score", self.record),
            70.0
        )
        self.assertTrue(
            self.logger._get_assessment_result_field("passed", self.record)
        )
        self.assertEqual(
            self.logger._get_assessment_result_field("execution_decision", self.record),
            "ALLOWED"
        )

    def test_get_assessment_result_fields_failed(self):
        """Test assessment result fields for failed assessment."""
        self.record.assessment_results["passed"] = False
        
        self.assertEqual(
            self.logger._get_assessment_result_field("execution_decision", self.record),
            "BLOCKED"
        )

    def test_get_performance_metrics_fields(self):
        """Test extracting performance metrics fields."""
        self.record.performance_metrics.update({
            "assessment_duration_ms": 1500,
            "rows_per_second": 666.67
        })
        
        self.assertEqual(
            self.logger._get_performance_metrics_field("assessment_duration_ms", self.record),
            1500
        )
        self.assertEqual(
            self.logger._get_performance_metrics_field("rows_per_second", self.record),
            666.67
        )

    def test_get_performance_metrics_fields_with_cache_info(self):
        """Test performance metrics with cache info."""
        self.record.cache_info = {"cache_used": True}
        
        self.assertTrue(
            self.logger._get_performance_metrics_field("cache_used", self.record)
        )

    def test_get_field_value_from_record(self):
        """Test comprehensive field value extraction."""
        self.record.assessment_results["overall_score"] = 88.0
        
        # Test successful field extraction
        value = self.logger._get_field_value_from_record(
            "overall_score", self.record, self.main_record
        )
        self.assertEqual(value, 88.0)
        
        # Test fallback to main_record
        value = self.logger._get_field_value_from_record(
            "fallback_field", self.record, self.main_record
        )
        self.assertEqual(value, "fallback_value")

    def test_get_dict_format_field_value(self):
        """Test dict format field value extraction."""
        self.record.assessment_results.update({
            "overall_score": 90.0,
            "passed": True
        })
        self.record.data_fingerprint["row_count"] = 2000
        
        # Test various field extractions
        self.assertEqual(
            self.logger._get_dict_format_field_value("assessment_id", self.record, {}),
            "test_001"
        )
        self.assertEqual(
            self.logger._get_dict_format_field_value("overall_score", self.record, {}),
            90.0
        )
        self.assertTrue(
            self.logger._get_dict_format_field_value("passed", self.record, {})
        )
        self.assertEqual(
            self.logger._get_dict_format_field_value("row_count", self.record, {}),
            2000
        )


class TestVerodatLoggerRecordFormatting(unittest.TestCase):
    """Test record formatting for Verodat API."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = VerodatLogger({"enabled": True})
        self.record = AuditRecord("test_001", datetime.now(), "3.1.0")

    def test_format_record_to_row_list_format(self):
        """Test formatting record to row with list format standard."""
        standard = {
            "fields": [
                {"name": "assessment_id", "type": "string"},
                {"name": "overall_score", "type": "number"}
            ]
        }
        
        self.record.assessment_results["overall_score"] = 85.5
        
        row = self.logger._format_record_to_row(self.record, standard, "assessment_logs")
        
        self.assertEqual(len(row), 2)
        self.assertEqual(row[0], "test_001")
        self.assertEqual(row[1], 85.5)

    def test_format_record_to_row_dict_format(self):
        """Test formatting record to row with dict format standard."""
        standard = {
            "fields": {
                "assessment_id": {"type": "string"},
                "overall_score": {"type": "number"}
            }
        }
        
        self.record.assessment_results["overall_score"] = 75.0
        
        row = self.logger._format_record_to_row(self.record, standard, "assessment_logs")
        
        self.assertEqual(len(row), 2)
        self.assertEqual(row[0], "test_001")
        self.assertEqual(row[1], 75.0)

    def test_format_dimension_scores_list_format(self):
        """Test formatting dimension scores with list format standard."""
        standard = {
            "fields": [
                {"name": "assessment_id", "type": "string"},
                {"name": "dimension_name", "type": "string"},
                {"name": "dimension_score", "type": "number"},
                {"name": "dimension_passed", "type": "boolean"}
            ]
        }
        
        self.record.assessment_results["dimension_scores"] = {
            "validity": 18.5,
            "completeness": 16.0
        }
        
        rows = self.logger._format_dimension_scores(self.record, standard)
        
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], "test_001")
        self.assertIn(rows[0][1], ["validity", "completeness"])
        self.assertIn(rows[0][2], [18.5, 16.0])
        self.assertIn(rows[0][3], ["TRUE", "FALSE"])

    def test_format_dimension_scores_dict_format(self):
        """Test formatting dimension scores with dict format standard."""
        standard = {
            "fields": {
                "assessment_id": {"type": "string"},
                "dimension_name": {"type": "string"},
                "dimension_score": {"type": "number"},
                "dimension_passed": {"type": "boolean"}
            }
        }
        
        self.record.assessment_results["dimension_scores"] = {
            "validity": 18.5,
            "completeness": 14.0
        }
        
        rows = self.logger._format_dimension_scores(self.record, standard)
        
        self.assertEqual(len(rows), 2)
        # Check that both dimensions are represented
        dimension_names = [row[1] for row in rows]
        self.assertIn("validity", dimension_names)
        self.assertIn("completeness", dimension_names)

    def test_format_dimension_scores_non_dict(self):
        """Test formatting dimension scores when not a dict."""
        standard = {"fields": []}
        self.record.assessment_results["dimension_scores"] = "invalid"
        
        rows = self.logger._format_dimension_scores(self.record, standard)
        self.assertEqual(len(rows), 0)

    def test_format_dimension_scores_with_compound_key(self):
        """Test formatting dimension scores with compound key field."""
        standard = {
            "fields": [
                {"name": "assessment_id", "type": "string"},
                {"name": "dimension_name", "type": "string"},
                {"name": "dimension_score", "type": "number"},
                {"name": "G360_VERSION_KEY", "type": "string"}
            ]
        }
        
        self.record.assessment_results["dimension_scores"] = {"validity": 18.0}
        
        rows = self.logger._format_dimension_scores(self.record, standard)
        
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][3], "test_001:validity")

    def test_format_failed_validations_list_format(self):
        """Test formatting failed validations with list format standard."""
        standard = {
            "fields": [
                {"name": "assessment_id", "type": "string"},
                {"name": "validation_id", "type": "string"},
                {"name": "dimension", "type": "string"},
                {"name": "field_name", "type": "string"},
                {"name": "issue_type", "type": "string"}
            ]
        }
        
        self.record.assessment_results["failed_checks"] = [
            {
                "dimension": "validity",
                "field_name": "email",
                "issue_type": "invalid_format",
                "affected_rows": 10,
                "affected_percentage": 2.0,
                "sample_failures": ["bad@email", "invalid@"],
                "remediation": "Fix email format"
            },
            {
                "dimension": "completeness",
                "field_name": "name",
                "issue_type": "missing_value",
                "affected_rows": 5
            }
        ]
        
        rows = self.logger._format_failed_validations(self.record, standard)
        
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], "test_001")  # assessment_id
        self.assertEqual(rows[0][1], "val_000")  # validation_id
        self.assertEqual(rows[0][2], "validity")  # dimension
        self.assertEqual(rows[1][1], "val_001")  # validation_id for second record

    def test_format_failed_validations_non_list(self):
        """Test formatting failed validations when not a list."""
        standard = {"fields": []}
        self.record.assessment_results["failed_checks"] = "invalid"
        
        rows = self.logger._format_failed_validations(self.record, standard)
        self.assertEqual(len(rows), 0)

    def test_format_failed_validations_non_dict_items(self):
        """Test formatting failed validations with non-dict items."""
        standard = {"fields": []}
        self.record.assessment_results["failed_checks"] = ["invalid_item", {"dimension": "test"}]
        
        rows = self.logger._format_failed_validations(self.record, standard)
        self.assertEqual(len(rows), 1)  # Only the dict item


class TestVerodatLoggerPayloadPreparation(unittest.TestCase):
    """Test payload preparation for Verodat API."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "enabled": True,
            "endpoints": {
                "assessment_logs": {"standard": "test_standard"}
            }
        }
        self.logger = VerodatLogger(self.config)
        self.record = AuditRecord("test_001", datetime.now(), "3.1.0")

    def test_prepare_payload_assessment_logs(self):
        """Test preparing payload for assessment logs."""
        mock_standard = {
            "fields": [{"name": "assessment_id", "type": "string"}]
        }
        
        with patch.object(self.logger, '_load_standard', return_value=mock_standard):
            payload = self.logger._prepare_payload([self.record], "assessment_logs")
            
            self.assertEqual(len(payload), 2)
            self.assertIn("header", payload[0])
            self.assertIn("rows", payload[1])

    def test_prepare_payload_dimension_scores(self):
        """Test preparing payload for dimension scores."""
        mock_standard = {
            "fields": [{"name": "assessment_id", "type": "string"}]
        }
        
        self.record.assessment_results["dimension_scores"] = {"validity": 18.0}
        
        with patch.object(self.logger, '_load_standard', return_value=mock_standard):
            payload = self.logger._prepare_payload([self.record], "dimension_scores")
            
            self.assertEqual(len(payload), 2)
            self.assertIn("header", payload[0])
            self.assertIn("rows", payload[1])

    def test_prepare_payload_failed_validations(self):
        """Test preparing payload for failed validations."""
        mock_standard = {
            "fields": [{"name": "assessment_id", "type": "string"}]
        }
        
        self.record.assessment_results["failed_checks"] = [
            {"dimension": "validity", "field_name": "email"}
        ]
        
        with patch.object(self.logger, '_load_standard', return_value=mock_standard):
            payload = self.logger._prepare_payload([self.record], "failed_validations")
            
            self.assertEqual(len(payload), 2)
            self.assertIn("header", payload[0])
            self.assertIn("rows", payload[1])


class TestVerodatLoggerAPIOperations(unittest.TestCase):
    """Test API operations and upload functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "enabled": True,
            "api_key": "test_key",
            "base_url": "https://test.verodat.io/api/v3",
            "workspace_id": 123,
            "endpoints": {
                "assessment_logs": {"schedule_request_id": 456}
            },
            "batch_settings": {
                "retry_attempts": 2,
                "retry_delay_seconds": 0.1
            },
            "connection": {
                "timeout_seconds": 30,
                "verify_ssl": True
            }
        }
        self.logger = VerodatLogger(self.config)
        self.record = AuditRecord("test_001", datetime.now(), "3.1.0")

    def test_upload_disabled_logger(self):
        """Test upload when logger is disabled."""
        config = {"enabled": False}
        logger = VerodatLogger(config)
        
        result = logger.upload([self.record], "assessment_logs")
        self.assertTrue(result)  # Should silently succeed

    def test_upload_empty_records(self):
        """Test upload with empty records list."""
        result = self.logger.upload([], "assessment_logs")
        self.assertTrue(result)  # Should silently succeed

    def test_upload_missing_schedule_request_id(self):
        """Test upload with missing schedule_request_id."""
        config = {
            "enabled": True,
            "endpoints": {
                "assessment_logs": {}  # Missing schedule_request_id
            }
        }
        logger = VerodatLogger(config)
        
        with patch('builtins.print') as mock_print:
            result = logger.upload([self.record], "assessment_logs")
            
            self.assertFalse(result)
            mock_print.assert_called()

    @patch('requests.post')
    def test_upload_success(self, mock_post):
        """Test successful upload to Verodat API."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        with patch.object(self.logger, '_prepare_payload', return_value=[]):
            result = self.logger.upload([self.record], "assessment_logs")
            
            self.assertTrue(result)
            mock_post.assert_called_once()
            
            # Verify request parameters
            call_args = mock_post.call_args
            self.assertIn("ApiKey test_key", call_args[1]["headers"]["Authorization"])
            self.assertEqual(call_args[1]["timeout"], 30)
            self.assertTrue(call_args[1]["verify"])

    @patch('requests.post')
    def test_upload_server_error_with_retry_success(self, mock_post):
        """Test upload with server error followed by success."""
        mock_fail = Mock()
        mock_fail.status_code = 500
        mock_fail.text = "Server error"
        
        mock_success = Mock()
        mock_success.status_code = 200
        
        mock_post.side_effect = [mock_fail, mock_success]
        
        with patch.object(self.logger, '_prepare_payload', return_value=[]), \
             patch('time.sleep'):  # Speed up test
            result = self.logger.upload([self.record], "assessment_logs")
            
            self.assertTrue(result)
            self.assertEqual(mock_post.call_count, 2)

    @patch('requests.post')
    def test_upload_client_error_no_retry(self, mock_post):
        """Test upload with client error (no retry)."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_post.return_value = mock_response
        
        with patch.object(self.logger, '_prepare_payload', return_value=[]), \
             patch('builtins.print'):
            result = self.logger.upload([self.record], "assessment_logs")
            
            self.assertFalse(result)
            self.assertEqual(mock_post.call_count, 1)  # No retry for client errors

    @patch('requests.post')
    def test_upload_max_retries_exceeded(self, mock_post):
        """Test upload failure after max retries."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_post.return_value = mock_response
        
        with patch.object(self.logger, '_prepare_payload', return_value=[]), \
             patch('time.sleep'), \
             patch('builtins.print'):
            result = self.logger.upload([self.record], "assessment_logs")
            
            self.assertFalse(result)
            self.assertEqual(mock_post.call_count, 3)  # Initial + 2 retries

    @patch('requests.post')
    def test_upload_exception_handling(self, mock_post):
        """Test upload with request exception."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with patch.object(self.logger, '_prepare_payload', return_value=[]), \
             patch('builtins.print'):
            result = self.logger.upload([self.record], "assessment_logs")
            
            self.assertFalse(result)

    @patch('requests.post')
    def test_upload_exception_with_retry(self, mock_post):
        """Test upload with exception followed by success."""
        mock_success = Mock()
        mock_success.status_code = 200
        
        mock_post.side_effect = [
            requests.exceptions.ConnectionError("Connection failed"),
            mock_success
        ]
        
        with patch.object(self.logger, '_prepare_payload', return_value=[]), \
             patch('time.sleep'), \
             patch('builtins.print'):
            result = self.logger.upload([self.record], "assessment_logs")
            
            self.assertTrue(result)
            self.assertEqual(mock_post.call_count, 2)


class TestVerodatLoggerBatchOperations(unittest.TestCase):
    """Test batch operations and processing."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "enabled": True,
            "batch_settings": {"batch_size": 2}
        }
        self.logger = VerodatLogger(self.config)

    def test_add_to_batch(self):
        """Test adding records to batch."""
        record = AuditRecord("test_001", datetime.now(), "3.1.0")
        
        # Add record with dimension scores and failed checks
        record.assessment_results["dimension_scores"] = {"validity": 18.0}
        record.assessment_results["failed_checks"] = [{"dimension": "test"}]
        
        self.logger.add_to_batch(record)
        
        self.assertEqual(len(self.logger._assessment_logs_batch), 1)
        self.assertEqual(len(self.logger._dimension_scores_batch), 1)
        self.assertEqual(len(self.logger._failed_validations_batch), 1)

    def test_add_to_batch_without_dimension_scores(self):
        """Test adding record without dimension scores."""
        record = AuditRecord("test_001", datetime.now(), "3.1.0")
        
        self.logger.add_to_batch(record)
        
        self.assertEqual(len(self.logger._assessment_logs_batch), 1)
        self.assertEqual(len(self.logger._dimension_scores_batch), 0)
        self.assertEqual(len(self.logger._failed_validations_batch), 0)

    def test_get_batches_assessment_logs(self):
        """Test getting batches for assessment logs."""
        # Add 5 records
        for i in range(5):
            record = AuditRecord(f"test_{i:03d}", datetime.now(), "3.1.0")
            self.logger._assessment_logs_batch.append(record)
        
        batches = self.logger._get_batches("assessment_logs")
        
        self.assertEqual(len(batches), 3)  # 2 full batches + 1 partial
        self.assertEqual(len(batches[0]), 2)
        self.assertEqual(len(batches[1]), 2)
        self.assertEqual(len(batches[2]), 1)

    def test_get_batches_dimension_scores(self):
        """Test getting batches for dimension scores."""
        # Add records to dimension scores batch
        for i in range(3):
            record = AuditRecord(f"test_{i:03d}", datetime.now(), "3.1.0")
            self.logger._dimension_scores_batch.append(record)
        
        batches = self.logger._get_batches("dimension_scores")
        
        self.assertEqual(len(batches), 2)  # 1 full batch + 1 partial
        self.assertEqual(len(batches[0]), 2)
        self.assertEqual(len(batches[1]), 1)

    def test_get_batches_failed_validations(self):
        """Test getting batches for failed validations."""
        # Add records to failed validations batch
        for i in range(4):
            record = AuditRecord(f"test_{i:03d}", datetime.now(), "3.1.0")
            self.logger._failed_validations_batch.append(record)
        
        batches = self.logger._get_batches("failed_validations")
        
        self.assertEqual(len(batches), 2)  # 2 full batches
        self.assertEqual(len(batches[0]), 2)
        self.assertEqual(len(batches[1]), 2)

    def test_get_batches_unknown_dataset(self):
        """Test getting batches for unknown dataset type."""
        batches = self.logger._get_batches("unknown_dataset")
        self.assertEqual(len(batches), 0)

    def test_flush_all_success(self):
        """Test successful flush of all batches."""
        # Add test records
        record = AuditRecord("test_001", datetime.now(), "3.1.0")
        record.assessment_results["dimension_scores"] = {"validity": 18.0}
        record.assessment_results["failed_checks"] = [{"dimension": "test"}]
        
        self.logger.add_to_batch(record)
        self.logger.add_to_batch(record)  # Add twice
        
        with patch.object(self.logger, 'upload', return_value=True) as mock_upload:
            results = self.logger.flush_all()
            
            # Should have called upload for all three dataset types
            self.assertEqual(mock_upload.call_count, 3)
            
            # Check results
            self.assertTrue(results["assessment_logs"]["success"])
            self.assertEqual(results["assessment_logs"]["records_uploaded"], 2)
            self.assertTrue(results["dimension_scores"]["success"])
            self.assertEqual(results["dimension_scores"]["records_uploaded"], 2)
            self.assertTrue(results["failed_validations"]["success"])
            self.assertEqual(results["failed_validations"]["records_uploaded"], 2)
            
            # Check that batches were cleared
            self.assertEqual(len(self.logger._assessment_logs_batch), 0)
            self.assertEqual(len(self.logger._dimension_scores_batch), 0)
            self.assertEqual(len(self.logger._failed_validations_batch), 0)

    def test_flush_all_partial_failure(self):
        """Test flush with partial failure."""
        # Add test records with dimension scores to populate the dimension batch
        record = AuditRecord("test_001", datetime.now(), "3.1.0")
        record.assessment_results["dimension_scores"] = {"validity": 18.0}
        self.logger.add_to_batch(record)
        
        def mock_upload_side_effect(records, dataset_type):
            # Fail for dimension_scores, succeed for others
            return dataset_type != "dimension_scores"
        
        with patch.object(self.logger, 'upload', side_effect=mock_upload_side_effect):
            results = self.logger.flush_all()
            
            # Check results
            self.assertTrue(results["assessment_logs"]["success"])
            self.assertFalse(results["dimension_scores"]["success"])
            self.assertEqual(results["dimension_scores"]["records_uploaded"], 0)
            
            # Failed batch should not be cleared (dimension_scores batch should still have records)
            self.assertEqual(len(self.logger._dimension_scores_batch), 1)  # Should still have the failed record


class TestVerodatLoggerThreadSafety(unittest.TestCase):
    """Test thread safety of Verodat logger operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {"enabled": True}
        self.logger = VerodatLogger(self.config)

    def test_concurrent_add_to_batch(self):
        """Test concurrent add_to_batch operations."""
        def add_records(thread_id):
            for i in range(10):
                record = AuditRecord(f"thread_{thread_id}_record_{i}", datetime.now(), "3.1.0")
                record.assessment_results["dimension_scores"] = {"validity": 18.0}
                self.logger.add_to_batch(record)
        
        # Create multiple threads
        threads = []
        num_threads = 3
        
        for i in range(num_threads):
            thread = threading.Thread(target=add_records, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all records were added
        total_expected = num_threads * 10
        self.assertEqual(len(self.logger._assessment_logs_batch), total_expected)
        self.assertEqual(len(self.logger._dimension_scores_batch), total_expected)

    def test_concurrent_batch_operations(self):
        """Test concurrent batch operations (add and get)."""
        # Pre-populate batches
        for i in range(20):
            record = AuditRecord(f"record_{i}", datetime.now(), "3.1.0")
            self.logger._assessment_logs_batch.append(record)
        
        def get_batches():
            return self.logger._get_batches("assessment_logs")
        
        def add_more_records():
            for i in range(10):
                record = AuditRecord(f"new_record_{i}", datetime.now(), "3.1.0")
                self.logger.add_to_batch(record)
        
        # Run operations concurrently
        thread1 = threading.Thread(target=get_batches)
        thread2 = threading.Thread(target=add_more_records)
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # Should not crash and final count should be consistent
        final_count = len(self.logger._assessment_logs_batch)
        self.assertGreaterEqual(final_count, 20)  # At least original records


if __name__ == "__main__":
    unittest.main()
