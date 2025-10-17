"""
ADRI Enterprise Logging - Verodat Integration.

Verodat logger for centralized audit logging, migrated from core/verodat_logger.py.
Integrates with Verodat API to upload ADRI assessment audit logs,
using ADRI standards as the schema definition.
"""

import json
import os
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
import yaml

# Clean imports for modular architecture
from .local import AuditRecord


class LogBatch:
    """Stub class for log batch operations."""

    def __init__(self, logs: list = None):
        """Initialize LogBatch with logs."""
        self.logs = logs or []


class APIClient:
    """Stub class for API client operations."""

    def __init__(self, base_url: str = "", api_key: str = ""):
        """Initialize APIClient with connection details."""
        self.base_url = base_url
        self.api_key = api_key


class AuthenticationManager:
    """Stub class for authentication management."""

    def __init__(self, auth_config: dict = None):
        """Initialize AuthenticationManager with configuration."""
        self.auth_config = auth_config or {}


class EnterpriseLogger:
    """
    Enterprise audit logger with Verodat API integration.

    Renamed from VerodatLogger. Provides centralized logging to Verodat
    for enterprise audit trails and compliance requirements.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Verodat logger with configuration.

        Args:
            config: Verodat configuration dictionary
        """
        self.config = config
        self.enabled = config.get("enabled", False)

        # Extract API settings
        self.api_key = self._resolve_env_var(config.get("api_key", ""))
        self.base_url = config.get("base_url", "https://verodat.io/api/v3")
        self.workspace_id = config.get("workspace_id")

        # Batch settings
        batch_settings = config.get("batch_settings", {})
        self.batch_size = batch_settings.get("batch_size", 100)
        # Reduced default from 60s to 5s for faster workflow orchestration
        self.flush_interval = batch_settings.get("flush_interval_seconds", 5)
        self.retry_attempts = batch_settings.get("retry_attempts", 3)
        self.retry_delay = batch_settings.get("retry_delay_seconds", 5)

        # Connection settings
        connection_settings = config.get("connection", {})
        self.timeout = connection_settings.get("timeout_seconds", 30)
        self.verify_ssl = connection_settings.get("verify_ssl", True)

        # Initialize batches
        self._assessment_logs_batch: List[AuditRecord] = []
        self._dimension_scores_batch: List[AuditRecord] = []
        self._failed_validations_batch: List[AuditRecord] = []
        self._batch_lock = threading.Lock()

        # Load standards cache
        self._standards_cache: Dict[str, Dict[str, Any]] = {}

    def _resolve_env_var(self, value: str) -> str:
        """Resolve environment variable references like ${VAR_NAME}."""
        if value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            return os.environ.get(env_var, value)
        return value

    def _load_standard(self, standard_name: str) -> Dict[str, Any]:
        """
        Load an ADRI standard for schema mapping.

        Args:
            standard_name: Name of the standard to load

        Returns:
            Dict containing the standard definition
        """
        if standard_name in self._standards_cache:
            return self._standards_cache[standard_name]

        # Try to load from standards directory with updated paths
        standard_paths = [
            f"src/adri/standards/audit_logs/{standard_name}.yaml",
            f"adri/standards/audit_logs/{standard_name}.yaml",
            f"src/adri/standards/{standard_name}.yaml",
            f"adri/standards/{standard_name}.yaml",
            f"{standard_name}.yaml",
        ]

        for path in standard_paths:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    standard = yaml.safe_load(f) or {}
                    self._standards_cache[standard_name] = standard
                    return standard

        # Return a mock standard for testing
        # In production, this would raise an error
        return {"standard_name": standard_name, "fields": {}}

    def _map_adri_to_verodat_type(self, adri_type: str) -> str:
        """
        Map ADRI field type to Verodat type.

        Args:
            adri_type: ADRI standard field type

        Returns:
            Verodat-compatible type string
        """
        type_mapping = {
            "string": "string",
            "integer": "numeric",
            "number": "numeric",
            "float": "numeric",
            "datetime": "date",
            "date": "date",
            "boolean": "string",  # Verodat uses "TRUE"/"FALSE" strings
        }
        return type_mapping.get(adri_type.lower(), "string")

    def _build_verodat_header(self, standard: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Build Verodat header from ADRI standard.

        Args:
            standard: ADRI standard definition

        Returns:
            List of header field definitions for Verodat
        """
        header = []
        fields = standard.get("fields", [])

        # Handle both list and dict formats for flexibility
        if isinstance(fields, list):
            # List format (actual ADRI standard structure)
            for field_spec in fields:
                field_name = field_spec.get("name")
                field_type = field_spec.get("type", "string")
                verodat_type = self._map_adri_to_verodat_type(field_type)
                header.append({"name": field_name, "type": verodat_type})
        else:
            # Dict format (for testing compatibility)
            for field_name, field_spec in fields.items():
                verodat_type = self._map_adri_to_verodat_type(
                    field_spec.get("type", "string")
                )
                header.append({"name": field_name, "type": verodat_type})

        return header

    def _format_value(self, value: Any, field_type: str) -> Any:
        """
        Format a value according to Verodat requirements.

        Args:
            value: Value to format
            field_type: ADRI field type

        Returns:
            Formatted value for Verodat
        """
        if value is None:
            return None

        # Handle datetime formatting
        if field_type in ["datetime", "date"]:
            if isinstance(value, datetime):
                return value.strftime("%Y-%m-%dT%H:%M:%SZ")
            elif isinstance(value, str):
                # Ensure it ends with Z for UTC
                if not value.endswith("Z"):
                    return value.replace("+00:00", "Z")
                return value

        # Handle boolean formatting
        elif field_type == "boolean":
            return "TRUE" if value else "FALSE"

        # Handle JSON serialization for complex types
        elif isinstance(value, (list, dict)):
            return json.dumps(value)

        return value

    def _format_record_to_row(
        self, record: AuditRecord, standard: Dict[str, Any], dataset_type: str
    ) -> List[Any]:
        """
        Format an audit record to Verodat row format based on standard.

        Args:
            record: Audit record to format
            standard: ADRI standard defining the schema
            dataset_type: Type of dataset (assessment_logs, etc.)

        Returns:
            List of values in order defined by standard
        """
        row = []
        fields = standard.get("fields", [])

        # Convert record to dict for easier access
        record_dict = record.to_verodat_format()
        main_record = record_dict["main_record"]

        # Handle both list and dict formats
        if isinstance(fields, list):
            # List format (actual ADRI standard structure)
            for field_spec in fields:
                field_name = field_spec.get("name")
                field_type = field_spec.get("type", "string")

                # Get value from main_record
                value = main_record.get(field_name)

                # Format the value
                formatted_value = self._format_value(value, field_type)
                row.append(formatted_value)
        else:
            # Dict format (for testing compatibility)
            for field_name, field_spec in fields.items():
                field_type = field_spec.get("type", "string")
                value = main_record.get(field_name)
                formatted_value = self._format_value(value, field_type)
                row.append(formatted_value)

        return row

    def upload(self, records: List[AuditRecord], dataset_type: str) -> bool:
        """
        Upload records to Verodat API.

        Args:
            records: List of audit records to upload
            dataset_type: Type of dataset (assessment_logs, dimension_scores, etc.)

        Returns:
            True if upload successful, False otherwise
        """
        if not self.enabled:
            return True  # Silently succeed if disabled

        if not records:
            return True  # Nothing to upload

        # Get endpoint configuration
        endpoint_config = self.config.get("endpoints", {}).get(dataset_type, {})
        schedule_request_id = endpoint_config.get("schedule_request_id")

        if not schedule_request_id:
            print(f"Warning: No schedule_request_id configured for {dataset_type}")
            return False

        # Prepare payload
        data = self._prepare_payload(records, dataset_type)
        payload = {"data": data}

        # Prepare request
        url = f"{self.base_url}/workspaces/{self.workspace_id}/schedule-request/{schedule_request_id}/autoload/upload"
        headers = {
            "Authorization": f"ApiKey {self.api_key}",
            "Content-Type": "application/json",
        }

        # Try upload with retry logic
        for attempt in range(self.retry_attempts + 1):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                    verify=self.verify_ssl,
                )

                if response.status_code == 200:
                    return True
                elif response.status_code >= 500 and attempt < self.retry_attempts:
                    # Server error, retry
                    time.sleep(self.retry_delay)
                    continue
                else:
                    # Client error or final attempt
                    print(
                        f"Failed to upload to Verodat: {response.status_code} - {response.text}"
                    )
                    return False

            except Exception as e:
                print(f"Error uploading to Verodat: {e}")
                if attempt < self.retry_attempts:
                    time.sleep(self.retry_delay)
                    continue
                return False

        return False

    def _prepare_payload(
        self, records: List[AuditRecord], dataset_type: str
    ) -> List[Dict[str, Any]]:
        """
        Prepare the complete payload for Verodat API.

        Args:
            records: List of audit records
            dataset_type: Type of dataset to prepare

        Returns:
            Verodat API payload structure
        """
        # Get the standard for this dataset
        endpoint_config = self.config.get("endpoints", {}).get(dataset_type, {})
        standard_name = endpoint_config.get("standard", f"{dataset_type}_standard")
        standard = self._load_standard(standard_name)

        # Build header
        header = self._build_verodat_header(standard)

        # Build rows
        rows = []
        for record in records:
            if dataset_type == "dimension_scores":
                # Special handling for dimension scores (multiple rows per record)
                dimension_rows = self._format_dimension_scores(record, standard)
                rows.extend(dimension_rows)
            elif dataset_type == "failed_validations":
                # Special handling for failed validations (multiple rows per record)
                failed_validation_rows = self._format_failed_validations(
                    record, standard
                )
                rows.extend(failed_validation_rows)
            else:
                row = self._format_record_to_row(record, standard, dataset_type)
                rows.append(row)

        # Return Verodat payload format
        return [{"header": header}, {"rows": rows}]

    def _format_dimension_scores(
        self, record: AuditRecord, standard: Dict[str, Any]
    ) -> List[List[Any]]:
        """Format dimension scores from audit record."""
        rows = []
        dimension_scores = record.assessment_results.get("dimension_scores", {})

        if isinstance(dimension_scores, dict):
            for dim_name, dim_score in dimension_scores.items():
                row = []
                fields = standard.get("fields", [])

                if isinstance(fields, list):
                    for field_spec in fields:
                        field_name = field_spec.get("name")
                        field_type = field_spec.get("type", "string")

                        if field_name == "assessment_id":
                            value = record.assessment_id
                        elif field_name == "dimension_name":
                            value = dim_name
                        elif field_name == "dimension_score":
                            value = dim_score
                        elif field_name == "dimension_passed":
                            # Handle None values properly to prevent TypeError
                            # Return boolean value directly, not string, to avoid double conversion
                            if dim_score is None:
                                value = False
                            else:
                                value = dim_score > 15
                        elif field_name == "issues_found":
                            value = "0"  # Default
                        elif field_name == "details":
                            value = json.dumps(
                                {"score": dim_score, "dimension": dim_name}
                            )
                        else:
                            value = None

                        formatted_value = self._format_value(value, field_type)
                        row.append(formatted_value)

                rows.append(row)

        return rows

    def _format_failed_validations(
        self, record: AuditRecord, standard: Dict[str, Any]
    ) -> List[List[Any]]:
        """Format failed validations from audit record."""
        rows = []
        failed_checks_list = record.assessment_results.get("failed_checks", [])

        if isinstance(failed_checks_list, list):
            for idx, check in enumerate(failed_checks_list):
                if not isinstance(check, dict):
                    continue

                row = []
                fields = standard.get("fields", [])
                validation_id = f"val_{idx:03d}"

                if isinstance(fields, list):
                    for field_spec in fields:
                        field_name = field_spec.get("name")
                        field_type = field_spec.get("type", "string")

                        if field_name == "assessment_id":
                            value = record.assessment_id
                        elif field_name == "validation_id":
                            value = validation_id
                        elif field_name == "dimension":
                            value = check.get("dimension", "unknown")
                        elif field_name == "field_name":
                            value = check.get("field_name", "")
                        elif field_name == "issue_type":
                            value = check.get("issue_type", "unknown")
                        elif field_name == "affected_rows":
                            value = check.get("affected_rows", 0)
                        elif field_name == "affected_percentage":
                            value = check.get("affected_percentage", 0.0)
                        elif field_name == "sample_failures":
                            samples = check.get("sample_failures", [])
                            value = json.dumps(samples) if samples else ""
                        elif field_name == "remediation":
                            value = check.get("remediation", "")
                        else:
                            value = None

                        formatted_value = self._format_value(value, field_type)
                        row.append(formatted_value)

                rows.append(row)

        return rows

    def add_to_batch(self, record: AuditRecord) -> None:
        """
        Add a record to the appropriate batch.

        Args:
            record: Audit record to batch
        """
        with self._batch_lock:
            self._assessment_logs_batch.append(record)

            # Also add to dimension scores and failed validations if applicable
            if record.assessment_results.get("dimension_scores"):
                self._dimension_scores_batch.append(record)

            if record.assessment_results.get("failed_checks"):
                self._failed_validations_batch.append(record)

    def _get_batches(self, dataset_type: str) -> List[List[AuditRecord]]:
        """
        Get batches of records for upload.

        Args:
            dataset_type: Type of dataset

        Returns:
            List of batches
        """
        with self._batch_lock:
            if dataset_type == "assessment_logs":
                records = self._assessment_logs_batch[:]
            elif dataset_type == "dimension_scores":
                records = self._dimension_scores_batch[:]
            elif dataset_type == "failed_validations":
                records = self._failed_validations_batch[:]
            else:
                records = []

        # Split into batches
        batches = []
        for i in range(0, len(records), self.batch_size):
            batch = records[i : i + self.batch_size]
            batches.append(batch)

        return batches

    def flush_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Flush all batched records to Verodat.

        Returns:
            Dict with upload results for each dataset type
        """
        results = {}

        # Process each dataset type
        for dataset_type in [
            "assessment_logs",
            "dimension_scores",
            "failed_validations",
        ]:
            batches = self._get_batches(dataset_type)

            total_records = sum(len(batch) for batch in batches)
            success = True

            for batch in batches:
                if not self.upload(batch, dataset_type):
                    success = False
                    break

            if success:
                # Clear the batch
                with self._batch_lock:
                    if dataset_type == "assessment_logs":
                        self._assessment_logs_batch.clear()
                    elif dataset_type == "dimension_scores":
                        self._dimension_scores_batch.clear()
                    elif dataset_type == "failed_validations":
                        self._failed_validations_batch.clear()

            results[dataset_type] = {
                "success": success,
                "records_uploaded": total_records if success else 0,
            }

        return results

    def get_batch_status(self) -> Dict[str, int]:
        """
        Get current batch status.

        Returns:
            Dict with count of records in each batch
        """
        with self._batch_lock:
            return {
                "assessment_logs": len(self._assessment_logs_batch),
                "dimension_scores": len(self._dimension_scores_batch),
                "failed_validations": len(self._failed_validations_batch),
            }


# Helper function for backward compatibility
def log_to_verodat(
    assessment_result: Any,
    execution_context: Dict[str, Any],
    data_info: Optional[Dict[str, Any]] = None,
    performance_metrics: Optional[Dict[str, Any]] = None,
    failed_checks: Optional[List[Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Log an assessment to Verodat.

    Args:
        assessment_result: Assessment result object
        execution_context: Execution context information
        data_info: Data information
        performance_metrics: Performance metrics
        failed_checks: Failed validation checks
        config: Verodat configuration

    Returns:
        True if successful, False otherwise
    """
    if not config or not config.get("enabled", False):
        return True

    logger = EnterpriseLogger(config)

    # Create audit record
    timestamp = datetime.now()
    assessment_id = f"adri_{timestamp.strftime('%Y%m%d_%H%M%S')}_{os.urandom(3).hex()}"

    try:
        from ..version import __version__
    except ImportError:
        __version__ = "unknown"

    record = AuditRecord(assessment_id, timestamp, __version__)

    # Populate record (simplified)
    record.execution_context.update(execution_context)
    if hasattr(assessment_result, "overall_score"):
        record.assessment_results["overall_score"] = assessment_result.overall_score
    if hasattr(assessment_result, "passed"):
        record.assessment_results["passed"] = assessment_result.passed

    # Add to batch and try immediate upload for single record
    logger.add_to_batch(record)
    return logger.upload([record], "assessment_logs")


# Backward compatibility alias
VerodatLogger = EnterpriseLogger
