"""
ADRI Enterprise - Verodat API Integration.

Provides centralized logging and monitoring through Verodat API for enterprise deployments.
This module replaces the basic stub in src/adri/logging/enterprise.py with full-featured
enterprise integration.
"""

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class VerodatLogger:
    """
    Enterprise Verodat API integration for centralized logging.

    Provides batch processing, retry logic, and advanced logging capabilities
    for enterprise deployments.
    """

    def __init__(
        self,
        api_url: str,
        api_key: str,
        batch_size: int = 10,
        retry_attempts: int = 3,
        timeout: int = 30,
    ):
        """
        Initialize Verodat logger.

        Args:
            api_url: Verodat API endpoint URL
            api_key: Verodat API key for authentication
            batch_size: Number of records to batch before sending (default: 10)
            retry_attempts: Number of retry attempts on failure (default: 3)
            timeout: Request timeout in seconds (default: 30)
        """
        self.api_url = api_url
        self.api_key = api_key
        self.batch_size = batch_size
        self.retry_attempts = retry_attempts
        self.timeout = timeout
        self._batch_buffer: list[dict[str, Any]] = []

    def log_assessment(
        self,
        assessment_data: dict[str, Any],
        workflow_context: dict[str, Any] | None = None,
        data_provenance: dict[str, Any] | None = None,
    ) -> bool:
        """
        Log assessment data to Verodat API with optional context.

        Args:
            assessment_data: Assessment results and metadata
            workflow_context: Optional workflow execution context
            data_provenance: Optional data source provenance

        Returns:
            True if successful, False otherwise
        """
        try:
            # Enrich assessment data with enterprise context
            enriched_data = {
                **assessment_data,
                "workflow_context": workflow_context,
                "data_provenance": data_provenance,
            }

            # Add to batch buffer
            self._batch_buffer.append(enriched_data)

            # Send batch if buffer is full
            if len(self._batch_buffer) >= self.batch_size:
                return self._flush_batch()

            return True

        except Exception as e:
            logger.error(f"Failed to log assessment to Verodat: {e}")
            return False

    def log_workflow_step(
        self,
        step_name: str,
        workflow_context: dict[str, Any],
        step_data: dict[str, Any] | None = None,
    ) -> bool:
        """
        Log workflow step execution to Verodat API.

        Args:
            step_name: Name of the workflow step
            workflow_context: Workflow execution context
            step_data: Optional step-specific data

        Returns:
            True if successful, False otherwise
        """
        try:
            log_data = {
                "type": "workflow_step",
                "step_name": step_name,
                "workflow_context": workflow_context,
                "step_data": step_data,
            }

            return self._send_to_verodat(log_data)

        except Exception as e:
            logger.error(f"Failed to log workflow step to Verodat: {e}")
            return False

    def _flush_batch(self) -> bool:
        """
        Flush batched records to Verodat API.

        Returns:
            True if successful, False otherwise
        """
        if not self._batch_buffer:
            return True

        try:
            batch_data = {"batch": self._batch_buffer}
            success = self._send_to_verodat(batch_data)

            if success:
                self._batch_buffer.clear()

            return success

        except Exception as e:
            logger.error(f"Failed to flush batch to Verodat: {e}")
            return False

    def _send_to_verodat(
        self, data: dict[str, Any], attempt: int = 1
    ) -> bool:
        """
        Send data to Verodat API with retry logic.

        Args:
            data: Data to send
            attempt: Current attempt number

        Returns:
            True if successful, False otherwise
        """
        try:
            headers = {
                "Authorization": f"ApiKey {self.api_key}",
                "Content-Type": "application/json",
            }

            response = requests.post(
                self.api_url,
                json=data,
                headers=headers,
                timeout=self.timeout,
            )

            if response.status_code == 200:
                return True

            # Retry on server errors
            if response.status_code >= 500 and attempt < self.retry_attempts:
                logger.warning(
                    f"Verodat API error (attempt {attempt}/{self.retry_attempts}): "
                    f"{response.status_code}"
                )
                return self._send_to_verodat(data, attempt + 1)

            logger.error(
                f"Verodat API request failed: {response.status_code} - {response.text}"
            )
            return False

        except requests.exceptions.Timeout:
            if attempt < self.retry_attempts:
                logger.warning(
                    f"Verodat API timeout (attempt {attempt}/{self.retry_attempts})"
                )
                return self._send_to_verodat(data, attempt + 1)
            logger.error("Verodat API request timed out after all retry attempts")
            return False

        except Exception as e:
            logger.error(f"Error sending data to Verodat: {e}")
            return False

    def close(self) -> bool:
        """
        Flush any remaining batched records and close the logger.

        Returns:
            True if successful, False otherwise
        """
        return self._flush_batch()


def send_to_verodat(
    assessment_data: dict[str, Any], api_url: str, api_key: str
) -> bool:
    """
    Convenience function to send assessment data to Verodat API.

    This provides backward compatibility with the basic function from
    src/adri/logging/enterprise.py. For single assessments, bypasses
    batching and sends immediately.

    Args:
        assessment_data: Dictionary containing assessment results
        api_url: Verodat API endpoint URL
        api_key: Verodat API key for authentication

    Returns:
        True if upload successful, False otherwise

    Example:
        >>> data = {
        ...     "assessment_id": "test_001",
        ...     "overall_score": 85.5,
        ...     "passed": True
        ... }
        >>> send_to_verodat(data, "https://api.verodat.com/upload", "your-api-key")
        True
    """
    # For single assessment, bypass batching and send directly
    logger_instance = VerodatLogger(api_url, api_key, batch_size=1)
    success = logger_instance.log_assessment(assessment_data)
    # Batch size 1 means it auto-flushes immediately
    return success
