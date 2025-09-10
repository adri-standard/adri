"""
Stress Testing Suite for ADRI Validator.

This module contains stress tests to validate the system's behavior under extreme conditions.

NOTE: These tests use extreme datasets and are marked with @pytest.mark.stress
They will be skipped by default. Run with: pytest --stress
"""

import gc
import multiprocessing
import os
import random
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import List
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from adri.core.assessor import AssessmentEngine
from adri.core.audit_logger import AuditLogger
from adri.core.protection import DataProtectionEngine, ProtectionError

# Import test utilities to prevent token explosion
try:
    from tests.test_utils import skip_if_ci, TestDataGenerator
except ImportError:
    # Fallback if test_utils not available
    TestDataGenerator = None

    def skip_if_ci():
        """Fallback skip_if_ci function."""
        pass


@pytest.mark.stress
class TestStressPerformance:
    """Stress tests for extreme conditions.

    These tests will be skipped by default. Run with: pytest --stress
    """

    @pytest.fixture
    def generate_extreme_dataset(self):
        """Generate datasets for stress testing with size controls."""

        def _generate(
            rows: int, cols: int = 10, sparse: bool = False, nested: bool = False
        ):
            # Apply size limits based on environment
            if TestDataGenerator:
                rows = TestDataGenerator.get_safe_row_count(rows, test_type="stress")
            np.random.seed(42)

            if sparse:
                # Sparse dataset with many NaN values
                data = {}
                for i in range(cols):
                    values = np.random.uniform(0, 100, rows)
                    # Make 70% of values NaN
                    mask = np.random.random(rows) < 0.7
                    values[mask] = np.nan
                    data[f"col_{i}"] = values
            elif nested:
                # Dataset with nested structures
                data = {
                    "id": range(rows),
                    "nested_data": [
                        {"level1": {"level2": {"value": np.random.random()}}}
                        for _ in range(rows)
                    ],
                    "list_data": [
                        [np.random.randint(0, 100) for _ in range(10)]
                        for _ in range(rows)
                    ],
                }
            else:
                # Standard stress test dataset
                data = {
                    "id": range(rows),
                    "text": ["x" * 1000 for _ in range(rows)],  # Long strings
                    "numbers": np.random.uniform(-1e10, 1e10, rows),  # Large numbers
                    "categories": np.random.choice(
                        ["A"] * 100, rows
                    ),  # Low cardinality
                }

            return pd.DataFrame(data)

        return _generate

    def test_stress_maximum_concurrent_operations(self, generate_extreme_dataset):
        """Test maximum concurrent operations the system can handle."""
        num_threads = 100  # Stress test with 100 concurrent threads
        datasets = [generate_extreme_dataset(100) for _ in range(num_threads)]
        engine = DataProtectionEngine()

        successful_operations = 0
        failed_operations = 0

        def run_assessment(data):
            nonlocal successful_operations, failed_operations
            try:
                with patch.object(engine, "ensure_standard_exists"):
                    with patch.object(engine, "assess_data_quality") as mock_assess:
                        mock_assess.return_value = Mock(
                            overall_score=85.0, passed=True, dimension_scores={}
                        )

                        def process_data(data):
                            return len(data)

                        result = engine.protect_function_call(
                            func=process_data,
                            args=(data,),
                            kwargs={},
                            data_param="data",
                            function_name="stress_test",
                            min_score=80.0,
                        )
                        successful_operations += 1
                        return result
            except Exception:
                failed_operations += 1
                return None

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(run_assessment, data) for data in datasets]
            [f.result(timeout=10) for f in futures]

        duration = time.time() - start_time

        # Should handle high concurrency
        assert (
            successful_operations >= num_threads * 0.95
        ), f"Only {successful_operations}/{num_threads} operations succeeded"
        assert duration < 10.0, f"High concurrency test took {duration:.3f}s"

    def test_stress_memory_leak_detection(self, generate_extreme_dataset):
        """Test for memory leaks under repeated operations."""
        import psutil

        process = psutil.Process(os.getpid())

        engine = DataProtectionEngine()
        data = generate_extreme_dataset(10000)

        # Get baseline memory
        gc.collect()

        # Run many iterations
        iterations = 100
        memory_samples = []

        for i in range(iterations):
            with patch.object(engine, "ensure_standard_exists"):
                with patch.object(engine, "assess_data_quality") as mock_assess:
                    mock_assess.return_value = Mock(
                        overall_score=85.0, passed=True, dimension_scores={}
                    )

                    def process_data(data):
                        return data.mean().mean()

                    engine.protect_function_call(
                        func=process_data,
                        args=(data,),
                        kwargs={},
                        data_param="data",
                        function_name=f"iteration_{i}",
                        min_score=80.0,
                    )

            if i % 10 == 0:
                gc.collect()
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)

        # Check for memory leak
        # Memory should not grow significantly over iterations
        memory_growth = (memory_samples[-1] - memory_samples[0]) / memory_samples[0]
        assert (
            memory_growth < 0.2
        ), f"Memory grew by {memory_growth:.1%} indicating potential leak"

    def test_stress_extreme_dataset_size(self, generate_extreme_dataset):
        """Test with extremely large dataset (limited by available memory)."""
        skip_if_ci()  # Skip in CI to avoid memory issues

        # Create the largest dataset we can handle
        try:
            # Try 1 million rows (will be limited by TestDataGenerator if needed)
            huge_data = generate_extreme_dataset(1000000, cols=5)
            engine = DataProtectionEngine()

            with patch.object(engine, "ensure_standard_exists"):
                with patch.object(engine, "assess_data_quality") as mock_assess:
                    mock_assess.return_value = Mock(
                        overall_score=85.0, passed=True, dimension_scores={}
                    )

                    def process_data(data):
                        return len(data)

                    start_time = time.time()
                    result = engine.protect_function_call(
                        func=process_data,
                        args=(huge_data,),
                        kwargs={},
                        data_param="data",
                        function_name="huge_dataset",
                        min_score=80.0,
                    )
                    duration = time.time() - start_time

                    assert result == 1000000
                    assert duration < 5.0, f"Huge dataset took {duration:.3f}s"
        except MemoryError:
            pytest.skip("Not enough memory for extreme dataset test")

    def test_stress_rapid_fire_requests(self):
        """Test system under rapid-fire requests."""
        engine = DataProtectionEngine()
        data = pd.DataFrame({"value": range(100)})

        request_count = 1000
        start_time = time.time()

        with patch.object(engine, "ensure_standard_exists"):
            with patch.object(engine, "assess_data_quality") as mock_assess:
                mock_assess.return_value = Mock(
                    overall_score=85.0, passed=True, dimension_scores={}
                )

                def process_data(data):
                    return len(data)

                for _ in range(request_count):
                    engine.protect_function_call(
                        func=process_data,
                        args=(data,),
                        kwargs={},
                        data_param="data",
                        function_name="rapid_fire",
                        min_score=80.0,
                    )

        duration = time.time() - start_time
        requests_per_second = request_count / duration if duration > 0 else 0

        # Should handle at least 100 requests per second
        assert (
            requests_per_second >= 100
        ), f"Only {requests_per_second:.1f} requests/sec, expected >= 100"

    def test_stress_cache_overflow(self):
        """Test cache behavior when it overflows."""
        engine = DataProtectionEngine()

        # Enable caching
        with patch(
            "adri.config.manager.ConfigManager.get_protection_config"
        ) as mock_config:
            mock_config.return_value = {
                "cache_duration_hours": 1,
                "default_min_score": 80,
                "default_failure_mode": "raise",
            }

            # Fill cache with many entries
            for i in range(10000):
                cache_key = f"key_{i}"
                engine._assessment_cache[cache_key] = (
                    Mock(overall_score=80.0 + (i % 20)),
                    time.time(),
                )

            # Cache should handle overflow gracefully
            assert len(engine._assessment_cache) <= 10000

            # Should still be able to add new entries
            engine._assessment_cache["new_key"] = (
                Mock(overall_score=85.0),
                time.time(),
            )
            assert "new_key" in engine._assessment_cache

    def test_stress_audit_log_massive_writes(self, tmp_path):
        """Test audit logger with massive number of writes."""
        skip_if_ci()  # Skip in CI to avoid long running test

        log_file = tmp_path / "stress_audit.jsonl"
        logger = AuditLogger(str(log_file))

        assessment_result = Mock()
        assessment_result.overall_score = 85.0
        assessment_result.passed = True
        assessment_result.standard_id = "stress_test"
        assessment_result.assessment_date = None
        assessment_result.dimension_scores = {}
        assessment_result.metadata = {}
        assessment_result.rule_execution_log = []
        assessment_result.field_analysis = {}

        # Write log entries (reduced for safety)
        num_entries = int(os.environ.get("ADRI_STRESS_LOG_ENTRIES", "10000"))
        batch_size = 1000

        start_time = time.time()
        for batch in range(0, num_entries, batch_size):
            for i in range(batch_size):
                logger.log_assessment(
                    assessment_result=assessment_result,
                    data_shape=(100, 10),
                    execution_context={"entry": batch + i},
                )

        duration = time.time() - start_time
        entries_per_second = num_entries / duration if duration > 0 else 0

        # Should handle high-volume logging
        assert (
            entries_per_second >= 1000
        ), f"Only {entries_per_second:.0f} log entries/sec"

        # Verify file size is reasonable
        file_size_mb = log_file.stat().st_size / 1024 / 1024
        assert file_size_mb < 1000, f"Log file too large: {file_size_mb:.1f}MB"

    def test_stress_multiprocess_assessment(self, generate_extreme_dataset):
        """Test assessment across multiple processes."""
        datasets = [generate_extreme_dataset(1000) for _ in range(10)]

        def assess_in_process(data_dict):
            """Run in separate process."""
            # Recreate DataFrame from dict (for pickling)
            data = pd.DataFrame(data_dict)
            engine = DataProtectionEngine()

            with patch.object(engine, "ensure_standard_exists"):
                with patch.object(engine, "assess_data_quality") as mock_assess:
                    mock_assess.return_value = Mock(
                        overall_score=85.0, passed=True, dimension_scores={}
                    )

                    def process_data(data):
                        return len(data)

                    return engine.protect_function_call(
                        func=process_data,
                        args=(data,),
                        kwargs={},
                        data_param="data",
                        function_name="multiprocess",
                        min_score=80.0,
                    )

        # Convert DataFrames to dicts for pickling
        data_dicts = [df.to_dict() for df in datasets]

        start_time = time.time()

        with ProcessPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(assess_in_process, data) for data in data_dicts]
            results = [f.result(timeout=10) for f in futures]

        duration = time.time() - start_time

        assert len(results) == 10
        assert all(r == 1000 for r in results)
        assert duration < 5.0, f"Multiprocess test took {duration:.3f}s"

    def test_stress_sparse_data_handling(self, generate_extreme_dataset):
        """Test performance with sparse data (many NaN values)."""
        sparse_data = generate_extreme_dataset(10000, cols=50, sparse=True)
        engine = AssessmentEngine()

        standard = {
            "metadata": {"name": "sparse_test", "version": "1.0.0"},
            "standards": {"fields": {}, "requirements": {"overall_minimum": 80}},
        }

        start_time = time.time()
        result = engine.assess(sparse_data, standard)
        duration = time.time() - start_time

        assert result is not None
        assert duration < 2.0, f"Sparse data assessment took {duration:.3f}s"

    def test_stress_recovery_from_errors(self):
        """Test system recovery from various error conditions."""
        engine = DataProtectionEngine()
        data = pd.DataFrame({"value": range(100)})

        error_count = 0
        success_count = 0

        for i in range(100):
            try:
                with patch.object(engine, "ensure_standard_exists"):
                    with patch.object(engine, "assess_data_quality") as mock_assess:
                        # Randomly inject errors
                        if i % 10 == 0:
                            mock_assess.side_effect = Exception("Simulated error")
                        else:
                            mock_assess.return_value = Mock(
                                overall_score=85.0, passed=True, dimension_scores={}
                            )
                            mock_assess.side_effect = None

                        def process_data(data):
                            return len(data)

                        engine.protect_function_call(
                            func=process_data,
                            args=(data,),
                            kwargs={},
                            data_param="data",
                            function_name="recovery_test",
                            min_score=80.0,
                            on_failure="continue",
                        )
                        success_count += 1
            except Exception:
                error_count += 1

        # System should recover from errors
        assert (
            success_count >= 80
        ), f"Only {success_count} operations succeeded after errors"
        assert error_count <= 20, f"Too many errors: {error_count}"


