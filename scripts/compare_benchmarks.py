#!/usr/bin/env python3
"""Compare benchmark results with previous runs and check against thresholds."""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from tabulate import tabulate


class BenchmarkComparison:
    """Compare benchmark results and generate reports."""

    def __init__(self, threshold_config_path: str = ".github/benchmark-thresholds.yml"):
        """Initialize with threshold configuration."""
        self.thresholds = self._load_thresholds(threshold_config_path)

    def _load_thresholds(self, config_path: str) -> dict:
        """Load threshold configuration from YAML file."""
        config_file = Path(config_path)
        if not config_file.exists():
            print(
                f"Warning: Threshold config not found at {config_path}, using defaults"
            )
            return self._get_default_thresholds()

        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
        return config

    def _get_default_thresholds(self) -> dict:
        """Return default threshold configuration."""
        return {
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
            "test_thresholds": {},
        }

    def load_benchmark_results(self, file_path: str) -> dict:
        """Load benchmark results from JSON file."""
        with open(file_path, "r") as f:
            return json.load(f)

    def extract_benchmark_metrics(self, results: dict) -> Dict[str, dict]:
        """Extract metrics from pytest-benchmark results."""
        benchmarks = {}

        if "benchmarks" in results:
            for bench in results["benchmarks"]:
                name = bench.get("name", "unknown")
                benchmarks[name] = {
                    "mean": bench.get("stats", {}).get("mean", 0)
                    * 1000,  # Convert to ms
                    "min": bench.get("stats", {}).get("min", 0) * 1000,
                    "max": bench.get("stats", {}).get("max", 0) * 1000,
                    "stddev": bench.get("stats", {}).get("stddev", 0) * 1000,
                    "rounds": bench.get("stats", {}).get("rounds", 0),
                    "iterations": bench.get("stats", {}).get("iterations", 0),
                }

        return benchmarks

    def compare_results(self, current: dict, previous: Optional[dict] = None) -> dict:
        """Compare current results with previous run."""
        current_metrics = self.extract_benchmark_metrics(current)
        previous_metrics = self.extract_benchmark_metrics(previous) if previous else {}

        comparison = {
            "tests": {},
            "regressions": [],
            "improvements": [],
            "new_tests": [],
            "missing_tests": [],
            "threshold_breaches": [],
        }

        # Check each current test
        for test_name, current_data in current_metrics.items():
            test_comparison = {
                "current": current_data,
                "previous": None,
                "change_percent": None,
                "status": "NEW",
            }

            # Check against thresholds
            test_config = self.thresholds.get("test_thresholds", {}).get(test_name, {})
            max_time = test_config.get("max_time_ms")
            if max_time and current_data["mean"] > max_time:
                comparison["threshold_breaches"].append(
                    {
                        "test": test_name,
                        "threshold": max_time,
                        "actual": current_data["mean"],
                        "exceeded_by_percent": (
                            (current_data["mean"] - max_time) / max_time
                        )
                        * 100,
                    }
                )

            if test_name in previous_metrics:
                previous_data = previous_metrics[test_name]
                test_comparison["previous"] = previous_data

                # Calculate change
                if previous_data["mean"] > 0:
                    change_percent = (
                        (current_data["mean"] - previous_data["mean"])
                        / previous_data["mean"]
                    ) * 100
                    test_comparison["change_percent"] = change_percent

                    # Determine regression tolerance
                    tolerance = test_config.get(
                        "regression_tolerance_percent",
                        self.thresholds["thresholds"]["regression_tolerance_percent"],
                    )

                    if change_percent > tolerance:
                        test_comparison["status"] = "REGRESSION"
                        comparison["regressions"].append(
                            {
                                "test": test_name,
                                "previous_ms": previous_data["mean"],
                                "current_ms": current_data["mean"],
                                "regression_percent": change_percent,
                                "tolerance": tolerance,
                            }
                        )
                    elif change_percent < -5:  # Improvement threshold
                        test_comparison["status"] = "IMPROVED"
                        comparison["improvements"].append(
                            {
                                "test": test_name,
                                "previous_ms": previous_data["mean"],
                                "current_ms": current_data["mean"],
                                "improvement_percent": abs(change_percent),
                            }
                        )
                    else:
                        test_comparison["status"] = "STABLE"
            else:
                comparison["new_tests"].append(test_name)

            comparison["tests"][test_name] = test_comparison

        # Check for missing tests
        for test_name in previous_metrics:
            if test_name not in current_metrics:
                comparison["missing_tests"].append(test_name)

        return comparison

    def generate_summary(self, comparison: dict) -> str:
        """Generate a markdown summary for GitHub Actions."""
        lines = ["# 📊 Benchmark Comparison Report\n"]

        # Overall status
        has_regressions = len(comparison["regressions"]) > 0
        has_breaches = len(comparison["threshold_breaches"]) > 0

        if has_regressions or has_breaches:
            lines.append("## ⚠️ Status: Issues Detected\n")
        else:
            lines.append("## ✅ Status: All Checks Passed\n")

        # Summary statistics
        lines.append("### Summary")
        summary_data = [
            ["Total Tests", len(comparison["tests"])],
            ["Regressions", len(comparison["regressions"])],
            ["Improvements", len(comparison["improvements"])],
            ["Threshold Breaches", len(comparison["threshold_breaches"])],
            ["New Tests", len(comparison["new_tests"])],
            ["Missing Tests", len(comparison["missing_tests"])],
        ]
        lines.append(
            tabulate(summary_data, headers=["Metric", "Count"], tablefmt="github")
        )
        lines.append("")

        # Regressions
        if comparison["regressions"]:
            lines.append("\n### ❌ Performance Regressions\n")
            reg_data = []
            for reg in comparison["regressions"]:
                reg_data.append(
                    [
                        reg["test"],
                        f"{reg['previous_ms']:.2f}",
                        f"{reg['current_ms']:.2f}",
                        f"+{reg['regression_percent']:.1f}%",
                        f"{reg['tolerance']}%",
                    ]
                )
            lines.append(
                tabulate(
                    reg_data,
                    headers=[
                        "Test",
                        "Previous (ms)",
                        "Current (ms)",
                        "Change",
                        "Tolerance",
                    ],
                    tablefmt="github",
                )
            )
            lines.append("")

        # Threshold breaches
        if comparison["threshold_breaches"]:
            lines.append("\n### 🚨 Threshold Breaches\n")
            breach_data = []
            for breach in comparison["threshold_breaches"]:
                breach_data.append(
                    [
                        breach["test"],
                        f"{breach['threshold']:.2f}",
                        f"{breach['actual']:.2f}",
                        f"+{breach['exceeded_by_percent']:.1f}%",
                    ]
                )
            lines.append(
                tabulate(
                    breach_data,
                    headers=["Test", "Threshold (ms)", "Actual (ms)", "Exceeded By"],
                    tablefmt="github",
                )
            )
            lines.append("")

        # Improvements
        if comparison["improvements"]:
            lines.append("\n### 🎉 Performance Improvements\n")
            imp_data = []
            for imp in comparison["improvements"]:
                imp_data.append(
                    [
                        imp["test"],
                        f"{imp['previous_ms']:.2f}",
                        f"{imp['current_ms']:.2f}",
                        f"-{imp['improvement_percent']:.1f}%",
                    ]
                )
            lines.append(
                tabulate(
                    imp_data,
                    headers=["Test", "Previous (ms)", "Current (ms)", "Improvement"],
                    tablefmt="github",
                )
            )
            lines.append("")

        # Test details
        lines.append("\n### 📈 All Test Results\n")
        test_data = []
        for test_name, data in comparison["tests"].items():
            current = data["current"]
            status_emoji = {
                "REGRESSION": "❌",
                "IMPROVED": "✅",
                "STABLE": "➖",
                "NEW": "🆕",
            }

            row = [
                f"{status_emoji.get(data['status'], '❓')} {test_name}",
                f"{current['mean']:.2f}",
                f"{current['min']:.2f}",
                f"{current['max']:.2f}",
            ]

            if data["previous"]:
                change = data.get("change_percent", 0)
                if change > 0:
                    row.append(f"+{change:.1f}%")
                elif change < 0:
                    row.append(f"{change:.1f}%")
                else:
                    row.append("0.0%")
            else:
                row.append("N/A")

            test_data.append(row)

        lines.append(
            tabulate(
                test_data,
                headers=["Test", "Mean (ms)", "Min (ms)", "Max (ms)", "Change"],
                tablefmt="github",
            )
        )
        lines.append("")

        # New and missing tests
        if comparison["new_tests"]:
            lines.append(f"\n### 🆕 New Tests: {', '.join(comparison['new_tests'])}\n")

        if comparison["missing_tests"]:
            lines.append(
                f"\n### ⚠️ Missing Tests: {', '.join(comparison['missing_tests'])}\n"
            )

        return "\n".join(lines)

    def check_enforcement(self, comparison: dict) -> Tuple[bool, List[str]]:
        """Check if enforcement rules are violated."""
        enforcement = self.thresholds.get("enforcement", {})
        violations = []

        if enforcement.get("fail_on_regression", False):
            if comparison["regressions"]:
                violations.append(
                    f"Found {len(comparison['regressions'])} performance regressions"
                )

        if enforcement.get("fail_on_threshold_breach", False):
            if comparison["threshold_breaches"]:
                violations.append(
                    f"Found {len(comparison['threshold_breaches'])} threshold breaches"
                )

        # Check warning levels
        warn_threshold = enforcement.get("warn_on_regression_percent", 5)
        for reg in comparison["regressions"]:
            if reg["regression_percent"] > warn_threshold:
                print(
                    f"⚠️  Warning: {reg['test']} regressed by {reg['regression_percent']:.1f}%"
                )

        return len(violations) == 0, violations


