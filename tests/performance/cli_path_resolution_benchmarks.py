"""
Performance Benchmarks for ADRI CLI Path Resolution.

Comprehensive performance testing for the enhanced path resolution functionality
to ensure that the new features don't introduce performance regressions and
maintain acceptable response times for CLI operations.

Benchmarks include:
- Project root detection performance from various depths
- Path resolution speed across different path types
- Memory usage during path operations
- Performance under concurrent usage scenarios
- Comparison with baseline performance metrics
"""

import unittest
import tempfile
import shutil
import os
import sys
import time
import threading
from pathlib import Path
import yaml
import statistics
from typing import List, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import path resolution functions for benchmarking
from src.adri.cli import (
    _find_adri_project_root,
    _resolve_project_path,
    setup_command,
)


@dataclass
class PerformanceBenchmark:
    """Performance benchmark result."""
    test_name: str
    operation_count: int
    total_time: float
    average_time: float
    min_time: float
    max_time: float
    std_deviation: float
    operations_per_second: float


@dataclass
class PerformanceThreshold:
    """Performance threshold for validation."""
    max_average_time: float
    max_total_time: float
    min_ops_per_second: float


class PathResolutionBenchmarks:
    """Benchmark suite for path resolution performance."""

    def __init__(self):
        self.benchmarks: List[PerformanceBenchmark] = []
        self.thresholds = {
            "project_root_finding": PerformanceThreshold(0.01, 1.0, 100.0),
            "path_resolution": PerformanceThreshold(0.001, 0.5, 1000.0),
            "cross_directory": PerformanceThreshold(0.01, 2.0, 50.0),
            "concurrent_operations": PerformanceThreshold(0.02, 5.0, 25.0),
        }

    def benchmark_function(self, test_name: str, func, iterations: int = 100) -> PerformanceBenchmark:
        """Benchmark a function with multiple iterations."""
        times = []

        for _ in range(iterations):
            start_time = time.perf_counter()
            func()
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        total_time = sum(times)
        average_time = total_time / iterations
        min_time = min(times)
        max_time = max(times)
        std_deviation = statistics.stdev(times) if len(times) > 1 else 0.0
        ops_per_second = iterations / total_time if total_time > 0 else 0.0

        benchmark = PerformanceBenchmark(
            test_name=test_name,
            operation_count=iterations,
            total_time=total_time,
            average_time=average_time,
            min_time=min_time,
            max_time=max_time,
            std_deviation=std_deviation,
            operations_per_second=ops_per_second
        )

        self.benchmarks.append(benchmark)
        return benchmark

    def validate_benchmark(self, benchmark: PerformanceBenchmark, threshold_key: str) -> bool:
        """Validate benchmark against performance thresholds."""
        if threshold_key not in self.thresholds:
            return True

        threshold = self.thresholds[threshold_key]

        return (
            benchmark.average_time <= threshold.max_average_time and
            benchmark.total_time <= threshold.max_total_time and
            benchmark.operations_per_second >= threshold.min_ops_per_second
        )

    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        return {
            "benchmarks": [
                {
                    "test_name": b.test_name,
                    "operation_count": b.operation_count,
                    "total_time": round(b.total_time, 6),
                    "average_time": round(b.average_time, 6),
                    "min_time": round(b.min_time, 6),
                    "max_time": round(b.max_time, 6),
                    "std_deviation": round(b.std_deviation, 6),
                    "operations_per_second": round(b.operations_per_second, 2),
                }
                for b in self.benchmarks
            ],
            "thresholds": {
                key: {
                    "max_average_time": t.max_average_time,
                    "max_total_time": t.max_total_time,
                    "min_ops_per_second": t.min_ops_per_second,
                }
                for key, t in self.thresholds.items()
            },
            "timestamp": time.time(),
        }


