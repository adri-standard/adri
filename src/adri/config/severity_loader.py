"""Severity defaults configuration loader.

Loads and manages default severity assignments for auto-generated validation rules.
"""

import os
from pathlib import Path

import yaml

from ..core.severity import Severity


class SeverityDefaultsLoader:
    """Loads and provides access to severity default configuration.

    This class loads the severity_defaults.yaml configuration file and provides
    methods to retrieve default severity levels for specific rule types and dimensions.

    Example:
        >>> loader = SeverityDefaultsLoader()
        >>> severity = loader.get_severity("validity", "type")
        >>> print(severity)
        CRITICAL
    """

    _instance = None
    _config: dict | None = None

    def __new__(cls):
        """Implement singleton pattern for config caching."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the loader and load configuration if not already loaded."""
        if self._config is None:
            self._load_config()

    def _load_config(self):
        """Load severity defaults from YAML configuration file."""
        # Default config path
        config_file = Path(__file__).parent / "severity_defaults.yaml"

        # Allow override via environment variable
        env_config_path = os.environ.get("ADRI_SEVERITY_CONFIG")
        if env_config_path and os.path.exists(env_config_path):
            config_file = Path(env_config_path)

        try:
            with open(config_file, encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
        except Exception as e:
            # Fallback to hardcoded defaults if config file can't be loaded
            import warnings

            warnings.warn(
                f"Failed to load severity defaults config from {config_file}: {e}. "
                "Using hardcoded defaults."
            )
            self._config = self._get_hardcoded_defaults()

    def _get_hardcoded_defaults(self) -> dict:
        """Get hardcoded default configuration as fallback."""
        return {
            "severity_defaults": {
                "validity": {
                    "type": "CRITICAL",
                    "allowed_values": "CRITICAL",
                    "pattern": "WARNING",
                    "numeric_bounds": "CRITICAL",
                    "date_bounds": "CRITICAL",
                    "length_bounds": "CRITICAL",
                    "custom": "WARNING",
                },
                "completeness": {
                    "not_null": "CRITICAL",
                    "not_empty": "CRITICAL",
                    "required_fields": "CRITICAL",
                },
                "consistency": {
                    "format": "WARNING",
                    "case": "WARNING",
                    "uniqueness": "CRITICAL",
                    "cross_field": "WARNING",
                    "primary_key": "CRITICAL",
                },
                "freshness": {
                    "age_check": "WARNING",
                    "recency": "INFO",
                    "staleness": "INFO",
                },
                "plausibility": {
                    "range_check": "WARNING",
                    "categorical_frequency": "WARNING",
                    "statistical_outlier": "INFO",
                    "business_rule": "CRITICAL",
                },
            }
        }

    def get_severity(
        self, dimension: str, rule_type: str, default: str = "CRITICAL"
    ) -> Severity:
        """Get severity level for a specific dimension and rule type.

        Args:
            dimension: Dimension name (validity, completeness, etc.)
            rule_type: Rule type (type, not_null, pattern, etc.)
            default: Default severity if not found in config (default: "CRITICAL")

        Returns:
            Severity enum value

        Examples:
            >>> loader = SeverityDefaultsLoader()
            >>> loader.get_severity("validity", "type")
            <Severity.CRITICAL: 'CRITICAL'>
            >>> loader.get_severity("consistency", "format")
            <Severity.WARNING: 'WARNING'>
        """
        if self._config is None:
            self._load_config()

        try:
            # Check for overrides first
            overrides = self._config.get("overrides", {})
            # Handle None overrides (empty/commented in YAML)
            if (
                overrides
                and dimension in overrides
                and rule_type in overrides.get(dimension, {})
            ):
                severity_str = overrides[dimension][rule_type]
                return Severity.from_string(severity_str)

            # Check severity_defaults
            severity_defaults = self._config.get("severity_defaults", {})
            if severity_defaults and dimension in severity_defaults:
                dimension_defaults = severity_defaults.get(dimension, {})
                if dimension_defaults and rule_type in dimension_defaults:
                    severity_str = dimension_defaults[rule_type]
                    return Severity.from_string(severity_str)

            # Return default if not found
            return Severity.from_string(default)

        except Exception:
            # Fallback to default on any error
            return Severity.from_string(default)

    def get_all_defaults(self) -> dict[str, dict[str, str]]:
        """Get all severity defaults organized by dimension.

        Returns:
            Dictionary mapping dimensions to rule_type->severity mappings

        Example:
            >>> loader = SeverityDefaultsLoader()
            >>> defaults = loader.get_all_defaults()
            >>> defaults["validity"]["type"]
            'CRITICAL'
        """
        if self._config is None:
            self._load_config()

        return self._config.get("severity_defaults", {})

    def reload_config(self):
        """Reload configuration from file (useful for testing or runtime updates)."""
        self._config = None
        self._load_config()
