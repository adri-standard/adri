"""Configuration management for the ADRI framework.

This module defines configuration dataclasses and management utilities that provide
centralized, type-safe configuration handling throughout the ADRI system.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .exceptions import ConfigurationError


@dataclass
class InferenceConfig:
    """Configuration for standard generation inference.

    Controls how the StandardGenerator infers field requirements and constraints
    from sample data during automatic standard creation.
    """

    # Enumeration inference settings
    enum_max_unique: int = 20
    """Maximum unique values before treating a field as non-enumerable"""

    enum_min_coverage: float = 0.8
    """Minimum coverage required for enumeration inference (0.0-1.0)"""

    # Numeric range inference settings
    range_margin_pct: float = 0.1
    """Percentage margin to add to inferred numeric ranges"""

    # Pattern inference settings
    regex_inference_enabled: bool = False
    """Whether to enable regex pattern inference (can be resource-intensive)"""

    # Date inference settings
    date_margin_days: int = 30
    """Number of days to add as margin for date range inference"""

    # Primary key inference settings
    max_pk_combo_size: int = 3
    """Maximum number of fields to consider for compound primary keys"""

    # Quality thresholds
    min_data_quality_for_inference: float = 0.7
    """Minimum data quality score required for reliable inference"""

    # Performance settings
    max_sample_size: int = 10000
    """Maximum number of records to analyze for inference"""

    inference_timeout_seconds: int = 300
    """Timeout for inference operations in seconds"""

    def validate(self) -> list[str]:
        """Validate configuration values.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not 1 <= self.enum_max_unique <= 1000:
            errors.append("enum_max_unique must be between 1 and 1000")

        if not 0.0 <= self.enum_min_coverage <= 1.0:
            errors.append("enum_min_coverage must be between 0.0 and 1.0")

        if not 0.0 <= self.range_margin_pct <= 1.0:
            errors.append("range_margin_pct must be between 0.0 and 1.0")

        if self.date_margin_days < 0:
            errors.append("date_margin_days must be non-negative")

        if not 1 <= self.max_pk_combo_size <= 10:
            errors.append("max_pk_combo_size must be between 1 and 10")

        if not 0.0 <= self.min_data_quality_for_inference <= 1.0:
            errors.append("min_data_quality_for_inference must be between 0.0 and 1.0")

        if self.max_sample_size <= 0:
            errors.append("max_sample_size must be positive")

        if self.inference_timeout_seconds <= 0:
            errors.append("inference_timeout_seconds must be positive")

        return errors


