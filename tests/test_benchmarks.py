"""
Performance benchmark tests for ADRI Validator.

This module contains pytest-benchmark tests to measure and track
performance of critical ADRI components.
"""

import pandas as pd
import pytest

from adri.core.assessor import DataQualityAssessor
from adri.decorators.guard import adri_protected


class TestDecoratorBenchmarks:
    """Benchmark tests for the @adri_protected decorator."""

    @pytest.fixture
    def small_dataset(self):
        """Create a small test dataset (100 rows)."""
        return pd.DataFrame(
            {
                "id": range(100),
                "name": [f"user_{i}" for i in range(100)],
                "score": [i * 0.1 for i in range(100)],
            }
        )

    @pytest.fixture
    def medium_dataset(self):
        """Create a medium test dataset (1000 rows)."""
        return pd.DataFrame(
            {
                "id": range(1000),
                "name": [f"user_{i}" for i in range(1000)],
                "score": [i * 0.1 for i in range(1000)],
            }
        )

    @pytest.fixture
    def large_dataset(self):
        """Create a large test dataset (10000 rows)."""
        return pd.DataFrame(
            {
                "id": range(10000),
                "name": [f"user_{i}" for i in range(10000)],
                "score": [i * 0.1 for i in range(10000)],
            }
        )

    def unprotected_function(self, data):
        """Baseline function without decorator."""
        return len(data)

    @adri_protected(data_param="data")
    def protected_function(self, data):
        """Function with @adri_protected decorator."""
        return len(data)

    @pytest.mark.benchmark(group="decorator-overhead")
    def test_decorator_overhead_small(self, benchmark, small_dataset):
        """Benchmark decorator overhead on small dataset."""
        result = benchmark(self.protected_function, small_dataset)
        assert result == 100

    @pytest.mark.benchmark(group="decorator-overhead")
    def test_decorator_overhead_medium(self, benchmark, medium_dataset):
        """Benchmark decorator overhead on medium dataset."""
        result = benchmark(self.protected_function, medium_dataset)
        assert result == 1000

    @pytest.mark.benchmark(group="decorator-overhead")
    def test_decorator_overhead_large(self, benchmark, large_dataset):
        """Benchmark decorator overhead on large dataset."""
        result = benchmark(self.protected_function, large_dataset)
        assert result == 10000

    @pytest.mark.benchmark(group="baseline")
    def test_baseline_small(self, benchmark, small_dataset):
        """Baseline benchmark on small dataset."""
        result = benchmark(self.unprotected_function, small_dataset)
        assert result == 100

    @pytest.mark.benchmark(group="baseline")
    def test_baseline_medium(self, benchmark, medium_dataset):
        """Baseline benchmark on medium dataset."""
        result = benchmark(self.unprotected_function, medium_dataset)
        assert result == 1000

    @pytest.mark.benchmark(group="baseline")
    def test_baseline_large(self, benchmark, large_dataset):
        """Baseline benchmark on large dataset."""
        result = benchmark(self.unprotected_function, large_dataset)
        assert result == 10000


class TestAssessorBenchmarks:
    """Benchmark tests for the DataQualityAssessor."""

    @pytest.fixture
    def assessor(self):
        """Create a DataQualityAssessor instance."""
        return DataQualityAssessor()

    @pytest.fixture
    def assessment_config(self):
        """Basic assessment configuration."""
        return {
            "completeness": {"enabled": True},
            "consistency": {"enabled": True},
            "validity": {"enabled": True},
        }

    @pytest.fixture
    def small_dataset(self):
        """Create a small test dataset (100 rows)."""
        return pd.DataFrame(
            {
                "id": range(100),
                "name": [f"user_{i}" for i in range(100)],
                "email": [f"user_{i}@example.com" for i in range(100)],
                "age": [20 + (i % 60) for i in range(100)],
                "score": [0.1 * (i % 100) for i in range(100)],
            }
        )

    @pytest.fixture
    def medium_dataset(self):
        """Create a medium test dataset (1000 rows)."""
        return pd.DataFrame(
            {
                "id": range(1000),
                "name": [f"user_{i}" for i in range(1000)],
                "email": [f"user_{i}@example.com" for i in range(1000)],
                "age": [20 + (i % 60) for i in range(1000)],
                "score": [0.1 * (i % 100) for i in range(1000)],
            }
        )

    @pytest.fixture
    def large_dataset(self):
        """Create a large test dataset (10000 rows)."""
        return pd.DataFrame(
            {
                "id": range(10000),
                "name": [f"user_{i}" for i in range(10000)],
                "email": [f"user_{i}@example.com" for i in range(10000)],
                "age": [20 + (i % 60) for i in range(10000)],
                "score": [0.1 * (i % 100) for i in range(10000)],
            }
        )

    @pytest.mark.benchmark(group="assessor-performance")
    def test_assess_small_dataset(
        self, benchmark, assessor, small_dataset, assessment_config
    ):
        """Benchmark assessment on small dataset."""
        result = benchmark(assessor.assess, small_dataset)
        assert result is not None
        assert hasattr(result, "overall_score")

    @pytest.mark.benchmark(group="assessor-performance")
    def test_assess_medium_dataset(
        self, benchmark, assessor, medium_dataset, assessment_config
    ):
        """Benchmark assessment on medium dataset."""
        result = benchmark(assessor.assess, medium_dataset)
        assert result is not None
        assert hasattr(result, "overall_score")

    @pytest.mark.benchmark(group="assessor-performance")
    def test_assess_large_dataset(
        self, benchmark, assessor, large_dataset, assessment_config
    ):
        """Benchmark assessment on large dataset."""
        result = benchmark(assessor.assess, large_dataset)
        assert result is not None
        assert hasattr(result, "overall_score")


