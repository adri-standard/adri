"""
ADRI Workflow Logging - JSONL-based Workflow Execution and Data Provenance Logging.

Logs workflow execution context and data provenance for compliance-grade audit trails
in workflow orchestration scenarios.
"""

import json
import os
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class WorkflowExecution:
    """Represents a workflow execution record."""

    execution_id: str
    run_id: str
    workflow_id: str
    workflow_version: str
    step_id: str
    step_sequence: int
    run_at_utc: str
    data_source_type: str
    timestamp: str
    assessment_id: str
    data_checksum: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV writing."""
        return {
            "execution_id": self.execution_id,
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "workflow_version": self.workflow_version,
            "step_id": self.step_id,
            "step_sequence": self.step_sequence,
            "run_at_utc": self.run_at_utc,
            "data_source_type": self.data_source_type or "",
            "timestamp": self.timestamp,
            "assessment_id": self.assessment_id,
            "data_checksum": self.data_checksum,
        }


@dataclass
class DataProvenance:
    """Represents data provenance record."""

    execution_id: str
    source_type: str
    timestamp: str

    # Verodat-specific fields
    verodat_query_id: Optional[int] = None
    verodat_account_id: Optional[int] = None
    verodat_workspace_id: Optional[int] = None
    verodat_run_at_utc: Optional[str] = None
    verodat_query_sql: Optional[str] = None

    # File-specific fields
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    file_hash: Optional[str] = None

    # API-specific fields
    api_endpoint: Optional[str] = None
    api_http_method: Optional[str] = None
    api_response_hash: Optional[str] = None

    # Previous step fields
    previous_step_id: Optional[str] = None
    previous_execution_id: Optional[str] = None

    # Common fields
    data_retrieved_at_utc: Optional[str] = None
    record_count: Optional[int] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV writing."""
        return {
            "execution_id": self.execution_id,
            "source_type": self.source_type,
            "verodat_query_id": self.verodat_query_id or "",
            "verodat_account_id": self.verodat_account_id or "",
            "verodat_workspace_id": self.verodat_workspace_id or "",
            "verodat_run_at_utc": self.verodat_run_at_utc or "",
            "verodat_query_sql": self.verodat_query_sql or "",
            "file_path": self.file_path or "",
            "file_size_bytes": self.file_size_bytes or "",
            "file_hash": self.file_hash or "",
            "api_endpoint": self.api_endpoint or "",
            "api_http_method": self.api_http_method or "",
            "api_response_hash": self.api_response_hash or "",
            "previous_step_id": self.previous_step_id or "",
            "previous_execution_id": self.previous_execution_id or "",
            "data_retrieved_at_utc": self.data_retrieved_at_utc or "",
            "record_count": self.record_count or "",
            "notes": self.notes or "",
            "timestamp": self.timestamp,
        }


