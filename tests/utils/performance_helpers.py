"""
Performance Testing Helper Utilities

This module provides helper utilities for performance testing with centralized
threshold management. It simplifies the migration from hardcoded thresholds
to the centralized system.

Key Features:
- Context managers for performance testing
- Assertion helpers with better error messages
- Migration utilities for updating existing tests
- Performance monitoring decorators

Usage:
    from tests.utils.performance_helpers import performance_test, assert_performance

    with performance_test("micro", "config_load") as timer:
        config = loader.load_config()
    # Automatically asserts against threshold

    # Or manual assertion with better error message
    assert_performance(duration, "micro", "config_load", "Config loading")
"""

import time
import functools
from contextlib import contextmanager
from typing import Optional, Union, Callable, Any, Generator, Dict

from tests.performance_thresholds import (
    get_performance_threshold,
    detect_platform_info,
    is_ci_environment,
    calculate_threshold_multiplier
)


class PerformanceTimer:
    """
    Simple performance timer with threshold checking capabilities.

    Provides accurate timing and automatic threshold validation.
    """

    def __init__(self, category: str, operation: str, description: Optional[str] = None):
        """
        Initialize performance timer.

        Args:
            category: Threshold category (micro, small, medium, large, concurrent)
            operation: Specific operation name
            description: Optional description for error messages
        """
        self.category = category
        self.operation = operation
        self.description = description or f"{category}.{operation}"
        self.threshold = get_performance_threshold(category, operation)
        self.start_time = None
        self.end_time = None
        self.duration = None

    def start(self) -> None:
        """Start timing."""
        self.start_time = time.time()

    def stop(self) -> float:
        """
        Stop timing and return duration.

        Returns:
            Duration in seconds
        """
        if self.start_time is None:
            raise RuntimeError("Timer not started")

        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        return self.duration

    def check_threshold(self, raise_on_failure: bool = True) -> bool:
        """
        Check if duration meets threshold.

        Args:
            raise_on_failure: Whether to raise AssertionError on threshold failure

        Returns:
            True if within threshold, False otherwise

        Raises:
            AssertionError: If raise_on_failure=True and threshold exceeded
        """
        if self.duration is None:
            raise RuntimeError("Timer not stopped")

        within_threshold = self.duration <= self.threshold

        if not within_threshold and raise_on_failure:
            platform_info = detect_platform_info()
            multiplier = calculate_threshold_multiplier()

            error_msg = (
                f"Performance threshold exceeded for {self.description}:\n"
                f"  Actual: {self.duration:.3f}s\n"
                f"  Threshold: {self.threshold:.3f}s\n"
                f"  Exceeded by: {(self.duration - self.threshold):.3f}s\n"
                f"  Platform: {platform_info['platform']} "
                f"({'CI' if platform_info['is_ci'] else 'local'})\n"
                f"  Multiplier: {multiplier:.1f}x\n"
                f"  Category: {self.category}, Operation: {self.operation}"
            )
            raise AssertionError(error_msg)

        return within_threshold

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic threshold checking."""
        self.stop()
        # Only check threshold if no exception occurred during execution
        if exc_type is None:
            self.check_threshold()


@contextmanager
def performance_test(category: str, operation: str = "default",
                    description: Optional[str] = None,
                    auto_assert: bool = True) -> Generator[PerformanceTimer, None, None]:
    """
    Context manager for performance testing with automatic threshold checking.

    Args:
        category: Threshold category (micro, small, medium, large, concurrent)
        operation: Specific operation name or 'default'
        description: Optional description for error messages
        auto_assert: Whether to automatically assert threshold on exit

    Yields:
        PerformanceTimer instance for manual control if needed

    Example:
        with performance_test("micro", "config_load") as timer:
            config = loader.load_config()
        # Automatically checks threshold

        # Or without auto-assertion for manual control
        with performance_test("micro", "config_load", auto_assert=False) as timer:
            config = loader.load_config()
        if timer.duration > timer.threshold * 0.8:  # Custom logic
            print(f"Warning: slow operation: {timer.duration:.3f}s")
    """
    timer = PerformanceTimer(category, operation, description)
    timer.start()

    try:
        yield timer
    finally:
        timer.stop()
        if auto_assert:
            timer.check_threshold()


def assert_performance(duration: float, category: str, operation: str = "default",
                      description: Optional[str] = None) -> None:
    """
    Assert that a duration meets performance threshold.

    Provides detailed error message with platform information on failure.

    Args:
        duration: Actual duration in seconds
        category: Threshold category (micro, small, medium, large, concurrent)
        operation: Specific operation name or 'default'
        description: Optional description for error messages

    Raises:
        AssertionError: If duration exceeds threshold

    Example:
        start_time = time.time()
        config = loader.load_config()
        duration = time.time() - start_time
        assert_performance(duration, "micro", "config_load", "Config loading")
    """
    threshold = get_performance_threshold(category, operation)

    if duration > threshold:
        platform_info = detect_platform_info()
        multiplier = calculate_threshold_multiplier()
        desc = description or f"{category}.{operation}"

        error_msg = (
            f"Performance threshold exceeded for {desc}:\n"
            f"  Actual: {duration:.3f}s\n"
            f"  Threshold: {threshold:.3f}s\n"
            f"  Exceeded by: {(duration - threshold):.3f}s\n"
            f"  Platform: {platform_info['platform']} "
            f"({'CI' if platform_info['is_ci'] else 'local'})\n"
            f"  Multiplier: {multiplier:.1f}x\n"
            f"  Category: {category}, Operation: {operation}"
        )
        raise AssertionError(error_msg)


def performance_monitor(category: str, operation: str = "default",
                       description: Optional[str] = None,
                       auto_assert: bool = True) -> Callable:
    """
    Decorator for automatic performance monitoring of functions.

    Args:
        category: Threshold category (micro, small, medium, large, concurrent)
        operation: Specific operation name or 'default'
        description: Optional description for error messages
        auto_assert: Whether to automatically assert threshold

    Returns:
        Decorated function with performance monitoring

    Example:
        @performance_monitor("micro", "config_load")
        def load_config_file(path):
            return ConfigLoader().load_config(path)

        # Function automatically checks performance threshold
        config = load_config_file("config.yaml")
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            desc = description or f"{func.__name__}"

            with performance_test(category, operation, desc, auto_assert):
                return func(*args, **kwargs)

        return wrapper
    return decorator


