"""
Workflow adapter implementations.

Provides adapters for integrating with workflow orchestration frameworks
like Prefect and Airflow.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class WorkflowAdapter(ABC):
    """Abstract base class for workflow framework adapters.

    Workflow adapters provide standardized hooks for integrating
    ADRI assessments with workflow orchestration frameworks.
    """

    @abstractmethod
    def on_assessment_start(self, assessment_id: str, metadata: Dict[str, Any]) -> None:
        """Call when assessment starts.

        Args:
            assessment_id: Unique assessment identifier
            metadata: Assessment metadata (standard, data info, etc.)
        """
        pass

    @abstractmethod
    def on_assessment_complete(
        self, assessment_id: str, assessment_result: Any
    ) -> None:
        """Call when assessment completes.

        Args:
            assessment_id: Unique assessment identifier
            assessment_result: Complete AssessmentResult object
        """
        pass

    @abstractmethod
    def on_assessment_error(self, assessment_id: str, error: Exception) -> None:
        """Call when assessment fails with error.

        Args:
            assessment_id: Unique assessment identifier
            error: Exception that occurred
        """
        pass


class PrefectAdapter(WorkflowAdapter):
    """Adapter for Prefect workflow orchestration.

    Integrates ADRI assessments with Prefect flows by setting
    task run states and logging results.

    Usage:
        from prefect import task
        from adri.callbacks import PrefectAdapter

        adapter = PrefectAdapter()

        @task
        @adri_protected(
            standard="invoice_standard.yaml",
            workflow_adapter=adapter
        )
        def process_invoices(data):
            return analyze(data)
    """

    def __init__(self, log_level: str = "INFO"):
        """Initialize Prefect adapter.

        Args:
            log_level: Logging level for Prefect messages
        """
        self.log_level = log_level
        self._prefect_available = self._check_prefect()

    def _check_prefect(self) -> bool:
        """Check if Prefect is available."""
        try:
            import prefect

            logger.debug(f"Prefect available: {prefect.__version__}")
            return True
        except ImportError:
            logger.warning(
                "Prefect not installed. Install with: pip install prefect>=2.0.0"
            )
            return False

    def on_assessment_start(self, assessment_id: str, metadata: Dict[str, Any]) -> None:
        """Log assessment start to Prefect."""
        if not self._prefect_available:
            return

        try:
            from prefect import get_run_logger

            prefect_logger = get_run_logger()
            prefect_logger.info(
                f"ADRI assessment started: {assessment_id}",
                extra={"assessment_id": assessment_id, "metadata": metadata},
            )
        except Exception as e:
            logger.debug(f"Could not log to Prefect: {e}")

    def on_assessment_complete(
        self, assessment_id: str, assessment_result: Any
    ) -> None:
        """Log assessment completion to Prefect."""
        if not self._prefect_available:
            return

        try:
            from prefect import get_run_logger

            prefect_logger = get_run_logger()

            # Log completion
            prefect_logger.info(
                f"ADRI assessment completed: {assessment_id}",
                extra={
                    "assessment_id": assessment_id,
                    "passed": assessment_result.passed,
                    "score": assessment_result.overall_score,
                },
            )

            # Log warning if assessment failed
            if not assessment_result.passed:
                prefect_logger.warning(
                    f"Assessment {assessment_id} failed quality check "
                    f"(score: {assessment_result.overall_score:.2f})"
                )

        except Exception as e:
            logger.debug(f"Could not log to Prefect: {e}")

    def on_assessment_error(self, assessment_id: str, error: Exception) -> None:
        """Log assessment error to Prefect."""
        if not self._prefect_available:
            return

        try:
            from prefect import get_run_logger

            prefect_logger = get_run_logger()
            prefect_logger.error(
                f"ADRI assessment error: {assessment_id}",
                extra={
                    "assessment_id": assessment_id,
                    "error": str(error),
                    "error_type": type(error).__name__,
                },
                exc_info=error,
            )
        except Exception as e:
            logger.debug(f"Could not log to Prefect: {e}")


class AirflowAdapter(WorkflowAdapter):
    """Adapter for Apache Airflow workflow orchestration.

    Integrates ADRI assessments with Airflow DAGs by pushing
    XComs and logging to Airflow's logging system.

    Usage:
        from airflow.decorators import task
        from adri.callbacks import AirflowAdapter

        adapter = AirflowAdapter()

        @task
        @adri_protected(
            standard="invoice_standard.yaml",
            workflow_adapter=adapter
        )
        def process_invoices(data):
            return analyze(data)
    """

    def __init__(
        self, xcom_key_prefix: str = "adri_assessment", push_to_xcom: bool = True
    ):
        """Initialize Airflow adapter.

        Args:
            xcom_key_prefix: Prefix for XCom keys
            push_to_xcom: Whether to push results to XCom
        """
        self.xcom_key_prefix = xcom_key_prefix
        self.push_to_xcom = push_to_xcom
        self._airflow_available = self._check_airflow()

    def _check_airflow(self) -> bool:
        """Check if Airflow is available."""
        try:
            import airflow

            logger.debug(f"Airflow available: {airflow.__version__}")
            return True
        except ImportError:
            logger.warning(
                "Airflow not installed. Install with: pip install apache-airflow>=2.0.0"
            )
            return False

    def _get_task_instance(self) -> Optional[Any]:
        """Get current Airflow task instance from context."""
        if not self._airflow_available:
            return None

        try:
            from airflow.operators.python import get_current_context

            context = get_current_context()
            return context.get("task_instance")
        except Exception as e:
            logger.debug(f"Could not get Airflow context: {e}")
            return None

    def on_assessment_start(self, assessment_id: str, metadata: Dict[str, Any]) -> None:
        """Log assessment start to Airflow."""
        if not self._airflow_available:
            return

        try:
            from airflow.utils.log.logging_mixin import LoggingMixin

            airflow_logger = LoggingMixin().log
            airflow_logger.info(f"ADRI assessment started: {assessment_id}")

            # Push to XCom if enabled
            if self.push_to_xcom:
                ti = self._get_task_instance()
                if ti:
                    ti.xcom_push(
                        key=f"{self.xcom_key_prefix}_{assessment_id}_start",
                        value=metadata,
                    )
        except Exception as e:
            logger.debug(f"Could not log to Airflow: {e}")

    def on_assessment_complete(
        self, assessment_id: str, assessment_result: Any
    ) -> None:
        """Log assessment completion to Airflow."""
        if not self._airflow_available:
            return

        try:
            from airflow.utils.log.logging_mixin import LoggingMixin

            airflow_logger = LoggingMixin().log
            airflow_logger.info(
                f"ADRI assessment completed: {assessment_id} "
                f"(passed={assessment_result.passed}, "
                f"score={assessment_result.overall_score:.2f})"
            )

            # Log warning if assessment failed
            if not assessment_result.passed:
                airflow_logger.warning(
                    f"Assessment {assessment_id} failed quality check"
                )

            # Push to XCom if enabled
            if self.push_to_xcom:
                ti = self._get_task_instance()
                if ti:
                    result_data = {
                        "assessment_id": assessment_id,
                        "passed": assessment_result.passed,
                        "score": assessment_result.overall_score,
                        "timestamp": (
                            assessment_result.assessment_date.isoformat()
                            if hasattr(assessment_result, "assessment_date")
                            and assessment_result.assessment_date
                            else None
                        ),
                    }
                    ti.xcom_push(
                        key=f"{self.xcom_key_prefix}_{assessment_id}_result",
                        value=result_data,
                    )
        except Exception as e:
            logger.debug(f"Could not log to Airflow: {e}")

    def on_assessment_error(self, assessment_id: str, error: Exception) -> None:
        """Log assessment error to Airflow."""
        if not self._airflow_available:
            return

        try:
            from airflow.utils.log.logging_mixin import LoggingMixin

            airflow_logger = LoggingMixin().log
            airflow_logger.error(
                f"ADRI assessment error: {assessment_id} - {error}", exc_info=error
            )

            # Push error to XCom if enabled
            if self.push_to_xcom:
                ti = self._get_task_instance()
                if ti:
                    error_data = {
                        "assessment_id": assessment_id,
                        "error": str(error),
                        "error_type": type(error).__name__,
                    }
                    ti.xcom_push(
                        key=f"{self.xcom_key_prefix}_{assessment_id}_error",
                        value=error_data,
                    )
        except Exception as e:
            logger.debug(f"Could not log to Airflow: {e}")