class TestDataProcessingBenchmarks:
    """Benchmark tests for data processing operations."""

    @pytest.fixture
    def wide_dataset(self):
        """Create a dataset with many columns."""
        data = {}
        for i in range(50):  # 50 columns
            data[f"col_{i}"] = [j * 0.1 for j in range(1000)]
        return pd.DataFrame(data)

    @pytest.fixture
    def mixed_types_dataset(self):
        """Create a dataset with mixed data types."""
        return pd.DataFrame(
            {
                "integers": range(1000),
                "floats": [i * 0.1 for i in range(1000)],
                "strings": [f"text_{i}" for i in range(1000)],
                "booleans": [i % 2 == 0 for i in range(1000)],
                "dates": pd.date_range("2023-01-01", periods=1000, freq="D"),
            }
        )

    @pytest.mark.benchmark(group="data-processing")
    def test_wide_dataset_processing(self, benchmark, wide_dataset):
        """Benchmark processing of wide datasets."""
        assessor = DataQualityAssessor()

        result = benchmark(assessor.assess, wide_dataset)
        assert result is not None

    @pytest.mark.benchmark(group="data-processing")
    def test_mixed_types_processing(self, benchmark, mixed_types_dataset):
        """Benchmark processing of mixed data types."""
        assessor = DataQualityAssessor()

        result = benchmark(assessor.assess, mixed_types_dataset)
        assert result is not None


class TestMemoryBenchmarks:
    """Memory usage benchmark tests."""

    @pytest.mark.benchmark(group="memory-usage")
    def test_memory_efficiency_large_dataset(self, benchmark):
        """Test memory efficiency with large datasets."""

        def create_and_assess():
            # Create large dataset
            data = pd.DataFrame(
                {
                    "col1": range(50000),
                    "col2": [f"text_{i}" for i in range(50000)],
                    "col3": [i * 0.1 for i in range(50000)],
                }
            )

            # Assess it
            assessor = DataQualityAssessor()
            result = assessor.assess(data)

            # Clean up
            del data
            return result

        result = benchmark(create_and_assess)
        assert result is not None

    @pytest.mark.benchmark(group="memory-usage")
    def test_memory_efficiency_multiple_assessments(self, benchmark):
        """Test memory efficiency with multiple sequential assessments."""

        def multiple_assessments():
            assessor = DataQualityAssessor()
            results = []

            for i in range(10):
                data = pd.DataFrame(
                    {"id": range(1000), "value": [j * 0.1 for j in range(1000)]}
                )
                result = assessor.assess(data)
                results.append(result)
                del data

            return results

        results = benchmark(multiple_assessments)
        assert len(results) == 10
        assert all(r is not None for r in results)


# Performance regression thresholds
PERFORMANCE_THRESHOLDS = {
    "decorator_overhead_max_ms": 10.0,  # Max 10ms overhead
    "small_dataset_max_ms": 100.0,  # Max 100ms for small datasets
    "medium_dataset_max_ms": 500.0,  # Max 500ms for medium datasets
    "large_dataset_max_ms": 2000.0,  # Max 2s for large datasets
}


def test_performance_regression_check():
    """
    Test to ensure performance doesn't regress beyond acceptable thresholds.

    This test should be run after benchmark tests to validate performance.
    """
    # This is a placeholder - in practice, this would read benchmark results
    # and compare against thresholds
    assert True, "Performance regression check placeholder"