def main():
    """Main function for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Compare benchmark results")
    parser.add_argument("current", help="Path to current benchmark results JSON")
    parser.add_argument("--previous", help="Path to previous benchmark results JSON")
    parser.add_argument(
        "--thresholds",
        default=".github/benchmark-thresholds.yml",
        help="Path to threshold configuration",
    )
    parser.add_argument("--output", help="Output file for summary (default: stdout)")
    parser.add_argument(
        "--github-output",
        action="store_true",
        help="Write to GITHUB_STEP_SUMMARY if available",
    )
    parser.add_argument(
        "--enforce",
        action="store_true",
        help="Exit with error if enforcement rules are violated",
    )

    args = parser.parse_args()

    # Initialize comparison
    comparator = BenchmarkComparison(args.thresholds)

    # Load results
    current = comparator.load_benchmark_results(args.current)
    previous = None
    if args.previous:
        try:
            previous = comparator.load_benchmark_results(args.previous)
        except FileNotFoundError:
            print(f"Warning: Previous results not found at {args.previous}")

    # Compare results
    comparison = comparator.compare_results(current, previous)

    # Generate summary
    summary = comparator.generate_summary(comparison)

    # Output summary
    if args.output:
        with open(args.output, "w") as f:
            f.write(summary)
        print(f"Summary written to {args.output}")
    else:
        print(summary)

    # Write to GitHub summary if requested
    if args.github_output:
        import os

        github_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if github_summary_path:
            with open(github_summary_path, "a") as f:
                f.write(summary)
            print("Summary appended to GITHUB_STEP_SUMMARY")

    # Check enforcement
    if args.enforce:
        passed, violations = comparator.check_enforcement(comparison)
        if not passed:
            print("\n❌ Enforcement checks failed:")
            for violation in violations:
                print(f"  - {violation}")
            sys.exit(1)

    # Exit with appropriate code
    if comparison["regressions"] or comparison["threshold_breaches"]:
        sys.exit(1 if args.enforce else 0)

    return 0


if __name__ == "__main__":
    main()
