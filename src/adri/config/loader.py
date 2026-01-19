# @ADRI_FEATURE[config_loader, scope=SHARED]
# Description: Configuration management and environment-based contract resolution
"""
ADRI Configuration Loader.

Streamlined configuration loading logic, simplified from adri/config/manager.py.
Removes complex configuration management while preserving essential functionality.
"""

import os
from pathlib import Path
from typing import Any

import yaml


class ConfigurationLoader:
    """
    Streamlined configuration loader for ADRI. Simplified from ConfigManager.

    Handles basic configuration loading, validation, and path resolution
    without the complex management features of the original.
    """

    def __init__(self):
        """Initialize the configuration loader."""

    def create_default_config(self, project_name: str) -> dict[str, Any]:
        """
        Create a default ADRI configuration.

        Args:
            project_name: Name of the project

        Returns:
            Dict containing the default configuration structure
        """
        return {
            "adri": {
                "version": "4.0.0",
                "project_name": project_name,
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "contracts": "./ADRI/dev/contracts",
                            "assessments": "./ADRI/dev/assessments",
                            "training_data": "./ADRI/dev/training-data",
                            "audit_logs": "./ADRI/dev/audit-logs",
                        },
                        "protection": {
                            "default_failure_mode": "warn",
                            "default_min_score": 75,
                            "cache_duration_hours": 0.5,
                        },
                    },
                    "production": {
                        "paths": {
                            "contracts": "./ADRI/prod/contracts",
                            "assessments": "./ADRI/prod/assessments",
                            "training_data": "./ADRI/prod/training-data",
                            "audit_logs": "./ADRI/prod/audit-logs",
                        },
                        "protection": {
                            "default_failure_mode": "raise",
                            "default_min_score": 85,
                            "cache_duration_hours": 24,
                        },
                    },
                },
                "protection": {
                    "default_failure_mode": "raise",
                    "default_min_score": 80,
                    "cache_duration_hours": 1,
                    "auto_generate_contracts": True,
                    "verbose_protection": False,
                },
                "assessment": {
                    "caching": {"enabled": True, "ttl": "24h"},
                    "output": {"format": "json"},
                    "performance": {"max_rows": 1000000, "timeout": "5m"},
                },
                "generation": {
                    "default_thresholds": {
                        "completeness_min": 85,
                        "validity_min": 90,
                        "consistency_min": 80,
                    }
                },
            }
        }

    def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate basic configuration structure.

        Args:
            config: Configuration dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check top-level structure
            if "adri" not in config:
                return False

            adri_config = config["adri"]

            # Check required fields
            required_fields = ["project_name", "environments", "default_environment"]
            for field in required_fields:
                if field not in adri_config:
                    return False

            # Check environments structure
            environments = adri_config["environments"]
            if not isinstance(environments, dict):
                return False

            # Check that each environment has paths
            for env_name, env_config in environments.items():
                if "paths" not in env_config:
                    return False

                paths = env_config["paths"]
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

        except (KeyError, TypeError, ValueError):
            return False

    def save_config(
        self, config: dict[str, Any], config_path: str = "ADRI/config.yaml"
    ) -> None:
        """
        Save configuration to YAML file.

        Args:
            config: Configuration dictionary to save
            config_path: Path to save the configuration file (default: ADRI/config.yaml)
        """
        # Ensure parent directory exists
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)

    def load_config(
        self, config_path: str = "adri-config.yaml"
    ) -> dict[str, Any] | None:
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to the configuration file

        Returns:
            Configuration dictionary or None if file doesn't exist or is invalid
        """
        if not os.path.exists(config_path):
            return None

        try:
            with open(config_path, encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
                return config_data if isinstance(config_data, dict) else None
        except (yaml.YAMLError, OSError):
            return None

    def find_config_file(self, start_path: str = ".") -> str | None:
        """
        Find ADRI config file at standard location.

        Searches up the directory tree for ADRI/config.yaml, stopping at
        the user's home directory.

        Args:
            start_path: Directory to start searching from

        Returns:
            Path to config file if found at ADRI/config.yaml, None otherwise

        Note:
            Configuration file must be located at ADRI/config.yaml.
            Run 'adri setup' to initialize if not found.
        """
        current_path = Path(start_path).resolve()
        home_path = Path.home().resolve()

        # Search up the directory tree, stopping at home directory
        for path in [current_path] + list(current_path.parents):
            config_path = path / "ADRI" / "config.yaml"
            if config_path.exists():
                return str(config_path)

            # Stop after checking home directory - don't search above it
            if path == home_path:
                break

        return None

    def get_active_config(
        self, config_path: str | None = None
    ) -> dict[str, Any] | None:
        """
        Get the active configuration with environment variable precedence.

        Precedence order (highest to lowest):
        1. ADRI_CONFIG (inline YAML string)
        2. ADRI_CONFIG_PATH or ADRI_CONFIG_FILE (explicit file path)
        3. config_path parameter
        4. ADRI/config.yaml in current or parent directories
        5. None (no config found)

        Args:
            config_path: Specific config file path, or None to search

        Returns:
            Configuration dictionary or None if no config found

        Note:
            Configuration file must be located at ADRI/config.yaml.
            Run 'adri setup' to initialize if not found.
        """
        # Highest precedence: ADRI_CONFIG environment variable (inline YAML)
        inline_config = os.environ.get("ADRI_CONFIG")
        if inline_config:
            try:
                config_data = yaml.safe_load(inline_config)
                if isinstance(config_data, dict):
                    return config_data
            except yaml.YAMLError:
                # Invalid YAML, fall through to next option
                pass

        # Second precedence: ADRI_CONFIG_PATH or ADRI_CONFIG_FILE
        env_config_path = os.environ.get("ADRI_CONFIG_PATH") or os.environ.get(
            "ADRI_CONFIG_FILE"
        )
        if env_config_path:
            config = self.load_config(env_config_path)
            if config:
                return config

        # Third precedence: Explicit config_path parameter
        if config_path:
            config = self.load_config(config_path)
            if config:
                return config

        # Fourth precedence: Auto-discovery
        discovered_path = self.find_config_file()
        if discovered_path:
            return self.load_config(discovered_path)

        return None

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
        Get configuration for a specific environment with ADRI_ENV override.

        Args:
            config: Full configuration dictionary
            environment: Environment name, or None for default

        Returns:
            Environment configuration

        Raises:
            ValueError: If environment is not found
        """
        adri_config = config["adri"]

        # Track if environment came from ADRI_ENV to enable fallback only for that case
        from_adri_env = False
        if not environment and os.environ.get("ADRI_ENV"):
            from_adri_env = True

        # Use effective environment (respects ADRI_ENV)
        requested_env = environment  # Store original request
        environment = self._get_effective_environment(config, environment)

        # If effective environment doesn't exist, only fall back if it came from
        # ADRI_ENV
        if environment not in adri_config["environments"]:
            # Only fall back to default if the invalid environment came from ADRI_ENV
            # (not explicit request)
            if from_adri_env and not requested_env:
                default_env = adri_config.get("default_environment", "development")
                if default_env in adri_config["environments"]:
                    environment = default_env
                else:
                    raise ValueError(
                        f"Environment '{environment}' not found in configuration"
                    )
            else:
                raise ValueError(
                    f"Environment '{environment}' not found in configuration"
                )

        env_config = adri_config["environments"][environment]
        if not isinstance(env_config, dict):
            raise ValueError(f"Invalid environment configuration for '{environment}'")

        return env_config

    def get_protection_config(self, environment: str | None = None) -> dict[str, Any]:
        """
        Get protection configuration with environment-specific overrides.

        Args:
            environment: Environment name, or None for current environment

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

        # Start with global protection config
        protection_config = adri_config.get("protection", {}).copy()
        if not isinstance(protection_config, dict):
            protection_config = {}

        # Use effective environment (respects ADRI_ENV)
        environment = self._get_effective_environment(config, environment)

        if environment in adri_config["environments"]:
            env_config = adri_config["environments"][environment]
            env_protection = env_config.get("protection", {})
            if isinstance(env_protection, dict):
                protection_config.update(env_protection)

        return protection_config

    def resolve_contract_path(
        self, contract_name: str, environment: str | None = None
    ) -> str:
        """
        Resolve a contract name to full absolute path with ADRI_CONTRACTS_DIR override.

        Precedence for contracts directory:
        1. ADRI_CONTRACTS_DIR environment variable (if set)
        2. Config file paths
        3. Default ADRI/{env}/contracts structure

        Args:
            contract_name: Name of contract (with or without .yaml extension)
            environment: Environment to use

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

        # Determine base directory from config file location
        config_file_path = os.environ.get("ADRI_CONFIG_PATH")
        if not config_file_path:
            config_file_path = self.find_config_file()

        # Determine base directory - use config file location if available, else cwd
        if config_file_path:
            base_dir = Path(config_file_path).parent
            # If config is in ADRI/config.yaml, go up to project root
            if base_dir.name == "ADRI":
                base_dir = base_dir.parent
        else:
            base_dir = Path.cwd()

        # Use effective environment (respects ADRI_ENV)
        environment = self._get_effective_environment(config, environment)

        if not config:
            # Fallback to default path structure
            env_dir = "dev" if environment != "production" else "prod"
            contract_path = base_dir / "ADRI" / env_dir / "contracts" / contract_name
            return str(contract_path)

        try:
            env_config = self.get_environment_config(config, environment)
            contracts_dir = env_config["paths"]["contracts"]

            # Convert relative path to absolute based on config file location
            contracts_path = Path(contracts_dir)

            # If relative path, resolve from config file directory
            if not contracts_path.is_absolute():
                contracts_path = (base_dir / contracts_dir).resolve()
            else:
                contracts_path = contracts_path.resolve()

            # Combine with contract filename and ensure absolute path
            full_path = (contracts_path / contract_name).resolve()
            return str(full_path)

        except (KeyError, ValueError, AttributeError):
            # Fallback on any error
            env_dir = "dev" if environment != "production" else "prod"
            contract_path = base_dir / "ADRI" / env_dir / "contracts" / contract_name
            return str(contract_path)

    def create_directory_structure(self, config: dict[str, Any]) -> None:
        """
        Create the directory structure based on configuration.

        Args:
            config: Configuration dictionary containing paths
        """
        adri_config = config["adri"]
        environments = adri_config["environments"]

        # Create directories for each environment
        for env_name, env_config in environments.items():
            paths = env_config["paths"]
            for path_type, path_value in paths.items():
                Path(path_value).mkdir(parents=True, exist_ok=True)

    def get_assessments_dir(self, environment: str | None = None) -> str:
        """
        Get the assessments directory for an environment with ADRI_ENV override.

        Args:
            environment: Environment to use

        Returns:
            Path to assessments directory
        """
        config = self.get_active_config()

        # Use effective environment (respects ADRI_ENV)
        environment = self._get_effective_environment(config, environment)

        if not config:
            env_dir = "dev" if environment != "production" else "prod"
            return f"./ADRI/{env_dir}/assessments"

        try:
            env_config = self.get_environment_config(config, environment)
            return env_config["paths"]["assessments"]
        except (KeyError, ValueError, AttributeError):
            env_dir = "dev" if environment != "production" else "prod"
            return f"./ADRI/{env_dir}/assessments"

    def get_training_data_dir(self, environment: str | None = None) -> str:
        """
        Get the training data directory for an environment with ADRI_ENV override.

        Args:
            environment: Environment to use

        Returns:
            Path to training data directory
        """
        config = self.get_active_config()

        # Use effective environment (respects ADRI_ENV)
        environment = self._get_effective_environment(config, environment)

        if not config:
            env_dir = "dev" if environment != "production" else "prod"
            return f"./ADRI/{env_dir}/training-data"

        try:
            env_config = self.get_environment_config(config, environment)
            return env_config["paths"]["training_data"]
        except (KeyError, ValueError, AttributeError):
            env_dir = "dev" if environment != "production" else "prod"
            return f"./ADRI/{env_dir}/training-data"


# Convenience functions for simplified usage
def load_adri_config(config_path: str | None = None) -> dict[str, Any] | None:
    """
    Load ADRI configuration using simplified interface.

    Args:
        config_path: Specific config file path, or None to search

    Returns:
        Configuration dictionary or None if not found
    """
    loader = ConfigurationLoader()
    return loader.get_active_config(config_path)


def get_protection_settings(environment: str | None = None) -> dict[str, Any]:
    """
    Get protection settings for an environment.

    Args:
        environment: Environment name, or None for default

    Returns:
        Protection configuration dictionary
    """
    loader = ConfigurationLoader()
    return loader.get_protection_config(environment)


def resolve_contract_file(contract_name: str, environment: str | None = None) -> str:
    """
    Resolve contract name to file path.

    Args:
        contract_name: Name of contract
        environment: Environment to use

    Returns:
        Full path to contract file
    """
    loader = ConfigurationLoader()
    return loader.resolve_contract_path(contract_name, environment)


# Backward compatibility alias
ConfigManager = ConfigurationLoader
# @ADRI_FEATURE_END[config_loader]
