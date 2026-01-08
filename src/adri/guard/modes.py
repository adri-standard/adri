# @ADRI_FEATURE[guard_protection_modes, scope=OPEN_SOURCE]
# Description: Data protection modes (fail-fast, selective, warn-only) for guard decorator
"""
ADRI Guard Modes.

Protection mode classes extracted and refactored from the original core/protection.py.
Provides clean separation of different protection strategies.
"""

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

# Clean imports for modular architecture
from ..analysis.contract_generator import ContractGenerator
from ..config.loader import ConfigurationLoader
from ..validator.engine import DataQualityAssessor

logger = logging.getLogger(__name__)


class FailureMode:
    """Stub class for failure mode configuration."""

    def __init__(self, mode_type: str = "default"):
        """Initialize FailureMode with mode type."""
        self.mode_type = mode_type


class ProtectionError(Exception):
    """Exception raised when data protection fails."""


class ProtectionMode(ABC):
    """
    Base class for all protection modes.

    Defines the interface that all protection modes must implement.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize protection mode with configuration."""
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def handle_failure(self, assessment_result: Any, error_message: str) -> None:
        """
        Handle assessment failure based on this protection mode's strategy.

        Args:
            assessment_result: The failed assessment result
            error_message: Formatted error message

        Raises:
            ProtectionError: If the mode requires stopping execution
        """

    @abstractmethod
    def handle_success(self, assessment_result: Any, success_message: str) -> None:
        """
        Handle assessment success based on this protection mode's strategy.

        Args:
            assessment_result: The successful assessment result
            success_message: Formatted success message
        """

    @property
    @abstractmethod
    def mode_name(self) -> str:
        """Return the name of this protection mode."""

    def get_description(self) -> str:
        """Return a description of what this protection mode does."""
        return f"{self.mode_name} protection mode"


class FailFastMode(ProtectionMode):
    """
    Fail-fast protection mode.

    Immediately raises an exception when data quality is insufficient.
    This is the strictest protection mode - no bad data passes through.
    """

    @property
    def mode_name(self) -> str:
        """Return the mode name."""
        return "fail-fast"

    def handle_failure(self, assessment_result: Any, error_message: str) -> None:
        """Raise ProtectionError to stop execution immediately."""
        self.logger.error("Fail-fast mode: %s", error_message)
        raise ProtectionError(error_message)

    def handle_success(
        self, assessment_result: Any, success_message: str, verbose: bool = False
    ) -> None:
        """Log success and continue execution.

        Args:
            assessment_result: The successful assessment result
            success_message: Formatted success message
            verbose: Whether to print to stdout (default: False to avoid corrupting JSON pipelines)
        """
        self.logger.info(f"Fail-fast mode success: {success_message}")
        if verbose:
            print(success_message)

    def get_description(self) -> str:
        """Return a description of this protection mode."""
        return "Fail-fast mode: Immediately stops execution when data quality is insufficient"


class SelectiveMode(ProtectionMode):
    """
    Selective protection mode.

    Continues execution but logs failures for later review.
    Allows some flexibility while maintaining audit trail.
    """

    @property
    def mode_name(self) -> str:
        """Return the mode name."""
        return "selective"

    def handle_failure(
        self, assessment_result: Any, error_message: str, verbose: bool = False
    ) -> None:
        """Log failure but continue execution.

        Args:
            assessment_result: The failed assessment result
            error_message: Formatted error message
            verbose: Whether to print to stdout (default: False to avoid corrupting JSON pipelines)
        """
        self.logger.warning(
            f"Selective mode: Data quality issue detected but continuing - {error_message}"
        )
        if verbose:
            print(
                "⚠️  ADRI Warning: Data quality below threshold but continuing execution"
            )
            print(f"📊 Score: {assessment_result.overall_score:.1f}")

    def handle_success(
        self, assessment_result: Any, success_message: str, verbose: bool = False
    ) -> None:
        """Log success and continue execution.

        Args:
            assessment_result: The successful assessment result
            success_message: Formatted success message
            verbose: Whether to print to stdout (default: False to avoid corrupting JSON pipelines)
        """
        self.logger.debug(f"Selective mode success: {success_message}")
        if verbose:
            print(
                f"✅ ADRI: Quality check passed ({assessment_result.overall_score:.1f}/100)"
            )

    def get_description(self) -> str:
        """Return a description of this protection mode."""
        return "Selective mode: Logs quality issues but continues execution"


