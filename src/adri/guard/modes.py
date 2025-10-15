"""
ADRI Guard Modes.

Protection mode classes extracted and refactored from the original core/protection.py.
Provides clean separation of different protection strategies.
"""

import logging
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import pandas as pd
import yaml

# Clean imports for modular architecture
from ..analysis.standard_generator import StandardGenerator
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

    pass


class ProtectionMode(ABC):
    """
    Base class for all protection modes.

    Defines the interface that all protection modes must implement.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
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
        pass

    @abstractmethod
    def handle_success(self, assessment_result: Any, success_message: str) -> None:
        """
        Handle assessment success based on this protection mode's strategy.

        Args:
            assessment_result: The successful assessment result
            success_message: Formatted success message
        """
        pass

    @property
    @abstractmethod
    def mode_name(self) -> str:
        """Return the name of this protection mode."""
        pass

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

    def handle_success(self, assessment_result: Any, success_message: str) -> None:
        """Log success and continue execution."""
        self.logger.info(f"Fail-fast mode success: {success_message}")
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

    def handle_failure(self, assessment_result: Any, error_message: str) -> None:
        """Log failure but continue execution."""
        self.logger.warning(
            f"Selective mode: Data quality issue detected but continuing - {error_message}"
        )
        print("⚠️  ADRI Warning: Data quality below threshold but continuing execution")
        print(f"📊 Score: {assessment_result.overall_score:.1f}")

    def handle_success(self, assessment_result: Any, success_message: str) -> None:
        """Log success and continue execution."""
        self.logger.debug(f"Selective mode success: {success_message}")
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

    def handle_failure(self, assessment_result: Any, error_message: str) -> None:
        """Show warning but continue execution."""
        self.logger.warning(f"Warn-only mode: {error_message}")
        print("⚠️  ADRI Data Quality Warning:")
        print(f"📊 Score: {assessment_result.overall_score:.1f} (below threshold)")
        print("💡 Consider improving data quality for better AI agent performance")

    def handle_success(self, assessment_result: Any, success_message: str) -> None:
        """Log success quietly."""
        self.logger.debug(f"Warn-only mode success: {success_message}")
        print("✅ ADRI: Data quality check passed")

    def get_description(self) -> str:
        """Return a description of this protection mode."""
        return "Warn-only mode: Shows warnings but never stops execution"


class DataProtectionEngine:
    """
    Main data protection engine using configurable protection modes.

    Refactored from the original DataProtectionEngine to use the new mode-based architecture.
    """

    def __init__(self, protection_mode: Optional[ProtectionMode] = None):
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
    def protection_config(self) -> Dict[str, Any]:
        """Get protection config, loading lazily if needed."""
        if self._protection_config is None:
            self._protection_config = self._load_protection_config()
        return self._protection_config

    @property
    def full_config(self) -> Dict[str, Any]:
        """Get full config, loading lazily if needed."""
        if self._full_config is None:
            # Trigger loading via protection_config property
            _ = self.protection_config
        return self._full_config or {}

    def _load_protection_config(self) -> Dict[str, Any]:
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
                pass

        # Return default config
        if not self._full_config:
            self._full_config = {}
        return self._get_default_protection_config()

    def _get_default_protection_config(self) -> Dict[str, Any]:
        """Get default protection configuration."""
        return {
            "default_min_score": 80,
            "default_failure_mode": "raise",
            "auto_generate_standards": True,
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
        standard_name: Optional[str] = None,
        min_score: Optional[float] = None,
        dimensions: Optional[Dict[str, float]] = None,
        on_failure: Optional[str] = None,
        on_assessment: Optional[Callable[[Any], None]] = None,
        auto_generate: Optional[bool] = None,
        cache_assessments: Optional[bool] = None,
        verbose: Optional[bool] = None,
        reasoning_mode: bool = False,
        store_prompt: bool = True,
        store_response: bool = True,
        llm_config: Optional[Dict] = None,
        workflow_context: Optional[Dict] = None,
        data_provenance: Optional[Dict] = None,
    ) -> Any:
        """
        Protect a function call with data quality checks.

        Args:
            func: Function to protect
            args: Function positional arguments
            kwargs: Function keyword arguments
            data_param: Name of parameter containing data to check
            function_name: Name of the function being protected
            standard_name: Standard name (name-only, resolved via environment config)
            min_score: Minimum quality score required
            dimensions: Specific dimension requirements
            on_failure: How to handle quality failures (overrides protection mode)
            auto_generate: Whether to auto-generate missing standards
            cache_assessments: Whether to cache assessment results
            verbose: Whether to show verbose output
            reasoning_mode: Enable AI/LLM reasoning step validation
            store_prompt: Store AI prompts to JSONL audit logs
            store_response: Store AI responses to JSONL audit logs
            llm_config: LLM configuration dict
            workflow_context: Workflow execution metadata for orchestration tracking (optional)
            data_provenance: Data source provenance for lineage tracking (optional)

        Returns:
            Result of the protected function call

        Raises:
            ValueError: If data parameter is not found
            ProtectionError: If data quality is insufficient (fail-fast mode)
        """
        # Use unified threshold resolution for consistency with CLI
        from ..validator.engine import ThresholdResolver

        # Resolve standard name to file path using environment configuration
        resolved_standard_path = None
        if standard_name:
            resolved_standard_path = self._resolve_standard_file_path(standard_name)

        # Apply unified threshold resolution (same logic as CLI)
        # Note: We don't check if file exists here - let _ensure_standard_exists handle it
        threshold_info = ThresholdResolver.resolve_assessment_threshold(
            standard_path=(
                resolved_standard_path
                if (resolved_standard_path and os.path.exists(resolved_standard_path))
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

            # Resolve standard name to filename
            standard_filename = self._resolve_standard(
                function_name, data_param, standard_name
            )

            # Get full path using environment config
            if not resolved_standard_path:
                resolved_standard_path = self._resolve_standard_file_path(
                    standard_filename.replace(".yaml", "")
                )

            # Determine if auto-generation should be enabled
            should_auto_generate = (
                auto_generate
                if auto_generate is not None
                else self.protection_config.get("auto_generate_standards", True)
            )

            # Ensure standard exists at the resolved path
            self._ensure_standard_exists(
                resolved_standard_path, data, auto_generate=should_auto_generate
            )

            # Assess data quality using the resolved path
            start_time = time.time()
            assessment_result = self._assess_data_quality(data, resolved_standard_path)
            assessment_duration = time.time() - start_time

            if verbose:
                self.logger.info(
                    f"Assessment completed in {assessment_duration:.2f}s, score: {assessment_result.overall_score:.1f}"
                )

            # Invoke assessment callback if provided (before pass/fail checking)
            self._invoke_assessment_callback(on_assessment, assessment_result, verbose)

            # Workflow logging not available in open-source version
            # For workflow orchestration and data provenance tracking, use adri-enterprise
            if workflow_context and verbose:
                self.logger.info(
                    "Workflow context provided but logging not available in open-source version"
                )

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
                    resolved_standard_path,
                    function_name,
                    verbose,
                )
                effective_mode.handle_success(assessment_result, success_message)
            else:
                error_message = self._format_error_message(
                    assessment_result, min_score, resolved_standard_path
                )
                effective_mode.handle_failure(assessment_result, error_message)

            # Reasoning mode not available in open-source version
            # For AI reasoning logging and validation, use adri-enterprise
            if reasoning_mode and verbose:
                self.logger.warning(
                    "Reasoning mode requested but not available in open-source version"
                )

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

    def _resolve_standard(
        self,
        function_name: str,
        data_param: str,
        standard_name: Optional[str] = None,
    ) -> str:
        """
        Resolve which standard to use for protection.

        Uses name-only resolution for governance compliance.
        """
        if standard_name:
            return f"{standard_name}.yaml"

        # Auto-generate standard name from function and parameter
        pattern = self.protection_config.get(
            "standard_naming_pattern", "{function_name}_{data_param}_standard.yaml"
        )
        return pattern.format(function_name=function_name, data_param=data_param)

    def _ensure_standard_exists(
        self, standard_path: str, sample_data: Any, auto_generate: bool = True
    ) -> None:
        """Ensure a standard exists, using full StandardGenerator for rich rules.

        This uses the SAME StandardGenerator as the CLI to ensure consistent,
        high-quality standards with full profiling and rule inference.

        Args:
            standard_path: Full path to the standard file
            sample_data: Sample data to generate standard from
            auto_generate: Whether to auto-generate the standard if missing

        Raises:
            ProtectionError: If standard doesn't exist and auto_generate is False
        """
        self.logger.info("Checking if standard exists at: %s", standard_path)
        if os.path.exists(standard_path):
            self.logger.info("Standard already exists, skipping auto-generation")
            return

        # Check if auto-generation is enabled
        if not auto_generate:
            raise ProtectionError(
                f"Standard file not found at: {standard_path}\n"
                f"Auto-generation is disabled (auto_generate=False)"
            )

        self.logger.info(
            "Auto-generating standard with full profiling: %s", standard_path
        )

        try:
            # Create directory if needed
            dir_path = os.path.dirname(standard_path)
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
                        f"Cannot generate standard from data type: {type(sample_data)}"
                    )
            else:
                df = sample_data

            # Extract data name from standard path
            data_name = Path(standard_path).stem.replace("_standard", "")

            # Use SAME generator as CLI for consistency and rich rule generation
            generator = StandardGenerator()

            # Generate rich standard with full profiling and rule inference
            # This includes: allowed_values, min/max_value, patterns, length_bounds, date_bounds, etc.
            standard_dict = generator.generate(
                data=df,
                data_name=data_name,
                generation_config={"overall_minimum": 75.0},  # Match CLI defaults
            )

            # Save to YAML
            with open(standard_path, "w", encoding="utf-8") as f:
                yaml.dump(standard_dict, f, default_flow_style=False, sort_keys=False)

            self.logger.info(
                "Successfully generated rich standard at: %s", standard_path
            )

            # Validate the generated standard to ensure it's valid
            try:
                from adri.standards.validator import get_validator

                validator = get_validator()
                result = validator.validate_standard_file(
                    standard_path, use_cache=False
                )

                if not result.is_valid:
                    self.logger.error(
                        "Generated standard failed validation: %s",
                        result.format_errors(),
                    )
                    raise ProtectionError(
                        f"Generated standard is invalid:\n{result.format_errors()}"
                    )

                self.logger.debug("Generated standard passed validation")

            except ImportError:
                # Validator not available, skip validation
                self.logger.debug(
                    "StandardValidator not available, skipping validation"
                )

        except ProtectionError:
            # Re-raise ProtectionError as-is
            raise
        except Exception as e:
            # Log the actual error for debugging
            self.logger.error(
                "Failed to generate standard at %s: %s", standard_path, e, exc_info=True
            )
            raise ProtectionError(f"Failed to generate standard: {e}")

    def _assess_data_quality(self, data: Any, standard_path: str) -> Any:
        """Assess data quality against a standard using same engine as CLI."""
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
        # Pass FULL config (not just protection_config) to enable audit logging
        # DataQualityAssessor needs the 'audit' section from full config
        config_for_assessor = getattr(self, "full_config", self.protection_config)
        assessor = DataQualityAssessor(config_for_assessor)
        result = assessor.assess(df, standard_path)

        # Mark the result with decorator source for debugging
        if hasattr(result, "assessment_source"):
            result.assessment_source = "decorator"

        return result

    def _check_dimension_requirements(
        self, assessment_result: Any, dimensions: Dict[str, float]
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
        self, assessment_result: Any, min_score: float, standard: str
    ) -> str:
        """Format a detailed error message."""
        standard_name = Path(standard).stem.replace("_standard", "")

        message_lines = [
            "🛡️ ADRI Protection: BLOCKED ❌",
            "",
            f"📊 Quality Score: {assessment_result.overall_score:.1f}/100 (Required: {min_score:.1f}/100)",
            f"📋 Standard: {standard_name}",
            "",
            "🔧 Fix This:",
            f"   1. Review standard: adri show-standard {standard_name}",
            "   2. Fix data issues and retry",
            f"   3. Test fixes: adri assess <data> --standard {standard_name}",
        ]

        return "\n".join(message_lines)

    def _resolve_standard_file_path(
        self, standard_name: Optional[str]
    ) -> Optional[str]:
        """
        Resolve standard name to file path using environment configuration.

        Standard resolution is governance-controlled via adri-config.yaml.
        Only standard names are accepted (not file paths) to ensure:
        - Centralized control of standard locations
        - Environment-based resolution (dev/prod)
        - No path injection or security issues

        Args:
            standard_name: Name of the standard (e.g., "customer_data")

        Returns:
            Full path to standard file resolved via environment config
        """
        if not standard_name:
            return None

        loader = ConfigurationLoader()
        # Environment-based resolution:
        # dev -> ./ADRI/dev/standards/{name}.yaml
        # prod -> ./ADRI/prod/standards/{name}.yaml
        return loader.resolve_standard_path(standard_name)

    def _format_success_message(
        self,
        assessment_result: Any,
        min_score: float,
        standard: str,
        function_name: str,
        verbose: bool,
    ) -> str:
        """Format a success message."""
        standard_name = Path(standard).stem.replace("_standard", "")

        if verbose:
            return (
                f"🛡️ ADRI Protection: ALLOWED ✅\n"
                f"📊 Quality Score: {assessment_result.overall_score:.1f}/100 (Required: {min_score:.1f}/100)\n"
                f"📋 Standard: {standard_name}\n"
                f"🚀 Function: {function_name}"
            )
        else:
            return (
                f"🛡️ ADRI Protection: ALLOWED ✅\n"
                f"📊 Score: {assessment_result.overall_score:.1f}/100 | Standard: {standard_name}"
            )

    def _invoke_assessment_callback(
        self,
        callback: Optional[Callable[[Any], None]],
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
def fail_fast_mode(config: Optional[Dict[str, Any]] = None) -> FailFastMode:
    """Create a fail-fast protection mode."""
    return FailFastMode(config)


def selective_mode(config: Optional[Dict[str, Any]] = None) -> SelectiveMode:
    """Create a selective protection mode."""
    return SelectiveMode(config)


def warn_only_mode(config: Optional[Dict[str, Any]] = None) -> WarnOnlyMode:
    """Create a warn-only protection mode."""
    return WarnOnlyMode(config)
