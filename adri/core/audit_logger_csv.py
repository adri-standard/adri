"""
Enhanced ADRI Audit Logger Module with CSV Output.

Captures comprehensive audit logs for all ADRI assessments directly in
Verodat-compatible CSV format with three linked datasets.
"""

import csv
import hashlib
import json
import os
import socket
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .verodat_logger import VerodatLogger

from adri.version import __version__


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
            "standard_path": "",
            "standard_checksum": "",
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

    def to_dict(self) -> Dict[str, Any]:
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

    def to_verodat_format(self) -> Dict[str, Any]:
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
                        "issue_type": check.get("issue", "unknown"),
                        "affected_rows": check.get("affected_rows", 0),
                        "affected_percentage": check.get("affected_percentage", 0.0),
                        "sample_failures": json.dumps(check.get("samples", [])),
                        "remediation": check.get("remediation", ""),
                    }
                )

        return {
            "main_record": main_record,
            "dimension_records": dimension_records,
            "failed_validation_records": failed_validation_records,
        }


class CSVAuditLogger:
    """Handles audit logging for ADRI assessments with direct CSV output."""

    # Define CSV headers for each dataset
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
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the CSV audit logger with configuration.

        Args:
            config: Configuration dictionary with keys:
                - enabled: Whether audit logging is enabled
                - log_dir: Directory for log files
                - log_prefix: Prefix for log files (default: 'adri')
                - log_level: Logging level (INFO, DEBUG, ERROR)
                - include_data_samples: Whether to include data samples
                - max_log_size_mb: Maximum log file size before rotation
        """
        config = config or {}

        self.enabled = config.get("enabled", False)
        self.log_dir = Path(config.get("log_dir", "./logs"))
        self.log_prefix = config.get("log_prefix", "adri")
        self.log_level = config.get("log_level", "INFO")
        self.include_data_samples = config.get("include_data_samples", True)
        self.max_log_size_mb = config.get("max_log_size_mb", 100)

        # File paths for the three CSV files
        self.assessment_log_path = (
            self.log_dir / f"{self.log_prefix}_assessment_logs.csv"
        )
        self.dimension_score_path = (
            self.log_dir / f"{self.log_prefix}_dimension_scores.csv"
        )
        self.failed_validation_path = (
            self.log_dir / f"{self.log_prefix}_failed_validations.csv"
        )

        # Thread safety
        self._lock = threading.Lock()

        # Optional Verodat logger for external integration
        self.verodat_logger: Optional["VerodatLogger"] = None

        # Initialize CSV files if enabled
        if self.enabled:
            self._initialize_csv_files()

    def _initialize_csv_files(self) -> None:
        """Initialize CSV files with headers if they don't exist."""
        with self._lock:
            # Ensure log directory exists
            self.log_dir.mkdir(parents=True, exist_ok=True)

            # Initialize assessment log file
            if not self.assessment_log_path.exists():
                with open(self.assessment_log_path, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=self.ASSESSMENT_LOG_HEADERS)
                    writer.writeheader()

            # Initialize dimension score file
            if not self.dimension_score_path.exists():
                with open(self.dimension_score_path, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=self.DIMENSION_SCORE_HEADERS)
                    writer.writeheader()

            # Initialize failed validation file
            if not self.failed_validation_path.exists():
                with open(self.failed_validation_path, "w", newline="") as f:
                    writer = csv.DictWriter(
                        f, fieldnames=self.FAILED_VALIDATION_HEADERS
                    )
                    writer.writeheader()

    def log_assessment(
        self,
        assessment_result: Any,
        execution_context: Dict[str, Any],
        data_info: Optional[Dict[str, Any]] = None,
        performance_metrics: Optional[Dict[str, Any]] = None,
        failed_checks: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[AuditRecord]:
        """
        Log an assessment directly to CSV files.

        Args:
            assessment_result: The assessment result object
            execution_context: Context about the function execution
            data_info: Information about the data assessed
            performance_metrics: Performance metrics
            failed_checks: List of failed validation checks

        Returns:
            AuditRecord if logging is enabled, None otherwise
        """
        if not self.enabled:
            return None

        # Generate assessment ID
        timestamp = datetime.now()
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

        # Write to CSV files
        self._write_to_csv_files(record)

        return record

    def _write_to_csv_files(self, record: AuditRecord) -> None:
        """Write audit record to the three CSV files."""
        verodat_data = record.to_verodat_format()

        with self._lock:
            # Check for file rotation
            self._check_rotation()

            # Write main record to assessment log
            with open(self.assessment_log_path, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.ASSESSMENT_LOG_HEADERS)
                writer.writerow(verodat_data["main_record"])

            # Write dimension records
            if verodat_data["dimension_records"]:
                with open(self.dimension_score_path, "a", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=self.DIMENSION_SCORE_HEADERS)
                    writer.writerows(verodat_data["dimension_records"])

            # Write failed validation records
            if verodat_data["failed_validation_records"]:
                with open(self.failed_validation_path, "a", newline="") as f:
                    writer = csv.DictWriter(
                        f, fieldnames=self.FAILED_VALIDATION_HEADERS
                    )
                    writer.writerows(verodat_data["failed_validation_records"])

    def _check_rotation(self) -> None:
        """Check if log files need rotation."""
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
                # Rotate log file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                rotated_path = file_path.with_suffix(f".{timestamp}.csv")
                file_path.rename(rotated_path)

                # Recreate file with headers
                if file_path == self.assessment_log_path:
                    headers = self.ASSESSMENT_LOG_HEADERS
                elif file_path == self.dimension_score_path:
                    headers = self.DIMENSION_SCORE_HEADERS
                else:
                    headers = self.FAILED_VALIDATION_HEADERS

                with open(file_path, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()

    def get_log_files(self) -> Dict[str, Path]:
        """Get the paths to the current log files."""
        return {
            "assessment_logs": self.assessment_log_path,
            "dimension_scores": self.dimension_score_path,
            "failed_validations": self.failed_validation_path,
        }

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

            # Reinitialize with headers (without re-acquiring lock)
            # Ensure log directory exists
            self.log_dir.mkdir(parents=True, exist_ok=True)

            # Initialize assessment log file
            if not self.assessment_log_path.exists():
                with open(self.assessment_log_path, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=self.ASSESSMENT_LOG_HEADERS)
                    writer.writeheader()

            # Initialize dimension score file
            if not self.dimension_score_path.exists():
                with open(self.dimension_score_path, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=self.DIMENSION_SCORE_HEADERS)
                    writer.writeheader()

            # Initialize failed validation file
            if not self.failed_validation_path.exists():
                with open(self.failed_validation_path, "w", newline="") as f:
                    writer = csv.DictWriter(
                        f, fieldnames=self.FAILED_VALIDATION_HEADERS
                    )
                    writer.writeheader()


# Add alias for backward compatibility
AuditLoggerCSV = CSVAuditLogger
