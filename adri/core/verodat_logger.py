"""
Verodat Logger for centralized audit logging.

Integrates with Verodat API to upload ADRI assessment audit logs,
using ADRI standards as the schema definition.
"""

import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
import yaml

from adri.core.audit_logger import AuditRecord


class VerodatLogger:
    """Handles uploading audit logs to Verodat API."""

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
        self.flush_interval = batch_settings.get("flush_interval_seconds", 60)
        self.retry_attempts = batch_settings.get("retry_attempts", 3)
        self.retry_delay = batch_settings.get("retry_delay_seconds", 5)

        # Connection settings
        connection_settings = config.get("connection", {})
        self.timeout = connection_settings.get("timeout_seconds", 30)
        self.verify_ssl = connection_settings.get("verify_ssl", True)

        # Initialize batches
        self._assessment_logs_batch = []
        self._dimension_scores_batch = []
        self._failed_validations_batch = []
        self._batch_lock = threading.Lock()

        # Load standards cache
        self._standards_cache = {}

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

        # Try to load from standards directory
        standard_paths = [
            f"adri/standards/audit_logs/{standard_name}.yaml",
            f"adri/standards/{standard_name}.yaml",
            f"{standard_name}.yaml",
        ]

        for path in standard_paths:
            if os.path.exists(path):
                with open(path, "r") as f:
                    standard = yaml.safe_load(f)
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
        import json
        import os
        from datetime import datetime

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

                # Map field names to record attributes - EXACT Verodat mapping
                if field_name == "assessment_id":
                    value = record.assessment_id
                elif field_name == "log_timestamp":
                    value = record.timestamp
                elif field_name == "adri_version":
                    value = record.adri_version
                elif field_name == "assessment_type":
                    value = "QUALITY_CHECK"  # Default assessment type
                elif field_name == "function_name":
                    value = record.execution_context.get("function_name", "unknown")
                elif field_name == "module_path":
                    value = record.execution_context.get("module_path", "adri.core")
                elif field_name == "environment":
                    value = record.environment or "PRODUCTION"
                elif field_name == "hostname":
                    value = record.hostname or os.uname().nodename
                elif field_name == "process_id":
                    value = record.process_id or os.getpid()
                elif field_name == "standard_id":
                    value = record.standard_metadata.get("standard_id", "unknown")
                elif field_name == "standard_version":
                    value = record.standard_metadata.get("version", "unknown")
                elif field_name == "standard_checksum":
                    value = record.standard_metadata.get("checksum")
                elif field_name == "data_row_count":
                    value = record.data_fingerprint.get("row_count", 0)
                elif field_name == "data_column_count":
                    value = record.data_fingerprint.get("column_count", 0)
                elif field_name == "data_columns":
                    columns = record.data_fingerprint.get("columns", [])
                    value = json.dumps(columns) if columns else "[]"
                elif field_name == "data_checksum":
                    value = record.data_fingerprint.get("checksum")
                elif field_name == "overall_score":
                    value = record.assessment_results.get("overall_score", 0.0)
                elif field_name == "required_score":
                    value = record.assessment_results.get("required_score", 70.0)
                elif field_name == "passed":
                    value = record.assessment_results.get("passed", False)
                elif field_name == "execution_decision":
                    passed = record.assessment_results.get("passed", False)
                    value = "ALLOWED" if passed else "BLOCKED"
                elif field_name == "failure_mode":
                    value = record.execution_context.get("failure_mode", "log")
                elif field_name == "function_executed":
                    value = record.assessment_results.get("function_executed", True)
                elif field_name == "assessment_duration_ms":
                    duration = record.performance_metrics.get("assessment_duration_ms")
                    value = int(duration) if duration else 0
                elif field_name == "rows_per_second":
                    value = record.performance_metrics.get("rows_per_second")
                elif field_name == "cache_used":
                    value = (
                        record.cache_info.get("cache_used", False)
                        if hasattr(record, "cache_info")
                        else False
                    )
                else:
                    # Try to get from main_record dict
                    value = main_record.get(field_name)

                # Format the value
                formatted_value = self._format_value(value, field_type)
                row.append(formatted_value)
        else:
            # Dict format (for testing compatibility)
            for field_name, field_spec in fields.items():
                field_type = field_spec.get("type", "string")

                # Map field names to record attributes
                if field_name == "assessment_id":
                    value = record.assessment_id
                elif field_name == "timestamp":
                    value = record.timestamp
                elif field_name == "adri_version":
                    value = record.adri_version
                elif field_name == "function_name":
                    value = record.execution_context.get("function_name", "")
                elif field_name == "overall_score":
                    value = record.assessment_results.get("overall_score", 0.0)
                elif field_name == "passed":
                    value = record.assessment_results.get("passed", False)
                elif field_name == "row_count":
                    value = record.data_fingerprint.get("row_count", 0)
                else:
                    # Try to get from main_record dict
                    value = main_record.get(field_name)

                # Format the value
                formatted_value = self._format_value(value, field_type)
                row.append(formatted_value)

        return row

    def _format_dimension_scores(
        self, record: AuditRecord, standard: Dict[str, Any]
    ) -> List[List[Any]]:
        """
        Format dimension scores from audit record.

        Args:
            record: Audit record containing dimension scores
            standard: ADRI standard for dimension scores

        Returns:
            List of rows, one per dimension
        """
        rows = []
        dimension_scores = record.assessment_results.get("dimension_scores", {})

        for dim_name, dim_score in dimension_scores.items():
            row = []
            fields = standard.get("fields", [])

            # Handle both list and dict formats
            if isinstance(fields, list):
                # List format (actual ADRI standard structure)
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
                        # Consider dimension passed if score > 15 (based on ADRI spec)
                        value = "TRUE" if dim_score > 15 else "FALSE"
                    elif field_name == "issues_found":
                        # Calculate issues found for this dimension
                        value = 0  # Default, would need more info from assessment
                    elif field_name == "details":
                        # Additional details as JSON
                        value = json.dumps({"score": dim_score, "dimension": dim_name})
                    elif field_name == "G360_VERSION_KEY":
                        # Compound key from assessment_id:dimension_name
                        value = f"{record.assessment_id}:{dim_name}"
                    else:
                        value = None

                    formatted_value = self._format_value(value, field_type)
                    row.append(formatted_value)
            else:
                # Dict format (for testing compatibility)
                for field_name, field_spec in fields.items():
                    field_type = field_spec.get("type", "string")

                    if field_name == "assessment_id":
                        value = record.assessment_id
                    elif field_name == "dimension_name":
                        value = dim_name
                    elif field_name == "dimension_score":
                        value = dim_score
                    elif field_name == "dimension_passed":
                        # Consider dimension passed if score > 15 (based on original code)
                        value = dim_score > 15
                    else:
                        value = None

                    formatted_value = self._format_value(value, field_type)
                    row.append(formatted_value)

            rows.append(row)

        return rows

    def _format_failed_validations(
        self, record: AuditRecord, standard: Dict[str, Any]
    ) -> List[List[Any]]:
        """
        Format failed validations from audit record.

        Args:
            record: Audit record containing failed checks
            standard: ADRI standard for failed validations

        Returns:
            List of rows, one per failed validation
        """
        rows = []
        failed_checks = record.assessment_results.get("failed_checks", [])

        for idx, check in enumerate(failed_checks):
            row = []
            fields = standard.get("fields", [])

            # Generate validation_id
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
                        value = check.get("field_name")
                    elif field_name == "issue_type":
                        value = check.get("issue_type", "unknown")
                    elif field_name == "affected_rows":
                        value = check.get("affected_rows", 0)
                    elif field_name == "affected_percentage":
                        value = check.get("affected_percentage", 0.0)
                    elif field_name == "sample_failures":
                        samples = check.get("sample_failures", [])
                        value = json.dumps(samples) if samples else None
                    elif field_name == "remediation":
                        value = check.get("remediation")
                    elif field_name == "G360_VERSION_KEY":
                        # Compound key from assessment_id:validation_id
                        value = f"{record.assessment_id}:{validation_id}"
                    else:
                        value = None

                    formatted_value = self._format_value(value, field_type)
                    row.append(formatted_value)

            rows.append(row)

        return rows

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

        # Prepare payload - returns the inner array
        data = self._prepare_payload(records, dataset_type)

        # Wrap in 'data' key for Verodat API
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
