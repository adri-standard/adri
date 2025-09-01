"""
ADRI Data Protection Engine.

Core functionality for protecting agent workflows from dirty data.
Handles standard generation, data assessment, and quality enforcement.
"""

import logging
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

import pandas as pd

from ..analysis.standard_generator import StandardGenerator
from ..config.manager import ConfigManager
from ..core.assessor import AssessmentEngine
from ..core.audit_logger import AuditLogger
from ..standards import StandardNotFoundError, StandardsLoader

logger = logging.getLogger(__name__)


class ProtectionError(Exception):
    """Exception raised when data protection fails."""

    pass


class DataProtectionEngine:
    """
    Core engine for data quality protection in agent workflows.

    Handles:
    - Standard resolution and generation
    - Data quality assessment
    - Quality failure handling
    - Caching and performance optimization
    """

    def __init__(self):
        """Initialize the data protection engine."""
        self.config_manager = ConfigManager()
        self.protection_config = self.config_manager.get_protection_config()
        self._assessment_cache = {}
        self.standards_loader = StandardsLoader()

        # Initialize audit logger with audit configuration
        audit_config = self.config_manager.get_audit_config()
        self.audit_logger = AuditLogger(config=audit_config)

        logger.debug("DataProtectionEngine initialized")

    def resolve_standard(
        self,
        function_name: str,
        data_param: str,
        standard_file: Optional[str] = None,
        standard_name: Optional[str] = None,
    ) -> Union[str, Dict]:
        """
        Resolve which standard to use for protection.

        This method tries bundled standards first, then falls back to file-based standards.

        Args:
            function_name: Name of the function being protected
            data_param: Name of the data parameter
            standard_file: Explicit standard file path (highest priority)
            standard_name: Custom standard name (medium priority)

        Returns:
            Either a file path (str) for file-based standards or a dict for bundled standards
        """
        # Try bundled standards first
        bundled_standard = self._try_bundled_standard(
            function_name, data_param, standard_file, standard_name
        )
        if bundled_standard is not None:
            return bundled_standard

        # Fall back to file-based standards
        if standard_file:
            # Explicit standard file specified
            return self.config_manager.resolve_standard_path_simple(standard_file)

        if standard_name:
            # Custom standard name specified
            standard_filename = f"{standard_name}.yaml"
            return self.config_manager.resolve_standard_path_simple(standard_filename)

        # Auto-generate standard name from function and parameter
        pattern = self.protection_config.get(
            "standard_naming_pattern", "{function_name}_{data_param}_standard.yaml"
        )
        standard_filename = pattern.format(
            function_name=function_name, data_param=data_param
        )

        return self.config_manager.resolve_standard_path_simple(standard_filename)

    def _try_bundled_standard(
        self,
        function_name: str,
        data_param: str,
        standard_file: Optional[str] = None,
        standard_name: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Try to find a matching bundled standard.

        Args:
            function_name: Name of the function being protected
            data_param: Name of the data parameter
            standard_file: Explicit standard file path
            standard_name: Custom standard name

        Returns:
            Bundled standard dict if found, None otherwise
        """
        try:
            # If explicit standard file is specified, try to find it in bundled standards
            if standard_file:
                # Extract just the filename without path and extension
                base_name = Path(standard_file).stem
                if base_name.endswith("_standard"):
                    base_name = base_name[:-9]  # Remove '_standard' suffix

                if self.standards_loader.standard_exists(base_name):
                    logger.debug(
                        f"Found bundled standard for explicit file: {base_name}"
                    )
                    return self.standards_loader.load_standard(base_name)

            # If custom standard name is specified, try to find it
            if standard_name:
                if self.standards_loader.standard_exists(standard_name):
                    logger.debug(f"Found bundled standard: {standard_name}")
                    return self.standards_loader.load_standard(standard_name)

            # Try common naming patterns for bundled standards
            potential_names = [
                f"{function_name}_{data_param}_standard",
                f"{data_param}_standard",
                f"{function_name}_standard",
                "customer_data_standard",  # Common fallback
                "high_quality_agent_data_standard",  # Generic high-quality standard
            ]

            for name in potential_names:
                if self.standards_loader.standard_exists(name):
                    logger.debug(
                        f"Found bundled standard with pattern matching: {name}"
                    )
                    return self.standards_loader.load_standard(name)

            logger.debug(
                "No matching bundled standard found, falling back to file-based standards"
            )
            return None

        except StandardNotFoundError:
            logger.debug(
                "Bundled standard not found, falling back to file-based standards"
            )
            return None
        except Exception as e:
            logger.warning(
                f"Error trying bundled standards: {e}, falling back to file-based standards"
            )
            return None

    def ensure_standard_exists(
        self, standard: Union[str, Dict], sample_data: Any
    ) -> bool:
        """
        Ensure a standard exists, generating it if necessary.

        Args:
            standard: Either a file path (str) or bundled standard dict
            sample_data: Sample data to generate standard from

        Returns:
            True if standard exists or was created successfully

        Raises:
            ProtectionError: If standard generation fails
        """
        # If it's a bundled standard (dict), it already exists
        if isinstance(standard, dict):
            logger.debug("Using bundled standard (already exists)")
            return True

        # It's a file path, check if it exists
        standard_path = standard
        if os.path.exists(standard_path):
            logger.debug(f"Standard already exists: {standard_path}")
            return True

        if not self.protection_config.get("auto_generate_standards", True):
            raise ProtectionError(
                f"Standard file not found: {standard_path}\n"
                "Auto-generation is disabled. Please create the standard manually or enable auto_generate_standards."
            )

        logger.info(f"Generating new standard: {standard_path}")

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(standard_path), exist_ok=True)

            # Convert data to DataFrame if needed
            if not isinstance(sample_data, pd.DataFrame):
                if hasattr(sample_data, "to_pandas"):
                    # Handle other data types that can convert to pandas
                    df = sample_data.to_pandas()
                elif isinstance(sample_data, (list, dict)):
                    df = pd.DataFrame(sample_data)
                else:
                    raise ProtectionError(
                        f"Cannot generate standard from data type: {type(sample_data)}\n"
                        "Supported types: pandas.DataFrame, list, dict"
                    )
            else:
                df = sample_data

            # Apply data sampling if configured
            sampling_limit = self.protection_config.get("data_sampling_limit", 1000)
            if len(df) > sampling_limit:
                logger.info(
                    f"Sampling {sampling_limit} rows from {len(df)} total rows for standard generation"
                )
                df = df.head(sampling_limit)

            # Use proper ADRI workflow: Profile data then generate standard
            from ..analysis.data_profiler import DataProfiler

            # Profile the data to understand its structure
            profiler = DataProfiler()
            data_profile = profiler.profile_data(df, max_rows=sampling_limit)

            # Generate standard using the profile
            generator = StandardGenerator()
            data_name = (
                os.path.basename(standard_path)
                .replace("_standard.yaml", "")
                .replace(".yaml", "")
            )

            # Get generation configuration from protection config
            generation_config = self.protection_config.get(
                "generation",
                {
                    "default_thresholds": {
                        "completeness_min": 85,
                        "validity_min": 90,
                        "consistency_min": 80,
                    }
                },
            )

            standard_dict = generator.generate_standard(
                data_profile=data_profile,
                data_name=data_name,
                generation_config=generation_config,
            )

            # Save standard to YAML file
            import yaml

            with open(standard_path, "w") as f:
                yaml.dump(
                    standard_dict,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    indent=2,
                )

            logger.info(f"Successfully generated standard: {standard_path}")
            return True

        except Exception as e:
            raise ProtectionError(f"Failed to generate standard: {e}")

    def assess_data_quality(self, data: Any, standard: Union[str, Dict]) -> Any:
        """
        Assess data quality against a standard with caching.

        Args:
            data: Data to assess
            standard: Either a file path (str) or bundled standard dict

        Returns:
            Assessment result object

        Raises:
            ProtectionError: If assessment fails
        """
        # Generate cache key
        data_hash = self._generate_data_hash(data)
        if isinstance(standard, dict):
            # For bundled standards, use the standard ID for caching
            standard_id = standard.get("standards", {}).get("id", "bundled_standard")
            cache_key = f"bundled:{standard_id}:{data_hash}"
        else:
            # For file-based standards, use the file path
            cache_key = f"{standard}:{data_hash}"

        # Check cache
        cache_duration_hours = self.protection_config.get("cache_duration_hours", 1)
        if cache_duration_hours > 0 and cache_key in self._assessment_cache:
            cached_result, timestamp = self._assessment_cache[cache_key]
            if time.time() - timestamp < cache_duration_hours * 3600:
                logger.debug(f"Using cached assessment result for {cache_key}")
                return cached_result

        if isinstance(standard, dict):
            logger.debug(
                f"Running fresh assessment with bundled standard: {standard.get('standards', {}).get('id', 'unknown')}"
            )
        else:
            logger.debug(f"Running fresh assessment for {standard}")

        try:
            # Convert data to DataFrame if needed
            if not isinstance(data, pd.DataFrame):
                if hasattr(data, "to_pandas"):
                    df = data.to_pandas()
                elif isinstance(data, (list, dict)):
                    df = pd.DataFrame(data)
                else:
                    raise ProtectionError(
                        f"Cannot assess data type: {type(data)}\n"
                        "Supported types: pandas.DataFrame, list, dict"
                    )
            else:
                df = data

            # Run assessment
            assessor = AssessmentEngine()

            if isinstance(standard, dict):
                # For bundled standards, pass the dict directly
                result = assessor.assess_with_standard_dict(df, standard)
            else:
                # For file-based standards, pass the file path
                result = assessor.assess(df, standard)

            # Cache result
            if cache_duration_hours > 0:
                self._assessment_cache[cache_key] = (result, time.time())

            return result

        except Exception as e:
            raise ProtectionError(f"Assessment failed: {e}")

    def handle_quality_failure(
        self,
        assessment_result: Any,
        failure_mode: str,
        min_score: float,
        standard_path: Optional[str] = None,
    ) -> None:
        """
        Handle data quality failure based on configured mode.

        Args:
            assessment_result: The failed assessment result
            failure_mode: How to handle failure ("raise", "warn", "continue")
            min_score: The minimum required score
            standard_path: Path to the standard file (for error messages)

        Raises:
            ProtectionError: If failure_mode is "raise"
        """
        error_message = self._format_quality_error(
            assessment_result, min_score, standard_path
        )

        if failure_mode == "raise":
            raise ProtectionError(error_message)
        elif failure_mode == "warn":
            logger.warning(f"Data quality warning: {error_message}")
        elif failure_mode == "continue":
            logger.debug(f"Data quality failure (continuing): {error_message}")
        else:
            # Invalid failure mode, default to raise
            logger.error(
                f"Invalid failure mode '{failure_mode}', defaulting to 'raise'"
            )
            raise ProtectionError(error_message)

    def protect_function_call(
        self,
        func: Callable,
        args: tuple,
        kwargs: dict,
        data_param: str,
        function_name: str,
        standard_file: Optional[str] = None,
        standard_name: Optional[str] = None,
        min_score: Optional[float] = None,
        dimensions: Optional[Dict[str, float]] = None,
        on_failure: Optional[str] = None,
        auto_generate: Optional[bool] = None,
        cache_assessments: Optional[bool] = None,
        verbose: Optional[bool] = None,
    ) -> Any:
        """
        Protect a function call with data quality checks.

        Args:
            func: Function to protect
            args: Function positional arguments
            kwargs: Function keyword arguments
            data_param: Name of parameter containing data to check
            function_name: Name of the function being protected
            standard_file: Explicit standard file to use
            standard_name: Custom standard name
            min_score: Minimum quality score required
            dimensions: Specific dimension requirements
            on_failure: How to handle quality failures
            auto_generate: Whether to auto-generate missing standards
            cache_assessments: Whether to cache assessment results
            verbose: Whether to show verbose output

        Returns:
            Result of the protected function call

        Raises:
            ValueError: If data parameter is not found
            ProtectionError: If data quality is insufficient
        """
        # Extract data from function parameters
        data = self._extract_data_parameter(func, args, kwargs, data_param)

        # Apply configuration defaults
        min_score = (
            min_score
            if min_score is not None
            else self.protection_config.get("default_min_score", 80)
        )
        on_failure = (
            on_failure
            if on_failure is not None
            else self.protection_config.get("default_failure_mode", "raise")
        )
        verbose = (
            verbose
            if verbose is not None
            else self.protection_config.get("verbose_protection", False)
        )

        if verbose:
            logger.info(
                f"Protecting function '{function_name}' with min_score={min_score}"
            )

        # Resolve standard (could be file path or bundled standard dict)
        standard = self.resolve_standard(
            function_name, data_param, standard_file, standard_name
        )

        if verbose:
            if isinstance(standard, dict):
                standard_id = standard.get("standards", {}).get(
                    "id", "bundled_standard"
                )
                logger.info(f"Using bundled standard: {standard_id}")
            else:
                logger.info(f"Using standard file: {standard}")

        # Ensure standard exists
        self.ensure_standard_exists(standard, data)

        # Track assessment start time for performance metrics
        start_time = time.time()

        # Assess data quality
        assessment_result = self.assess_data_quality(data, standard)
        assessment_duration = time.time() - start_time

        if verbose:
            logger.info(
                f"Assessment score: {assessment_result.overall_score}/{min_score}"
            )

        # Prepare audit log context
        standard_info = {}
        if isinstance(standard, dict):
            standard_info = {
                "type": "bundled",
                "id": standard.get("standards", {}).get("id", "unknown"),
                "name": standard.get("standards", {}).get("name", "unknown"),
                "version": standard.get("standards", {}).get("version", "1.0.0"),
            }
        else:
            standard_info = {
                "type": "file",
                "path": standard,
                "name": Path(standard).stem.replace("_standard", ""),
            }

        # Check if assessment passed
        assessment_passed = assessment_result.overall_score >= min_score

        # Check dimension requirements if specified
        dimension_failures = []
        if dimensions and assessment_passed:
            for dim_name, required_score in dimensions.items():
                if dim_name in assessment_result.dimension_scores:
                    dim_score_obj = assessment_result.dimension_scores[dim_name]
                    actual_score = (
                        dim_score_obj.score if hasattr(dim_score_obj, "score") else 0
                    )
                    if actual_score < required_score:
                        assessment_passed = False
                        dimension_failures.append(
                            {
                                "dimension": dim_name,
                                "actual": actual_score,
                                "required": required_score,
                            }
                        )

        # Log the assessment to audit trail
        try:
            # Prepare execution context for audit logging
            execution_context = {
                "function_name": function_name,
                "data_param": data_param,
                "min_score": min_score,
                "on_failure": on_failure,
                "standard_info": standard_info,
                "dimension_requirements": dimensions,
                "dimension_failures": dimension_failures,
                "assessment_duration": assessment_duration,
                "assessment_passed": assessment_passed,
            }

            # Prepare data info
            data_info = {
                "data_shape": data.shape if isinstance(data, pd.DataFrame) else None,
                "data_type": type(data).__name__,
            }

            if isinstance(data, pd.DataFrame):
                data_info["row_count"] = len(data)
                data_info["column_count"] = len(data.columns)
                data_info["columns"] = list(data.columns)

            # Log the assessment using the single log_assessment method
            self.audit_logger.log_assessment(
                assessment_result=assessment_result,
                execution_context=execution_context,
                data_info=data_info,
            )

        except Exception as e:
            logger.warning(f"Failed to create audit log: {e}")
            # Continue execution even if audit logging fails

        # Handle failures if assessment didn't pass
        if not assessment_passed:
            if assessment_result.overall_score < min_score:
                # Pass standard path only if standard is a string (file path)
                standard_path = standard if isinstance(standard, str) else None
                self.handle_quality_failure(
                    assessment_result, on_failure, min_score, standard_path
                )

            # Check dimension-specific requirements
            if dimensions:
                self._check_dimension_requirements(
                    assessment_result, dimensions, on_failure
                )

        # Quality checks passed, execute the function
        success_message = self._format_quality_success(
            assessment_result, min_score, standard, function_name, verbose
        )

        if verbose:
            logger.info(success_message)
        else:
            # Always show some success indication, even in non-verbose mode
            print(success_message)

        return func(*args, **kwargs)

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
            logger.warning(f"Could not inspect function signature: {e}")

        raise ValueError(
            f"Could not find data parameter '{data_param}' in function arguments.\n"
            f"Available kwargs: {list(kwargs.keys())}\n"
            f"Available positional args: {len(args)} arguments"
        )

    def _generate_data_hash(self, data: Any) -> str:
        """Generate a hash for data caching."""
        import hashlib

        try:
            if isinstance(data, pd.DataFrame):
                # Use shape and column names for DataFrame hash
                content = f"{data.shape}:{list(data.columns)}:{data.dtypes.to_dict()}"
            else:
                content = str(data)[:1000]  # Limit to avoid memory issues

            return hashlib.sha256(content.encode()).hexdigest()[:16]
        except Exception:
            # Fallback to timestamp-based cache key
            return str(int(time.time()))

    def _format_quality_error(
        self,
        assessment_result: Any,
        min_score: float,
        standard: Union[str, Dict, None] = None,
    ) -> str:
        """Format a detailed quality error message with actionable CLI commands."""
        # Extract standard name for CLI commands
        standard_name = "your-standard"
        if isinstance(standard, str):
            # File-based standard
            standard_name = Path(standard).stem.replace("_standard", "")
        elif isinstance(standard, dict):
            # Bundled standard
            standards_section = standard.get("standards", {})
            standard_name = standards_section.get("id", "bundled-standard")

        error_lines = [
            "🛡️ ADRI Protection: BLOCKED ❌",
            "",
            "❌ Data quality too low for reliable agent execution",
            "   Your agent needs high-quality data to work properly. ADRI prevented execution to protect against unreliable results.",
            "",
            "📊 Quality Assessment:",
            f"   Overall Score: {assessment_result.overall_score:.1f}/100 (Required: {min_score:.1f}/100)",
        ]

        if isinstance(standard, str):
            error_lines.append(f"   Standard: {standard}")
        elif isinstance(standard, dict):
            standards_section = standard.get("standards", {})
            standard_id = standards_section.get("id", "bundled-standard")
            error_lines.append(f"   Standard: {standard_id} (bundled)")

        # Add dimension breakdown if available
        if hasattr(assessment_result, "dimension_scores"):
            error_lines.extend(["", "   📋 Dimension Details:"])

            # Identify the main problem areas
            problem_dimensions = []
            for dim_name, dim_result in assessment_result.dimension_scores.items():
                score = dim_result.score if hasattr(dim_result, "score") else 0
                status = "✅" if score >= 15 else "❌"  # Assuming 15/20 is good
                error_lines.append(f"   {status} {dim_name.title()}: {score:.1f}/20")
                if score < 15:
                    problem_dimensions.append(dim_name)

        # Add specific problem identification
        main_issues = self._identify_main_issues(assessment_result, problem_dimensions)
        if main_issues:
            error_lines.extend(["", "🔍 Main Issues Found:", f"   {main_issues}"])

        # Add actionable CLI commands
        error_lines.extend(
            [
                "",
                "🔧 Fix This Now:",
                "   1. adri export-report --latest",
                f"   2. adri show-standard {standard_name}",
                f"   3. adri assess <fixed-data> --standard {standard_name}",
                "",
                "💬 Message for Your Data Team:",
                '   "Our AI agent requires data meeting the attached ADRI standard. Current data fails',
                f'   quality checks ({main_issues if main_issues else "multiple issues"}). Please review the',
                '   attached report and fix the identified issues."',
                "",
                "📞 Need Help?",
                "   • View detailed report: adri list-assessments --recent 1 --verbose",
                "   • Understand requirements: adri validate-standard " + standard_name,
                "   • Test your fixes: adri assess <your-data> --standard "
                + standard_name,
            ]
        )

        return "\n".join(error_lines)

    def _identify_main_issues(
        self, assessment_result: Any, problem_dimensions: list
    ) -> str:
        """Identify the main data quality issues for user-friendly messaging."""
        if not problem_dimensions:
            return "quality threshold not met"

        issue_descriptions = {
            "validity": "invalid data formats detected (e.g., bad emails, invalid dates)",
            "completeness": "missing required data fields",
            "consistency": "inconsistent data formats across records",
            "freshness": "data is too old or timestamps are invalid",
            "plausibility": "unrealistic values detected (outliers, impossible ranges)",
        }

        main_issues = []
        for dim in problem_dimensions[:2]:  # Show top 2 issues
            if dim in issue_descriptions:
                main_issues.append(issue_descriptions[dim])

        if len(main_issues) == 1:
            return main_issues[0]
        elif len(main_issues) == 2:
            return f"{main_issues[0]} and {main_issues[1]}"
        else:
            return f"{len(problem_dimensions)} data quality issues"

    def _format_quality_success(
        self,
        assessment_result: Any,
        min_score: float,
        standard: Union[str, Dict, None] = None,
        function_name: str = "function",
        verbose: bool = False,
    ) -> str:
        """Format a quality success message with tiered verbosity levels."""
        # Extract standard name and metadata
        standard_name = "your-standard"
        standard_version = "1.0.0"
        standard_created = False

        if isinstance(standard, dict):
            # Bundled standard
            standards_section = standard.get("standards", {})
            standard_name = standards_section.get("name", "bundled-standard")
            standard_version = standards_section.get("version", "1.0.0")
            standard_created = False  # Bundled standards are never "just created"
        elif isinstance(standard, str):
            # File-based standard
            standard_name = Path(standard).stem.replace("_standard", "")
            # Try to extract version from standard file if it exists
            if os.path.exists(standard):
                try:
                    import yaml

                    with open(standard, "r") as f:
                        standard_data = yaml.safe_load(f)
                        if (
                            "standards" in standard_data
                            and "version" in standard_data["standards"]
                        ):
                            standard_version = standard_data["standards"]["version"]
                except Exception as e:
                    logger.warning(f"Error reading standard version: {e}")
                    # Use default version if can't read

            # Check if this was a new standard creation
            standard_created = self._was_standard_just_created(standard)

        # Build success message based on verbosity level
        if verbose:
            return self._format_verbose_success(
                assessment_result,
                min_score,
                standard_name,
                standard_version,
                standard_created,
                standard if isinstance(standard, str) else None,
            )
        else:
            return self._format_minimal_success(
                assessment_result,
                min_score,
                standard_name,
                standard_version,
                standard_created,
            )

    def _format_minimal_success(
        self,
        assessment_result: Any,
        min_score: float,
        standard_name: str,
        standard_version: str,
        standard_created: bool,
    ) -> str:
        """Format minimal success message for non-verbose mode."""
        new_indicator = " (NEW)" if standard_created else ""

        return (
            f"🛡️ ADRI Protection: ALLOWED ✅\n"
            f"📊 Quality Score: {assessment_result.overall_score:.1f}/100 (Required: {min_score:.1f}/100)\n"
            f"📋 Standard: {standard_name} v{standard_version}{new_indicator}"
        )

    def _format_verbose_success(
        self,
        assessment_result: Any,
        min_score: float,
        standard_name: str,
        standard_version: str,
        standard_created: bool,
        standard_path: Optional[str] = None,
    ) -> str:
        """Format detailed success message for verbose mode."""
        new_indicator = " (NEW)" if standard_created else ""

        success_lines = [
            "🛡️ ADRI Protection: ALLOWED ✅",
            "✅ Data quality meets requirements for reliable execution",
            "",
            "📊 Quality Assessment:",
            f"   Overall Score: {assessment_result.overall_score:.1f}/100 (Required: {min_score:.1f}/100)",
            f"   Standard Applied: {standard_name} v{standard_version}{new_indicator}",
        ]

        # Add dimension breakdown
        if hasattr(assessment_result, "dimension_scores"):
            success_lines.append("   📋 All dimensions passed quality checks")
            success_lines.append("")
            success_lines.append("   Dimension Details:")

            for dim_name, dim_result in assessment_result.dimension_scores.items():
                score = dim_result.score if hasattr(dim_result, "score") else 0
                status = "✅" if score >= 15 else "⚠️"
                success_lines.append(f"   {status} {dim_name.title()}: {score:.1f}/20")

        # Add new standard guidance
        if standard_created:
            success_lines.extend(
                [
                    "",
                    "🎯 Since this is a NEW standard:",
                    f"   • Review details: adri show-standard {standard_name} --verbose",
                    "   • See all standards: adri list-standards --verbose",
                    f"   • Validate standard: adri validate-standard {standard_name}",
                    "",
                    "📚 Customize Your Standard:",
                    "   • Add domain rules: https://github.com/your-org/adri-standard/blob/main/ADRI/docs/custom-rules.md",
                    "   • Adjust settings: https://github.com/your-org/adri-standard/blob/main/ADRI/docs/configuration.md",
                ]
            )
        else:
            success_lines.extend(
                [
                    "",
                    "🔍 Learn More:",
                    f"   • View standard details: adri show-standard {standard_name}",
                    "   • See assessment history: adri list-assessments --recent 5",
                    f"   • Validate new data: adri assess <data> --standard {standard_name}",
                ]
            )

        return "\n".join(success_lines)

    def _was_standard_just_created(self, standard_path: Optional[str]) -> bool:
        """Check if a standard was just created (within the last few seconds)."""
        if not standard_path or not os.path.exists(standard_path):
            return False

        try:
            # Check if file was created very recently (within last 5 seconds)
            file_age = time.time() - os.path.getctime(standard_path)
            return file_age < 5.0
        except Exception:
            return False

    def _check_dimension_requirements(
        self, assessment_result: Any, dimensions: Dict[str, float], on_failure: str
    ) -> None:
        """Check dimension-specific requirements."""
        if not hasattr(assessment_result, "dimension_scores"):
            logger.warning("Assessment result does not contain dimension scores")
            return

        for dim_name, required_score in dimensions.items():
            if dim_name in assessment_result.dimension_scores:
                dim_score_obj = assessment_result.dimension_scores[dim_name]
                actual_score = (
                    dim_score_obj.score if hasattr(dim_score_obj, "score") else 0
                )
                if actual_score < required_score:
                    error_msg = (
                        f"Dimension '{dim_name}' score insufficient: "
                        f"{actual_score:.1f}/20 (required: {required_score:.1f}/20)"
                    )

                    if on_failure == "raise":
                        raise ProtectionError(error_msg)
                    elif on_failure == "warn":
                        logger.warning(f"Data quality warning: {error_msg}")
                    # Continue silently for "continue" mode
            else:
                error_msg = f"Required dimension '{dim_name}' not found in assessment"
                if on_failure == "raise":
                    raise ProtectionError(error_msg)
                elif on_failure == "warn":
                    logger.warning(f"Data quality warning: {error_msg}")