@dataclass
class ValidationConfig:
    """Configuration for validation engine operations.

    Controls how the ValidationEngine performs data quality assessments
    and handles various validation scenarios.
    """

    # Audit and logging settings
    audit_enabled: bool = True
    """Whether to enable comprehensive audit logging"""

    performance_tracking: bool = True
    """Whether to track and log performance metrics"""

    # Retry and timeout settings
    max_retries: int = 3
    """Maximum number of retries for failed operations"""

    timeout_seconds: int = 30
    """Timeout for individual validation operations"""

    # Validation behavior settings
    fail_fast: bool = False
    """Whether to stop validation on first failure"""

    strict_mode: bool = False
    """Whether to use strict validation (no error tolerance)"""

    # Memory and performance settings
    chunk_size: int = 1000
    """Number of records to process in each chunk"""

    parallel_processing: bool = False
    """Whether to enable parallel processing of validation tasks"""

    max_workers: int | None = None
    """Maximum number of worker threads (None for auto-detection)"""

    # Result settings
    include_field_analysis: bool = True
    """Whether to include detailed field analysis in results"""

    include_sample_failures: bool = True
    """Whether to include sample failure records in results"""

    max_sample_failures: int = 100
    """Maximum number of sample failures to include"""

    # Dimension-specific settings
    dimension_weights: dict[str, float] = field(
        default_factory=lambda: {
            "validity": 1.0,
            "completeness": 1.0,
            "consistency": 1.0,
            "freshness": 1.0,
            "plausibility": 1.0,
        }
    )
    """Default weights for quality dimensions"""

    def validate(self) -> list[str]:
        """Validate configuration values.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if self.max_retries < 0:
            errors.append("max_retries must be non-negative")

        if self.timeout_seconds <= 0:
            errors.append("timeout_seconds must be positive")

        if self.chunk_size <= 0:
            errors.append("chunk_size must be positive")

        if self.max_workers is not None and self.max_workers <= 0:
            errors.append("max_workers must be positive when specified")

        if self.max_sample_failures < 0:
            errors.append("max_sample_failures must be non-negative")

        # Validate dimension weights
        for dimension, weight in self.dimension_weights.items():
            if not isinstance(weight, (int, float)) or weight < 0:
                errors.append(
                    f"dimension_weights[{dimension}] must be a non-negative number"
                )

        return errors


@dataclass
class AuditConfig:
    """Configuration for audit logging.

    Controls how the audit system logs operations and maintains compliance records.
    """

    enabled: bool = True
    """Whether audit logging is enabled"""

    log_dir: str = "ADRI/dev/audit-logs"
    """Directory for storing audit logs"""

    log_prefix: str = "adri"
    """Prefix for audit log filenames"""

    log_level: str = "INFO"
    """Logging level (DEBUG, INFO, WARNING, ERROR)"""

    include_data_samples: bool = True
    """Whether to include data samples in audit logs (when safe)"""

    max_log_size_mb: int = 100
    """Maximum log file size in MB before rotation"""

    log_retention_days: int = 90
    """Number of days to retain audit logs"""

    compress_rotated_logs: bool = True
    """Whether to compress rotated log files"""


@dataclass
class EnvironmentConfig:
    """Configuration for a specific environment (dev/prod).

    Defines the paths and settings for an ADRI environment.
    """

    name: str
    """Environment name (e.g., 'development', 'production')"""

    paths: dict[str, str] = field(default_factory=dict)
    """Directory paths for this environment"""

    audit: AuditConfig = field(default_factory=AuditConfig)
    """Audit configuration for this environment"""

    validation: ValidationConfig = field(default_factory=ValidationConfig)
    """Validation configuration for this environment"""

    inference: InferenceConfig = field(default_factory=InferenceConfig)
    """Inference configuration for this environment"""


@dataclass
class ProjectConfig:
    """Configuration for an ADRI project.

    Root configuration that contains all project-wide settings and environments.
    """

    project_name: str
    """Name of the ADRI project"""

    version: str = "4.0.0"
    """ADRI framework version"""

    default_environment: str = "development"
    """Default environment to use"""

    environments: dict[str, EnvironmentConfig] = field(default_factory=dict)
    """Available environments and their configurations"""

    def get_environment(self, environment_name: str | None = None) -> EnvironmentConfig:
        """Get configuration for a specific environment.

        Args:
            environment_name: Name of environment (uses default if None)

        Returns:
            Environment configuration

        Raises:
            ConfigurationError: If environment is not found
        """
        env_name = environment_name or self.default_environment

        if env_name not in self.environments:
            raise ConfigurationError(
                f"Environment '{env_name}' not found",
                f"Available environments: {list(self.environments.keys())}",
            )

        return self.environments[env_name]

    def validate(self) -> list[str]:
        """Validate the entire project configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not self.project_name.strip():
            errors.append("project_name cannot be empty")

        if not self.environments:
            errors.append("At least one environment must be configured")

        if self.default_environment not in self.environments:
            errors.append(
                f"default_environment '{self.default_environment}' not found in environments"
            )

        # Validate each environment
        for env_name, env_config in self.environments.items():
            if env_config.name != env_name:
                errors.append(
                    f"Environment name mismatch: key='{env_name}', name='{env_config.name}'"
                )

            # Validate nested configs
            for validation_error in env_config.validation.validate():
                errors.append(
                    f"Environment '{env_name}' validation: {validation_error}"
                )

            for inference_error in env_config.inference.validate():
                errors.append(f"Environment '{env_name}' inference: {inference_error}")

        return errors


