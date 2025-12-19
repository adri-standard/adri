"""JSONL audit log reader for ADRI workflow orchestration.

This module provides the ADRILogReader class for reading JSONL-formatted
audit logs from ADRI's standard log directory structure.

The reader supports:
- Reading assessment log records with native JSON types
- Filtering and querying log records
- Reading linked dimension scores and failed validations
- Sorted reading based on write_seq field for stable ordering
"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypedDict


class AssessmentLogRecord(TypedDict):
    """Assessment log record structure from JSONL format."""

    assessment_id: str
    timestamp: str
    adri_version: str
    assessment_type: str
    function_name: str
    module_path: str
    environment: str
    hostname: str
    process_id: int
    standard_id: str
    standard_version: str
    standard_checksum: str
    standard_path: str
    data_row_count: int
    data_column_count: int
    data_columns: list[str]
    data_checksum: str
    overall_score: float
    required_score: float
    passed: bool
    execution_decision: str
    failure_mode: str
    function_executed: bool
    assessment_duration_ms: int
    rows_per_second: float
    cache_used: bool
    execution_id: str
    prompt_id: str
    response_id: str
    write_seq: int


class DimensionScoreRecord(TypedDict):
    """Dimension score record structure from JSONL format."""

    assessment_id: str
    dimension_name: str
    dimension_score: float
    dimension_passed: bool
    issues_found: int
    details: dict[str, Any]
    write_seq: int


class FailedValidationRecord(TypedDict):
    """Failed validation record structure from JSONL format."""

    assessment_id: str
    validation_id: str
    dimension: str
    field_name: str
    issue_type: str
    affected_rows: int
    affected_percentage: float
    sample_failures: list[Any]
    remediation: str
    write_seq: int


class ADRILogReader:
    """Read and parse JSONL audit logs for workflow orchestration.

    This class provides methods to read ADRI's JSONL-formatted audit logs
    from the standard log directory structure. It supports reading:
    - Assessment logs (main records)
    - Dimension scores (per assessment)
    - Failed validations (per assessment)
    - Workflow orchestration queries (latest assessments, filtering by time/ID)

    All records are parsed with native JSON types (booleans, arrays, etc.)
    and sorted by write_seq for stable ordering.

    Workflow Orchestration Support:
        The reader includes methods specifically designed for workflow engines:
        - get_latest_assessment_id(): Quick access to most recent assessment
        - get_assessments_since(timestamp): Time-based filtering
        - read_assessment_by_id(assessment_id): Direct ID lookup

    Example:
        >>> reader = ADRILogReader({"paths": {"audit_logs": "ADRI/dev/audit-logs"}})
        >>> assessments = reader.read_assessment_logs(limit=10)
        >>> for assessment in assessments:
        ...     print(f"Assessment {assessment['assessment_id']}: {assessment['passed']}")
        ...     scores = reader.read_dimension_scores(assessment['assessment_id'])

        >>> # Workflow orchestration example
        >>> latest_id = reader.get_latest_assessment_id()
        >>> recent = reader.get_assessments_since("2025-10-08T12:00:00")

    Thread-safety: This class is read-only and thread-safe for concurrent reads.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize log reader with configuration.

        Args:
            config: Configuration dictionary with 'paths' key containing
                   'audit_logs' path. Defaults to 'ADRI/dev/audit-logs'
                   if not specified.
        """
        # Get log directory from config, with fallback to standard location
        log_dir_str = config.get("paths", {}).get("audit_logs", "ADRI/dev/audit-logs")
        self.log_dir = Path(log_dir_str)

        # Define paths to the three JSONL log files
        self.assessment_log_path = self.log_dir / "adri_assessment_logs.jsonl"
        self.dimension_score_path = self.log_dir / "adri_dimension_scores.jsonl"
        self.failed_validation_path = self.log_dir / "adri_failed_validations.jsonl"

    def read_assessment_logs(
        self,
        limit: int | None = None,
        filter_fn: Callable[[AssessmentLogRecord], bool] | None = None,
    ) -> list[AssessmentLogRecord]:
        """Read assessment log records from JSONL file.

        Reads the assessment log file line by line, parsing each line as JSON.
        Records are sorted by write_seq field for stable ordering. Malformed
        lines are skipped with a warning.

        Args:
            limit: Maximum number of records to return. None for all records.
            filter_fn: Optional function to filter records. Should return True
                      to include a record, False to exclude it.

        Returns:
            List of assessment log records as dictionaries, sorted by write_seq.
            Returns empty list if log file doesn't exist.

        Example:
            >>> # Get last 5 passed assessments
            >>> reader.read_assessment_logs(
            ...     limit=5,
            ...     filter_fn=lambda r: r['passed']
            ... )
        """
        if not self.assessment_log_path.exists():
            return []

        records: list[AssessmentLogRecord] = []

        try:
            with open(self.assessment_log_path, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        record = json.loads(line)

                        # Apply filter if provided
                        if filter_fn and not filter_fn(record):
                            continue

                        records.append(record)

                        # Apply limit if specified
                        if limit and len(records) >= limit:
                            break

                    except json.JSONDecodeError as e:
                        # Skip malformed lines with warning
                        print(
                            f"Warning: Skipping malformed JSON at line {line_num}: {e}"
                        )
                        continue

        except Exception as e:
            print(f"Error reading assessment logs: {e}")
            return []

        # Sort by write_seq for stable ordering
        records.sort(key=lambda r: r.get("write_seq", 0))

        return records

    def read_dimension_scores(self, assessment_id: str) -> list[DimensionScoreRecord]:
        """Read dimension scores for a specific assessment.

        Args:
            assessment_id: The assessment ID to filter by.

        Returns:
            List of dimension score records for the specified assessment,
            sorted by write_seq. Returns empty list if file doesn't exist.
        """
        if not self.dimension_score_path.exists():
            return []

        records: list[DimensionScoreRecord] = []

        try:
            with open(self.dimension_score_path, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        record = json.loads(line)

                        # Filter by assessment_id
                        if record.get("assessment_id") == assessment_id:
                            records.append(record)

                    except json.JSONDecodeError as e:
                        print(
                            f"Warning: Skipping malformed JSON at line {line_num}: {e}"
                        )
                        continue

        except Exception as e:
            print(f"Error reading dimension scores: {e}")
            return []

        # Sort by write_seq for stable ordering
        records.sort(key=lambda r: r.get("write_seq", 0))

        return records

    def read_failed_validations(
        self, assessment_id: str
    ) -> list[FailedValidationRecord]:
        """Read failed validations for a specific assessment.

        Args:
            assessment_id: The assessment ID to filter by.

        Returns:
            List of failed validation records for the specified assessment,
            sorted by write_seq. Returns empty list if file doesn't exist.
        """
        if not self.failed_validation_path.exists():
            return []

        records: list[FailedValidationRecord] = []

        try:
            with open(self.failed_validation_path, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        record = json.loads(line)

                        # Filter by assessment_id
                        if record.get("assessment_id") == assessment_id:
                            records.append(record)

                    except json.JSONDecodeError as e:
                        print(
                            f"Warning: Skipping malformed JSON at line {line_num}: {e}"
                        )
                        continue

        except Exception as e:
            print(f"Error reading failed validations: {e}")
            return []

        # Sort by write_seq for stable ordering
        records.sort(key=lambda r: r.get("write_seq", 0))

        return records

    def get_latest_assessments(self, limit: int = 10) -> list[AssessmentLogRecord]:
        """Get N most recent assessments.

        Convenience method to get the most recent assessments sorted by
        timestamp in descending order (newest first).

        Args:
            limit: Number of recent assessments to return. Default 10.

        Returns:
            List of assessment log records sorted by timestamp descending.
        """
        # Read all assessments
        assessments = self.read_assessment_logs()

        # Sort by timestamp descending (newest first)
        assessments.sort(key=lambda r: r.get("timestamp", ""), reverse=True)

        # Return limited number
        return assessments[:limit]

    # Workflow Orchestration Methods

    def get_latest_assessment_id(self) -> str | None:
        """Get the most recent assessment ID.

        Used by workflow engines to quickly access the ID of the most
        recent assessment without retrieving full records.

        Returns:
            The assessment_id of the most recent assessment, or None if
            no logs exist.

        Example:
            >>> reader = ADRILogReader(config)
            >>> latest_id = reader.get_latest_assessment_id()
            >>> if latest_id:
            ...     assessment = reader.read_assessment_by_id(latest_id)
        """
        latest = self.get_latest_assessments(limit=1)
        if latest:
            return latest[0]["assessment_id"]
        return None

    def get_assessments_since(self, timestamp: str) -> list[AssessmentLogRecord]:
        """Get assessments after a given timestamp.

        Used by workflow engines to retrieve assessments that occurred
        after a specific point in time. Useful for incremental processing
        and monitoring.

        Args:
            timestamp: ISO format timestamp string to filter by
                      (e.g., "2025-10-08T12:00:00")

        Returns:
            List of assessment records with timestamp > provided timestamp,
            sorted by write_seq for stable ordering. Returns empty list
            if no matching assessments found.

        Example:
            >>> reader = ADRILogReader(config)
            >>> recent = reader.get_assessments_since("2025-10-08T12:00:00")
            >>> for assessment in recent:
            ...     print(f"New assessment: {assessment['assessment_id']}")
        """
        # Use read_assessment_logs with filter for timestamps after the provided value
        return self.read_assessment_logs(
            filter_fn=lambda r: r.get("timestamp", "") > timestamp
        )

    def read_assessment_by_id(self, assessment_id: str) -> AssessmentLogRecord | None:
        """Get full assessment details by ID.

        Used by workflow engines to retrieve complete information about
        a specific assessment identified by its ID.

        Args:
            assessment_id: The assessment ID to look up
                          (e.g., "adri_20251008_120000_abc123")

        Returns:
            The assessment record if found, None otherwise.

        Example:
            >>> reader = ADRILogReader(config)
            >>> assessment = reader.read_assessment_by_id("adri_20251008_120000_abc123")
            >>> if assessment:
            ...     print(f"Score: {assessment['overall_score']}")
            ...     print(f"Passed: {assessment['passed']}")
        """
        # Use read_assessment_logs with filter matching the specific ID
        results = self.read_assessment_logs(
            limit=1, filter_fn=lambda r: r.get("assessment_id") == assessment_id
        )
        return results[0] if results else None

    # Property Aliases for Backward Compatibility

    @property
    def assessment_logs_path(self) -> Path:
        """Alias for assessment_log_path for backward compatibility.

        Some workflow engines may use the plural form of the property name.
        This alias ensures compatibility without requiring code changes.

        Returns:
            Path to the assessment logs JSONL file.
        """
        return self.assessment_log_path

    @property
    def dimension_scores_path(self) -> Path:
        """Alias for dimension_score_path for backward compatibility.

        Some workflow engines may use the plural form of the property name.
        This alias ensures compatibility without requiring code changes.

        Returns:
            Path to the dimension scores JSONL file.
        """
        return self.dimension_score_path

    @property
    def failed_validations_path(self) -> Path:
        """Alias for failed_validation_path for backward compatibility.

        Some workflow engines may use the plural form of the property name.
        This alias ensures compatibility without requiring code changes.

        Returns:
            Path to the failed validations JSONL file.
        """
        return self.failed_validation_path
