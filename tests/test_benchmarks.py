"""Performance benchmarks for ADRI validator."""

import numpy as np
import pandas as pd
import pytest

from adri.analysis.data_profiler import DataProfiler
from adri.analysis.standard_generator import StandardGenerator
from adri.core.assessor import AssessmentEngine


@pytest.mark.performance
class TestPerformanceBenchmarks:
    """Performance benchmark tests for core ADRI functionality."""

    @pytest.fixture
    def large_dataset(self):
        """Generate a large dataset for benchmarking."""
        np.random.seed(42)
        size = 10000
        return pd.DataFrame(
            {
                "id": range(size),
                "name": [f"Customer_{i}" for i in range(size)],
                "age": np.random.randint(18, 80, size),
                "email": [f"user{i}@example.com" for i in range(size)],
                "score": np.random.uniform(0, 100, size),
                "category": np.random.choice(["A", "B", "C", "D"], size),
                "date": pd.date_range("2020-01-01", periods=size, freq="h"),
                "is_active": np.random.choice([True, False], size),
                "value": np.random.exponential(100, size),
                "description": [f"Description text {i}" * 10 for i in range(size)],
            }
        )

    @pytest.fixture
    def medium_dataset(self):
        """Generate a medium dataset for benchmarking."""
        np.random.seed(42)
        size = 1000
        return pd.DataFrame(
            {
                "id": range(size),
                "name": [f"Item_{i}" for i in range(size)],
                "price": np.random.uniform(10, 1000, size),
                "quantity": np.random.randint(1, 100, size),
                "category": np.random.choice(
                    ["Electronics", "Clothing", "Food", "Books"], size
                ),
            }
        )

    @pytest.fixture
    def assessment_engine(self):
        """Create an assessment engine instance."""
        return AssessmentEngine()

    @pytest.fixture
    def data_profiler(self):
        """Create a data profiler instance."""
        return DataProfiler()

    @pytest.fixture
    def standard_generator(self):
        """Create a standard generator instance."""
        return StandardGenerator()

    @pytest.mark.timeout(60)
    def test_benchmark_data_loading(self, benchmark, large_dataset, tmp_path):
        """Benchmark data loading performance."""
        # Save dataset to CSV
        csv_path = tmp_path / "large_dataset.csv"
        large_dataset.to_csv(csv_path, index=False)

        # Benchmark CSV loading using pandas
        result = benchmark(pd.read_csv, str(csv_path))
        assert result is not None
        assert len(result) == len(large_dataset)

    @pytest.mark.timeout(60)
    def test_benchmark_data_profiling(self, benchmark, data_profiler, large_dataset):
        """Benchmark data profiling performance."""
        result = benchmark(data_profiler.profile_data, large_dataset)
        assert result is not None
        assert "summary" in result
        assert "fields" in result

    @pytest.mark.timeout(60)
    def test_benchmark_standard_generation(
        self, benchmark, standard_generator, data_profiler, medium_dataset
    ):
        """Benchmark standard generation performance."""
        # First profile the data
        data_profile = data_profiler.profile_data(medium_dataset)

        # Create generation config
        generation_config = {
            "default_thresholds": {
                "completeness_min": 85,
                "validity_min": 90,
                "consistency_min": 80,
            }
        }

        # Benchmark standard generation
        result = benchmark(
            standard_generator.generate_standard,
            data_profile,
            "test_standard",
            generation_config,
        )
        assert result is not None
        assert "metadata" in result
        assert "standards" in result

    @pytest.mark.timeout(60)
    def test_benchmark_assessment_simple(
        self, benchmark, assessment_engine, medium_dataset
    ):
        """Benchmark simple assessment performance."""
        # Create a simple standard
        standard = {
            "metadata": {"name": "test_standard", "version": "1.0.0"},
            "standards": {"fields": {}, "requirements": {"overall_minimum": 80}},
        }

        result = benchmark(assessment_engine.assess, medium_dataset, standard)
        assert result is not None
        assert hasattr(result, "overall_score")

    @pytest.mark.timeout(60)
    def test_benchmark_assessment_complex(
        self, benchmark, assessment_engine, large_dataset
    ):
        """Benchmark complex assessment with field requirements."""
        # Create a complex standard with field requirements
        standard = {
            "metadata": {"name": "complex_standard", "version": "1.0.0"},
            "standards": {
                "fields": {
                    "email": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                        "required": True,
                    },
                    "age": {
                        "type": "integer",
                        "range": {"min": 18, "max": 120},
                        "required": True,
                    },
                    "score": {
                        "type": "float",
                        "range": {"min": 0, "max": 100},
                        "required": True,
                    },
                },
                "requirements": {
                    "overall_minimum": 85,
                    "dimension_minimums": {
                        "validity": 90,
                        "completeness": 95,
                        "consistency": 85,
                    },
                },
            },
        }

        result = benchmark(assessment_engine.assess, large_dataset, standard)
        assert result is not None
        assert hasattr(result, "overall_score")
        assert hasattr(result, "dimension_scores")

    @pytest.mark.timeout(60)
    def test_benchmark_batch_assessment(self, benchmark, assessment_engine):
        """Benchmark batch assessment of multiple datasets."""
        # Create multiple small datasets
        datasets = []
        for i in range(10):
            df = pd.DataFrame(
                {
                    "id": range(100),
                    "value": np.random.uniform(0, 100, 100),
                    "category": np.random.choice(["A", "B", "C"], 100),
                }
            )
            datasets.append(df)

        standard = {
            "metadata": {"name": "batch_standard", "version": "1.0.0"},
            "standards": {"fields": {}, "requirements": {"overall_minimum": 80}},
        }

        def assess_batch():
            results = []
            for df in datasets:
                result = assessment_engine.assess(df, standard)
                results.append(result)
            return results

        results = benchmark(assess_batch)
        assert len(results) == 10
        assert all(hasattr(r, "overall_score") for r in results)

    @pytest.mark.timeout(60)
    def test_benchmark_memory_usage(self, benchmark, assessment_engine, large_dataset):
        """Benchmark memory usage during assessment."""
        standard = {
            "metadata": {"name": "memory_test", "version": "1.0.0"},
            "standards": {"fields": {}, "requirements": {"overall_minimum": 80}},
        }

        # This will also track memory usage if pytest-benchmark is configured for it
        result = benchmark(assessment_engine.assess, large_dataset, standard)
        assert result is not None

    @pytest.mark.timeout(60)
    @pytest.mark.parametrize("size", [100, 1000, 5000])
    def test_benchmark_scaling(self, benchmark, assessment_engine, size):
        """Benchmark assessment performance with different dataset sizes."""
        # Generate dataset of specified size
        df = pd.DataFrame(
            {
                "id": range(size),
                "value": np.random.uniform(0, 100, size),
                "category": np.random.choice(["A", "B", "C"], size),
            }
        )

        standard = {
            "metadata": {"name": "scaling_test", "version": "1.0.0"},
            "standards": {"fields": {}, "requirements": {"overall_minimum": 80}},
        }

        result = benchmark(assessment_engine.assess, df, standard)
        assert result is not None
        assert hasattr(result, "overall_score")