class TestProjectRootFindingPerformance(unittest.TestCase):
    """Performance tests for project root detection."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        self.benchmarks = PathResolutionBenchmarks()

        # Create deep directory structure for testing
        self.project_root = Path(self.temp_dir)
        self.setup_deep_directory_structure()

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def setup_deep_directory_structure(self):
        """Create deep directory structure for performance testing."""
        # Create ADRI config at root
        adri_dir = self.project_root / "ADRI"
        adri_dir.mkdir(exist_ok=True)
        config_path = adri_dir / "config.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump({
                "adri": {
                    "project_name": "performance_test",
                    "version": "4.0.0",
                    "default_environment": "development"
                }
            }, f)

        # Create multiple levels of nesting
        for depth in range(1, 11):
            nested_path = self.project_root
            for level in range(depth):
                nested_path = nested_path / f"level_{level}"
            nested_path.mkdir(parents=True, exist_ok=True)

    def test_project_root_finding_performance_shallow(self):
        """Benchmark project root finding from shallow directory."""
        os.chdir(self.project_root)

        benchmark = self.benchmarks.benchmark_function(
            "project_root_finding_shallow",
            lambda: _find_adri_project_root(),
            iterations=1000
        )

        self.assertTrue(
            self.benchmarks.validate_benchmark(benchmark, "project_root_finding"),
            f"Performance regression in shallow root finding: {benchmark.average_time:.6f}s average"
        )

        print(f"📊 Shallow root finding: {benchmark.operations_per_second:.1f} ops/sec")

    def test_project_root_finding_performance_deep(self):
        """Benchmark project root finding from deep directory."""
        # Go to deepest directory
        deep_dir = self.project_root / "level_0" / "level_1" / "level_2" / "level_3" / "level_4"
        os.chdir(deep_dir)

        benchmark = self.benchmarks.benchmark_function(
            "project_root_finding_deep",
            lambda: _find_adri_project_root(),
            iterations=500
        )

        self.assertTrue(
            self.benchmarks.validate_benchmark(benchmark, "project_root_finding"),
            f"Performance regression in deep root finding: {benchmark.average_time:.6f}s average"
        )

        print(f"📊 Deep root finding: {benchmark.operations_per_second:.1f} ops/sec")

    def test_project_root_finding_performance_very_deep(self):
        """Benchmark project root finding from very deep directory."""
        # Go to very deep directory
        very_deep_dir = self.project_root
        for i in range(10):
            very_deep_dir = very_deep_dir / f"level_{i}"
        os.chdir(very_deep_dir)

        benchmark = self.benchmarks.benchmark_function(
            "project_root_finding_very_deep",
            lambda: _find_adri_project_root(),
            iterations=200
        )

        # Allow slightly relaxed performance for very deep structures
        self.assertLess(benchmark.average_time, 0.05,
            f"Root finding too slow from very deep directory: {benchmark.average_time:.6f}s")

        print(f"📊 Very deep root finding: {benchmark.operations_per_second:.1f} ops/sec")


class TestPathResolutionPerformance(unittest.TestCase):
    """Performance tests for path resolution functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        self.benchmarks = PathResolutionBenchmarks()

        # Create ADRI project structure
        self.project_root = Path(self.temp_dir)
        os.chdir(self.project_root)

        result = setup_command(force=True, project_name="perf_test")
        self.assertEqual(result, 0)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_tutorial_path_resolution_performance(self):
        """Benchmark tutorial path resolution performance."""
        tutorial_paths = [
            "tutorials/invoice_processing/invoice_data.csv",
            "tutorials/customer_service/customer_data.csv",
            "tutorials/financial_analysis/market_data.csv",
            "tutorials/compliance_monitoring/audit_data.csv",
        ]

        def resolve_tutorial_paths():
            for path in tutorial_paths:
                _resolve_project_path(path)

        benchmark = self.benchmarks.benchmark_function(
            "tutorial_path_resolution",
            resolve_tutorial_paths,
            iterations=500
        )

        self.assertTrue(
            self.benchmarks.validate_benchmark(benchmark, "path_resolution"),
            f"Tutorial path resolution too slow: {benchmark.average_time:.6f}s average"
        )

        print(f"📊 Tutorial path resolution: {benchmark.operations_per_second:.1f} ops/sec")

    def test_environment_path_resolution_performance(self):
        """Benchmark dev/prod environment path resolution performance."""
        env_paths = [
            "dev/contracts/invoice_standard.yaml",
            "dev/assessments/report_001.json",
            "dev/training-data/snapshot_123.csv",
            "dev/audit-logs/audit_log.csv",
            "prod/contracts/prod_standard.yaml",
            "prod/assessments/prod_report.json",
            "prod/training-data/prod_snapshot.csv",
            "prod/audit-logs/prod_audit.csv",
        ]

        def resolve_env_paths():
            for path in env_paths:
                _resolve_project_path(path)

        benchmark = self.benchmarks.benchmark_function(
            "environment_path_resolution",
            resolve_env_paths,
            iterations=500
        )

        self.assertTrue(
            self.benchmarks.validate_benchmark(benchmark, "path_resolution"),
            f"Environment path resolution too slow: {benchmark.average_time:.6f}s average"
        )

        print(f"📊 Environment path resolution: {benchmark.operations_per_second:.1f} ops/sec")

    def test_mixed_path_resolution_performance(self):
        """Benchmark mixed path type resolution performance."""
        mixed_paths = [
            "tutorials/invoice_processing/data.csv",
            "dev/contracts/test.yaml",
            "ADRI/tutorials/customer_service/data.csv",
            "prod/assessments/report.json",
            "config/settings.yaml",
            "data/raw_data.csv",
        ]

        def resolve_mixed_paths():
            for path in mixed_paths:
                _resolve_project_path(path)

        benchmark = self.benchmarks.benchmark_function(
            "mixed_path_resolution",
            resolve_mixed_paths,
            iterations=500
        )

        self.assertTrue(
            self.benchmarks.validate_benchmark(benchmark, "path_resolution"),
            f"Mixed path resolution too slow: {benchmark.average_time:.6f}s average"
        )

        print(f"📊 Mixed path resolution: {benchmark.operations_per_second:.1f} ops/sec")