@pytest.mark.stress
class TestPerformanceUnderLoad:
    """Test performance characteristics under sustained load.

    These tests will be skipped by default. Run with: pytest --stress
    """

    def test_sustained_load_performance(self, generate_extreme_dataset):
        """Test performance under sustained load for extended period."""
        engine = DataProtectionEngine()
        data = generate_extreme_dataset(5000)

        # Run for 10 seconds
        test_duration = 10
        start_time = time.time()
        operation_count = 0
        response_times = []

        with patch.object(engine, "ensure_standard_exists"):
            with patch.object(engine, "assess_data_quality") as mock_assess:
                mock_assess.return_value = Mock(
                    overall_score=85.0, passed=True, dimension_scores={}
                )

                def process_data(data):
                    return len(data)

                while time.time() - start_time < test_duration:
                    op_start = time.time()

                    engine.protect_function_call(
                        func=process_data,
                        args=(data,),
                        kwargs={},
                        data_param="data",
                        function_name="sustained_load",
                        min_score=80.0,
                    )

                    response_times.append(time.time() - op_start)
                    operation_count += 1

        # Calculate performance metrics
        avg_response_time = sum(response_times) / len(response_times)
        p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
        p99_response_time = sorted(response_times)[int(len(response_times) * 0.99)]

        # Performance should remain stable
        assert (
            avg_response_time < 0.1
        ), f"Average response time {avg_response_time:.3f}s too high"
        assert (
            p95_response_time < 0.2
        ), f"P95 response time {p95_response_time:.3f}s too high"
        assert (
            p99_response_time < 0.5
        ), f"P99 response time {p99_response_time:.3f}s too high"
        assert (
            operation_count >= 100
        ), f"Only {operation_count} operations in {test_duration}s"

    def test_performance_degradation_over_time(self, tmp_path):
        """Test for performance degradation over time."""
        engine = DataProtectionEngine()
        data = pd.DataFrame({"value": range(1000)})

        # Track performance over batches
        batch_size = 100
        num_batches = 10
        batch_times = []

        with patch.object(engine, "ensure_standard_exists"):
            with patch.object(engine, "assess_data_quality") as mock_assess:
                mock_assess.return_value = Mock(
                    overall_score=85.0, passed=True, dimension_scores={}
                )

                def process_data(data):
                    return len(data)

                for batch in range(num_batches):
                    batch_start = time.time()

                    for _ in range(batch_size):
                        engine.protect_function_call(
                            func=process_data,
                            args=(data,),
                            kwargs={},
                            data_param="data",
                            function_name="degradation_test",
                            min_score=80.0,
                        )

                    batch_times.append(time.time() - batch_start)

        # Check for performance degradation
        # Later batches should not be significantly slower than earlier ones
        first_half_avg = sum(batch_times[:5]) / 5
        second_half_avg = sum(batch_times[5:]) / 5

        degradation = (second_half_avg - first_half_avg) / first_half_avg
        assert degradation < 0.2, f"Performance degraded by {degradation:.1%} over time"
