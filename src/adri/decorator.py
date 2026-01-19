# @ADRI_FEATURE[decorator_adri_protected, scope=OPEN_SOURCE]
# Description: Core @adri_protected decorator for data quality protection in agent workflows
"""
ADRI Guard Decorator.

Main decorator interface migrated from adri/decorators/guard.py.
Provides the @adri_protected decorator for protecting agent workflows from dirty data.
"""

import functools
import logging
from collections.abc import Callable

# Clean imports for modular architecture
from .guard.modes import DataProtectionEngine, ProtectionError

logger = logging.getLogger(__name__)


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
    reasoning_mode: bool = False,
    workflow_context: dict | None = None,
):
    """
    Protect agent functions with ADRI data quality checks.

    This decorator validates data quality using environment-based contract resolution.
    The contract location is determined by your active environment (dev/prod) as
    configured in adri-config.yaml, ensuring governance and consistency.

    Args:
        contract: Contract name (REQUIRED) - e.g., "customer_data" or "financial_data"
                 NOTE: Only names are accepted, not file paths. The actual file location
                 is determined by your environment configuration:
                 - Dev: ./ADRI/dev/contracts/{contract}.yaml
                 - Prod: ./ADRI/prod/contracts/{contract}.yaml
        data_param: Name of the parameter containing data to check (default: "data")
        min_score: Minimum quality score required (0-100, uses config default if None)
        dimensions: Specific dimension requirements (e.g., {"validity": 19, "completeness": 18})
        on_failure: How to handle quality failures ("raise", "warn", "continue", uses config default if None)
        on_assessment: Optional callback function to receive AssessmentResult after assessment completes.
                      Signature: Callable[[AssessmentResult], None]. Useful for capturing assessment IDs
                      and results in workflow runners. Callback exceptions are logged as warnings without
                      disrupting the protection flow. (default: None)
        auto_generate: Whether to auto-generate missing contracts (default: True)
        cache_assessments: Whether to cache assessment results (uses config default if None)
        verbose: Whether to show detailed protection logs (uses config default if None)

    Returns:
        Decorated function that includes data quality protection

    Raises:
        ProtectionError: If data quality is insufficient and on_failure="raise"
        ValueError: If the specified data parameter is not found

    Examples:
        Basic usage with contract name only:
        ```python
        @adri_protected(contract="customer_data")
        def process_customers(data):
            return processed_data
        ```

        High-stakes production workflow:
        ```python
        @adri_protected(
            contract="financial_data",
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
            contract="user_profile",
            data_param="user_data",
            min_score=70
        )
        def update_profile(user_data, settings):
            return updated_profile
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
            contract="transaction_data",
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
        Contract files are automatically resolved based on your environment configuration.
        To control where contracts are stored, update your adri-config.yaml file.
    """

    # Check for missing contract parameter and provide helpful error message
    if contract is None:
        raise ValueError(
            "🛡️ ADRI Error: Missing required 'contract' parameter\n\n"
            "The @adri_protected decorator needs a name for your data quality contract.\n"
            "ADRI will use an existing contract or auto-create one with this name.\n\n"
            "Examples:\n"
            '  @adri_protected(contract="customer_data")\n'
            '  @adri_protected(contract="financial_transactions")\n\n'
            "What happens:\n"
            "  • If 'customer_data.yaml' exists → ADRI uses it\n"
            "  • If it doesn't exist → ADRI creates it from your data\n\n"
            "Available commands:\n"
            "  adri list-contracts           # See existing contracts\n"
            "  adri generate-contract <data> # Pre-create a contract\n\n"
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

                # Protect the function call with name-only contract resolution
                return engine.protect_function_call(
                    func=func,
                    args=args,
                    kwargs=kwargs,
                    data_param=data_param,
                    function_name=func.__name__,
                    contract_name=contract,
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
                "contract": contract,
                "data_param": data_param,
                "min_score": min_score,
                "dimensions": dimensions,
                "on_failure": on_failure,
                "on_assessment": on_assessment,
                "auto_generate": auto_generate,
                "cache_assessments": cache_assessments,
                "verbose": verbose,
            },
        )

        return wrapper

    return decorator


# Examples of common usage patterns (recommended configurations):
#
# High-quality production workflow:
# @adri_protected(contract="financial_data", min_score=90, on_failure="raise")
#
# Development/testing workflow:
# @adri_protected(contract="test_data", min_score=70, on_failure="warn", verbose=True)
#
# Financial-grade protection:
# @adri_protected(
#     contract="banking_data",
#     min_score=95,
#     dimensions={"validity": 19, "completeness": 19, "consistency": 18},
#     on_failure="raise"
# )
# @ADRI_FEATURE_END[decorator_adri_protected]