class TestConcurrentPerformance(unittest.TestCase):
    """Performance tests for concurrent path resolution operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        self.benchmarks = PathResolutionBenchmarks()

        # Create ADRI project
        self.project_root = Path(self.temp_dir)
        os.chdir(self.project_root)

        result = setup_command(force=True, project_name="concurrent_perf_test")
        self.assertEqual(result, 0)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_concurrent_path_resolution_performance(self):
        """Benchmark concurrent path resolution operations."""
        paths_to_test = [
            "tutorials/invoice_processing/data.csv",
            "dev/contracts/test.yaml",
            "prod/assessments/report.json",
            "tutorials/customer_service/customer_data.csv",
            "dev/training-data/snapshot.csv",
        ]

        def worker_function(path_list):
            """Worker function for concurrent testing."""
            for path in path_list:
                _resolve_project_path(path)
                _find_adri_project_root()

        # Test concurrent operations
        start_time = time.perf_counter()

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for _ in range(10):  # 10 threads
                futures.append(executor.submit(worker_function, paths_to_test))

            # Wait for all threads to complete
            for future in as_completed(futures):
                future.result()

        end_time = time.perf_counter()
        total_time = end_time - start_time
        total_operations = 10 * len(paths_to_test) * 2  # 2 operations per path (resolve + find_root)

        # Create benchmark result
        benchmark = PerformanceBenchmark(
            test_name="concurrent_path_operations",
            operation_count=total_operations,
            total_time=total_time,
            average_time=total_time / total_operations,
            min_time=0.0,  # Not measured individually
            max_time=0.0,  # Not measured individually
            std_deviation=0.0,  # Not measured individually
            operations_per_second=total_operations / total_time
        )

        self.benchmarks.append(benchmark)

        # Validate concurrent performance
        self.assertTrue(
            self.benchmarks.validate_benchmark(benchmark, "concurrent_operations"),
            f"Concurrent operations too slow: {benchmark.average_time:.6f}s average"
        )

        print(f"📊 Concurrent operations: {benchmark.operations_per_second:.1f} ops/sec")

    def test_memory_usage_during_path_operations(self):
        """Test memory usage during intensive path operations."""
        try:
            import psutil
            process = psutil.Process()

            # Measure initial memory usage
            initial_memory = process.memory_info().rss / (1024 * 1024)  # MB

            # Perform intensive path operations
            paths = [
                "tutorials/invoice_processing/data.csv",
                "dev/contracts/test.yaml",
                "prod/assessments/report.json",
            ] * 100  # 300 path operations

            for path in paths:
                _resolve_project_path(path)
                _find_adri_project_root()

            # Measure final memory usage
            final_memory = process.memory_info().rss / (1024 * 1024)  # MB
            memory_increase = final_memory - initial_memory

            print(f"📊 Memory usage: {initial_memory:.1f}MB → {final_memory:.1f}MB (+{memory_increase:.1f}MB)")

            # Memory usage should not increase significantly
            self.assertLess(memory_increase, 50.0,
                f"Memory usage increased too much: {memory_increase:.1f}MB")

        except ImportError:
            print("⚠️  psutil not available - skipping memory usage test")


class TestPathResolutionRegressionBenchmarks(unittest.TestCase):
    """Regression testing for path resolution performance."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        self.benchmarks = PathResolutionBenchmarks()

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def create_test_project_with_complexity(self, num_directories: int = 50):
        """Create a project with specified complexity for testing."""
        os.chdir(self.temp_dir)

        # Setup basic ADRI project
        result = setup_command(force=True, project_name=f"complex_test_{num_directories}")
        self.assertEqual(result, 0)

        # Create additional directories to simulate complex project
        for i in range(num_directories):
            complex_dir = Path(f"complex_module_{i}/src/components/ui")
            complex_dir.mkdir(parents=True, exist_ok=True)

            # Create some files
            (complex_dir / f"component_{i}.py").touch()
            (complex_dir / f"test_{i}.py").touch()

    def test_performance_scaling_with_project_complexity(self):
        """Test how performance scales with project complexity."""
        complexity_levels = [10, 25, 50]
        results = {}

        for complexity in complexity_levels:
            with self.subTest(complexity=complexity):
                # Clean up and recreate for each test
                os.chdir(self.original_cwd)
                if Path(self.temp_dir).exists():
                    shutil.rmtree(self.temp_dir)
                self.temp_dir = tempfile.mkdtemp()

                self.create_test_project_with_complexity(complexity)

                # Move to a nested directory for testing
                test_dir = Path("complex_module_5/src/components")
                os.chdir(test_dir)

                # Benchmark root finding from complex project
                start_time = time.perf_counter()
                for _ in range(100):
                    _find_adri_project_root()
                end_time = time.perf_counter()

                avg_time = (end_time - start_time) / 100
                results[complexity] = avg_time

                print(f"📊 Complexity {complexity} dirs: {avg_time:.6f}s average")

        # Verify performance doesn't degrade significantly with complexity
        if len(results) >= 2:
            min_complexity = min(results.keys())
            max_complexity = max(results.keys())

            performance_ratio = results[max_complexity] / results[min_complexity]
            self.assertLess(performance_ratio, 3.0,
                f"Performance degrades too much with complexity: {performance_ratio:.2f}x slower")

    def test_performance_with_missing_config_scenarios(self):
        """Test performance when config file is missing (fallback scenarios)."""
        os.chdir(self.temp_dir)

        # Don't create ADRI config - test fallback performance
        # Create some directory structure anyway
        for i in range(20):
            test_dir = Path(f"test_dir_{i}/nested/structure")
            test_dir.mkdir(parents=True, exist_ok=True)

        # Move to nested directory
        os.chdir("test_dir_10/nested/structure")

        # Benchmark root finding when no config exists (should fail fast)
        benchmark = self.benchmarks.benchmark_function(
            "missing_config_root_finding",
            lambda: _find_adri_project_root(),
            iterations=100
        )

        # Should fail fast - not spend too much time searching
        self.assertLess(benchmark.average_time, 0.01,
            f"Missing config search too slow: {benchmark.average_time:.6f}s")

        print(f"📊 Missing config handling: {benchmark.operations_per_second:.1f} ops/sec")


