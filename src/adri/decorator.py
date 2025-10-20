"""
ADRI Guard Decorator.

Main decorator interface migrated from adri/decorators/guard.py.
Provides the @adri_protected decorator for protecting agent workflows from dirty data.
"""

import functools
import logging
from typing import Callable, Dict, Optional

# Clean imports for modular architecture
from .guard.modes import DataProtectionEngine, ProtectionError

logger = logging.getLogger(__name__)


def adri_protected(
    standard: Optional[str] = None,
    data_param: str = "data",
    min_score: Optional[float] = None,
    dimensions: Optional[Dict[str, float]] = None,
    on_failure: Optional[str] = None,
    on_assessment: Optional[Callable] = None,
    auto_generate: bool = True,
    cache_assessments: Optional[bool] = None,
    verbose: Optional[bool] = None,
    reasoning_mode: bool = False,
    store_prompt: bool = True,
    store_response: bool = True,
    llm_config: Optional[Dict] = None,
    workflow_context: Optional[Dict] = None,
    data_provenance: Optional[Dict] = None,
):
    """
    Protect agent functions with ADRI data quality checks.

    This decorator validates data quality using environment-based standard resolution.
    The standard location is determined by your active environment (dev/prod) as
    configured in adri-config.yaml, ensuring governance and consistency.

    Args:
        standard: Standard name (REQUIRED) - e.g., "customer_data" or "financial_data"
                 NOTE: Only names are accepted, not file paths. The actual file location
                 is determined by your environment configuration:
                 - Dev: ./ADRI/dev/standards/{standard}.yaml
                 - Prod: ./ADRI/prod/standards/{standard}.yaml
        data_param: Name of the parameter containing data to check (default: "data")
        min_score: Minimum quality score required (0-100, uses config default if None)
        dimensions: Specific dimension requirements (e.g., {"validity": 19, "completeness": 18})
        on_failure: How to handle quality failures ("raise", "warn", "continue", uses config default if None)
        on_assessment: Optional callback function to receive AssessmentResult after assessment completes.
                      Signature: Callable[[AssessmentResult], None]. Useful for capturing assessment IDs
                      and results in workflow runners. Callback exceptions are logged as warnings without
                      disrupting the protection flow. (default: None)
        auto_generate: Whether to auto-generate missing standards (default: True)
        cache_assessments: Whether to cache assessment results (uses config default if None)
        verbose: Whether to show detailed protection logs (uses config default if None)
        reasoning_mode: Enable AI/LLM reasoning step validation (default: False)
        store_prompt: Store AI prompts to JSONL audit logs (default: True, only if reasoning_mode=True)
        store_response: Store AI responses to JSONL audit logs (default: True, only if reasoning_mode=True)
        llm_config: LLM configuration dict with keys: model, temperature, seed, max_tokens (optional)
        workflow_context: Workflow execution metadata dict with keys: run_id, workflow_id, workflow_version,
                         step_id, step_sequence, run_at_utc (optional, for workflow orchestration)
        data_provenance: Data source provenance dict with keys: source_type, and source-specific fields
                        (optional, for data lineage tracking)

    Returns:
        Decorated function that includes data quality protection

    Raises:
        ProtectionError: If data quality is insufficient and on_failure="raise"
        ValueError: If the specified data parameter is not found

    Examples:
        Basic usage with standard name only:
        ```python
        @adri_protected(standard="customer_data")
        def process_customers(data):
            return processed_data
        ```

        High-stakes production workflow:
        ```python
        @adri_protected(
            standard="financial_data",
            min_score=90,
            dimensions={"validity": 19, "completeness": 18},
            on_failure="raise"
        )
        def process_transaction(financial_data, metadata):
            return transaction_result
        ```

        Development with custom data parameter:
        ```python
        @adri_protected(
            standard="user_profile",
            data_param="user_data",
            min_score=70
        )
        def update_profile(user_data, settings):
            return updated_profile
        ```

        AI/LLM workflow with reasoning validation:
        ```python
        @adri_protected(
            standard="ai_reasoning_standard",
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
            standard="ai_decision_step",
            data_param="customer_data",
            workflow_context=workflow_context,
            data_provenance=data_provenance,
            on_failure="raise"
        )
        def assess_credit_risk(customer_data):
            # AI decision logic
            return risk_assessment
        ```

        Capturing assessment results with callback:
        ```python
        # Workflow runner tracking assessments
        assessment_log = []

        def capture_assessment(result):
            assessment_log.append({
                "assessment_id": result.assessment_id,
                "score": result.overall_score,
                "passed": result.passed
            })

        @adri_protected(
            standard="transaction_data",
            on_assessment=capture_assessment,
            on_failure="raise"
        )
        def process_transaction(data):
            # Process validated data
            return transaction_result

        # Assessment ID and results are captured without breaking decorator transparency
        result = process_transaction(transaction_data)
        # assessment_log now contains the assessment details
        ```

    Note:
        Standard files are automatically resolved based on your environment configuration.
        To control where standards are stored, update your adri-config.yaml file.

        When reasoning_mode=True, prompts and responses are logged to separate JSONL files
        (adri_reasoning_prompts.jsonl and adri_reasoning_responses.jsonl) with relational
        links to the main assessment logs via prompt_id and response_id fields.
    """

    # Check for missing standard parameter and provide helpful error message
    if standard is None:
        raise ValueError(
            "🛡️ ADRI Error: Missing required 'standard' parameter\n\n"
            "The @adri_protected decorator needs a name for your data quality standard.\n"
            "ADRI will use an existing standard or auto-create one with this name.\n\n"
            "Examples:\n"
            '  @adri_protected(standard="customer_data")\n'
            '  @adri_protected(standard="financial_transactions")\n\n'
            "What happens:\n"
            "  • If 'customer_data.yaml' exists → ADRI uses it\n"
            "  • If it doesn't exist → ADRI creates it from your data\n\n"
            "Available commands:\n"
            "  adri list-standards           # See existing standards\n"
            "  adri generate-standard <data> # Pre-create a standard\n\n"
            "For more help: adri --help"
        )

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Check if protection engine is available
                if DataProtectionEngine is None:
                    logger.warning(
                        "DataProtectionEngine not available, executing function without protection"
                    )
                    return func(*args, **kwargs)

                # Initialize protection engine
                engine = DataProtectionEngine()

                # Protect the function call with name-only standard resolution
                return engine.protect_function_call(
                    func=func,
                    args=args,
                    kwargs=kwargs,
                    data_param=data_param,
                    function_name=func.__name__,
                    standard_name=standard,
                    min_score=min_score,
                    dimensions=dimensions,
                    on_failure=on_failure,
                    on_assessment=on_assessment,
                    auto_generate=auto_generate,
                    cache_assessments=cache_assessments,
                    verbose=verbose,
                    reasoning_mode=reasoning_mode,
                    store_prompt=store_prompt,
                    store_response=store_response,
                    llm_config=llm_config,
                    workflow_context=workflow_context,
                    data_provenance=data_provenance,
                )

            except ProtectionError:
                # Re-raise protection errors as-is (they have detailed messages)
                raise
            except Exception as e:
                # Wrap unexpected errors with context
                logger.error(f"Unexpected error in @adri_protected decorator: {e}")
                if ProtectionError != Exception:
                    raise ProtectionError(
                        f"Data protection failed for function '{func.__name__}': {e}\n"
                        "This may indicate a configuration or system issue."
                    )
                else:
                    # Fallback if ProtectionError is not available
                    raise Exception(
                        f"Data protection failed for function '{func.__name__}': {e}"
                    )

        # Mark the function as ADRI protected
        setattr(wrapper, "_adri_protected", True)
        setattr(
            wrapper,
            "_adri_config",
            {
                "standard": standard,
                "data_param": data_param,
                "min_score": min_score,
                "dimensions": dimensions,
                "on_failure": on_failure,
                "on_assessment": on_assessment,
                "auto_generate": auto_generate,
                "cache_assessments": cache_assessments,
                "verbose": verbose,
                "workflow_context": workflow_context,
                "data_provenance": data_provenance,
            },
        )

        return wrapper

    return decorator


# Examples of common usage patterns (recommended configurations):
#
# High-quality production workflow:
# @adri_protected(standard="financial_data", min_score=90, on_failure="raise")
#
# Development/testing workflow:
# @adri_protected(standard="test_data", min_score=70, on_failure="warn", verbose=True)
#
# Financial-grade protection:
# @adri_protected(
#     standard="banking_data",
#     min_score=95,
#     dimensions={"validity": 19, "completeness": 19, "consistency": 18},
#     on_failure="raise"
# )
