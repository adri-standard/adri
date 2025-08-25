"""
Configuration manager for ADRI V2.

Handles creation, validation, and management of ADRI configuration files.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ConfigManager:
    """Manages ADRI configuration files and validation."""

    def __init__(self):
        """Initialize the configuration manager."""
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
                "version": "2.0",
                "project_name": project_name,
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
                "default_environment": "development",
                "protection": {
                    "default_failure_mode": "raise",
                    "default_min_score": 80,
                    "cache_duration_hours": 1,
                    "auto_generate_standards": True,
                    "data_sampling_limit": 1000,
                    "standard_naming_pattern": "{function_name}_{data_param}_standard.yaml",
                    "verbose_protection": False,
                },
                "assessment": {
                    "caching": {
                        "enabled": True,
                        "strategy": "content_hash",
                        "ttl": "24h",
                    },
                    "output": {
                        "format": "json",
                        "include_recommendations": True,
                        "include_raw_scores": False,
                    },
                    "performance": {"max_rows": 1000000, "timeout": "5m"},
                },
                "generation": {
                    "default_thresholds": {
                        "completeness_min": 85,
                        "validity_min": 90,
                        "consistency_min": 80,
                        "freshness_max_age": "7d",
                        "plausibility_outlier_threshold": 3.0,
                    },
                    "comments": {
                        "include_domain_suggestions": True,
                        "include_examples": True,
                        "include_references": False,
                    },
                },
                "logging": {
                    "level": "INFO",
                    "file": ".adri/logs/adri.log",
                    "max_size": "10MB",
                    "backup_count": 5,
                },
            }
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration structure.

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
            required_fields = [
                "version",
                "project_name",
                "environments",
                "default_environment",
            ]
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

        except Exception:
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
                # Ensure we return the correct type
                if isinstance(config_data, dict):
                    return config_data
                else:
                    return None
        except (yaml.YAMLError, IOError):
            return None

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

        # Create cache directory
        Path(".adri/cache").mkdir(parents=True, exist_ok=True)

        # Create logs directory
        Path(".adri/logs").mkdir(parents=True, exist_ok=True)

    def find_config_file(self, start_path: str = ".") -> Optional[str]:
        """
        Find ADRI config file by searching up the directory tree.

        Args:
            start_path: Directory to start searching from

        Returns:
            Path to config file or None if not found
        """
        current_path = Path(start_path).resolve()

        # Search up the directory tree for ADRI/adri-config.yaml
        for path in [current_path] + list(current_path.parents):
            # Primary location: ADRI/adri-config.yaml
            adri_config_path = path / "ADRI" / "adri-config.yaml"
            if adri_config_path.exists():
                return str(adri_config_path)

            # Fallback locations for backward compatibility
            fallback_names = [
                "adri-config.yaml",
                "adri-config.yml",
                ".adri.yaml",
                ".adri.yml",
            ]
            for config_name in fallback_names:
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
        """
        adri_config = config["adri"]

        if environment is None:
            environment = adri_config.get("default_environment", "development")

        if environment not in adri_config["environments"]:
            raise ValueError(f"Environment '{environment}' not found in configuration")

        env_config = adri_config["environments"][environment]
        # Ensure we return the correct type
        if isinstance(env_config, dict):
            return env_config
        else:
            raise ValueError(f"Invalid environment configuration for '{environment}'")

    def resolve_standard_path(
        self,
        standard_name: str,
        config: Dict[str, Any],
        environment: Optional[str] = None,
    ) -> str:
        """
        Resolve a standard name to full path using configuration.

        Args:
            standard_name: Name of standard (with or without .yaml extension)
            config: Configuration dictionary
            environment: Environment to use

        Returns:
            Full path to standard file
        """
        env_config = self.get_environment_config(config, environment)
        standards_dir = env_config["paths"]["standards"]

        # Add .yaml extension if not present
        if not standard_name.endswith((".yaml", ".yml")):
            standard_name += ".yaml"

        return os.path.join(standards_dir, standard_name)

    def get_assessments_dir(
        self, config: Dict[str, Any], environment: Optional[str] = None
    ) -> str:
        """
        Get the assessments directory for an environment.

        Args:
            config: Configuration dictionary
            environment: Environment to use

        Returns:
            Path to assessments directory
        """
        env_config = self.get_environment_config(config, environment)
        assessments_path = env_config["paths"]["assessments"]
        # Ensure we return a string
        if isinstance(assessments_path, str):
            return assessments_path
        else:
            raise ValueError("Invalid assessments path configuration")

    def get_training_data_dir(
        self, config: Dict[str, Any], environment: Optional[str] = None
    ) -> str:
        """
        Get the training data directory for an environment.

        Args:
            config: Configuration dictionary
            environment: Environment to use

        Returns:
            Path to training data directory
        """
        env_config = self.get_environment_config(config, environment)
        training_data_path = env_config["paths"]["training_data"]
        # Ensure we return a string
        if isinstance(training_data_path, str):
            return training_data_path
        else:
            raise ValueError("Invalid training data path configuration")

    def validate_paths(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that all configured paths exist and are accessible.

        Args:
            config: Configuration dictionary

        Returns:
            Dictionary with validation results
        """
        # Properly type the results dictionary
        results: Dict[str, Any] = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "path_status": {},
        }

        adri_config = config["adri"]

        for env_name, env_config in adri_config["environments"].items():
            paths = env_config["paths"]

            for path_type, path_value in paths.items():
                path_obj = Path(path_value)
                status = {
                    "exists": path_obj.exists(),
                    "is_directory": path_obj.is_dir() if path_obj.exists() else False,
                    "readable": (
                        os.access(path_value, os.R_OK) if path_obj.exists() else False
                    ),
                    "writable": (
                        os.access(path_value, os.W_OK) if path_obj.exists() else False
                    ),
                    "file_count": 0,
                }

                if status["exists"] and status["is_directory"]:
                    try:
                        status["file_count"] = len(list(path_obj.glob("*")))
                    except PermissionError:
                        status["file_count"] = -1  # Permission denied

                results["path_status"][f"{env_name}.{path_type}"] = status

                # Check for issues - ensure we're working with lists
                warnings_list = results["warnings"]
                errors_list = results["errors"]

                if not status["exists"]:
                    if isinstance(warnings_list, list):
                        warnings_list.append(
                            f"Path does not exist: {path_value} ({env_name}.{path_type})"
                        )
                elif not status["is_directory"]:
                    if isinstance(errors_list, list):
                        errors_list.append(
                            f"Path is not a directory: {path_value} ({env_name}.{path_type})"
                        )
                    results["valid"] = False
                elif not status["readable"]:
                    if isinstance(errors_list, list):
                        errors_list.append(
                            f"Path is not readable: {path_value} ({env_name}.{path_type})"
                        )
                    results["valid"] = False
                elif not status["writable"]:
                    if isinstance(warnings_list, list):
                        warnings_list.append(
                            f"Path is not writable: {path_value} ({env_name}.{path_type})"
                        )

        return results

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
                "data_sampling_limit": 1000,
                "standard_naming_pattern": "{function_name}_{data_param}_standard.yaml",
                "verbose_protection": False,
            }

        adri_config = config["adri"]

        # Start with global protection config
        protection_config_raw = adri_config.get("protection", {})
        if isinstance(protection_config_raw, dict):
            protection_config = protection_config_raw.copy()
        else:
            protection_config = {}

        # Override with environment-specific settings
        if environment is None:
            environment = adri_config.get("default_environment", "development")

        if environment in adri_config["environments"]:
            env_config = adri_config["environments"][environment]
            if "protection" in env_config:
                env_protection = env_config["protection"]
                if isinstance(env_protection, dict):
                    protection_config.update(env_protection)

        return protection_config

    def resolve_standard_path_simple(
        self, standard_name: str, environment: Optional[str] = None
    ) -> str:
        """
        Resolve a standard name to full path using active configuration.

        Args:
            standard_name: Name of standard (with or without .yaml extension)
            environment: Environment to use

        Returns:
            Full path to standard file
        """
        config = self.get_active_config()
        if not config:
            # Fallback to default path structure
            if environment is None:
                environment = "development"

            if not standard_name.endswith((".yaml", ".yml")):
                standard_name += ".yaml"

            return os.path.join(f"./ADRI/{environment[:3]}/standards", standard_name)

        return self.resolve_standard_path(standard_name, config, environment)

    def get_audit_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        Get audit configuration with environment-specific overrides.

        Args:
            environment: Environment name, or None for current environment

        Returns:
            Audit configuration dictionary
        """
        config = self.get_active_config()
        if not config:
            # Return default audit config if no config file found
            return {
                "enabled": True,
                "log_location": "./logs/adri_audit.jsonl",
                "log_level": "INFO",
                "include_data_samples": False,
                "max_log_size_mb": 100,
                "batch_mode": False,
                "batch_size": 100,
                "privacy_settings": {
                    "exclude_pii": True,
                    "hash_sensitive_fields": True,
                },
            }

        adri_config = config.get("adri", {})

        # Start with global audit config
        audit_config_raw = adri_config.get("audit", {})
        if isinstance(audit_config_raw, dict):
            audit_config = audit_config_raw.copy()
        else:
            audit_config = {}

        # Add default values if not present
        defaults = {
            "enabled": True,
            "log_location": "./logs/adri_audit.jsonl",
            "log_level": "INFO",
            "include_data_samples": False,
            "max_log_size_mb": 100,
            "batch_mode": False,
            "batch_size": 100,
            "privacy_settings": {"exclude_pii": True, "hash_sensitive_fields": True},
        }

        for key, value in defaults.items():
            if key not in audit_config:
                audit_config[key] = value

        # Override with environment-specific settings
        if environment is None:
            environment = adri_config.get("default_environment", "development")

        if "environments" in adri_config and environment in adri_config["environments"]:
            env_config = adri_config["environments"][environment]
            if "audit" in env_config:
                env_audit = env_config["audit"]
                if isinstance(env_audit, dict):
                    audit_config.update(env_audit)

        return audit_config
