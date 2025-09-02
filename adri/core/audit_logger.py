"""
ADRI Audit Logger Module.

Captures comprehensive audit logs for all ADRI assessments to support
compliance tracking and integration with Verodat data warehouse.
"""

import hashlib
import json
import os
import socket
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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
                        "issues_found": 0,  # Will be populated from failed_checks
                        "details": "{}",
                    }
                )

        # Failed validation records for adri_failed_validations
        failed_validation_records = []
        failed_checks_list = self.assessment_results.get("failed_checks", [])
        if isinstance(failed_checks_list, list):
            for idx, check in enumerate(failed_checks_list):
                if isinstance(check, dict):
                    failed_validation_records.append(
                        {
                            "assessment_id": self.assessment_id,
                            "validation_id": f"val_{idx:03d}",
                            "dimension": check.get("dimension", "unknown"),
                            "field_name": check.get("field", ""),
                            "issue_type": check.get("issue", "unknown"),
                            "affected_rows": check.get("affected_rows", 0),
                            "affected_percentage": check.get(
                                "affected_percentage", 0.0
                            ),
                            "sample_failures": json.dumps(check.get("samples", [])),
                            "remediation": check.get("remediation", ""),
                        }
                    )

        return {
            "main_record": main_record,
            "dimension_records": dimension_records,
            "failed_validation_records": failed_validation_records,
        }


class AuditLogger:
    """Handles audit logging for ADRI assessments."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the audit logger with configuration.

        Args:
            config: Configuration dictionary with keys:
                - enabled: Whether audit logging is enabled
                - log_location: Path to log file
                - log_level: Logging level (INFO, DEBUG, ERROR)
                - include_data_samples: Whether to include data samples
                - max_log_size_mb: Maximum log file size before rotation
                - batch_mode: Whether to batch records
                - batch_size: Number of records per batch
        """
        config = config or {}

        self.enabled = config.get("enabled", False)
        self.log_location = config.get("log_location", "./logs/adri_audit.jsonl")
        self.log_level = config.get("log_level", "INFO")
        self.include_data_samples = config.get("include_data_samples", True)
        self.max_log_size_mb = config.get("max_log_size_mb", 100)
        self.batch_mode = config.get("batch_mode", False)
        self.batch_size = config.get("batch_size", 100)

        # Thread safety
        self._lock = threading.Lock()
        self._batch: List[AuditRecord] = []

    def log_assessment(
        self,
        assessment_result: Any,
        execution_context: Dict[str, Any],
        data_info: Optional[Dict[str, Any]] = None,
        performance_metrics: Optional[Dict[str, Any]] = None,
        failed_checks: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[AuditRecord]:
        """
        Log an assessment to the audit trail.

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

            # Filter out PII if configured
            if not self.include_data_samples and "sample_data" in data_info:
                # Don't include sample data
                pass

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
            # Update all provided metrics
            for key, value in performance_metrics.items():
                if key in record.performance_metrics:
                    record.performance_metrics[key] = value
                # Handle duration_ms -> assessment_duration_ms mapping
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

        # Write to log file (only if enabled)
        if self.enabled:
            self._write_log(record)

        # Add to batch if in batch mode
        if self.batch_mode:
            with self._lock:
                self._batch.append(record)

        return record

    def _write_log(self, record: AuditRecord) -> None:
        """Write audit record to log file."""
        if not self.log_location:
            return

        with self._lock:
            # Ensure log directory exists
            log_dir = Path(self.log_location).parent
            log_dir.mkdir(parents=True, exist_ok=True)

            # Check log rotation
            self._check_rotation()

            # Write JSON line
            with open(self.log_location, "a") as f:
                f.write(record.to_json() + "\n")

    def _check_rotation(self) -> None:
        """Check if log file needs rotation."""
        if not os.path.exists(self.log_location):
            return

        # Get file size in MB
        file_size_mb = os.path.getsize(self.log_location) / (1024 * 1024)

        if file_size_mb >= self.max_log_size_mb:
            # Rotate log file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rotated_path = f"{self.log_location}.{timestamp}"
            os.rename(self.log_location, rotated_path)

    def get_verodat_batch(self) -> Optional[Dict[str, List[Dict]]]:
        """
        Get a batch of records formatted for Verodat upload.

        Returns:
            Dictionary with main_records, dimension_records, and failed_validation_records
        """
        if not self.batch_mode or len(self._batch) < self.batch_size:
            return None

        with self._lock:
            # Get batch
            batch = self._batch[: self.batch_size]
            self._batch = self._batch[self.batch_size :]

            # Convert to Verodat format
            main_records = []
            dimension_records = []
            failed_validation_records = []

            for record in batch:
                verodat_data = record.to_verodat_format()
                main_records.append(verodat_data["main_record"])
                dimension_records.extend(verodat_data["dimension_records"])
                failed_validation_records.extend(
                    verodat_data["failed_validation_records"]
                )

            return {
                "main_records": main_records,
                "dimension_records": dimension_records,
                "failed_validation_records": failed_validation_records,
            }