class ConfigurationManager:
    """Centralized configuration management for ADRI.

    Provides a unified interface for loading, validating, and accessing
    configuration across the ADRI framework.
    """

    def __init__(self, config_path: str | Path | None = None):
        """Initialize the configuration manager.

        Args:
            config_path: Path to configuration file (auto-discovered if None)
        """
        self.config_path = Path(config_path) if config_path else None
        self._project_config: ProjectConfig | None = None

    def load_config(self, config_path: str | Path | None = None) -> ProjectConfig:
        """Load project configuration from file.

        Args:
            config_path: Path to configuration file (uses instance path if None)

        Returns:
            Loaded project configuration

        Raises:
            ConfigurationError: If configuration cannot be loaded or is invalid
        """
        import yaml

        if config_path:
            self.config_path = Path(config_path)
        elif not self.config_path:
            # Auto-discover configuration
            self.config_path = self._find_config_file()

        if not self.config_path or not self.config_path.exists():
            raise ConfigurationError(
                "Configuration file not found", f"Looked for: {self.config_path}"
            )

        try:
            with open(self.config_path, encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}

            # Extract ADRI configuration section
            adri_config = config_data.get("adri", {})
            if not adri_config:
                raise ConfigurationError("Missing 'adri' section in configuration")

            # Convert to dataclasses
            self._project_config = self._parse_project_config(adri_config)

            # Validate configuration
            validation_errors = self._project_config.validate()
            if validation_errors:
                from .exceptions import format_validation_errors

                raise ConfigurationError(
                    "Configuration validation failed",
                    format_validation_errors(validation_errors),
                )

            return self._project_config

        except yaml.YAMLError as e:
            raise ConfigurationError("Invalid YAML configuration", str(e))
        except Exception as e:
            raise ConfigurationError("Failed to load configuration", str(e))

    def get_active_config(self) -> ProjectConfig | None:
        """Get the currently active project configuration.

        Returns:
            Active project configuration, or None if not loaded
        """
        return self._project_config

    def get_environment_config(
        self,
        project_config: ProjectConfig | None = None,
        environment_name: str | None = None,
    ) -> EnvironmentConfig:
        """Get configuration for a specific environment.

        Args:
            project_config: Project configuration (uses active if None)
            environment_name: Environment name (uses default if None)

        Returns:
            Environment configuration

        Raises:
            ConfigurationError: If configuration is not available
        """
        config = project_config or self._project_config
        if not config:
            raise ConfigurationError("No project configuration available")

        return config.get_environment(environment_name)

    def _find_config_file(self) -> Path | None:
        """Find the ADRI configuration file by searching upward from current directory.

        Returns:
            Path to configuration file, or None if not found
        """
        current_path = Path.cwd()

        while current_path != current_path.parent:
            config_file = current_path / "ADRI" / "config.yaml"
            if config_file.exists():
                return config_file
            current_path = current_path.parent

        # Check root directory
        config_file = current_path / "ADRI" / "config.yaml"
        return config_file if config_file.exists() else None

    def _parse_project_config(self, config_data: dict[str, Any]) -> ProjectConfig:
        """Parse configuration data into ProjectConfig dataclass.

        Args:
            config_data: Raw configuration data from YAML

        Returns:
            Parsed project configuration
        """
        # Parse environments
        environments = {}
        for env_name, env_data in config_data.get("environments", {}).items():
            env_config = EnvironmentConfig(
                name=env_name,
                paths=env_data.get("paths", {}),
                audit=AuditConfig(**env_data.get("audit", {})),
                validation=ValidationConfig(**env_data.get("validation", {})),
                inference=InferenceConfig(**env_data.get("inference", {})),
            )
            environments[env_name] = env_config

        return ProjectConfig(
            project_name=config_data.get("project_name", "Unnamed Project"),
            version=config_data.get("version", "4.0.0"),
            default_environment=config_data.get("default_environment", "development"),
            environments=environments,
        )