class WarnOnlyMode(ProtectionMode):
    """
    Warn-only protection mode.

    Shows warnings for quality issues but never stops execution.
    Useful for monitoring without impacting production workflows.
    """

    @property
    def mode_name(self) -> str:
        """Return the mode name."""
        return "warn-only"

    def handle_failure(
        self, assessment_result: Any, error_message: str, verbose: bool = False
    ) -> None:
        """Show warning but continue execution.

        Args:
            assessment_result: The failed assessment result
            error_message: Formatted error message
            verbose: Whether to print to stdout (default: False to avoid corrupting JSON pipelines)
        """
        self.logger.warning(f"Warn-only mode: {error_message}")
        if verbose:
            print("⚠️  ADRI Data Quality Warning:")
            print(f"📊 Score: {assessment_result.overall_score:.1f} (below threshold)")
            print("💡 Consider improving data quality for better AI agent performance")

    def handle_success(
        self, assessment_result: Any, success_message: str, verbose: bool = False
    ) -> None:
        """Log success quietly.

        Args:
            assessment_result: The successful assessment result
            success_message: Formatted success message
            verbose: Whether to print to stdout (default: False to avoid corrupting JSON pipelines)
        """
        self.logger.debug(f"Warn-only mode success: {success_message}")
        if verbose:
            print("✅ ADRI: Data quality check passed")

    def get_description(self) -> str:
        """Return a description of this protection mode."""
        return "Warn-only mode: Shows warnings but never stops execution"


