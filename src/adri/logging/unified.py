"""
Unified logger coordinating fast and slow path logging.

Implements dual-write pattern to provide both immediate manifest writes
(fast path) and comprehensive batch logging (slow path).
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from ..events.types import AssessmentManifest
from .fast_path import FastPathLogger

logger = logging.getLogger(__name__)


class UnifiedLogger:
    """Unified logger coordinating fast and slow path logging.

    Implements dual-write pattern:
    - Fast path: Immediate (<10ms) manifest writes for workflow orchestration
    - Slow path: Batched comprehensive logs for analytics and compliance

    This provides the best of both worlds: real-time access to assessment IDs
    with full detailed logging for audit and analysis.

    Usage:
        unified_logger = UnifiedLogger(
            fast_path_enabled=True,
            fast_path_storage="redis",
            slow_path_logger=existing_logger
        )

        # Dual write
        unified_logger.log_assessment(
            assessment_result=result,
            execution_context=context,
            data_info=info,
            performance_metrics=metrics
        )

        # Fast path read
        manifest = unified_logger.get_manifest(assessment_id)
    """

    def __init__(
        self,
        fast_path_enabled: bool = False,
        fast_path_storage: str = "memory",
        fast_path_config: Optional[Dict[str, Any]] = None,
        slow_path_logger: Optional[Any] = None,
    ):
        """Initialize unified logger.

        Args:
            fast_path_enabled: Whether to enable fast path logging
            fast_path_storage: Storage backend for fast path ("memory", "file", "redis")
            fast_path_config: Configuration for fast path logger
            slow_path_logger: Existing slow path logger (LocalLogger, EnterpriseLogger)
        """
        self.fast_path_enabled = fast_path_enabled
        self.slow_path_logger = slow_path_logger

        # Initialize fast path logger if enabled
        self.fast_path_logger: Optional[FastPathLogger] = None
        if fast_path_enabled:
            config = fast_path_config or {}
            self.fast_path_logger = FastPathLogger(
                storage=fast_path_storage,
                storage_dir=config.get("storage_dir"),
                redis_url=config.get("redis_url", "redis://localhost:6379"),
                ttl_seconds=config.get("ttl_seconds", 3600),
            )
            logger.info(f"Fast path logging enabled with {fast_path_storage} storage")
        else:
            logger.debug("Fast path logging disabled")

    def log_assessment(
        self,
        assessment_result: Any,
        execution_context: Optional[Dict[str, Any]] = None,
        data_info: Optional[Dict[str, Any]] = None,
        performance_metrics: Optional[Dict[str, Any]] = None,
        failed_checks: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Log assessment with dual-write pattern.

        Writes to both fast path (immediate) and slow path (batched).

        Args:
            assessment_result: Assessment result to log
            execution_context: Execution metadata
            data_info: Data information
            performance_metrics: Performance metrics
            failed_checks: Failed validation checks

        Returns:
            Audit record from slow path logger
        """
        # Fast path write (immediate, <10ms)
        if self.fast_path_enabled and self.fast_path_logger:
            try:
                self._write_fast_path(assessment_result)
            except Exception as e:
                # Fast path failure is non-critical
                logger.warning(f"Fast path write failed: {e}")

        # Slow path write (batched, comprehensive)
        audit_record = {}
        if self.slow_path_logger:
            try:
                audit_record = self.slow_path_logger.log_assessment(
                    assessment_result=assessment_result,
                    execution_context=execution_context,
                    data_info=data_info,
                    performance_metrics=performance_metrics,
                    failed_checks=failed_checks,
                )
            except Exception as e:
                logger.error(f"Slow path write failed: {e}")
                raise

        return audit_record

    def _write_fast_path(self, assessment_result: Any) -> None:
        """Write minimal manifest to fast path.

        Args:
            assessment_result: Assessment result to write
        """
        # Determine status
        status = "PASSED" if assessment_result.passed else "BLOCKED"

        # Extract standard name
        standard_name = None
        if hasattr(assessment_result, "standard_id") and assessment_result.standard_id:
            standard_name = assessment_result.standard_id
        elif (
            hasattr(assessment_result, "standard_path")
            and assessment_result.standard_path
        ):
            from pathlib import Path

            standard_name = Path(assessment_result.standard_path).stem.replace(
                "_standard", ""
            )

        # Create manifest
        manifest = AssessmentManifest(
            assessment_id=assessment_result.assessment_id,
            timestamp=(
                assessment_result.assessment_date
                if hasattr(assessment_result, "assessment_date")
                else datetime.now()
            ),
            status=status,
            score=assessment_result.overall_score,
            standard_name=standard_name,
        )

        # Write to fast path
        self.fast_path_logger.log_manifest(manifest)
        logger.debug(f"Fast path write completed for {assessment_result.assessment_id}")

    def get_manifest(self, assessment_id: str) -> Optional[AssessmentManifest]:
        """Get assessment manifest from fast path.

        Args:
            assessment_id: Assessment ID to retrieve

        Returns:
            AssessmentManifest if found, None otherwise
        """
        if not self.fast_path_enabled or not self.fast_path_logger:
            logger.debug("Fast path not enabled, cannot retrieve manifest")
            return None

        return self.fast_path_logger.get_manifest(assessment_id)

    def wait_for_completion(
        self, assessment_id: str, timeout: int = 30
    ) -> Optional[AssessmentManifest]:
        """Wait for assessment to complete (blocking).

        Args:
            assessment_id: Assessment ID to wait for
            timeout: Maximum seconds to wait

        Returns:
            AssessmentManifest when completed, None on timeout
        """
        if not self.fast_path_enabled or not self.fast_path_logger:
            logger.warning("Fast path not enabled, cannot wait for completion")
            return None

        return self.fast_path_logger.wait_for_completion(assessment_id, timeout)

    def close(self) -> None:
        """Clean up resources."""
        if self.fast_path_logger:
            self.fast_path_logger.close()
        if self.slow_path_logger and hasattr(self.slow_path_logger, "close"):
            self.slow_path_logger.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
