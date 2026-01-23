# @ADRI_FEATURE[config_loader, scope=SHARED]
# Description: Configuration management and environment-based contract resolution
"""
ADRI Configuration Loader.

Streamlined configuration loading logic, simplified from adri/config/manager.py.
Removes complex configuration management while preserving essential functionality.

Supports package-local contract resolution for atomic/self-contained package architectures
(e.g., playbooks, modules, plugins) via the package_context parameter.
"""

import logging
import os
from pathlib import Path
from typing import Any

import yaml

from .types import ContractResolutionResult, ResolutionConfig, ResolutionStrategy

logger = logging.getLogger(__name__)


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
                "paths": {
                    "contracts": "./ADRI/contracts",
                    "assessments": "./ADRI/assessments",
                    "training_data": "./ADRI/training-data",
                    "audit_logs": "./ADRI/audit-logs",
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
            required_fields = ["project_name", "paths"]
            for field in required_fields:
                if field not in adri_config:
                    return False

            # Check paths structure
            paths = adri_config["paths"]
            if not isinstance(paths, dict):
                return False

            # Check required paths
            required_paths = ["contracts", "assessments", "training_data", "audit_logs"]
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

    def get_paths_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Get paths configuration from the ADRI config.

        Args:
            config: Full configuration dictionary

        Returns:
            Paths configuration dictionary with contracts, assessments, etc.
        """
        adri_config = config.get("adri", {})
        paths = adri_config.get("paths", {})

        # Return with defaults for any missing paths
        return {
            "contracts": paths.get("contracts", "ADRI/contracts"),
            "assessments": paths.get("assessments", "ADRI/assessments"),
            "training_data": paths.get("training_data", "ADRI/training-data"),
            "audit_logs": paths.get("audit_logs", "ADRI/audit-logs"),
        }

    def get_environment_config(
        self, config: dict[str, Any], environment: str | None = None
    ) -> dict[str, Any]:
        """
        Get configuration for the environment.

        Note: In the OSS flat structure, this returns the paths config.
        The environment parameter is kept for backward compatibility but is ignored.

        Args:
            config: Full configuration dictionary
            environment: Ignored in OSS (kept for API compatibility)

        Returns:
            Configuration with paths
        """
        # For backward compatibility, return a dict with paths
        return {"paths": self.get_paths_config(config)}

    def get_protection_config(self, environment: str | None = None) -> dict[str, Any]:
        """
        Get protection configuration.

        Args:
            environment: Ignored in OSS (kept for API compatibility)

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

        # Get protection config from flat structure
        protection_config = adri_config.get("protection", {}).copy()
        if not isinstance(protection_config, dict):
            protection_config = {}

        return protection_config

    def get_resolution_config(self) -> ResolutionConfig:
        """
        Get the resolution configuration from config file or environment.

        Precedence:
        1. ADRI_RESOLUTION_STRATEGY environment variable
        2. Config file resolution.strategy
        3. Default (hybrid)

        Returns:
            ResolutionConfig with strategy and settings
        """
        config = self.get_active_config()

        # Start with defaults
        strategy = ResolutionStrategy.HYBRID
        package_subdirectory = "adri"
        fallback_enabled = True

        # Check environment variable override
        env_strategy = os.environ.get("ADRI_RESOLUTION_STRATEGY")
        if env_strategy:
            try:
                strategy = ResolutionStrategy.from_string(env_strategy)
            except ValueError:
                logger.warning(
                    f"Invalid ADRI_RESOLUTION_STRATEGY: {env_strategy}, using hybrid"
                )

        # Check environment variable for subdirectory
        env_subdir = os.environ.get("ADRI_PACKAGE_SUBDIRECTORY")
        if env_subdir:
            package_subdirectory = env_subdir

        # Load from config if available and no env override
        if config and not env_strategy:
            resolution_config = config.get("adri", {}).get("resolution", {})
            if resolution_config:
                return ResolutionConfig.from_dict(resolution_config)

        return ResolutionConfig(
            strategy=strategy,
            package_subdirectory=package_subdirectory,
            fallback_enabled=fallback_enabled,
        )

    def _resolve_package_context_path(self, package_context: str) -> Path:
        """Resolve package_context to an absolute path based on project root."""
        package_path = Path(package_context)
        if package_path.is_absolute():
            return package_path

        # Determine base directory from config file location (or cwd)
        config_file_path = os.environ.get("ADRI_CONFIG_PATH") or self.find_config_file()
        if config_file_path:
            base_dir = Path(config_file_path).parent
            if base_dir.name == "ADRI":
                base_dir = base_dir.parent
        else:
            base_dir = Path.cwd()

        return base_dir / package_path

    def _resolve_package_local_contract(
        self, contract_name: str, package_context: str, subdirectory: str = "adri"
    ) -> str | None:
        """
        Resolve contract from package-local directory.

        Searches for contract in {package_context}/{subdirectory}/{contract_name}.yaml

        Args:
            contract_name: Contract name (with or without .yaml extension)
            package_context: Absolute path to package directory
            subdirectory: Subdirectory name within package (default: "adri")

        Returns:
            Absolute path to contract if found, None otherwise
        """
        # Normalize contract name
        if not contract_name.endswith((".yaml", ".yml")):
            contract_name += ".yaml"

        package_path = self._resolve_package_context_path(package_context)

        # Check in package subdirectory
        contract_path = package_path / subdirectory / contract_name
        resolved_path = contract_path.resolve()

        if resolved_path.exists():
            logger.debug(f"Found package-local contract: {resolved_path}")
            return str(resolved_path)

        logger.debug(f"Package-local contract not found: {resolved_path}")
        return None

    def resolve_contract_path(
        self,
        contract_name: str,
        environment: str | None = None,
        package_context: str | None = None,
    ) -> str:
        """
        Resolve a contract name to full absolute path with package context support.

        Resolution behavior depends on configured strategy:
        - FLAT: Only check centralized directory (legacy behavior)
        - PACKAGE_LOCAL: Only check package_context directory
        - HYBRID: Check package_context first, fallback to centralized

        Precedence for resolution:
        1. ADRI_CONTRACTS_DIR environment variable (always highest, overrides strategy)
        2. Package-local resolution (if package_context provided and strategy allows)
        3. Config file paths (centralized)
        4. Default ADRI/contracts structure

        Args:
            contract_name: Name of contract (with or without .yaml extension)
            environment: Ignored in OSS (kept for API compatibility)
            package_context: Optional path to package directory for local resolution

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
            logger.debug(f"Resolved contract via ADRI_CONTRACTS_DIR: {full_path}")
            return str(full_path)

        # Get resolution configuration
        resolution_config = self.get_resolution_config()
        strategy = resolution_config.strategy

        # Package-local resolution (if applicable)
        if package_context and strategy in (
            ResolutionStrategy.PACKAGE_LOCAL,
            ResolutionStrategy.HYBRID,
        ):
            local_path = self._resolve_package_local_contract(
                contract_name, package_context, resolution_config.package_subdirectory
            )

            if local_path:
                return local_path

            # If package_context provided, return expected package-local path even if not found
            if strategy in (
                ResolutionStrategy.PACKAGE_LOCAL,
                ResolutionStrategy.HYBRID,
            ):
                package_path = self._resolve_package_context_path(package_context)
                expected_path = (
                    package_path
                    / resolution_config.package_subdirectory
                    / contract_name
                )
                logger.debug(f"Package-local contract expected at: {expected_path}")
                return str(expected_path.resolve())

        # FLAT strategy or HYBRID fallback: use centralized resolution
        return self._resolve_centralized_contract(contract_name)

    def _resolve_centralized_contract(self, contract_name: str) -> str:
        """
        Resolve contract from centralized directory (legacy behavior).

        Args:
            contract_name: Contract name with .yaml extension

        Returns:
            Full absolute path to contract file
        """
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

        if not config:
            # Fallback to default flat path structure
            contract_path = base_dir / "ADRI" / "contracts" / contract_name
            return str(contract_path)

        try:
            adri_config = config["adri"]
            contracts_dir = adri_config["paths"]["contracts"]

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
            # Fallback on any error - use flat structure
            contract_path = base_dir / "ADRI" / "contracts" / contract_name
            return str(contract_path)

    def resolve_contract_path_with_metadata(
        self,
        contract_name: str,
        environment: str | None = None,
        package_context: str | None = None,
    ) -> ContractResolutionResult:
        """
        Resolve contract path with full metadata about resolution.

        Same resolution logic as resolve_contract_path but returns
        a ContractResolutionResult with additional metadata useful
        for debugging and audit logging.

        Args:
            contract_name: Name of contract
            environment: Ignored (kept for API compatibility)
            package_context: Optional package directory for local resolution

        Returns:
            ContractResolutionResult with path and metadata
        """
        resolution_config = self.get_resolution_config()

        # Normalize contract name
        if not contract_name.endswith((".yaml", ".yml")):
            contract_name += ".yaml"

        # Check env override first
        env_contracts_dir = os.environ.get("ADRI_CONTRACTS_DIR")
        if env_contracts_dir:
            contracts_path = Path(env_contracts_dir)
            if not contracts_path.is_absolute():
                contracts_path = Path.cwd() / contracts_path
            full_path = (contracts_path / contract_name).resolve()
            return ContractResolutionResult(
                path=str(full_path),
                source="env_override",
                package_context=None,
                exists=full_path.exists(),
                strategy_used=resolution_config.strategy,
            )

        # Try package-local resolution
        if package_context and resolution_config.strategy in (
            ResolutionStrategy.PACKAGE_LOCAL,
            ResolutionStrategy.HYBRID,
        ):
            local_path = self._resolve_package_local_contract(
                contract_name, package_context, resolution_config.package_subdirectory
            )

            if local_path:
                return ContractResolutionResult(
                    path=local_path,
                    source="package_local",
                    package_context=package_context,
                    exists=True,
                    strategy_used=resolution_config.strategy,
                )

            # Package-local expected path when package_context provided
            if resolution_config.strategy in (
                ResolutionStrategy.PACKAGE_LOCAL,
                ResolutionStrategy.HYBRID,
            ):
                package_path = self._resolve_package_context_path(package_context)
                expected_path = (
                    package_path
                    / resolution_config.package_subdirectory
                    / contract_name
                )
                return ContractResolutionResult(
                    path=str(expected_path.resolve()),
                    source="package_local",
                    package_context=package_context,
                    exists=False,
                    strategy_used=resolution_config.strategy,
                )

        # Centralized fallback
        centralized_path = self._resolve_centralized_contract(contract_name)
        return ContractResolutionResult(
            path=centralized_path,
            source="centralized" if not package_context else "fallback",
            package_context=package_context,
            exists=Path(centralized_path).exists(),
            strategy_used=resolution_config.strategy,
        )

    def create_directory_structure(self, config: dict[str, Any]) -> None:
        """
        Create the directory structure based on configuration.

        Args:
            config: Configuration dictionary containing paths
        """
        adri_config = config["adri"]
        paths = adri_config["paths"]

        # Create directories for flat structure
        for path_type, path_value in paths.items():
            Path(path_value).mkdir(parents=True, exist_ok=True)

    def get_assessments_dir(self, environment: str | None = None) -> str:
        """
        Get the assessments directory.

        Args:
            environment: Ignored in OSS (kept for API compatibility)

        Returns:
            Path to assessments directory
        """
        config = self.get_active_config()

        if not config:
            return "./ADRI/assessments"

        try:
            adri_config = config["adri"]
            return adri_config["paths"]["assessments"]
        except (KeyError, ValueError, AttributeError):
            return "./ADRI/assessments"

    def get_training_data_dir(self, environment: str | None = None) -> str:
        """
        Get the training data directory.

        Args:
            environment: Ignored in OSS (kept for API compatibility)

        Returns:
            Path to training data directory
        """
        config = self.get_active_config()

        if not config:
            return "./ADRI/training-data"

        try:
            adri_config = config["adri"]
            return adri_config["paths"]["training_data"]
        except (KeyError, ValueError, AttributeError):
            return "./ADRI/training-data"


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
