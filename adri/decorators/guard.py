"""
ADRI Guard Decorator.

Provides the @adri_protected decorator for protecting agent workflows from dirty data.
"""

import functools
import logging
from typing import Callable, Dict, Optional

from ..core.protection import DataProtectionEngine, ProtectionError

logger = logging.getLogger(__name__)


def adri_protected(
    data_param: str = "data",
    standard_file: Optional[str] = None,
    standard_name: Optional[str] = None,
    standard_id: Optional[str] = None,
    min_score: Optional[float] = None,
    dimensions: Optional[Dict[str, float]] = None,
    on_failure: Optional[str] = None,
    auto_generate: Optional[bool] = None,
    cache_assessments: Optional[bool] = None,
    verbose: Optional[bool] = None,
):
    """
    Protect agent functions with ADRI data quality checks.

    This decorator automatically:
    1. Generates data quality standards (if they don't exist)
    2. Assesses data quality against the standard
    3. Guards function execution based on quality thresholds
    4. Provides detailed error reports when quality fails

    Args:
        data_param: Name of the parameter containing data to check (default: "data")
        standard_file: Explicit standard file to use (e.g., "customer_data.yaml")
        standard_name: Custom standard name (e.g., "customer_validation_v2")
        min_score: Minimum quality score required (0-100, uses config default if None)
        dimensions: Specific dimension requirements (e.g., {"validity": 19, "completeness": 18})
        on_failure: How to handle quality failures ("raise", "warn", "continue", uses config default if None)
        auto_generate: Whether to auto-generate missing standards (uses config default if None)
        cache_assessments: Whether to cache assessment results (uses config default if None)
        verbose: Whether to show detailed protection logs (uses config default if None)

    Returns:
        Decorated function that includes data quality protection

    Raises:
        ProtectionError: If data quality is insufficient and on_failure="raise"
        ValueError: If the specified data parameter is not found

    Examples:
        Basic protection with auto-generated standard:
        ```python
        @adri_protected(data_param="customer_data")
        def process_customers(customer_data):
            return processed_data
        ```

        Use existing standard file:
        ```python
        @adri_protected(
            data_param="claims_data",
            standard_file="insurance_claims_v2.yaml"
        )
        def validate_claim(claims_data):
            return validated_claim
        ```

        High-stakes workflow with strict requirements:
        ```python
        @adri_protected(
            data_param="financial_data",
            min_score=90,
            dimensions={"validity": 19, "completeness": 18},
            on_failure="raise"
        )
        def process_transaction(financial_data):
            return transaction_result
        ```

        Development-friendly configuration:
        ```python
        @adri_protected(
            data_param="test_data",
            min_score=70,
            on_failure="warn",
            verbose=True
        )
        def development_workflow(test_data):
            return results
        ```
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Initialize protection engine
                engine = DataProtectionEngine()

                # Protect the function call
                return engine.protect_function_call(
                    func=func,
                    args=args,
                    kwargs=kwargs,
                    data_param=data_param,
                    function_name=func.__name__,
                    standard_file=standard_file,
                    standard_name=standard_name,
                    min_score=min_score,
                    dimensions=dimensions,
                    on_failure=on_failure,
                    auto_generate=auto_generate,
                    cache_assessments=cache_assessments,
                    verbose=verbose,
                )

            except ProtectionError:
                # Re-raise protection errors as-is (they have detailed messages)
                raise
            except Exception as e:
                # Wrap unexpected errors with context
                logger.error(f"Unexpected error in @adri_protected decorator: {e}")
                raise ProtectionError(
                    f"Data protection failed for function '{func.__name__}': {e}\n"
                    "This may indicate a configuration or system issue."
                )

        # Mark the function as ADRI protected
        setattr(wrapper, "_adri_protected", True)
        setattr(
            wrapper,
            "_adri_config",
            {
                "data_param": data_param,
                "standard_file": standard_file,
                "standard_name": standard_name,
                "standard_id": standard_id,
                "min_score": min_score,
                "dimensions": dimensions,
                "on_failure": on_failure,
                "auto_generate": auto_generate,
                "cache_assessments": cache_assessments,
                "verbose": verbose,
            },
        )

        return wrapper

    return decorator


# Convenience aliases for common use cases
def adri_strict(data_param: str = "data", **kwargs):
    """
    Protect data strictly with high quality requirements.

    Equivalent to @adri_protected with min_score=90 and on_failure="raise".
    """
    return adri_protected(
        data_param=data_param,
        min_score=kwargs.pop("min_score", 90),
        on_failure=kwargs.pop("on_failure", "raise"),
        **kwargs,
    )


def adri_permissive(data_param: str = "data", **kwargs):
    """
    Provide permissive data protection for development and testing.

    Equivalent to @adri_protected with min_score=70 and on_failure="warn".
    """
    return adri_protected(
        data_param=data_param,
        min_score=kwargs.pop("min_score", 70),
        on_failure=kwargs.pop("on_failure", "warn"),
        verbose=kwargs.pop("verbose", True),
        **kwargs,
    )


def adri_financial(data_param: str = "data", **kwargs):
    """
    Apply financial-grade data protection with strict requirements.

    Equivalent to @adri_protected with high standards for financial data.
    """
    return adri_protected(
        data_param=data_param,
        min_score=kwargs.pop("min_score", 95),
        dimensions=kwargs.pop(
            "dimensions", {"validity": 19, "completeness": 19, "consistency": 18}
        ),
        on_failure=kwargs.pop("on_failure", "raise"),
        **kwargs,
    )
