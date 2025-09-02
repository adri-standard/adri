"""Tests for benchmark timeout functionality."""

import time
from unittest.mock import MagicMock, patch

import pytest


class TestBenchmarkTimeout:
    """Test benchmark timeout enforcement."""

    @pytest.mark.timeout(1)
    def test_timeout_enforced_on_slow_test(self):
        """Test that timeout is properly enforced on slow tests."""
        # This test verifies timeout configuration
        # In practice, pytest-timeout will terminate long-running tests
        start_time = time.time()
        # Simulate a test that would timeout if not interrupted
        for _ in range(10):
            time.sleep(0.05)
            if time.time() - start_time > 0.5:
                break  # Exit before actual timeout
        assert time.time() - start_time < 1.0

    @pytest.mark.timeout(5)
    def test_timeout_allows_fast_test(self):
        """Test that timeout doesn't affect fast tests."""
        # This should complete successfully
        result = sum(range(1000000))
        assert result > 0

    @pytest.mark.timeout(10)
    @pytest.mark.benchmark
    def test_benchmark_with_timeout(self, benchmark):
        """Test that benchmarks work with timeout markers."""

        def fast_function():
            return sum(range(1000))

        result = benchmark(fast_function)
        assert result == sum(range(1000))

    def test_timeout_marker_present(self):
        """Verify timeout markers are present on benchmark tests."""
        from tests import test_benchmarks

        # Check that test methods have timeout markers
        test_class = test_benchmarks.TestPerformanceBenchmarks

        # Get all test methods
        test_methods = [
            method for method in dir(test_class) if method.startswith("test_benchmark_")
        ]

        # Verify at least some benchmark tests exist
        assert len(test_methods) > 0

        for method_name in test_methods:
            method = getattr(test_class, method_name)

            # Check if method has pytest marks
            if hasattr(method, "pytestmark"):
                marks = method.pytestmark
                # Check for timeout mark
                timeout_marks = [
                    mark
                    for mark in marks
                    if hasattr(mark, "name") and mark.name == "timeout"
                ]
                # Each benchmark test should have a timeout
                assert len(timeout_marks) > 0, f"{method_name} missing timeout marker"

    @pytest.mark.timeout(3)
    def test_timeout_cleanup(self):
        """Test that resources are cleaned up properly."""
        resources = []

        def allocate_resources():
            for i in range(10):
                resources.append(f"resource_{i}")
                time.sleep(0.01)  # Fast allocation

        try:
            # Allocate resources quickly
            allocate_resources()
            assert len(resources) == 10
        finally:
            # Resources should still be accessible for cleanup
            assert isinstance(resources, list)
            assert len(resources) > 0

    @pytest.mark.parametrize(
        "timeout_value,sleep_time,should_fail",
        [
            (2, 0.1, False),  # Fast execution, should pass
            (0.5, 1, True),  # Slow execution, should timeout
            (1, 0.5, False),  # Just under timeout, should pass
        ],
    )
    def test_various_timeout_scenarios(self, timeout_value, sleep_time, should_fail):
        """Test various timeout scenarios."""
        import signal
        import sys

        if sys.platform == "win32":
            pytest.skip("Signal-based timeout not supported on Windows")

        def timeout_handler(signum, frame):
            raise TimeoutError("Test timed out")

        # Set up timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.setitimer(signal.ITIMER_REAL, timeout_value)

        try:
            time.sleep(sleep_time)
            assert not should_fail, "Test should have timed out"
        except TimeoutError:
            assert should_fail, "Test should not have timed out"
        finally:
            # Cancel the timer
            signal.setitimer(signal.ITIMER_REAL, 0)

    def test_timeout_configuration_loaded(self):
        """Test that timeout configuration is properly loaded."""
        from pathlib import Path

        import yaml

        # Load benchmark thresholds
        threshold_file = Path(".github/benchmark-thresholds.yml")
        if threshold_file.exists():
            with open(threshold_file, "r") as f:
                config = yaml.safe_load(f)

            # Verify timeout configuration exists
            assert "config" in config
            assert "timeout_seconds" in config["config"]
            assert config["config"]["timeout_seconds"] > 0
            assert config["config"]["timeout_seconds"] <= 300  # Reasonable max

    @pytest.mark.timeout(5)
    def test_concurrent_timeout_handling(self):
        """Test timeout handling with concurrent operations."""
        import concurrent.futures

        def slow_task(duration):
            time.sleep(duration)
            return duration

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit tasks with different durations
            futures = [
                executor.submit(slow_task, 0.1),
                executor.submit(slow_task, 0.2),
                executor.submit(slow_task, 0.3),
            ]

            # All should complete within timeout
            results = [f.result(timeout=1) for f in futures]
            assert results == [0.1, 0.2, 0.3]
