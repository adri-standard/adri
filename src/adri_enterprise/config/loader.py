# @ADRI_FEATURE[enterprise_config_loader, scope=ENTERPRISE]
# Description: Enterprise configuration loader with dev/prod environment support
"""
ADRI Enterprise Configuration Loader.

Extends the base ConfigurationLoader with environment-aware path resolution
for enterprise dev/prod folder structures.

Key Features:
- Auto-detects config format (flat vs environment-based)
- Supports ADRI_ENV environment variable for environment switching
- Maintains backward compatibility with flat OSS structure
- Provides environment-specific path resolution
"""

import os
from enum import Enum
from pathlib import Path
from typing import Any

from adri.config.loader import ConfigurationLoader


class ConfigFormat(Enum):
    """Configuration format types."""

    FLAT = "flat"  # Uses paths directly (OSS-compatible)
    ENVIRONMENT = "environment"  # Uses environments.{env}.paths (Enterprise)


def detect_config_format(config: dict[str, Any] | None) -> ConfigFormat:
    """
    Auto-detect whether config uses flat or environment-based structure.

    Args:
        config: Configuration dictionary or None

    Returns:
        ConfigFormat.ENVIRONMENT if 'environments' key exists, else ConfigFormat.FLAT
    """
    if not config:
        return ConfigFormat.FLAT

    adri_config = config.get("adri", {})

    # Check for environment-based structure
    if "environments" in adri_config and isinstance(adri_config["environments"], dict):
        return ConfigFormat.ENVIRONMENT

    return ConfigFormat.FLAT


