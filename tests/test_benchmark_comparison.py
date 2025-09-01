"""Tests for benchmark comparison functionality."""

import os
import sys

# Add scripts directory to path for imports - must be before other imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import json  # noqa: E402
import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402
from unittest.mock import MagicMock, mock_open, patch  # noqa: E402

import pytest  # noqa: E402
from compare_benchmarks import BenchmarkComparison  # noqa: E402


class TestBenchmarkComparison:
    """Test benchmark comparison functionality."""

    @pytest.fixture
    def sample_current_results(self):
        """Sample current benchmark results."""
        return {
            "benchmarks": [
                {
                    "name": "test_benchmark_data_loading",
                    "stats": {
                        "mean": 0.5,  # 500ms
                        "min": 0.4,
                        "max": 0.6,
                        "stddev": 0.05,
                        "rounds": 5,
                        "iterations": 1,
                    },
                },
                {
                    "name": "test_benchmark_assessment_simple",
                    "stats": {
                        "mean": 1.0,  # 1000ms
                        "min": 0.9,
                        "max": 1.1,
                        "stddev": 0.05,
                        "rounds": 5,
                        "iterations": 1,
                    },
                },
            ],
            "commit_sha": "abc123",
            "branch": "feature-branch",
            "timestamp": "2025-01-15T10:00:00",
        }

    @pytest.fixture
    def sample_previous_results(self):
        """Sample previous benchmark results."""
        return {
            "benchmarks": [
                {
                    "name": "test_benchmark_data_loading",
                    "stats": {
                        "mean": 0.4,  # 400ms - current (500ms) is slower, so regression
                        "min": 0.35,
                        "max": 0.45,
                        "stddev": 0.05,
                        "rounds": 5,
                        "iterations": 1,
                    },
                },
                {
                    "name": "test_benchmark_assessment_simple",
                    "stats": {
                        "mean": 1.2,  # 1200ms - current (1000ms) is faster, so improvement
                        "min": 1.1,
                        "max": 1.3,
                        "stddev": 0.05,
                        "rounds": 5,
                        "iterations": 1,
                    },
                },
            ],
            "commit_sha": "def456",
            "branch": "main",
            "timestamp": "2025-01-14T10:00:00",
        }

    @pytest.fixture
    def threshold_config(self, tmp_path):
        """Create a temporary threshold configuration."""
        config = {
            "thresholds": {
                "regression_tolerance_percent": 10,
                "decorator_overhead_percent": 10,
                "max_protected_time_ms": 100,
                "cli_max_time_10k_rows_ms": 5000,
                "memory_per_row_kb": 1.0,
            },
            "enforcement": {
                "fail_on_regression": False,
                "fail_on_threshold_breach": False,
                "warn_on_regression_percent": 5,
                "warn_on_threshold_approach": 90,
            },
            "test_thresholds": {
                "test_benchmark_data_loading": {
                    "max_time_ms": 600,
                    "regression_tolerance_percent": 15,
                },
                "test_benchmark_assessment_simple": {
                    "max_time_ms": 1100,
                    "regression_tolerance_percent": 10,
                },
            },
        }

        import yaml

        config_file = tmp_path / "benchmark-thresholds.yml"
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        return str(config_file)

    def test_load_benchmark_results(self, sample_current_results, tmp_path):
        """Test loading benchmark results from file."""
        # Save sample results to file
        results_file = tmp_path / "benchmark.json"
        with open(results_file, "w") as f:
            json.dump(sample_current_results, f)

        # Load results
        comparator = BenchmarkComparison()
        results = comparator.load_benchmark_results(str(results_file))

        assert results == sample_current_results
        assert len(results["benchmarks"]) == 2

    def test_extract_metrics(self, sample_current_results):
        """Test extracting metrics from benchmark results."""
        comparator = BenchmarkComparison()
        metrics = comparator.extract_benchmark_metrics(sample_current_results)

        assert len(metrics) == 2
        assert "test_benchmark_data_loading" in metrics
        assert (
            metrics["test_benchmark_data_loading"]["mean"] == 500.0
        )  # Converted to ms
        assert metrics["test_benchmark_assessment_simple"]["mean"] == 1000.0

    def test_compare_results_regression_detected(
        self, sample_current_results, sample_previous_results, threshold_config
    ):
        """Test comparison detecting performance regression."""
        comparator = BenchmarkComparison(threshold_config)
        comparison = comparator.compare_results(
            sample_current_results, sample_previous_results
        )

        # Should detect 1 regression (data_loading got slower: 400ms -> 500ms)
        assert len(comparison["regressions"]) == 1
        assert comparison["regressions"][0]["test"] == "test_benchmark_data_loading"
        assert comparison["regressions"][0]["regression_percent"] > 20  # 25% regression

        # Should detect 1 improvement (assessment_simple got faster: 1200ms -> 1000ms)
        assert len(comparison["improvements"]) == 1
        assert (
            comparison["improvements"][0]["test"] == "test_benchmark_assessment_simple"
        )

    def test_compare_results_threshold_breach(
        self, sample_current_results, threshold_config
    ):
        """Test detection of threshold breaches."""
        # Modify results to breach threshold
        sample_current_results["benchmarks"][0]["stats"][
            "mean"
        ] = 0.7  # 700ms > 600ms threshold

        comparator = BenchmarkComparison(threshold_config)
        comparison = comparator.compare_results(sample_current_results)

        assert len(comparison["threshold_breaches"]) == 1
        assert (
            comparison["threshold_breaches"][0]["test"] == "test_benchmark_data_loading"
        )
        assert comparison["threshold_breaches"][0]["threshold"] == 600
        assert comparison["threshold_breaches"][0]["actual"] == 700

    def test_generate_summary(
        self, sample_current_results, sample_previous_results, threshold_config
    ):
        """Test summary generation."""
        comparator = BenchmarkComparison(threshold_config)
        comparison = comparator.compare_results(
            sample_current_results, sample_previous_results
        )

        summary = comparator.generate_summary(comparison)

        # Check summary contains expected sections
        assert "# 📊 Benchmark Comparison Report" in summary
        assert "Status:" in summary
        assert "Summary" in summary
        assert "All Test Results" in summary

        # Should have table formatting
        assert "|" in summary
        assert "Mean (ms)" in summary

    def test_check_enforcement_no_violations(
        self, sample_current_results, threshold_config
    ):
        """Test enforcement check with no violations."""
        comparator = BenchmarkComparison(threshold_config)
        comparison = comparator.compare_results(sample_current_results)

        passed, violations = comparator.check_enforcement(comparison)

        assert passed is True
        assert len(violations) == 0

    def test_check_enforcement_with_violations(
        self, sample_current_results, sample_previous_results, threshold_config
    ):
        """Test enforcement check with violations."""
        import yaml

        # Enable enforcement
        with open(threshold_config, "r") as f:
            config = yaml.safe_load(f)

        config["enforcement"]["fail_on_regression"] = True

        with open(threshold_config, "w") as f:
            yaml.dump(config, f)

        comparator = BenchmarkComparison(threshold_config)
        comparison = comparator.compare_results(
            sample_current_results, sample_previous_results
        )

        # Add a regression
        comparison["regressions"].append(
            {"test": "test_fake", "regression_percent": 20}
        )

        passed, violations = comparator.check_enforcement(comparison)

        assert passed is False
        assert len(violations) > 0
        assert "performance regressions" in violations[0]

    def test_new_test_detection(self, sample_current_results, sample_previous_results):
        """Test detection of new tests."""
        # Add a new test to current results
        sample_current_results["benchmarks"].append(
            {
                "name": "test_new_benchmark",
                "stats": {
                    "mean": 0.3,
                    "min": 0.25,
                    "max": 0.35,
                    "stddev": 0.02,
                    "rounds": 5,
                    "iterations": 1,
                },
            }
        )

        comparator = BenchmarkComparison()
        comparison = comparator.compare_results(
            sample_current_results, sample_previous_results
        )

        assert "test_new_benchmark" in comparison["new_tests"]
        assert comparison["tests"]["test_new_benchmark"]["status"] == "NEW"

    def test_missing_test_detection(
        self, sample_current_results, sample_previous_results
    ):
        """Test detection of missing tests."""
        # Remove a test from current results
        sample_current_results["benchmarks"] = sample_current_results["benchmarks"][:1]

        comparator = BenchmarkComparison()
        comparison = comparator.compare_results(
            sample_current_results, sample_previous_results
        )

        assert "test_benchmark_assessment_simple" in comparison["missing_tests"]

    def test_comparison_without_previous_results(self, sample_current_results):
        """Test comparison when no previous results exist."""
        comparator = BenchmarkComparison()
        comparison = comparator.compare_results(sample_current_results, None)

        # All tests should be marked as new
        assert len(comparison["new_tests"]) == 2
        assert len(comparison["regressions"]) == 0
        assert len(comparison["improvements"]) == 0

    def test_stable_performance_detection(
        self, sample_current_results, sample_previous_results
    ):
        """Test detection of stable performance (no significant change)."""
        # Make performance nearly identical
        sample_previous_results["benchmarks"][0]["stats"][
            "mean"
        ] = 0.495  # Very close to 0.5

        comparator = BenchmarkComparison()
        comparison = comparator.compare_results(
            sample_current_results, sample_previous_results
        )

        # First test should be stable (< 5% change)
        assert comparison["tests"]["test_benchmark_data_loading"]["status"] == "STABLE"

    @patch(
        "sys.argv",
        ["compare_benchmarks.py", "current.json", "--previous", "previous.json"],
    )
    def test_cli_main_function(
        self, sample_current_results, sample_previous_results, tmp_path
    ):
        """Test the CLI main function."""
        # Create test files
        current_file = tmp_path / "current.json"
        previous_file = tmp_path / "previous.json"

        with open(current_file, "w") as f:
            json.dump(sample_current_results, f)

        with open(previous_file, "w") as f:
            json.dump(sample_previous_results, f)

        # Mock sys.argv
        with patch(
            "sys.argv",
            [
                "compare_benchmarks.py",
                str(current_file),
                "--previous",
                str(previous_file),
                "--output",
                str(tmp_path / "output.md"),
            ],
        ):
            from compare_benchmarks import main

            # Should exit with 0 (no enforcement)
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

            # Check output file was created
            assert (tmp_path / "output.md").exists()

    def test_performance_trend_analysis(self):
        """Test that multiple runs can be analyzed for trends."""
        comparator = BenchmarkComparison()

        # Simulate multiple benchmark runs showing a trend
        runs = []
        for i in range(5):
            runs.append(
                {
                    "benchmarks": [
                        {
                            "name": "test_trending",
                            "stats": {
                                "mean": 0.5 + (i * 0.05),  # Gradually getting slower
                                "min": 0.4 + (i * 0.05),
                                "max": 0.6 + (i * 0.05),
                                "stddev": 0.02,
                                "rounds": 5,
                                "iterations": 1,
                            },
                        }
                    ]
                }
            )

        # Compare first and last
        comparison = comparator.compare_results(runs[-1], runs[0])

        # Should detect regression
        assert len(comparison["regressions"]) == 1
        assert comparison["regressions"][0]["regression_percent"] > 30
