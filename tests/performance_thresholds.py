"""
Centralized Performance Threshold Management System

This module provides a centralized system for managing performance thresholds
across all ADRI test suites. It eliminates platform-specific CI failures by
providing realistic, environment-aware thresholds.

Key Features:
- Automatic platform detection (Windows, macOS, Linux)
- CI environment detection
- Windows CI-based threshold calculations (slowest platform)
- Centralized threshold configuration
- Backward compatibility with existing test patterns

Usage:
    from tests.performance_thresholds import get_performance_threshold

    # Replace: assert duration < 0.10
    # With: assert duration < get_performance_threshold("micro", "config_load")
"""

import os
import platform
import sys
from typing import Dict, Union, Optional


class PerformanceThresholdManager:
    """
    Central manager for performance thresholds with platform detection.

    Provides realistic thresholds based on Windows CI environment (slowest platform)
    and applies appropriate multipliers for different platforms and environments.
    """

    def __init__(self):
        """Initialize threshold manager with platform detection."""
        self._platform_info = self._detect_platform_info()
        self._multiplier = self._calculate_threshold_multiplier()
        self._base_thresholds = self._get_base_thresholds()

    def _detect_platform_info(self) -> Dict[str, Union[str, bool, float]]:
        """
        Detect platform and CI environment information.

        Returns:
            Dictionary containing platform, CI status, and performance characteristics
        """
        platform_system = platform.system().lower()
        is_ci = self._is_ci_environment()

        # Detect specific CI environments
        ci_provider = None
        if is_ci:
            if os.environ.get("GITHUB_ACTIONS"):
                ci_provider = "github_actions"
            elif os.environ.get("TRAVIS"):
                ci_provider = "travis"
            elif os.environ.get("CIRCLECI"):
                ci_provider = "circleci"
            elif os.environ.get("APPVEYOR"):
                ci_provider = "appveyor"
            else:
                ci_provider = "unknown"

        return {
            "platform": platform_system,
            "is_ci": is_ci,
            "ci_provider": ci_provider,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
            "architecture": platform.machine(),
        }

    def _is_ci_environment(self) -> bool:
        """
        Detect if running in CI environment.

        Returns:
            True if running in CI, False otherwise
        """
        ci_indicators = [
            "CI", "CONTINUOUS_INTEGRATION",
            "GITHUB_ACTIONS", "TRAVIS", "CIRCLECI", "APPVEYOR",
            "JENKINS_URL", "BUILDKITE", "GITLAB_CI"
        ]
        return any(os.environ.get(indicator) for indicator in ci_indicators)

    def _calculate_threshold_multiplier(self) -> float:
        """
        Calculate performance multiplier based on platform and environment.

        Windows CI is the baseline (1.0x) as it's the slowest platform.
        All other platforms get appropriate multipliers.

        Returns:
            Performance multiplier for current platform/environment
        """
        platform_system = self._platform_info["platform"]
        is_ci = self._platform_info["is_ci"]

        # Base multipliers for platforms (Windows CI = 1.0 baseline)
        platform_multipliers = {
            "windows": 1.0,  # Baseline - slowest platform
            "darwin": 0.7,   # macOS typically 30% faster
            "linux": 0.8,    # Linux typically 20% faster
        }

        # CI environment multipliers (additional slowdown)
        ci_multipliers = {
            "github_actions": 1.45,  # GitHub Actions can have significant variability (1.45 * 1.1 = ~1.6x)
            "travis": 1.1,
            "circleci": 1.1,
            "appveyor": 1.3,  # AppVeyor typically slowest
            "unknown": 1.2,   # Conservative for unknown CI
        }

        # Start with platform multiplier
        multiplier = platform_multipliers.get(platform_system, 1.0)

        # Apply CI multiplier if in CI environment
        if is_ci:
            ci_provider = self._platform_info.get("ci_provider", "unknown")
            ci_multiplier = ci_multipliers.get(ci_provider, 1.2)
            multiplier *= ci_multiplier

        # Additional safety margin for CI environments
        if is_ci:
            multiplier *= 1.1  # 10% safety margin for CI variability

        return multiplier

    def _get_base_thresholds(self) -> Dict[str, Dict[str, float]]:
        """
        Get base performance thresholds based on Windows CI performance.

        These thresholds are set based on actual Windows CI measurements
        and represent realistic expectations for the slowest platform.

        Returns:
            Nested dictionary of operation categories and their thresholds
        """
        return {
            # Micro operations (< 0.1s) - Basic operations like config loading
            "micro": {
                "config_load": 0.20,           # Config file loading (increased for CI variability)
                "config_cache": 0.08,          # Config cache access
                "validation_simple": 0.25,     # Simple validation operations (includes batch processing)
                "path_resolution": 0.10,       # Path resolution operations
                "environment_detection": 0.05, # Environment/platform detection
                "file_discovery": 0.20,        # File system discovery
                "default": 0.15,              # Default micro operation
            },

            # Small operations (0.1-1s) - Component initialization and simple processing
            "small": {
                "component_init": 0.80,        # Component initialization
                "data_validation": 1.20,       # Data validation processes
                "file_processing_small": 15.00, # Small file processing (increased for Windows CI JSONL bulk writes)
                "database_simple": 0.90,       # Simple database operations
                "network_request": 2.00,       # Network requests with timeout
                "default": 1.50,               # Default small operation
            },

            # Medium operations (1-10s) - Data processing and analysis
            "medium": {
                "data_profiling": 8.00,        # Data profiling operations
                "schema_analysis": 6.00,       # Schema analysis
                "file_processing_medium": 10.0, # Medium file processing
                "validation_complex": 7.50,    # Complex validation
                "standard_generation": 12.0,   # Standard generation
                "default": 10.0,               # Default medium operation
            },

            # Large operations (10s+) - Heavy processing and analysis
            "large": {
                "data_analysis": 60.0,         # Full data analysis
                "type_inference": 180.0,       # Type inference operations
                "standard_generation_full": 120.0, # Full standard generation
                "file_processing_large": 90.0, # Large file processing
                "integration_test": 45.0,      # Integration test workflows
                "default": 120.0,              # Default large operation
            },

            # Concurrent operations - Multi-threaded or parallel processing
            "concurrent": {
                "parallel_validation": 30.0,   # Parallel validation
                "concurrent_processing": 25.0, # Concurrent data processing
                "multi_thread_analysis": 40.0, # Multi-threaded analysis
                "default": 30.0,               # Default concurrent operation
            }
        }

    def get_threshold(self, category: str, operation: str) -> float:
        """
        Get performance threshold for a specific operation.

        Args:
            category: Threshold category (micro, small, medium, large, concurrent)
            operation: Specific operation name or 'default' for category default

        Returns:
            Performance threshold in seconds adjusted for current platform
        """
        if category not in self._base_thresholds:
            raise ValueError(f"Unknown threshold category: {category}")

        category_thresholds = self._base_thresholds[category]
        base_threshold = category_thresholds.get(operation, category_thresholds["default"])

        # Apply platform multiplier
        adjusted_threshold = base_threshold * self._multiplier

        return adjusted_threshold

    def get_platform_info(self) -> Dict[str, Union[str, bool, float]]:
        """Get detected platform information."""
        return self._platform_info.copy()

    def get_multiplier(self) -> float:
        """Get current platform multiplier."""
        return self._multiplier

    def reload_config(self) -> None:
        """Reload platform detection and thresholds."""
        self._platform_info = self._detect_platform_info()
        self._multiplier = self._calculate_threshold_multiplier()
        self._base_thresholds = self._get_base_thresholds()


