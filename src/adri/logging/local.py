# @ADRI_FEATURE[logging_local_jsonl, scope=SHARED]
# Description: Local JSONL audit logging system used by both enterprise and open source
"""
ADRI Local Logging - JSONL-based Audit Logging.

Enhanced audit logger module with JSONL output, migrated from core/audit_logger_csv.py.
Captures comprehensive audit logs for all ADRI assessments directly in
Verodat-compatible JSONL format with three linked datasets.
"""

import hashlib
import json
import os
import socket
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

# Enterprise logging functionality is available in the enterprise package

# Clean import for version info
from ..version import __version__


class AuditRecord:
    """Represents a single audit record for an ADRI assessment."""

    def __init__(self, assessment_id: str, timestamp: datetime, adri_version: str):
        """Initialize an audit record with required metadata."""
        self.assessment_id = assessment_id
        self.timestamp = timestamp
        self.adri_version = adri_version

        # Initialize all required sections
        self.assessment_metadata = {
            "assessment_id": assessment_id,
            "timestamp": (
                timestamp.isoformat() if timestamp else datetime.now().isoformat()
            ),
            "adri_version": adri_version,
            "assessment_type": "QUALITY_CHECK",
        }

        self.execution_context = {
            "function_name": "",
            "module_path": "",
            "environment": "UNKNOWN",
            "hostname": socket.gethostname(),
            "process_id": os.getpid(),
        }

        self.standard_applied = {
            "standard_id": "unknown",
            "standard_version": "unknown",
            "standard_checksum": "",
            "standard_path": "",  # Full absolute path to standard file
        }

        self.data_fingerprint = {
            "row_count": 0,
            "column_count": 0,
            "columns": [],
            "data_checksum": "",
        }

        self.assessment_results = {
            "overall_score": 0.0,
            "required_score": 75.0,
            "passed": False,
            "execution_decision": "BLOCKED",
            "dimension_scores": {},
            "failed_checks": [],
        }

        self.performance_metrics = {
            "assessment_duration_ms": 0,
            "rows_per_second": 0.0,
            "cache_used": False,
        }

        self.action_taken = {
            "decision": "BLOCK",
            "failure_mode": "raise",
            "function_executed": False,
            "remediation_suggested": [],
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert audit record to dictionary format."""
        return {
            "assessment_metadata": self.assessment_metadata,
            "execution_context": self.execution_context,
            "standard_applied": self.standard_applied,
            "data_fingerprint": self.data_fingerprint,
            "assessment_results": self.assessment_results,
            "performance_metrics": self.performance_metrics,
            "action_taken": self.action_taken,
        }

    def _count_dimension_issues(self, dim_name: str) -> int:
        """Count issues for a specific dimension."""
        failed_checks = self.assessment_results.get("failed_checks")
        if not isinstance(failed_checks, list):
            return 0

        count = 0
        for check in failed_checks:
            if isinstance(check, dict) and check.get("dimension") == dim_name:
                count += 1
        return count

    def to_json(self) -> str:
        """Convert audit record to JSON string."""
        return json.dumps(self.to_dict(), default=str)

    def to_verodat_format(self) -> dict[str, Any]:
        """
        Convert audit record to Verodat-compatible format.

        Returns a dictionary with:
        - main_record: Main assessment record for adri_assessment_logs dataset
        - dimension_records: Dimension scores for adri_dimension_scores dataset
        - failed_validation_records: Failed checks for adri_failed_validations dataset
        """
        # Main record for adri_assessment_logs
        main_record = {
            "assessment_id": self.assessment_id,
            "timestamp": self.assessment_metadata["timestamp"],
            "adri_version": self.adri_version,
            "assessment_type": self.assessment_metadata["assessment_type"],
            "function_name": self.execution_context["function_name"],
            "module_path": self.execution_context["module_path"],
            "environment": self.execution_context["environment"],
            "hostname": self.execution_context["hostname"],
            "process_id": self.execution_context["process_id"],
            "standard_id": self.standard_applied["standard_id"],
            "standard_version": self.standard_applied["standard_version"],
            "standard_checksum": self.standard_applied["standard_checksum"],
            "standard_path": self.standard_applied["standard_path"],
            "data_row_count": self.data_fingerprint["row_count"],
            "data_column_count": self.data_fingerprint["column_count"],
            "data_columns": json.dumps(self.data_fingerprint["columns"]),
            "data_checksum": self.data_fingerprint["data_checksum"],
            "overall_score": self.assessment_results["overall_score"],
            "required_score": self.assessment_results["required_score"],
            "passed": "TRUE" if self.assessment_results["passed"] else "FALSE",
            "execution_decision": self.assessment_results["execution_decision"],
            "failure_mode": self.action_taken["failure_mode"],
            "function_executed": (
                "TRUE" if self.action_taken["function_executed"] else "FALSE"
            ),
            "assessment_duration_ms": self.performance_metrics[
                "assessment_duration_ms"
            ],
            "rows_per_second": self.performance_metrics["rows_per_second"],
            "cache_used": "TRUE" if self.performance_metrics["cache_used"] else "FALSE",
            "execution_id": getattr(self, "execution_id", ""),
            "prompt_id": getattr(self, "prompt_id", ""),
            "response_id": getattr(self, "response_id", ""),
        }

        # Dimension records for adri_dimension_scores
        dimension_records = []
        dimension_scores_dict = self.assessment_results.get("dimension_scores", {})
        if isinstance(dimension_scores_dict, dict):
            for dim_name, dim_score in dimension_scores_dict.items():
                dimension_records.append(
                    {
                        "assessment_id": self.assessment_id,
                        "dimension_name": dim_name,
                        "dimension_score": dim_score,
                        "dimension_passed": "TRUE" if dim_score > 15 else "FALSE",
                        "issues_found": self._count_dimension_issues(dim_name),
                        "details": json.dumps(
                            {
                                "score": dim_score,
                                "max_score": 20,
                                "percentage": (dim_score / 20) * 100,
                            }
                        ),
                    }
                )

        # Failed validation records for adri_failed_validations
        failed_validation_records = []
        failed_checks_list = self.assessment_results.get("failed_checks", [])
        if isinstance(failed_checks_list, list):
            for idx, check in enumerate(failed_checks_list):
                failed_validation_records.append(
                    {
                        "assessment_id": self.assessment_id,
                        "validation_id": f"val_{idx:03d}",
                        "dimension": check.get("dimension", "unknown"),
                        "field_name": check.get("field", ""),
                        # Support both "issue_type" and "issue" keys for compatibility
                        "issue_type": check.get("issue_type")
                        or check.get("issue", "unknown"),
                        "affected_rows": check.get("affected_rows", 0),
                        "affected_percentage": check.get("affected_percentage", 0.0),
                        "sample_failures": json.dumps(check.get("samples", [])),
                        "remediation": check.get("remediation", ""),
                        "severity": check.get("severity", ""),
                        "auto_fix_available": check.get("auto_fix_available", False),
                    }
                )

        return {
            "main_record": main_record,
            "dimension_records": dimension_records,
            "failed_validation_records": failed_validation_records,
        }


class LocalLogger:
    """Local JSONL-based audit logger for ADRI assessments.

    This logger writes audit logs exclusively in JSONL format (JSON Lines) to three
    separate files in the configured audit log directory:
    - adri_assessment_logs.jsonl - Main assessment records
    - adri_dimension_scores.jsonl - Dimension scores per assessment
    - adri_failed_validations.jsonl - Failed validation details

    All records use native JSON types (booleans are true/false, not strings) and
    include a write_seq field for stable ordering. CSV format is no longer supported.

    Formerly known as CSVAuditLogger - now writes JSONL format only.
    """

    # Define field names for each dataset
    ASSESSMENT_LOG_HEADERS = [
        "assessment_id",
        "timestamp",
        "adri_version",
        "assessment_type",
        "function_name",
        "module_path",
        "environment",
        "hostname",
        "process_id",
        "standard_id",
        "standard_version",
        "standard_checksum",
        "standard_path",
        "data_row_count",
        "data_column_count",
        "data_columns",
        "data_checksum",
        "overall_score",
        "required_score",
        "passed",
        "execution_decision",
        "failure_mode",
        "function_executed",
        "assessment_duration_ms",
        "rows_per_second",
        "cache_used",
        "execution_id",
        "prompt_id",
        "response_id",
    ]

    DIMENSION_SCORE_HEADERS = [
        "assessment_id",
        "dimension_name",
        "dimension_score",
        "dimension_passed",
        "issues_found",
        "details",
    ]

    FAILED_VALIDATION_HEADERS = [
        "assessment_id",
        "validation_id",
        "dimension",
        "field_name",
        "issue_type",
        "affected_rows",
        "affected_percentage",
        "sample_failures",
        "remediation",
        "severity",
        "auto_fix_available",
    ]

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize the local CSV audit logger with configuration.

        Args:
            config: Configuration dictionary with keys:
                - enabled: Whether audit logging is enabled
                - log_dir: Directory for log files
                - log_prefix: Prefix for log files (default: 'adri')
                - log_level: Logging level (INFO, DEBUG, ERROR)
                - include_data_samples: Whether to include data samples
                - max_log_size_mb: Maximum log file size before rotation
                - sync_writes: Whether to flush after each write (default: True)
        """
        config = config or {}

        self.enabled = config.get("enabled", False)
        # Accept both log_dir and log_location for backward compatibility
        log_path = config.get("log_dir") or config.get("log_location", "./logs")
        # Extract directory from log_location if it includes filename
        if "/" in str(log_path) and str(log_path).endswith((".jsonl", ".log", ".csv")):
            log_path = str(Path(log_path).parent)
        self.log_dir = Path(log_path)
        self.log_prefix = config.get("log_prefix", "adri")
        self.log_level = config.get("log_level", "INFO")
        self.include_data_samples = config.get("include_data_samples", True)
        self.max_log_size_mb = config.get("max_log_size_mb", 100)
        self.sync_writes = config.get("sync_writes", True)

        # File paths for the three JSONL files
        self.assessment_log_path = (
            self.log_dir / f"{self.log_prefix}_assessment_logs.jsonl"
        )
        self.dimension_score_path = (
            self.log_dir / f"{self.log_prefix}_dimension_scores.jsonl"
        )
        self.failed_validation_path = (
            self.log_dir / f"{self.log_prefix}_failed_validations.jsonl"
        )

        # File paths for reasoning JSONL files (managed by ReasoningLogger)
        self.reasoning_prompts_path = (
            self.log_dir / f"{self.log_prefix}_reasoning_prompts.jsonl"
        )
        self.reasoning_responses_path = (
            self.log_dir / f"{self.log_prefix}_reasoning_responses.jsonl"
        )

        # Write sequence tracking for stable ordering
        self.write_seq_file = self.log_dir / f"{self.log_prefix}_write_seq.txt"
        self.write_seq_counter = 0

        # Thread safety
        self._lock = threading.Lock()

        # Optional Verodat logger for external integration
        self.verodat_config: dict[str, Any] | None = None

        # Initialize JSONL files and load write sequence if enabled
        if self.enabled:
            self._initialize_jsonl_files()
            self._load_write_seq()

    def _initialize_jsonl_files(self) -> None:
        """Initialize JSONL files (create empty files if they don't exist)."""
        with self._lock:
            # Ensure log directory exists
            self.log_dir.mkdir(parents=True, exist_ok=True)

            # Initialize assessment log file (JSONL doesn't need headers)
            if not self.assessment_log_path.exists():
                self.assessment_log_path.touch()

            # Initialize dimension score file
            if not self.dimension_score_path.exists():
                self.dimension_score_path.touch()

            # Initialize failed validation file
            if not self.failed_validation_path.exists():
                self.failed_validation_path.touch()

    def _load_write_seq(self) -> None:
        """Load write sequence counter from persistent file."""
        with self._lock:
            if self.write_seq_file.exists():
                try:
                    with open(self.write_seq_file, encoding="utf-8") as f:
                        self.write_seq_counter = int(f.read().strip())
                except (ValueError, OSError):
                    self.write_seq_counter = 0
            else:
                self.write_seq_counter = 0

    def _get_next_write_seq(self) -> int:
        """Get next write sequence number and persist it (must be called with lock held)."""
        self.write_seq_counter += 1
        # Persist to file for continuation across restarts
        try:
            with open(self.write_seq_file, "w", encoding="utf-8") as f:
                f.write(str(self.write_seq_counter))
                if self.sync_writes:
                    f.flush()
                    os.fsync(f.fileno())
        except OSError:
            # If write fails, counter is still in memory
            pass
        return self.write_seq_counter

    def _write_with_flush(self, file_handle, data: str) -> None:
        """Write data with immediate flush when sync_writes is enabled."""
        file_handle.write(data)
        if self.sync_writes:
            file_handle.flush()
            os.fsync(file_handle.fileno())

    def log_assessment(
        self,
        assessment_result: Any,
        execution_context: dict[str, Any],
        data_info: dict[str, Any] | None = None,
        performance_metrics: dict[str, Any] | None = None,
        failed_checks: list[dict[str, Any]] | None = None,
        execution_id: str | None = None,
        prompt_id: str | None = None,
        response_id: str | None = None,
    ) -> AuditRecord | None:
        """
        Log an assessment directly to JSONL files.

        Args:
            assessment_result: The assessment result object
            execution_context: Context about the function execution
            data_info: Information about the data assessed
            performance_metrics: Performance metrics
            failed_checks: List of failed validation checks
            execution_id: Optional workflow execution ID for linking
            prompt_id: Optional reasoning prompt ID for linking
            response_id: Optional reasoning response ID for linking

        Returns:
            AuditRecord if logging is enabled, None otherwise
        """
        if not self.enabled:
            return None

        # Use pre-generated assessment ID from result if available, otherwise
        # generate one
        timestamp = datetime.now()
        assessment_id = getattr(assessment_result, "assessment_id", None)
        if not assessment_id:
            # Fallback: generate assessment ID if not present (backward compatibility)
            assessment_id = (
                f"adri_{timestamp.strftime('%Y%m%d_%H%M%S')}_{os.urandom(3).hex()}"
            )

        # Create audit record
        record = AuditRecord(
            assessment_id=assessment_id, timestamp=timestamp, adri_version=__version__
        )

        # Update execution context
        record.execution_context.update(execution_context)
        if "environment" not in execution_context:
            record.execution_context["environment"] = os.environ.get(
                "ADRI_ENV", "PRODUCTION"
            )

        # Update standard information
        if hasattr(assessment_result, "standard_id"):
            record.standard_applied["standard_id"] = (
                assessment_result.standard_id or "unknown"
            )
        if hasattr(assessment_result, "standard_path"):
            record.standard_applied["standard_path"] = (
                assessment_result.standard_path or ""
            )

        # Update data fingerprint
        if data_info:
            record.data_fingerprint.update(
                {
                    k: v
                    for k, v in data_info.items()
                    if k in ["row_count", "column_count", "columns", "data_checksum"]
                }
            )

            # Calculate data checksum if not provided
            if not record.data_fingerprint["data_checksum"] and data_info.get(
                "row_count"
            ):
                checksum_str = (
                    f"{data_info.get('row_count')}_{data_info.get('column_count')}"
                )
                record.data_fingerprint["data_checksum"] = hashlib.sha256(
                    checksum_str.encode()
                ).hexdigest()[:16]

        # Update assessment results
        if hasattr(assessment_result, "overall_score"):
            record.assessment_results["overall_score"] = assessment_result.overall_score

        if hasattr(assessment_result, "passed"):
            record.assessment_results["passed"] = assessment_result.passed
            record.assessment_results["execution_decision"] = (
                "ALLOWED" if assessment_result.passed else "BLOCKED"
            )
            record.action_taken["decision"] = (
                "ALLOW" if assessment_result.passed else "BLOCK"
            )
            record.action_taken["function_executed"] = assessment_result.passed

        # Process dimension scores
        if hasattr(assessment_result, "dimension_scores"):
            dimension_scores = {}
            for dim_name, dim_obj in assessment_result.dimension_scores.items():
                if hasattr(dim_obj, "score"):
                    dimension_scores[dim_name] = dim_obj.score
                else:
                    dimension_scores[dim_name] = 0.0
            record.assessment_results["dimension_scores"] = dimension_scores

        # Add failed checks
        if failed_checks:
            record.assessment_results["failed_checks"] = failed_checks

        # Update performance metrics
        if performance_metrics:
            for key, value in performance_metrics.items():
                if key in record.performance_metrics:
                    record.performance_metrics[key] = value
                elif (
                    key == "duration_ms"
                    and "assessment_duration_ms" in record.performance_metrics
                ):
                    record.performance_metrics["assessment_duration_ms"] = value

            # Calculate rows per second if not provided
            if (
                performance_metrics.get("duration_ms")
                and data_info
                and data_info.get("row_count")
                and "rows_per_second" not in performance_metrics
            ):
                duration_seconds = performance_metrics["duration_ms"] / 1000.0
                if duration_seconds > 0:
                    record.performance_metrics["rows_per_second"] = (
                        data_info["row_count"] / duration_seconds
                    )

        # Store workflow and reasoning linking IDs
        record.execution_id = execution_id or ""
        record.prompt_id = prompt_id or ""
        record.response_id = response_id or ""

        # Write to JSONL files
        self._write_to_jsonl_files(record)

        return record

    def _write_to_jsonl_files(self, record: AuditRecord) -> None:
        """Write audit record to the three JSONL files."""
        verodat_data = record.to_verodat_format()

        with self._lock:
            # Get next write sequence
            write_seq = self._get_next_write_seq()

            # Check for file rotation
            self._check_rotation()

            # Write main record to assessment log as JSONL
            with open(self.assessment_log_path, "a", encoding="utf-8") as f:
                # Convert string boolean values back to actual booleans for JSONL
                main_record = verodat_data["main_record"].copy()
                main_record["write_seq"] = write_seq
                main_record["passed"] = main_record["passed"] == "TRUE"
                main_record["function_executed"] = (
                    main_record["function_executed"] == "TRUE"
                )
                main_record["cache_used"] = main_record["cache_used"] == "TRUE"
                # Convert JSON string back to list for data_columns
                if isinstance(main_record.get("data_columns"), str):
                    try:
                        main_record["data_columns"] = json.loads(
                            main_record["data_columns"]
                        )
                    except (json.JSONDecodeError, TypeError):
                        main_record["data_columns"] = []

                self._write_with_flush(
                    f, json.dumps(main_record, default=str, ensure_ascii=False) + "\n"
                )

            # Write dimension records as JSONL
            if verodat_data["dimension_records"]:
                with open(self.dimension_score_path, "a", encoding="utf-8") as f:
                    for dim_record in verodat_data["dimension_records"]:
                        # Convert string boolean back to actual boolean
                        dim_record_copy = dim_record.copy()
                        dim_record_copy["write_seq"] = write_seq
                        dim_record_copy["dimension_passed"] = (
                            dim_record["dimension_passed"] == "TRUE"
                        )
                        # Convert JSON string back to dict for details
                        if isinstance(dim_record_copy.get("details"), str):
                            try:
                                dim_record_copy["details"] = json.loads(
                                    dim_record_copy["details"]
                                )
                            except (json.JSONDecodeError, TypeError):
                                dim_record_copy["details"] = {}

                        self._write_with_flush(
                            f,
                            json.dumps(dim_record_copy, default=str, ensure_ascii=False)
                            + "\n",
                        )

            # Write failed validation records as JSONL
            if verodat_data["failed_validation_records"]:
                with open(self.failed_validation_path, "a", encoding="utf-8") as f:
                    for val_record in verodat_data["failed_validation_records"]:
                        # Convert JSON string back to list for sample_failures
                        val_record_copy = val_record.copy()
                        val_record_copy["write_seq"] = write_seq
                        if isinstance(val_record_copy.get("sample_failures"), str):
                            try:
                                val_record_copy["sample_failures"] = json.loads(
                                    val_record_copy["sample_failures"]
                                )
                            except (json.JSONDecodeError, TypeError):
                                val_record_copy["sample_failures"] = []

                        self._write_with_flush(
                            f,
                            json.dumps(val_record_copy, default=str, ensure_ascii=False)
                            + "\n",
                        )

    def _check_rotation(self) -> None:
        """Check if log files need rotation."""
        import time

        for file_path in [
            self.assessment_log_path,
            self.dimension_score_path,
            self.failed_validation_path,
        ]:
            if not file_path.exists():
                continue

            # Get file size in MB
            file_size_mb = file_path.stat().st_size / (1024 * 1024)

            if file_size_mb >= self.max_log_size_mb:
                # Rotate log file with Windows-safe handling
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                rotated_path = file_path.with_suffix(f".{timestamp}.jsonl")

                # Windows-safe file rotation
                try:
                    # Ensure unique filename to avoid conflicts
                    counter = 0
                    original_rotated_path = rotated_path
                    while rotated_path.exists():
                        counter += 1
                        rotated_path = original_rotated_path.with_suffix(
                            f".{timestamp}_{counter:03d}.jsonl"
                        )

                    # Small delay to ensure file handles are released on Windows
                    time.sleep(0.01)
                    file_path.rename(rotated_path)
                except (OSError, PermissionError):
                    # If rotation fails on Windows, continue without rotating
                    # This prevents blocking the logging process
                    continue

                # Recreate empty JSONL file
                try:
                    file_path.touch()
                except (OSError, PermissionError):
                    # If recreation fails, continue - file will be recreated on next
                    # write
                    pass

    def get_log_files(self) -> dict[str, Path]:
        """Get the paths to the current log files."""
        return {
            "assessment_logs": self.assessment_log_path,
            "dimension_scores": self.dimension_score_path,
            "failed_validations": self.failed_validation_path,
            "reasoning_prompts": self.reasoning_prompts_path,
            "reasoning_responses": self.reasoning_responses_path,
        }

    def to_verodat_format(self, log_type: str) -> dict[str, Any]:
        """
        Export logs in Verodat-compatible format with headers and rows.

        Args:
            log_type: Type of log to export ("assessment_logs", "dimension_scores", "failed_validations")

        Returns:
            Dictionary with "data" containing header and rows arrays
        """
        # Map log type to file path
        log_file_map = {
            "assessment_logs": self.assessment_log_path,
            "dimension_scores": self.dimension_score_path,
            "failed_validations": self.failed_validation_path,
        }

        if log_type not in log_file_map:
            raise ValueError(
                f"Invalid log_type: {log_type}. Must be one of {list(log_file_map.keys())}"
            )

        log_file = log_file_map[log_type]

        if not log_file.exists():
            # Return empty structure if file doesn't exist
            return {"data": [{"header": []}, {"rows": []}]}

        # Read all JSONL records
        records = []
        with open(log_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        if not records:
            return {"data": [{"header": []}, {"rows": []}]}

        # Build header from first record's keys
        first_record = records[0]
        header = []
        for key in first_record.keys():
            # Determine type based on value
            value = first_record[key]
            if isinstance(value, bool):
                field_type = "string"  # Verodat uses string for booleans
            elif isinstance(value, int):
                field_type = "integer"
            elif isinstance(value, float):
                field_type = "number"
            elif isinstance(value, list):
                field_type = "string"  # Arrays stored as JSON strings
            elif isinstance(value, dict):
                field_type = "string"  # Objects stored as JSON strings
            else:
                field_type = "string"

            header.append({"name": key, "type": field_type})

        # Build rows - convert each record to array of values matching header order
        rows = []
        for record in records:
            row = []
            for header_field in header:
                key = header_field["name"]
                value = record.get(key)

                # Convert types for Verodat format
                if isinstance(value, bool):
                    row.append("TRUE" if value else "FALSE")
                elif isinstance(value, (list, dict)):
                    row.append(json.dumps(value))
                elif value is None:
                    row.append("")
                else:
                    row.append(value)

            rows.append(row)

        return {"data": [{"header": header}, {"rows": rows}]}

    def clear_logs(self) -> None:
        """Clear all log files (useful for testing)."""
        if not self.enabled:
            return

        with self._lock:
            for file_path in [
                self.assessment_log_path,
                self.dimension_score_path,
                self.failed_validation_path,
            ]:
                if file_path.exists():
                    file_path.unlink()

            # Reinitialize JSONL files
            self._initialize_jsonl_files()


# Helper function for backward compatibility
def log_to_jsonl(
    assessment_result: Any,
    execution_context: dict[str, Any],
    data_info: dict[str, Any] | None = None,
    performance_metrics: dict[str, Any] | None = None,
    failed_checks: list[dict[str, Any]] | None = None,
    config: dict[str, Any] | None = None,
) -> AuditRecord | None:
    """
    Log an assessment to JSONL files.

    Args:
        assessment_result: Assessment result object
        execution_context: Execution context information
        data_info: Data information
        performance_metrics: Performance metrics
        failed_checks: Failed validation checks
        config: Logger configuration

    Returns:
        AuditRecord if successful, None otherwise
    """
    logger = LocalLogger(config)
    return logger.log_assessment(
        assessment_result=assessment_result,
        execution_context=execution_context,
        data_info=data_info,
        performance_metrics=performance_metrics,
        failed_checks=failed_checks,
    )


# Backward compatibility aliases - all now write JSONL format
# These aliases are provided for backward compatibility but should be considered deprecated.
# All logging is now JSONL-only. CSV format is no longer supported.
CSVAuditLogger = LocalLogger  # DEPRECATED: Historical name - now uses JSONL format
AuditLoggerCSV = LocalLogger  # DEPRECATED: Historical name - now uses JSONL format
log_to_csv = log_to_jsonl  # DEPRECATED: Historical function name - now writes JSONL


class LogRotator:
    """Stub class for log rotation functionality."""

    def __init__(self, log_directory: str, max_file_size: int, max_files: int):
        """Initialize the log rotator.

        Args:
            log_directory: Directory where logs are stored
            max_file_size: Maximum file size in bytes before rotation
            max_files: Maximum number of log files to keep
        """
        self.log_directory = log_directory
        self.max_file_size = max_file_size
        self.max_files = max_files


# @ADRI_FEATURE_END[logging_local_jsonl]