class TestPerformanceReporting(unittest.TestCase):
    """Test performance reporting and validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.benchmarks = PathResolutionBenchmarks()

    def test_performance_report_generation(self):
        """Test generation of performance reports."""
        # Add sample benchmark data
        sample_benchmark = PerformanceBenchmark(
            test_name="sample_test",
            operation_count=100,
            total_time=0.5,
            average_time=0.005,
            min_time=0.001,
            max_time=0.01,
            std_deviation=0.002,
            operations_per_second=200.0
        )

        self.benchmarks.benchmarks.append(sample_benchmark)

        # Generate report
        report = self.benchmarks.generate_performance_report()

        # Verify report structure
        self.assertIn("benchmarks", report)
        self.assertIn("thresholds", report)
        self.assertIn("timestamp", report)

        # Verify benchmark data
        benchmarks = report["benchmarks"]
        self.assertEqual(len(benchmarks), 1)

        benchmark_data = benchmarks[0]
        self.assertEqual(benchmark_data["test_name"], "sample_test")
        self.assertEqual(benchmark_data["operation_count"], 100)
        self.assertAlmostEqual(benchmark_data["total_time"], 0.5, places=6)

    def test_performance_threshold_validation(self):
        """Test performance threshold validation logic."""
        # Test passing benchmark
        good_benchmark = PerformanceBenchmark(
            test_name="good_performance",
            operation_count=100,
            total_time=0.1,
            average_time=0.001,
            min_time=0.0005,
            max_time=0.002,
            std_deviation=0.0003,
            operations_per_second=1000.0
        )

        self.assertTrue(
            self.benchmarks.validate_benchmark(good_benchmark, "path_resolution")
        )

        # Test failing benchmark
        slow_benchmark = PerformanceBenchmark(
            test_name="slow_performance",
            operation_count=100,
            total_time=10.0,
            average_time=0.1,
            min_time=0.05,
            max_time=0.2,
            std_deviation=0.03,
            operations_per_second=10.0
        )

        self.assertFalse(
            self.benchmarks.validate_benchmark(slow_benchmark, "path_resolution")
        )

    def test_benchmark_statistics_accuracy(self):
        """Test accuracy of benchmark statistics calculation."""
        # Create mock function with predictable timing
        def mock_operation():
            time.sleep(0.001)  # 1ms sleep

        benchmark = self.benchmarks.benchmark_function(
            "statistics_test",
            mock_operation,
            iterations=10
        )

        # Verify statistics are reasonable
        self.assertGreaterEqual(benchmark.average_time, 0.001)
        self.assertLessEqual(benchmark.average_time, 0.01)  # Allow for overhead
        self.assertEqual(benchmark.operation_count, 10)
        self.assertGreater(benchmark.operations_per_second, 100)
        self.assertLessEqual(benchmark.operations_per_second, 1000)


def run_comprehensive_performance_suite():
    """Run the complete performance benchmark suite and generate report."""
    import sys

    print("🚀 ADRI Path Resolution Performance Benchmark Suite")
    print("==================================================")
    print()

    # Create temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()

    try:
        os.chdir(temp_dir)

        # Setup ADRI project
        result = setup_command(force=True, project_name="benchmark_suite")
        if result != 0:
            print("❌ Failed to setup test project")
            return False

        benchmarks = PathResolutionBenchmarks()

        print("🔄 Running performance benchmarks...")
        print()

        # Benchmark 1: Project root finding
        print("📊 Benchmarking project root finding...")
        root_benchmark = benchmarks.benchmark_function(
            "project_root_finding",
            lambda: _find_adri_project_root(),
            iterations=1000
        )
        print(f"   Average: {root_benchmark.average_time:.6f}s")
        print(f"   Ops/sec: {root_benchmark.operations_per_second:.1f}")
        print()

        # Benchmark 2: Path resolution
        print("📊 Benchmarking path resolution...")
        paths = [
            "tutorials/invoice_processing/data.csv",
            "dev/contracts/test.yaml",
            "prod/assessments/report.json"
        ]

        def resolve_test_paths():
            for path in paths:
                _resolve_project_path(path)

        path_benchmark = benchmarks.benchmark_function(
            "path_resolution",
            resolve_test_paths,
            iterations=500
        )
        print(f"   Average: {path_benchmark.average_time:.6f}s")
        print(f"   Ops/sec: {path_benchmark.operations_per_second:.1f}")
        print()

        # Generate performance report
        report = benchmarks.generate_performance_report()

        print("📋 Performance Report Summary:")
        print("=============================")
        for benchmark_data in report["benchmarks"]:
            name = benchmark_data["test_name"]
            avg_time = benchmark_data["average_time"]
            ops_per_sec = benchmark_data["operations_per_second"]
            print(f"   {name}: {avg_time:.6f}s avg, {ops_per_sec:.1f} ops/sec")

        print()
        print("✅ Performance benchmark suite completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Performance benchmark suite failed: {e}")
        return False

    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)


if __name__ == '__main__':
    # Run comprehensive performance suite if executed directly
    if len(sys.argv) > 1 and sys.argv[1] == '--benchmark':
        success = run_comprehensive_performance_suite()
        sys.exit(0 if success else 1)
    else:
        # Run unit tests
        unittest.main()
