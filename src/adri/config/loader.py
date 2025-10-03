"""
ADRI Configuration Loader.

Streamlined configuration loading logic, simplified from adri/config/manager.py.
Removes complex configuration management while preserving essential functionality.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ConfigurationLoader:
    """
    Streamlined configuration loader for ADRI. Simplified from ConfigManager.

    Handles basic configuration loading, validation, and path resolution
    without the complex management features of the original.
    """

    def __init__(self):
        """Initialize the configuration loader."""
        pass

    def create_default_config(self, project_name: str) -> Dict[str, Any]:
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
                            "standards": "./ADRI/dev/standards",
                            "assessments": "./ADRI/dev/assessments",
                            "training_data": "./ADRI/dev/training-data",
                        },
                        "protection": {
                            "default_failure_mode": "warn",
                            "default_min_score": 75,
                            "cache_duration_hours": 0.5,
                        },
                    },
                    "production": {
                        "paths": {
                            "standards": "./ADRI/prod/standards",
                            "assessments": "./ADRI/prod/assessments",
                            "training_data": "./ADRI/prod/training-data",
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
                    "auto_generate_standards": True,
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

    def validate_config(self, config: Dict[str, Any]) -> bool:
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
                required_paths = ["standards", "assessments", "training_data"]
                for path_key in required_paths:
                    if path_key not in paths:
                        return False

            return True

        except (KeyError, TypeError, ValueError):
            return False

    def save_config(
        self, config: Dict[str, Any], config_path: str = "adri-config.yaml"
    ) -> None:
        """
        Save configuration to YAML file.

        Args:
            config: Configuration dictionary to save
            config_path: Path to save the configuration file
        """
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)

    def load_config(
        self, config_path: str = "adri-config.yaml"
    ) -> Optional[Dict[str, Any]]:
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
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f)
                return config_data if isinstance(config_data, dict) else None
        except (yaml.YAMLError, IOError):
            return None

    def find_config_file(self, start_path: str = ".") -> Optional[str]:
        """
        Find ADRI config file by searching up the directory tree.

        Args:
            start_path: Directory to start searching from

        Returns:
            Path to config file or None if not found
        """
        current_path = Path(start_path).resolve()

        # Search up the directory tree
        for path in [current_path] + list(current_path.parents):
            # Check common config file locations (new location first)
            config_names = [
                "ADRI/config.yaml",
                "adri-config.yaml",  # backward compatibility
                "adri-config.yml",  # backward compatibility
                "ADRI/adri-config.yaml",  # backward compatibility
                ".adri.yaml",
            ]

            for config_name in config_names:
                config_path = path / config_name
                if config_path.exists():
                    return str(config_path)

        return None

    def get_active_config(
        self, config_path: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get the active configuration, searching for config file if not specified.

        Args:
            config_path: Specific config file path, or None to search

        Returns:
            Configuration dictionary or None if no config found
        """
        if config_path is None:
            config_path = self.find_config_file()

        if config_path is None:
            return None

        return self.load_config(config_path)

    def get_environment_config(
        self, config: Dict[str, Any], environment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get configuration for a specific environment.

        Args:
            config: Full configuration dictionary
            environment: Environment name, or None for default

        Returns:
            Environment configuration

        Raises:
            ValueError: If environment is not found
        """
        adri_config = config["adri"]

        if environment is None:
            environment = adri_config.get("default_environment", "development")

        if environment not in adri_config["environments"]:
            raise ValueError(f"Environment '{environment}' not found in configuration")

        env_config = adri_config["environments"][environment]
        if not isinstance(env_config, dict):
            raise ValueError(f"Invalid environment configuration for '{environment}'")

        return env_config

    def get_protection_config(
        self, environment: Optional[str] = None
    ) -> Dict[str, Any]:
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
                "auto_generate_standards": True,
                "verbose_protection": False,
            }

        adri_config = config["adri"]

        # Start with global protection config
        protection_config = adri_config.get("protection", {}).copy()
        if not isinstance(protection_config, dict):
            protection_config = {}

        # Override with environment-specific settings
        if environment is None:
            environment = adri_config.get("default_environment", "development")

        if environment in adri_config["environments"]:
            env_config = adri_config["environments"][environment]
            env_protection = env_config.get("protection", {})
            if isinstance(env_protection, dict):
                protection_config.update(env_protection)

        return protection_config

    def resolve_standard_path(
        self, standard_name: str, environment: Optional[str] = None
    ) -> str:
        """
        Resolve a standard name to full absolute path using active configuration.

        Args:
            standard_name: Name of standard (with or without .yaml extension)
            environment: Environment to use

        Returns:
            Full absolute path to standard file
        """
        config = self.get_active_config()

        # Determine base directory from config file location
        # Check environment variable first
        config_file_path = os.environ.get("ADRI_CONFIG_PATH")
        if not config_file_path:
            config_file_path = self.find_config_file()

        # Determine base directory - use config file location if available, else cwd
        if config_file_path:
            base_dir = Path(config_file_path).parent
        else:
            base_dir = Path.cwd()

        # Determine environment
        if environment is None and config:
            environment = config.get("adri", {}).get(
                "default_environment", "development"
            )
        elif environment is None:
            environment = "development"

        if not config:
            # Fallback to default path structure
            env_dir = "dev" if environment != "production" else "prod"
            if not standard_name.endswith((".yaml", ".yml")):
                standard_name += ".yaml"
            standard_path = base_dir / "ADRI" / env_dir / "standards" / standard_name
            return str(standard_path)

        try:
            env_config = self.get_environment_config(config, environment)
            standards_dir = env_config["paths"]["standards"]

            # Add .yaml extension if not present
            if not standard_name.endswith((".yaml", ".yml")):
                standard_name += ".yaml"

            # Convert relative path to absolute based on config file location
            # Use Path.resolve() for cross-platform path resolution
            standards_path = Path(standards_dir)

            # If relative path, resolve from config file directory
            if not standards_path.is_absolute():
                standards_path = (base_dir / standards_dir).resolve()
            else:
                standards_path = standards_path.resolve()

            # Combine with standard filename and ensure absolute path
            full_path = (standards_path / standard_name).resolve()
            return str(full_path)

        except (KeyError, ValueError, AttributeError):
            # Fallback on any error
            env_dir = "dev" if environment != "production" else "prod"
            if not standard_name.endswith((".yaml", ".yml")):
                standard_name += ".yaml"
            standard_path = base_dir / "ADRI" / env_dir / "standards" / standard_name
            return str(standard_path)

    def create_directory_structure(self, config: Dict[str, Any]) -> None:
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

    def get_assessments_dir(self, environment: Optional[str] = None) -> str:
        """
        Get the assessments directory for an environment.

        Args:
            environment: Environment to use

        Returns:
            Path to assessments directory
        """
        config = self.get_active_config()
        if not config:
            env_dir = "dev" if environment != "production" else "prod"
            return f"./ADRI/{env_dir}/assessments"

        try:
            env_config = self.get_environment_config(config, environment)
            return env_config["paths"]["assessments"]
        except (KeyError, ValueError, AttributeError):
            env_dir = "dev" if environment != "production" else "prod"
            return f"./ADRI/{env_dir}/assessments"

    def get_training_data_dir(self, environment: Optional[str] = None) -> str:
        """
        Get the training data directory for an environment.

        Args:
            environment: Environment to use

        Returns:
            Path to training data directory
        """
        config = self.get_active_config()
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
def load_adri_config(config_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Load ADRI configuration using simplified interface.

    Args:
        config_path: Specific config file path, or None to search

    Returns:
        Configuration dictionary or None if not found
    """
    loader = ConfigurationLoader()
    return loader.get_active_config(config_path)


def get_protection_settings(environment: Optional[str] = None) -> Dict[str, Any]:
    """
    Get protection settings for an environment.

    Args:
        environment: Environment name, or None for default

    Returns:
        Protection configuration dictionary
    """
    loader = ConfigurationLoader()
    return loader.get_protection_config(environment)


def resolve_standard_file(standard_name: str, environment: Optional[str] = None) -> str:
    """
    Resolve standard name to file path.

    Args:
        standard_name: Name of standard
        environment: Environment to use

    Returns:
        Full path to standard file
    """
    loader = ConfigurationLoader()
    return loader.resolve_standard_path(standard_name, environment)


# Backward compatibility alias
ConfigManager = ConfigurationLoader