class DataProtectionEngine:
    """
    Main data protection engine using configurable protection modes.

    Refactored from the original DataProtectionEngine to use the new mode-based architecture.
    """

    def __init__(self, protection_mode: ProtectionMode | None = None):
        """
        Initialize the data protection engine.

        Args:
            protection_mode: Protection mode to use (defaults to FailFastMode)
        """
        self.protection_mode = protection_mode or FailFastMode()
        self.config_manager = ConfigurationLoader() if ConfigurationLoader else None
        # Don't load config in __init__ - load it lazily when needed
        # This ensures we pick up the correct working directory
        self._protection_config = None
        self._full_config = None
        self._assessment_cache = {}
        self.logger = logging.getLogger(__name__)

        # Initialize loggers (will be configured when config is loaded)
        self.local_logger = None
        self.enterprise_logger = None

        self.logger.debug(
            f"DataProtectionEngine initialized with {self.protection_mode.mode_name} mode"
        )

    @property
    def protection_config(self) -> dict[str, Any]:
        """Get protection config, loading lazily if needed."""
        if self._protection_config is None:
            self._protection_config = self._load_protection_config()
        return self._protection_config

    @property
    def full_config(self) -> dict[str, Any]:
        """Get full config, loading lazily if needed."""
        if self._full_config is None:
            # Trigger loading via protection_config property
            _ = self.protection_config
        return self._full_config or {}

    def _load_protection_config(self) -> dict[str, Any]:
        """Load protection configuration."""
        if self.config_manager:
            try:
                # Load FULL config to include audit settings for DataQualityAssessor
                full_config = self.config_manager.load_config()
                if not full_config:
                    self._full_config = {}
                    return self._get_default_protection_config()

                # Extract the 'adri' section which contains audit, protection, etc.
                # DataQualityAssessor expects config with 'audit' at top level
                self._full_config = full_config.get("adri", {})

                # Extract protection config directly from _full_config
                # Don't use get_protection_config() as it expects environment structure
                protection_config = self._full_config.get("protection", {})

                # Merge with defaults for any missing keys
                default_config = self._get_default_protection_config()
                return {**default_config, **protection_config}

            except Exception as e:
                self.logger.warning(f"Failed to load config: {e}")
                # Don't reset _full_config on exception - keep what we have

        # Return default config
        if not self._full_config:
            self._full_config = {}
        return self._get_default_protection_config()

    def _get_default_protection_config(self) -> dict[str, Any]:
        """Get default protection configuration."""
        return {
            "default_min_score": 80,
            "default_failure_mode": "raise",
            "auto_generate_contracts": True,
            "cache_duration_hours": 1,
            "verbose_protection": False,
        }

    def protect_function_call(
        self,
        func: Callable,
        args: tuple,
        kwargs: dict,
        data_param: str,
        function_name: str,
        contract_name: str | None = None,
        min_score: float | None = None,
        dimensions: dict[str, float] | None = None,
        on_failure: str | None = None,
        on_assessment: Callable[[Any], None] | None = None,
        auto_generate: bool | None = None,
        cache_assessments: bool | None = None,
        verbose: bool | None = None,
        reasoning_mode: bool = False,
        workflow_context: dict | None = None,
    ) -> Any:
        """
        Protect a function call with data quality checks.

        Args:
            func: Function to protect
            args: Function positional arguments
            kwargs: Function keyword arguments
            data_param: Name of parameter containing data to check
            function_name: Name of the function being protected
            contract_name: Contract name (name-only, resolved via environment config)
            min_score: Minimum quality score required
            dimensions: Specific dimension requirements
            on_failure: How to handle quality failures (overrides protection mode)
            auto_generate: Whether to auto-generate missing contracts
            cache_assessments: Whether to cache assessment results
            verbose: Whether to show verbose output

        Returns:
            Result of the protected function call

        Raises:
            ValueError: If data parameter is not found
            ProtectionError: If data quality is insufficient (fail-fast mode)
        """
        # Use unified threshold resolution for consistency with CLI
        from ..validator.engine import ThresholdResolver

        # Resolve contract name to file path using environment configuration
        resolved_contract_path = None
        if contract_name:
            resolved_contract_path = self._resolve_contract_file_path(contract_name)

        # Apply unified threshold resolution (same logic as CLI)
        # Note: We don't check if file exists here - let _ensure_standard_exists
        # handle it
        threshold_info = ThresholdResolver.resolve_assessment_threshold(
            standard_path=(
                resolved_contract_path
                if (resolved_contract_path and os.path.exists(resolved_contract_path))
                else None
            ),
            min_score_override=min_score,
            config=self.protection_config,
        )
        min_score = threshold_info.value

        if verbose:
            self.logger.info(
                "Threshold resolved: %s from %s",
                threshold_info.value,
                threshold_info.source,
            )
        verbose = (
            verbose
            if verbose is not None
            else self.protection_config.get("verbose_protection", False)
        )

        # Override protection mode if on_failure is specified
        effective_mode = self.protection_mode
        if on_failure:
            if on_failure == "raise":
                effective_mode = FailFastMode(self.protection_config)
            elif on_failure == "warn":
                effective_mode = WarnOnlyMode(self.protection_config)
            elif on_failure == "continue":
                effective_mode = SelectiveMode(self.protection_config)

        if verbose:
            self.logger.info(
                f"Protecting function '{function_name}' with {effective_mode.mode_name} mode, min_score={min_score}"
            )

        try:
            # Extract data from function parameters
            data = self._extract_data_parameter(func, args, kwargs, data_param)

            # Resolve contract name to filename
            contract_filename = self._resolve_contract(
                function_name, data_param, contract_name
            )

            # Get full path using environment config
            if not resolved_contract_path:
                resolved_contract_path = self._resolve_contract_file_path(
                    contract_filename.replace(".yaml", "")
                )

            # Determine if auto-generation should be enabled
            should_auto_generate = (
                auto_generate
                if auto_generate is not None
                else self.protection_config.get("auto_generate_contracts", True)
            )

            # Ensure contract exists at the resolved path
            self._ensure_contract_exists(
                resolved_contract_path, data, auto_generate=should_auto_generate
            )

            # Assess data quality using the resolved path
            start_time = time.time()
            assessment_result = self._assess_data_quality(
                data, resolved_contract_path, reasoning_mode=reasoning_mode
            )
            assessment_duration = time.time() - start_time

            if verbose:
                self.logger.info(
                    f"Assessment completed in {assessment_duration:.2f}s, score: {assessment_result.overall_score:.1f}"
                )

            # Invoke assessment callback if provided (before pass/fail checking)
            self._invoke_assessment_callback(on_assessment, assessment_result, verbose)

            # Check if assessment passed
            assessment_passed = assessment_result.overall_score >= min_score

            # Check dimension requirements if specified
            if dimensions and assessment_passed:
                assessment_passed = self._check_dimension_requirements(
                    assessment_result, dimensions
                )

            # Handle result based on protection mode
            if assessment_passed:
                success_message = self._format_success_message(
                    assessment_result,
                    min_score,
                    resolved_contract_path,
                    function_name,
                    verbose,
                )
                effective_mode.handle_success(
                    assessment_result, success_message, verbose=verbose
                )
            else:
                error_message = self._format_error_message(
                    assessment_result, min_score, resolved_contract_path
                )
                effective_mode.handle_failure(assessment_result, error_message)

            # Execute the protected function
            return func(*args, **kwargs)

        except ProtectionError:
            # Re-raise protection errors (from fail-fast mode)
            raise
        except Exception as e:
            self.logger.error(f"Protection engine error: {e}")
            raise ProtectionError(f"Data protection failed: {e}")

    def _extract_data_parameter(
        self, func: Callable, args: tuple, kwargs: dict, data_param: str
    ) -> Any:
        """Extract the data parameter from function arguments."""
        import inspect

        # Check kwargs first
        if data_param in kwargs:
            return kwargs[data_param]

        # Check positional args
        try:
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            if data_param in params:
                param_index = params.index(data_param)
                if param_index < len(args):
                    return args[param_index]
        except Exception as e:
            self.logger.warning(f"Could not inspect function signature: {e}")

        raise ValueError(
            f"Could not find data parameter '{data_param}' in function arguments.\n"
            f"Available kwargs: {list(kwargs.keys())}\n"
            f"Available positional args: {len(args)} arguments"
        )

    def _resolve_contract(
        self, function_name: str, data_param: str, contract_name: str | None = None
    ) -> str:
        """
        Resolve which contract to use for protection.

        Uses name-only resolution for governance compliance.
        """
        if contract_name:
            return f"{contract_name}.yaml"

        # Auto-generate contract name from function and parameter
        pattern = self.protection_config.get(
            "contract_naming_pattern", "{function_name}_{data_param}_contract.yaml"
        )
        return pattern.format(function_name=function_name, data_param=data_param)

    def _ensure_contract_exists(
        self, contract_path: str, sample_data: Any, auto_generate: bool = True
    ) -> None:
        """Ensure a contract exists, using full ContractGenerator for rich rules.

        This uses the SAME ContractGenerator as the CLI to ensure consistent,
        high-quality contracts with full profiling and rule inference.

        Args:
            contract_path: Full path to the contract file
            sample_data: Sample data to generate contract from
            auto_generate: Whether to auto-generate the contract if missing

        Raises:
            ProtectionError: If contract doesn't exist and auto_generate is False
        """
        # Resolve path to handle macOS symlinks (/var -> /private/var)
        contract_path = str(Path(contract_path).resolve())

        self.logger.info("Checking if contract exists at: %s", contract_path)
        if os.path.exists(contract_path):
            self.logger.info("Contract already exists, skipping auto-generation")
            return

        # Check if auto-generation is enabled
        if not auto_generate:
            raise ProtectionError(
                f"Contract file not found at: {contract_path}\n"
                f"Auto-generation is disabled (auto_generate=False)"
            )

        self.logger.info(
            "Auto-generating contract with full profiling: %s", contract_path
        )

        try:
            # Create directory if needed
            dir_path = os.path.dirname(contract_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
                self.logger.debug("Created directory: %s", dir_path)

            # Convert data to DataFrame
            if not isinstance(sample_data, pd.DataFrame):
                if isinstance(sample_data, list):
                    df = pd.DataFrame(sample_data)
                elif isinstance(sample_data, dict):
                    df = pd.DataFrame([sample_data])
                else:
                    raise ProtectionError(
                        f"Cannot generate contract from data type: {type(sample_data)}"
                    )
            else:
                df = sample_data

            # Extract data name from contract path
            data_name = Path(contract_path).stem.replace("_contract", "")

            # Use SAME generator as CLI for consistency and rich rule generation
            generator = ContractGenerator()

            # Generate rich contract with full profiling and rule inference
            # This includes: allowed_values, min/max_value, patterns, length_bounds,
            # date_bounds, etc.
            contract_dict = generator.generate(
                data=df,
                data_name=data_name,
                generation_config={"overall_minimum": 75.0},  # Match CLI defaults
            )

            # Save to YAML
            with open(contract_path, "w", encoding="utf-8") as f:
                yaml.dump(contract_dict, f, default_flow_style=False, sort_keys=False)

            self.logger.info(
                "Successfully generated rich contract at: %s", contract_path
            )

            # Validate the generated contract to ensure it's valid
            try:
                from ..contracts.validator import get_validator

                validator = get_validator()
                result = validator.validate_contract_file(
                    contract_path, use_cache=False
                )

                if not result.is_valid:
                    self.logger.error(
                        "Generated contract failed validation: %s",
                        result.format_errors(),
                    )
                    raise ProtectionError(
                        f"Generated contract is invalid:\n{result.format_errors()}"
                    )

                self.logger.debug("Generated contract passed validation")

            except ImportError:
                # Validator not available, skip validation
                self.logger.debug(
                    "ContractValidator not available, skipping validation"
                )

        except ProtectionError:
            # Re-raise ProtectionError as-is
            raise
        except Exception as e:
            # Log the actual error for debugging
            self.logger.error(
                "Failed to generate contract at %s: %s", contract_path, e, exc_info=True
            )
            raise ProtectionError(f"Failed to generate contract: {e}")

    def _assess_data_quality(
        self, data: Any, standard_path: str, reasoning_mode: bool = False
    ) -> Any:
        """Assess data quality against a standard using same engine as CLI."""
        # Handle JSON strings from AI reasoning steps
        if reasoning_mode and isinstance(data, str):
            self.logger.info("🤖 Reasoning mode: Parsing JSON string from AI response")
            try:
                # Remove markdown code fences if present
                content = data.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

                # Parse JSON
                parsed_data = json.loads(content)
                self.logger.info(
                    f"✅ JSON parsed successfully (type: {type(parsed_data).__name__})"
                )

                # Use parsed data for assessment
                data = parsed_data

            except json.JSONDecodeError as e:
                # JSON syntax error - this is a schema validation failure
                error_msg = (
                    f"AI response contains invalid JSON syntax: {e}\n"
                    f"Error location: {getattr(e, 'msg', 'unknown')}\n"
                    f"Line {getattr(e, 'lineno', 'unknown')}, column {getattr(e, 'colno', 'unknown')}\n"
                    f"Character position: {getattr(e, 'pos', 'unknown')}\n"
                    f"Response preview: {content[:500]}..."
                )
                self.logger.error(f"❌ JSON Parse Error: {error_msg}")
                raise ProtectionError(error_msg)

        # Convert data to DataFrame if needed (same logic as CLI)
        if not isinstance(data, pd.DataFrame):
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Handle dict with scalar values by wrapping in a list
                df = pd.DataFrame([data])
            else:
                raise ProtectionError(f"Cannot assess data type: {type(data)}")
        else:
            df = data

        # Use the same assessor as CLI for identical scoring logic
        # CRITICAL: Pass None (not {}) to allow DataQualityAssessor to auto-discover
        # audit config from environment variables (ADRI_LOG_DIR, ADRI_CONFIG_PATH)
        # Passing {} explicitly disables audit logging, which breaks decorator parity
        config_for_assessor = self.full_config

        # If full_config is empty/None, pass None to enable auto-discovery
        if not config_for_assessor:
            config_for_assessor = None

        assessor = DataQualityAssessor(config_for_assessor)
        result = assessor.assess(df, standard_path)

        # Mark the result with decorator source for debugging
        if hasattr(result, "assessment_source"):
            result.assessment_source = "decorator"

        return result

    def _check_dimension_requirements(
        self, assessment_result: Any, dimensions: dict[str, float]
    ) -> bool:
        """Check dimension-specific requirements."""
        if not hasattr(assessment_result, "dimension_scores"):
            return True

        for dim_name, required_score in dimensions.items():
            if dim_name in assessment_result.dimension_scores:
                dim_score_obj = assessment_result.dimension_scores[dim_name]
                actual_score = (
                    dim_score_obj.score if hasattr(dim_score_obj, "score") else 0
                )
                if actual_score < required_score:
                    return False

        return True

    def _format_error_message(
        self, assessment_result: Any, min_score: float, contract: str
    ) -> str:
        """Format a detailed error message with schema validation feedback."""
        contract_name = Path(contract).stem.replace("_contract", "")

        message_lines = ["🛡️ ADRI Protection: BLOCKED ❌", ""]

        # NEW: Check for schema validation issues FIRST
        if (
            hasattr(assessment_result, "metadata")
            and "schema_validation" in assessment_result.metadata
        ):
            schema_info = assessment_result.metadata["schema_validation"]
            warnings = schema_info.get("warnings", [])

            # Show CRITICAL and ERROR schema issues prominently
            critical_or_error_warnings = [
                w for w in warnings if w.get("severity") in ["CRITICAL", "ERROR"]
            ]

            if critical_or_error_warnings:
                message_lines.extend(
                    [
                        "⚠️  SCHEMA VALIDATION ISSUES DETECTED:",
                        f"   Field Match Rate: {schema_info.get('match_percentage', 0):.1f}%",
                        f"   Exact Matches: {schema_info.get('exact_matches', 0)}/{schema_info.get('total_standard_fields', 0)}",
                        "",
                    ]
                )

                # Show up to 3 most critical warnings
                for warning in critical_or_error_warnings[:3]:
                    severity_marker = (
                        "🔴" if warning.get("severity") == "CRITICAL" else "⚠️ "
                    )
                    message_lines.extend(
                        [
                            f"   {severity_marker} [{warning.get('severity')}] {warning.get('message', '')}"
                        ]
                    )

                    # Show remediation (truncated)
                    remediation = warning.get("remediation", "")
                    if remediation:
                        # Take first line or first 100 chars
                        remediation_preview = remediation.split("\n")[0][:100]
                        message_lines.append(f"   Fix: {remediation_preview}...")

                    # Show auto-fix hint for case mismatches
                    if (
                        warning.get("auto_fix_available")
                        and warning.get("type") == "FIELD_CASE_MISMATCH"
                    ):
                        case_matches = warning.get("case_insensitive_matches", {})
                        if case_matches:
                            # Show first 2 examples
                            examples = list(case_matches.items())[:2]
                            example_str = ", ".join(
                                [f"'{d}'→'{s}'" for d, s in examples]
                            )
                            message_lines.append(f"   Example fixes: {example_str}")

                    message_lines.append("")

        # Quality score information
        message_lines.extend(
            [
                f"📊 Quality Score: {assessment_result.overall_score:.1f}/100 (Required: {min_score:.1f}/100)",
                f"📋 Contract: {contract_name}",
                "",
                "🔧 Fix This:",
                f"   1. Review contract: adri show-contract {contract_name}",
                "   2. Fix data issues and retry",
                f"   3. Test fixes: adri assess <data> --contract {contract_name}",
            ]
        )

        return "\n".join(message_lines)

    def _resolve_contract_file_path(self, contract_name: str | None) -> str | None:
        """
        Resolve contract name to file path using environment configuration.

        Contract resolution is governance-controlled via adri-config.yaml.
        Only contract names are accepted (not file paths) to ensure:
        - Centralized control of contract locations
        - Environment-based resolution (dev/prod)
        - No path injection or security issues

        Args:
            contract_name: Name of the contract (e.g., "customer_data")

        Returns:
            Full path to contract file resolved via environment config
        """
        if not contract_name:
            return None

        loader = ConfigurationLoader()
        # Environment-based resolution:
        # dev -> ./ADRI/dev/contracts/{name}.yaml
        # prod -> ./ADRI/prod/contracts/{name}.yaml
        return loader.resolve_contract_path(contract_name)

    def _format_success_message(
        self,
        assessment_result: Any,
        min_score: float,
        contract: str,
        function_name: str,
        verbose: bool,
    ) -> str:
        """Format a success message."""
        contract_name = Path(contract).stem.replace("_contract", "")

        if verbose:
            return (
                f"🛡️ ADRI Protection: ALLOWED ✅\n"
                f"📊 Quality Score: {assessment_result.overall_score:.1f}/100 (Required: {min_score:.1f}/100)\n"
                f"📋 Contract: {contract_name}\n"
                f"🚀 Function: {function_name}"
            )
        else:
            return (
                f"🛡️ ADRI Protection: ALLOWED ✅\n"
                f"📊 Score: {assessment_result.overall_score:.1f}/100 | Contract: {contract_name}"
            )

    def _invoke_assessment_callback(
        self,
        callback: Callable[[Any], None] | None,
        assessment_result: Any,
        verbose: bool = False,
    ) -> None:
        """
        Safely invoke the assessment callback if provided.

        Callback exceptions are caught and logged as warnings to ensure
        they don't disrupt the data protection flow. The callback is an
        optional feature for capturing assessment metadata, not core protection.

        Args:
            callback: Optional callback function to invoke with assessment result
            assessment_result: Assessment result to pass to callback
            verbose: Whether to log callback invocation details
        """
        if callback is None:
            return

        try:
            if verbose:
                self.logger.debug(
                    f"Invoking assessment callback with result (score: {assessment_result.overall_score:.1f})"
                )

            # Invoke the callback with the assessment result
            callback(assessment_result)

            if verbose:
                self.logger.debug("Assessment callback completed successfully")

        except Exception as e:
            # Log callback errors as warnings but don't fail protection
            self.logger.warning(
                f"Assessment callback failed: {e}. "
                "Continuing with data protection flow. "
                "Check your callback implementation for errors.",
                exc_info=True,
            )


# Mode factory functions
def fail_fast_mode(config: dict[str, Any] | None = None) -> FailFastMode:
    """Create a fail-fast protection mode."""
    return FailFastMode(config)


def selective_mode(config: dict[str, Any] | None = None) -> SelectiveMode:
    """Create a selective protection mode."""
    return SelectiveMode(config)


def warn_only_mode(config: dict[str, Any] | None = None) -> WarnOnlyMode:
    """Create a warn-only protection mode."""
    return WarnOnlyMode(config)


# @ADRI_FEATURE_END[guard_protection_modes]