def measure_performance(func: Callable, *args, **kwargs) -> Dict[str, Union[float, Any]]:
    """
    Measure performance of a function call without threshold checking.

    Args:
        func: Function to measure
        *args: Arguments to pass to function
        **kwargs: Keyword arguments to pass to function

    Returns:
        Dictionary with 'result', 'duration', and 'platform_info'

    Example:
        result = measure_performance(loader.load_config, "config.yaml")
        print(f"Load time: {result['duration']:.3f}s")
        print(f"Platform: {result['platform_info']['platform']}")
    """
    platform_info = detect_platform_info()

    start_time = time.time()
    result = func(*args, **kwargs)
    duration = time.time() - start_time

    return {
        'result': result,
        'duration': duration,
        'platform_info': platform_info,
        'multiplier': calculate_threshold_multiplier(),
        'is_ci': platform_info['is_ci']
    }


def get_performance_report() -> Dict[str, Any]:
    """
    Get comprehensive performance environment report.

    Returns:
        Dictionary with platform information and threshold multipliers

    Example:
        report = get_performance_report()
        print(f"Running on {report['platform']} with {report['multiplier']:.1f}x multiplier")
    """
    platform_info = detect_platform_info()
    multiplier = calculate_threshold_multiplier()

    return {
        'platform': platform_info['platform'],
        'is_ci': platform_info['is_ci'],
        'ci_provider': platform_info.get('ci_provider'),
        'python_version': platform_info['python_version'],
        'architecture': platform_info['architecture'],
        'multiplier': multiplier,
        'threshold_adjustment': f"{multiplier:.1f}x baseline"
    }


# Migration helpers for updating existing tests
def replace_hardcoded_assertion(duration: float, hardcoded_threshold: float,
                               category: str, operation: str = "default",
                               description: Optional[str] = None) -> None:
    """
    Helper for migrating from hardcoded thresholds to centralized system.

    This function helps identify where hardcoded thresholds were too aggressive
    by comparing against the new centralized thresholds.

    Args:
        duration: Actual measured duration
        hardcoded_threshold: Original hardcoded threshold
        category: New threshold category
        operation: New operation name
        description: Operation description

    Example:
        # Old code: assert duration < 0.10
        # New code: replace_hardcoded_assertion(duration, 0.10, "micro", "config_load")
    """
    new_threshold = get_performance_threshold(category, operation)

    # Always use the centralized threshold
    assert_performance(duration, category, operation, description)

    # Log information about threshold change for debugging
    if hardcoded_threshold != new_threshold:
        platform_info = detect_platform_info()
        print(f"DEBUG: Threshold updated for {description or f'{category}.{operation}'}:")
        print(f"  Old hardcoded: {hardcoded_threshold:.3f}s")
        print(f"  New centralized: {new_threshold:.3f}s")
        print(f"  Actual duration: {duration:.3f}s")
        print(f"  Platform: {platform_info['platform']} ({'CI' if platform_info['is_ci'] else 'local'})")


class PerformanceBenchmark:
    """
    Performance benchmarking utility for comparing operations.

    Useful for establishing baseline performance and validating threshold settings.
    """

    def __init__(self, name: str):
        """Initialize benchmark with a name."""
        self.name = name
        self.measurements = []

    def measure(self, func: Callable, *args, **kwargs) -> float:
        """
        Measure function performance and record result.

        Args:
            func: Function to measure
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Duration in seconds
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time

        self.measurements.append({
            'duration': duration,
            'timestamp': start_time,
            'function': func.__name__ if hasattr(func, '__name__') else str(func)
        })

        return duration

    def get_statistics(self) -> Dict[str, float]:
        """
        Get statistical summary of measurements.

        Returns:
            Dictionary with min, max, mean, median durations
        """
        if not self.measurements:
            return {}

        durations = [m['duration'] for m in self.measurements]
        durations.sort()

        n = len(durations)
        median = durations[n // 2] if n % 2 == 1 else (durations[n // 2 - 1] + durations[n // 2]) / 2

        return {
            'count': n,
            'min': min(durations),
            'max': max(durations),
            'mean': sum(durations) / n,
            'median': median,
            'total': sum(durations)
        }

    def report(self) -> str:
        """
        Generate performance report string.

        Returns:
            Formatted performance report
        """
        stats = self.get_statistics()
        if not stats:
            return f"Benchmark '{self.name}': No measurements"

        platform_info = detect_platform_info()

        return (
            f"Performance Benchmark: {self.name}\n"
            f"Platform: {platform_info['platform']} ({'CI' if platform_info['is_ci'] else 'local'})\n"
            f"Measurements: {stats['count']}\n"
            f"Duration - Min: {stats['min']:.3f}s, Max: {stats['max']:.3f}s, "
            f"Mean: {stats['mean']:.3f}s, Median: {stats['median']:.3f}s\n"
            f"Total time: {stats['total']:.3f}s"
        )