class EnterpriseConfigurationLoader(ConfigurationLoader):
    """
    Enterprise configuration loader with dev/prod environment support.

    Auto-detects configuration format:
    - If config has 'environments' key: Uses dev/prod path structure
    - If config has direct 'paths' key: Uses flat structure (OSS-compatible)

    Environment precedence:
    1. Explicit environment parameter
    2. ADRI_ENV environment variable
    3. config default_environment
    4. "development" (fallback)

    Example:
        loader = EnterpriseConfigurationLoader()

        # Auto-detect and use config format
        contract_path = loader.resolve_contract_path("my_contract")

        # Explicitly specify environment
        prod_path = loader.resolve_contract_path("my_contract", environment="production")

        # Override via environment variable
        os.environ["ADRI_ENV"] = "production"
        contract_path = loader.resolve_contract_path("my_contract")
    """

    def __init__(self) -> None:
        """Initialize the enterprise configuration loader."""
        super().__init__()

    def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate configuration structure (supports both flat and env formats).

        Args:
            config: Configuration dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            if "adri" not in config:
                return False

            adri_config = config["adri"]
            config_format = detect_config_format(config)

            if config_format == ConfigFormat.ENVIRONMENT:
                # Validate environment-based structure
                if "environments" not in adri_config:
                    return False

                environments = adri_config["environments"]
                if not isinstance(environments, dict):
                    return False

                # Check that at least one environment exists with paths
                for env_name, env_config in environments.items():
                    if not isinstance(env_config, dict):
                        return False
                    if "paths" not in env_config:
                        return False
                    paths = env_config["paths"]
                    if not isinstance(paths, dict):
                        return False
                    # Check required path keys
                    required_paths = [
                        "contracts",
                        "assessments",
                        "training_data",
                        "audit_logs",
                    ]
                    for path_key in required_paths:
                        if path_key not in paths:
                            return False

                return True
            else:
                # Validate flat structure using base class
                return super().validate_config(config)

        except (KeyError, TypeError, ValueError):
            return False

    def _get_effective_environment(
        self, config: dict[str, Any] | None, environment: str | None = None
    ) -> str:
        """
        Get the effective environment with ADRI_ENV override support.

        Precedence:
        1. environment parameter (explicit, when provided)
        2. ADRI_ENV environment variable
        3. config default_environment
        4. "development" (fallback)

        Args:
            config: Configuration dictionary, or None
            environment: Explicit environment name, or None

        Returns:
            Effective environment name
        """
        # Highest precedence: explicit parameter
        if environment:
            return environment

        # Second: ADRI_ENV environment variable
        env_var = os.environ.get("ADRI_ENV")
        if env_var:
            return env_var

        # Third: config default
        if config:
            return config.get("adri", {}).get("default_environment", "development")

        # Fallback
        return "development"

    def get_environment_config(
        self, config: dict[str, Any], environment: str | None = None
    ) -> dict[str, Any]:
        """
        Get environment-specific config, supports both flat and env formats.

        For environment-based configs, returns the specific environment's config.
        For flat configs, returns a dict with the paths.

        Args:
            config: Full configuration dictionary
            environment: Environment name, or None for default

        Returns:
            Environment configuration with paths

        Raises:
            ValueError: If environment not found in environment-based config
        """
        config_format = detect_config_format(config)
        adri_config = config.get("adri", {})

        if config_format == ConfigFormat.ENVIRONMENT:
            env = self._get_effective_environment(config, environment)

            if "environments" not in adri_config:
                raise ValueError("No environments defined in configuration")

            environments = adri_config["environments"]

            if env not in environments:
                available_envs = list(environments.keys())
                raise ValueError(
                    f"Environment '{env}' not found in configuration. "
                    f"Available environments: {available_envs}"
                )

            return environments[env]
        else:
            # Flat structure - return paths config for compatibility
            return {"paths": self.get_paths_config(config)}

    def _get_base_dir(self) -> Path:
        """
        Determine the base directory for path resolution.

        Returns:
            Base directory path (typically project root)
        """
        config_file_path = os.environ.get("ADRI_CONFIG_PATH")
        if not config_file_path:
            config_file_path = self.find_config_file()

        if config_file_path:
            base_dir = Path(config_file_path).parent
            # If config is in ADRI/config.yaml, go up to project root
            if base_dir.name == "ADRI":
                base_dir = base_dir.parent
            return base_dir

        return Path.cwd()

    def resolve_contract_path(
        self, contract_name: str, environment: str | None = None
    ) -> str:
        """
        Resolve contract path respecting environment (dev/prod or flat).

        Precedence for contracts directory:
        1. ADRI_CONTRACTS_DIR environment variable (if set)
        2. Environment-specific paths from config (if env-based)
        3. Flat paths from config (if flat structure)
        4. Default ADRI/contracts structure

        Args:
            contract_name: Name of contract (with or without .yaml extension)
            environment: Environment to use (dev/prod), or None for default

        Returns:
            Full absolute path to contract file
        """
        # Add .yaml extension if not present
        if not contract_name.endswith((".yaml", ".yml")):
            contract_name += ".yaml"

        # Highest precedence: ADRI_CONTRACTS_DIR environment variable
        env_contracts_dir = os.environ.get("ADRI_CONTRACTS_DIR")
        if env_contracts_dir:
            contracts_path = Path(env_contracts_dir)
            if not contracts_path.is_absolute():
                contracts_path = Path.cwd() / contracts_path
            full_path = (contracts_path / contract_name).resolve()
            return str(full_path)

        config = self.get_active_config()
        base_dir = self._get_base_dir()

        if not config:
            # Fallback to default flat path structure
            contract_path = base_dir / "ADRI" / "contracts" / contract_name
            return str(contract_path)

        try:
            config_format = detect_config_format(config)

            if config_format == ConfigFormat.ENVIRONMENT:
                # Get environment-specific config
                env_config = self.get_environment_config(config, environment)
                contracts_dir = env_config["paths"]["contracts"]
            else:
                # Flat structure
                adri_config = config["adri"]
                contracts_dir = adri_config["paths"]["contracts"]

            # Convert relative path to absolute based on config file location
            contracts_path = Path(contracts_dir)

            # For environment configs, paths are relative to ADRI folder
            # e.g., ./dev/contracts means ADRI/dev/contracts
            if not contracts_path.is_absolute():
                if config_format == ConfigFormat.ENVIRONMENT:
                    # Environment paths are relative to ADRI folder
                    contracts_path = (base_dir / "ADRI" / contracts_dir).resolve()
                else:
                    # Flat paths are relative to project root
                    contracts_path = (base_dir / contracts_dir).resolve()
            else:
                contracts_path = contracts_path.resolve()

            # Combine with contract filename and ensure absolute path
            full_path = (contracts_path / contract_name).resolve()
            return str(full_path)

        except (KeyError, ValueError, AttributeError):
            # Fallback on any error - use flat structure
            contract_path = base_dir / "ADRI" / "contracts" / contract_name
            return str(contract_path)

    def get_assessments_dir(self, environment: str | None = None) -> str:
        """
        Get the assessments directory for the environment.

        Args:
            environment: Environment to use, or None for default

        Returns:
            Path to assessments directory
        """
        config = self.get_active_config()

        if not config:
            return "./ADRI/assessments"

        try:
            config_format = detect_config_format(config)

            if config_format == ConfigFormat.ENVIRONMENT:
                env_config = self.get_environment_config(config, environment)
                return env_config["paths"]["assessments"]
            else:
                adri_config = config["adri"]
                return adri_config["paths"]["assessments"]
        except (KeyError, ValueError, AttributeError):
            return "./ADRI/assessments"

    def get_training_data_dir(self, environment: str | None = None) -> str:
        """
        Get the training data directory for the environment.

        Args:
            environment: Environment to use, or None for default

        Returns:
            Path to training data directory
        """
        config = self.get_active_config()

        if not config:
            return "./ADRI/training-data"

        try:
            config_format = detect_config_format(config)

            if config_format == ConfigFormat.ENVIRONMENT:
                env_config = self.get_environment_config(config, environment)
                return env_config["paths"]["training_data"]
            else:
                adri_config = config["adri"]
                return adri_config["paths"]["training_data"]
        except (KeyError, ValueError, AttributeError):
            return "./ADRI/training-data"

    def get_audit_logs_dir(self, environment: str | None = None) -> str:
        """
        Get the audit logs directory for the environment.

        Args:
            environment: Environment to use, or None for default

        Returns:
            Path to audit logs directory
        """
        config = self.get_active_config()

        if not config:
            return "./ADRI/audit-logs"

        try:
            config_format = detect_config_format(config)

            if config_format == ConfigFormat.ENVIRONMENT:
                env_config = self.get_environment_config(config, environment)
                return env_config["paths"]["audit_logs"]
            else:
                adri_config = config["adri"]
                return adri_config["paths"]["audit_logs"]
        except (KeyError, ValueError, AttributeError):
            return "./ADRI/audit-logs"

    def get_protection_config(self, environment: str | None = None) -> dict[str, Any]:
        """
        Get protection configuration for the environment.

        Args:
            environment: Environment to use, or None for default

        Returns:
            Protection configuration dictionary
        """
        config = self.get_active_config()
        if not config:
            # Return default protection config if no config file found
            return {
                "default_failure_mode": "raise",
                "default_min_score": 80,
                "cache_duration_hours": 1,
                "auto_generate_contracts": True,
                "verbose_protection": False,
            }

        adri_config = config["adri"]
        config_format = detect_config_format(config)

        if config_format == ConfigFormat.ENVIRONMENT:
            try:
                env_config = self.get_environment_config(config, environment)
                protection_config = env_config.get("protection", {}).copy()
                if not isinstance(protection_config, dict):
                    protection_config = {}
                return protection_config
            except (KeyError, ValueError):
                pass

        # Flat structure or fallback
        protection_config = adri_config.get("protection", {}).copy()
        if not isinstance(protection_config, dict):
            protection_config = {}

        return protection_config

    def create_default_config(self, project_name: str) -> dict[str, Any]:
        """
        Create default enterprise config with environments.

        Args:
            project_name: Name of the project

        Returns:
            Dict containing the default enterprise configuration structure
        """
        return {
            "adri": {
                "version": "4.0.0",
                "project_name": project_name,
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "contracts": "./dev/contracts",
                            "assessments": "./dev/assessments",
                            "training_data": "./dev/training-data",
                            "audit_logs": "./dev/audit-logs",
                        },
                        "protection": {
                            "default_failure_mode": "warn",
                            "default_min_score": 70,
                            "cache_duration_hours": 1,
                            "auto_generate_contracts": True,
                            "verbose_protection": True,
                        },
                        "audit": {
                            "enabled": True,
                            "include_data_samples": True,
                            "log_level": "DEBUG",
                            "max_log_size_mb": 100,
                        },
                    },
                    "production": {
                        "paths": {
                            "contracts": "./prod/contracts",
                            "assessments": "./prod/assessments",
                            "training_data": "./prod/training-data",
                            "audit_logs": "./prod/audit-logs",
                        },
                        "protection": {
                            "default_failure_mode": "raise",
                            "default_min_score": 85,
                            "cache_duration_hours": 24,
                            "auto_generate_contracts": False,
                            "verbose_protection": False,
                        },
                        "audit": {
                            "enabled": True,
                            "include_data_samples": False,
                            "log_level": "INFO",
                            "max_log_size_mb": 500,
                        },
                    },
                },
            }
        }

    def create_directory_structure(self, config: dict[str, Any]) -> None:
        """
        Create the directory structure for all environments.

        Args:
            config: Configuration dictionary containing paths
        """
        config_format = detect_config_format(config)
        adri_config = config["adri"]

        if config_format == ConfigFormat.ENVIRONMENT:
            # Create directories for each environment
            for env_name, env_config in adri_config["environments"].items():
                paths = env_config.get("paths", {})
                for path_type, path_value in paths.items():
                    # Environment paths are relative to ADRI folder
                    full_path = Path("ADRI") / path_value
                    full_path.mkdir(parents=True, exist_ok=True)
        else:
            # Flat structure - use base class
            super().create_directory_structure(config)


# Convenience functions for simplified usage


def load_enterprise_config(config_path: str | None = None) -> dict[str, Any] | None:
    """
    Load ADRI configuration using enterprise loader.

    Args:
        config_path: Specific config file path, or None to search

    Returns:
        Configuration dictionary or None if not found
    """
    loader = EnterpriseConfigurationLoader()
    return loader.get_active_config(config_path)


def resolve_enterprise_contract(
    contract_name: str, environment: str | None = None
) -> str:
    """
    Resolve contract name to file path using enterprise loader.

    Args:
        contract_name: Name of contract
        environment: Environment to use (e.g., "development", "production")

    Returns:
        Full path to contract file
    """
    loader = EnterpriseConfigurationLoader()
    return loader.resolve_contract_path(contract_name, environment)


def get_enterprise_protection_settings(
    environment: str | None = None,
) -> dict[str, Any]:
    """
    Get protection settings for an environment using enterprise loader.

    Args:
        environment: Environment name, or None for default

    Returns:
        Protection configuration dictionary
    """
    loader = EnterpriseConfigurationLoader()
    return loader.get_protection_config(environment)


# @ADRI_FEATURE_END[enterprise_config_loader]
