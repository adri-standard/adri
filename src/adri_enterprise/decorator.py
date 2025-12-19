"""
ADRI Enterprise Decorator.

Enterprise wrapper extending the open source @adri_protected decorator with:
- AI reasoning step validation (reasoning_mode)
- Workflow orchestration context tracking (workflow_context)
- Data provenance and lineage tracking (data_provenance)
- Verodat API integration for centralized logging
- License validation requiring valid Verodat API key

This decorator wraps the base open source decorator, adding enterprise features
while delegating core functionality to maintain compatibility.

IMPORTANT: The verodat-adri package requires a valid Verodat API key to function.
Set the VERODAT_API_KEY environment variable before using this decorator.
"""

import functools
import logging
from collections.abc import Callable
from typing import Any

# Import base decorator from open source package
from adri.decorator import adri_protected as base_adri_protected
from adri.guard.modes import ProtectionError

# Import license validation
from adri_enterprise.license import (
    LicenseValidationError,
    validate_license,
)

logger = logging.getLogger(__name__)

# Track if license has been validated this session
_license_validated = False


def adri_protected(
    contract: str | None = None,
    data_param: str = "data",
    min_score: float | None = None,
    dimensions: dict[str, float] | None = None,
    on_failure: str | None = None,
    on_assessment: Callable | None = None,
    auto_generate: bool = True,
    cache_assessments: bool | None = None,
    verbose: bool | None = None,
    # Enterprise-specific parameters
    reasoning_mode: bool = False,
    store_prompt: bool = True,
    store_response: bool = True,
    llm_config: dict | None = None,
    workflow_context: dict | None = None,
    data_provenance: dict | None = None,
):
    """
    Enterprise version of @adri_protected with additional features.

    Extends the open source decorator with enterprise capabilities:
    - AI reasoning step logging and validation
    - Workflow orchestration context tracking
    - Data provenance and lineage tracking
    - Verodat API integration for centralized logging

    All open source parameters are supported and delegated to the base decorator.

    Args:
        contract: Contract name (REQUIRED) - e.g., "customer_data"
        data_param: Name of the parameter containing data to check (default: "data")
        min_score: Minimum quality score required (0-100)
        dimensions: Specific dimension requirements
        on_failure: How to handle quality failures ("raise", "warn", "continue")
        on_assessment: Optional callback function to receive AssessmentResult
        auto_generate: Whether to auto-generate missing contracts (default: True)
        cache_assessments: Whether to cache assessment results
        verbose: Whether to show detailed protection logs

        reasoning_mode: Enable AI/LLM reasoning step validation (default: False)
        store_prompt: Store AI prompts to JSONL audit logs (default: True)
        store_response: Store AI responses to JSONL audit logs (default: True)
        llm_config: LLM configuration dict with keys: model, temperature, seed, max_tokens
        workflow_context: Workflow execution metadata dict with keys:
                         run_id, workflow_id, workflow_version, step_id, step_sequence, run_at_utc
        data_provenance: Data source provenance dict with keys:
                        source_type, and source-specific fields (verodat_query_id, etc.)

    Returns:
        Decorated function that includes data quality protection with enterprise features

    Raises:
        ProtectionError: If data quality is insufficient and on_failure="raise"
        ValueError: If the specified data parameter is not found

    Examples:
        AI/LLM workflow with reasoning validation:
        ```python
        @adri_protected(
            contract="ai_reasoning_contract",
            data_param="projects",
            reasoning_mode=True,
            store_prompt=True,
            store_response=True,
            llm_config={
                "model": "claude-3-5-sonnet",
                "temperature": 0.1,
                "seed": 42
            }
        )
        def analyze_project_risks(projects):
            # AI reasoning logic here
            enhanced_data = ai_model.analyze(projects)
            return enhanced_data
        ```

        Workflow orchestration with context and provenance tracking:
        ```python
        workflow_context = {
            "run_id": "run_20250107_143022_a1b2c3d4",
            "workflow_id": "credit_approval_workflow",
            "workflow_version": "2.1.0",
            "step_id": "risk_assessment",
            "step_sequence": 3,
            "run_at_utc": "2025-01-07T14:30:22Z"
        }

        data_provenance = {
            "source_type": "verodat_query",
            "verodat_query_id": 12345,
            "verodat_account_id": 91,
            "verodat_workspace_id": 161,
            "record_count": 150
        }

        @adri_protected(
            contract="ai_decision_step",
            data_param="customer_data",
            workflow_context=workflow_context,
            data_provenance=data_provenance,
            on_failure="raise"
        )
        def assess_credit_risk(customer_data):
            # AI decision logic
            return risk_assessment
        ```
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            global _license_validated
            
            try:
                # Validate license on first use (lazy validation)
                if not _license_validated:
                    try:
                        validate_license()
                        _license_validated = True
                        logger.info("Verodat enterprise license validated successfully")
                    except LicenseValidationError as e:
                        logger.error(f"License validation failed: {e.message}")
                        if e.details:
                            logger.error(f"Details: {e.details}")
                        raise
                
                # Process enterprise features before base decorator
                if reasoning_mode and verbose:
                    logger.info(
                        f"Enterprise: Reasoning mode enabled for {func.__name__}"
                    )

                if workflow_context:
                    _log_workflow_context(workflow_context, func.__name__, verbose)

                if data_provenance:
                    _log_data_provenance(data_provenance, func.__name__, verbose)

                # Delegate to base decorator with open source + reasoning_mode parameters
                # reasoning_mode and workflow_context are now supported in base decorator
                base_decorator = base_adri_protected(
                    contract=contract,
                    data_param=data_param,
                    min_score=min_score,
                    dimensions=dimensions,
                    on_failure=on_failure,
                    on_assessment=on_assessment,
                    auto_generate=auto_generate,
                    cache_assessments=cache_assessments,
                    verbose=verbose,
                    reasoning_mode=reasoning_mode,
                    workflow_context=workflow_context,
                )

                # Execute the base decorated function
                result = base_decorator(func)(*args, **kwargs)

                # Post-processing: Log reasoning steps if enabled
                if reasoning_mode:
                    _log_reasoning_step(
                        func.__name__,
                        store_prompt,
                        store_response,
                        llm_config,
                        verbose,
                    )

                return result

            except ProtectionError:
                # Re-raise protection errors as-is
                raise
            except Exception as e:
                logger.error(
                    f"Enterprise decorator error for '{func.__name__}': {e}"
                )
                raise

        # Mark the function as ADRI protected (enterprise version)
        setattr(wrapper, "_adri_protected", True)
        setattr(wrapper, "_adri_enterprise", True)
        setattr(
            wrapper,
            "_adri_config",
            {
                "contract": contract,
                "data_param": data_param,
                "min_score": min_score,
                "dimensions": dimensions,
                "on_failure": on_failure,
                "on_assessment": on_assessment,
                "auto_generate": auto_generate,
                "cache_assessments": cache_assessments,
                "verbose": verbose,
                "reasoning_mode": reasoning_mode,
                "workflow_context": workflow_context,
                "data_provenance": data_provenance,
            },
        )

        return wrapper

    return decorator


def _log_workflow_context(
    workflow_context: dict[str, Any], function_name: str, verbose: bool = False
) -> None:
    """
    Log workflow orchestration context.

    This will be implemented in Phase 3 with full Verodat API integration.
    For now, provides basic logging.
    """
    if verbose:
        logger.info(
            f"Enterprise: Workflow context for {function_name}: "
            f"run_id={workflow_context.get('run_id')}, "
            f"workflow_id={workflow_context.get('workflow_id')}"
        )


def _log_data_provenance(
    data_provenance: dict[str, Any], function_name: str, verbose: bool = False
) -> None:
    """
    Log data provenance information.

    This will be implemented in Phase 3 with full Verodat API integration.
    For now, provides basic logging.
    """
    if verbose:
        logger.info(
            f"Enterprise: Data provenance for {function_name}: "
            f"source_type={data_provenance.get('source_type')}"
        )


def _log_reasoning_step(
    function_name: str,
    store_prompt: bool,
    store_response: bool,
    llm_config: dict | None,
    verbose: bool = False,
) -> None:
    """
    Log AI reasoning step information.

    This will be implemented in Phase 3 with reasoning step logging.
    For now, provides basic logging.
    """
    if verbose:
        logger.info(
            f"Enterprise: Reasoning mode for {function_name} "
            f"(store_prompt={store_prompt}, store_response={store_response})"
        )
        if llm_config:
            logger.info(f"Enterprise: LLM config: {llm_config}")