# Global instance for easy access
_threshold_manager = PerformanceThresholdManager()


# Convenience functions for direct use in tests
def get_performance_threshold(category: str, operation: str = "default") -> float:
    """
    Get performance threshold for a specific operation.

    Primary function for use in test files. Replaces hardcoded thresholds.

    Args:
        category: Threshold category (micro, small, medium, large, concurrent)
        operation: Specific operation name or 'default' for category default

    Returns:
        Performance threshold in seconds adjusted for current platform

    Example:
        # Replace: assert duration < 0.10
        # With: assert duration < get_performance_threshold("micro", "config_load")
    """
    return _threshold_manager.get_threshold(category, operation)


def detect_platform_info() -> Dict[str, Union[str, bool, float]]:
    """Get detected platform and CI environment information."""
    return _threshold_manager.get_platform_info()


def is_ci_environment() -> bool:
    """Check if running in CI environment."""
    return _threshold_manager.get_platform_info()["is_ci"]


def calculate_threshold_multiplier() -> float:
    """Get current platform performance multiplier."""
    return _threshold_manager.get_multiplier()


def get_base_thresholds() -> Dict[str, Dict[str, float]]:
    """Get base threshold configuration (for debugging/testing)."""
    return _threshold_manager._base_thresholds.copy()


# Threshold categories for easy reference
THRESHOLD_CATEGORIES = {
    "micro": "Operations < 0.1s (config loading, validation, etc.)",
    "small": "Operations 0.1-1s (component init, simple processing)",
    "medium": "Operations 1-10s (data analysis, schema processing)",
    "large": "Operations 10s+ (heavy analysis, type inference)",
    "concurrent": "Multi-threaded/parallel operations"
}


# Common operation mappings for quick migration
OPERATION_MAPPINGS = {
    # Config operations
    "config_load": ("micro", "config_load"),
    "config_cache": ("micro", "config_cache"),
    "config_validation": ("micro", "validation_simple"),

    # Analysis operations
    "data_profiling": ("medium", "data_profiling"),
    "type_inference": ("large", "type_inference"),
    "schema_analysis": ("medium", "schema_analysis"),

    # File operations
    "file_small": ("small", "file_processing_small"),
    "file_medium": ("medium", "file_processing_medium"),
    "file_large": ("large", "file_processing_large"),

    # Validation operations
    "validation_simple": ("micro", "validation_simple"),
    "validation_complex": ("medium", "validation_complex"),

    # Component operations
    "component_init": ("small", "component_init"),
    "integration_test": ("large", "integration_test"),
}


def get_threshold_for_operation(operation_key: str) -> float:
    """
    Convenience function to get threshold by operation key.

    Args:
        operation_key: Key from OPERATION_MAPPINGS

    Returns:
        Performance threshold for the operation

    Example:
        assert duration < get_threshold_for_operation("config_load")
    """
    if operation_key not in OPERATION_MAPPINGS:
        raise ValueError(f"Unknown operation key: {operation_key}. "
                        f"Available keys: {list(OPERATION_MAPPINGS.keys())}")

    category, operation = OPERATION_MAPPINGS[operation_key]
    return get_performance_threshold(category, operation)