class WorkflowLogger:
    """JSONL-based logger for workflow execution metadata and data provenance."""

    # Field names for reference (no headers needed in JSONL files)
    EXECUTION_LOG_HEADERS = [
        "execution_id",
        "run_id",
        "workflow_id",
        "workflow_version",
        "step_id",
        "step_sequence",
        "run_at_utc",
        "data_source_type",
        "timestamp",
        "assessment_id",
        "data_checksum",
    ]

    # Field names for reference (no headers needed in JSONL files)
    PROVENANCE_LOG_HEADERS = [
        "execution_id",
        "source_type",
        "verodat_query_id",
        "verodat_account_id",
        "verodat_workspace_id",
        "verodat_run_at_utc",
        "verodat_query_sql",
        "file_path",
        "file_size_bytes",
        "file_hash",
        "api_endpoint",
        "api_http_method",
        "api_response_hash",
        "previous_step_id",
        "previous_execution_id",
        "data_retrieved_at_utc",
        "record_count",
        "notes",
        "timestamp",
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the workflow logger with configuration.

        Args:
            config: Configuration dictionary with keys:
                - enabled: Whether workflow logging is enabled
                - log_dir: Directory for log files
                - log_prefix: Prefix for log files (default: 'adri')
                - max_log_size_mb: Maximum log file size before rotation
        """
        config = config or {}

        self.enabled = config.get("enabled", False)
        log_path = config.get("log_dir") or config.get("log_location", "./logs")
        # Extract directory from log_location if it includes filename
        if "/" in str(log_path) and str(log_path).endswith((".jsonl", ".log", ".csv")):
            log_path = str(Path(log_path).parent)
        self.log_dir = Path(log_path)
        self.log_prefix = config.get("log_prefix", "adri")
        self.max_log_size_mb = config.get("max_log_size_mb", 100)

        # File paths for JSONL files
        self.execution_log_path = (
            self.log_dir / f"{self.log_prefix}_workflow_executions.jsonl"
        )
        self.provenance_log_path = (
            self.log_dir / f"{self.log_prefix}_data_provenance.jsonl"
        )

        # Thread safety
        self._lock = threading.Lock()

        # Initialize JSONL files if enabled
        if self.enabled:
            self._initialize_jsonl_files()

    def _initialize_jsonl_files(self) -> None:
        """Initialize JSONL files if they don't exist."""
        with self._lock:
            # Ensure log directory exists
            self.log_dir.mkdir(parents=True, exist_ok=True)

            # Initialize execution log file (empty JSONL file, no headers)
            if not self.execution_log_path.exists():
                self.execution_log_path.touch()

            # Initialize provenance log file (empty JSONL file, no headers)
            if not self.provenance_log_path.exists():
                self.provenance_log_path.touch()

    def _generate_execution_id(self) -> str:
        """Generate unique execution ID."""
        timestamp = datetime.now()
        return f"exec_{timestamp.strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"

    def log_workflow_execution(
        self,
        workflow_context: Dict[str, Any],
        assessment_id: str,
        data_checksum: str,
    ) -> str:
        """
        Log workflow execution record.

        Args:
            workflow_context: Workflow context dictionary (validated against adri_execution_standard)
            assessment_id: ID of the associated assessment
            data_checksum: Checksum of the data assessed

        Returns:
            Generated execution_id for linking to other logs
        """
        if not self.enabled:
            return ""

        # Generate unique execution ID
        execution_id = self._generate_execution_id()
        timestamp = datetime.now().isoformat()

        # Create execution record
        execution = WorkflowExecution(
            execution_id=execution_id,
            run_id=workflow_context.get("run_id", ""),
            workflow_id=workflow_context.get("workflow_id", ""),
            workflow_version=workflow_context.get("workflow_version", ""),
            step_id=workflow_context.get("step_id", ""),
            step_sequence=workflow_context.get("step_sequence", 0),
            run_at_utc=workflow_context.get("run_at_utc", ""),
            data_source_type=workflow_context.get("data_source_type", ""),
            timestamp=timestamp,
            assessment_id=assessment_id,
            data_checksum=data_checksum,
        )

        # Write to JSONL
        with self._lock:
            self._check_rotation()
            with open(self.execution_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(execution.to_dict()) + "\n")

        return execution_id

    def log_data_provenance(
        self, execution_id: str, data_provenance: Dict[str, Any]
    ) -> None:
        """
        Log data provenance record.

        Args:
            execution_id: Execution ID to link provenance to
            data_provenance: Data provenance dictionary (validated against adri_provenance_standard)
        """
        if not self.enabled:
            return

        timestamp = datetime.now().isoformat()

        # Create provenance record
        provenance = DataProvenance(
            execution_id=execution_id,
            source_type=data_provenance.get("source_type", ""),
            timestamp=timestamp,
            # Verodat fields
            verodat_query_id=data_provenance.get("verodat_query_id"),
            verodat_account_id=data_provenance.get("verodat_account_id"),
            verodat_workspace_id=data_provenance.get("verodat_workspace_id"),
            verodat_run_at_utc=data_provenance.get("verodat_run_at_utc"),
            verodat_query_sql=data_provenance.get("verodat_query_sql"),
            # File fields
            file_path=data_provenance.get("file_path"),
            file_size_bytes=data_provenance.get("file_size_bytes"),
            file_hash=data_provenance.get("file_hash"),
            # API fields
            api_endpoint=data_provenance.get("api_endpoint"),
            api_http_method=data_provenance.get("api_http_method"),
            api_response_hash=data_provenance.get("api_response_hash"),
            # Previous step fields
            previous_step_id=data_provenance.get("previous_step_id"),
            previous_execution_id=data_provenance.get("previous_execution_id"),
            # Common fields
            data_retrieved_at_utc=data_provenance.get("data_retrieved_at_utc"),
            record_count=data_provenance.get("record_count"),
            notes=data_provenance.get("notes"),
        )

        # Write to JSONL
        with self._lock:
            self._check_rotation()
            with open(self.provenance_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(provenance.to_dict()) + "\n")

    def _check_rotation(self) -> None:
        """Check if log files need rotation."""
        import time

        for file_path in [self.execution_log_path, self.provenance_log_path]:
            if not file_path.exists():
                continue

            # Get file size in MB
            file_size_mb = file_path.stat().st_size / (1024 * 1024)

            if file_size_mb >= self.max_log_size_mb:
                # Rotate log file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                rotated_path = file_path.with_suffix(f".{timestamp}.jsonl")

                try:
                    # Ensure unique filename
                    counter = 0
                    original_rotated_path = rotated_path
                    while rotated_path.exists():
                        counter += 1
                        rotated_path = original_rotated_path.with_suffix(
                            f".{timestamp}_{counter:03d}.jsonl"
                        )

                    # Small delay for Windows
                    time.sleep(0.01)
                    file_path.rename(rotated_path)
                except (OSError, PermissionError):
                    # Continue without rotating on Windows if file is locked
                    continue

                # Recreate empty JSONL file (no headers needed)
                try:
                    file_path.touch()
                except (OSError, PermissionError):
                    # File will be recreated on next write
                    pass

    def get_log_files(self) -> Dict[str, Path]:
        """Get the paths to the current log files."""
        return {
            "workflow_executions": self.execution_log_path,
            "data_provenance": self.provenance_log_path,
        }

    def clear_logs(self) -> None:
        """Clear all log files (useful for testing)."""
        if not self.enabled:
            return

        with self._lock:
            for file_path in [self.execution_log_path, self.provenance_log_path]:
                if file_path.exists():
                    file_path.unlink()

            # Reinitialize empty JSONL files (inline to avoid deadlock)
            self.log_dir.mkdir(parents=True, exist_ok=True)

            # Initialize execution log file (empty JSONL file, no headers)
            self.execution_log_path.touch()

            # Initialize provenance log file (empty JSONL file, no headers)
            self.provenance_log_path.touch()
