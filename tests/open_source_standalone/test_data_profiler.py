"""
Standalone Tests for ADRI Data Profiler.

This is a self-contained test file for the open source ADRI package.
It provides comprehensive data profiler testing without enterprise dependencies.

Tests pattern analysis, inference accuracy, edge case handling, and performance.
No enterprise imports - uses only src/adri/* and standard pytest fixtures.
"""

import os
import sys
import tempfile
import time
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
import pandas as pd

# Modern imports only - no legacy patterns
from src.adri.analysis.data_profiler import DataProfiler, ProfileResult, FieldProfile, profile_dataframe
from src.adri.core.exceptions import DataValidationError, ConfigurationError


class TestDataProfilerStandalone:
    """Standalone test suite for ADRI Data Profiler."""

    def setup_method(self):
        """Setup for each test method."""
        # Test data with various quality levels
        self.high_quality_data = self._create_high_quality_data()
        self.medium_quality_data = self._create_medium_quality_data()
        self.low_quality_data = self._create_low_quality_data()

        # Initialize profiler
        self.profiler = DataProfiler()

    def _create_high_quality_data(self, rows: int = 100) -> pd.DataFrame:
        """Create high-quality test data."""
        np.random.seed(42)
        return pd.DataFrame({
            "customer_id": range(1, rows + 1),
            "name": [f"Customer_{i}" for i in range(rows)],
            "email": [f"customer{i}@company.com" for i in range(rows)],
            "age": [25 + (i % 40) for i in range(rows)],
            "salary": [50000 + (i * 500) for i in range(rows)],
            "registration_date": pd.date_range("2020-01-01", periods=rows, freq="D"),
            "status": ["active"] * (rows - 10) + ["inactive"] * 10
        })

    def _create_medium_quality_data(self, rows: int = 100) -> pd.DataFrame:
        """Create medium-quality test data with some issues."""
        data = pd.DataFrame({
            "customer_id": range(1, rows + 1),
            "name": [f"Customer_{i}" if i % 5 != 0 else None for i in range(rows)],
            "email": [f"customer{i}@company.com" if i % 4 != 0 else "invalid" for i in range(rows)],
            "age": [25 + (i % 40) if i % 6 != 0 else -1 for i in range(rows)],
            "salary": [50000 + (i * 500) if i % 7 != 0 else None for i in range(rows)],
            "registration_date": pd.date_range("2020-01-01", periods=rows, freq="D"),
            "status": ["active"] * 70 + ["inactive"] * 20 + [None] * 10
        })
        return data

    def _create_low_quality_data(self, rows: int = 100) -> pd.DataFrame:
        """Create low-quality test data with many issues."""
        pattern = [1, None, 3, 4, 5]
        name_pattern = ["Alice", "", None, "Diana", "Eve"]
        email_pattern = ["invalid-email", "bob@example.com", "charlie", "", "eve@example.com"]
        age_pattern = [-5, 30, 200, None, 32]
        salary_pattern = [None, 50000, -1000, 60000, None]
        status_pattern = [None, "active", "invalid", "", "inactive"]

        return pd.DataFrame({
            "customer_id": (pattern * (rows // 5 + 1))[:rows],
            "name": (name_pattern * (rows // 5 + 1))[:rows],
            "email": (email_pattern * (rows // 5 + 1))[:rows],
            "age": (age_pattern * (rows // 5 + 1))[:rows],
            "salary": (salary_pattern * (rows // 5 + 1))[:rows],
            "registration_date": [None] * rows,
            "status": (status_pattern * (rows // 5 + 1))[:rows]
        })

    @pytest.mark.unit
    @pytest.mark.data_processing
    def test_data_profiler_initialization(self):
        """Test data profiler initialization and configuration."""
        # Test default initialization
        profiler = DataProfiler()
        assert profiler is not None

        # Test with custom configuration
        config = {
            "sample_size": 1000,
            "enable_statistical_analysis": True,
            "enable_pattern_detection": True,
            "null_threshold": 0.05
        }
        configured_profiler = DataProfiler(config=config)
        assert configured_profiler is not None

    @pytest.mark.unit
    @pytest.mark.data_processing
    def test_basic_data_profiling(self):
        """Test basic data profiling functionality."""
        # Profile high quality data
        profile_result = self.profiler.profile_data(self.high_quality_data)

        # Verify profile result structure
        assert isinstance(profile_result, ProfileResult)
        assert hasattr(profile_result, 'field_profiles')
        assert hasattr(profile_result, 'summary_statistics')
        assert hasattr(profile_result, 'data_quality_score')

        # Verify field profiles exist for all columns
        expected_columns = ['customer_id', 'name', 'email', 'age', 'salary', 'registration_date', 'status']
        for column in expected_columns:
            assert column in profile_result.field_profiles

        # Verify data quality score is reasonable for high quality data
        assert 70 <= profile_result.data_quality_score <= 100

    @pytest.mark.unit
    @pytest.mark.data_processing
    def test_field_profile_analysis(self):
        """Test detailed field-level profiling."""
        profile_result = self.profiler.profile_data(self.high_quality_data)

        # Test string field profiling (name column)
        name_profile = profile_result.field_profiles['name']
        assert isinstance(name_profile, FieldProfile)
        assert name_profile.field_type == 'string'
        assert hasattr(name_profile, 'null_count')
        assert hasattr(name_profile, 'unique_count')
        assert hasattr(name_profile, 'min_length')
        assert hasattr(name_profile, 'max_length')

        # Verify reasonable values for high quality data
        assert name_profile.null_count <= 10  # Should have few nulls
        assert name_profile.unique_count > 0

        # Test numeric field profiling (age column)
        age_profile = profile_result.field_profiles['age']
        assert age_profile.field_type in ['integer', 'numeric']
        assert hasattr(age_profile, 'min_value')
        assert hasattr(age_profile, 'max_value')
        assert hasattr(age_profile, 'mean_value')
        assert hasattr(age_profile, 'std_dev')

        # Verify reasonable age values
        assert age_profile.min_value >= -50  # Allow for edge cases
        assert age_profile.max_value >= 18  # Should have normal adult ages

        # Test email field profiling (pattern detection)
        email_profile = profile_result.field_profiles['email']
        assert email_profile.field_type == 'string'
        if hasattr(email_profile, 'pattern_matches'):
            assert email_profile.pattern_matches > 0

    @pytest.mark.unit
    @pytest.mark.data_processing
    def test_data_quality_assessment(self):
        """Test data quality assessment across different quality levels."""
        # Profile different quality levels
        high_profile = self.profiler.profile_data(self.high_quality_data)
        medium_profile = self.profiler.profile_data(self.medium_quality_data)
        low_profile = self.profiler.profile_data(self.low_quality_data)

        # Quality scores should reflect data quality
        assert high_profile.data_quality_score > medium_profile.data_quality_score
        assert medium_profile.data_quality_score > low_profile.data_quality_score

        # High quality should score well
        assert high_profile.data_quality_score >= 80

        # Low quality should have lower score
        assert low_profile.data_quality_score <= 91

        # Verify meaningful score differences
        score_diff = high_profile.data_quality_score - low_profile.data_quality_score
        assert score_diff >= 5, f"Score difference too small: {score_diff}"

        # Check null counts reflect quality
        high_name_nulls = high_profile.field_profiles['name'].null_count
        low_name_nulls = low_profile.field_profiles['name'].null_count
        assert high_name_nulls <= low_name_nulls

    @pytest.mark.unit
    @pytest.mark.data_processing
    def test_statistical_analysis(self):
        """Test statistical analysis capabilities."""
        profile_result = self.profiler.profile_data(self.high_quality_data)

        # Test numeric field statistics
        salary_profile = profile_result.field_profiles['salary']

        # Verify statistical measures are calculated
        assert hasattr(salary_profile, 'mean_value')
        assert hasattr(salary_profile, 'median_value')
        assert hasattr(salary_profile, 'std_dev')
        assert hasattr(salary_profile, 'quartiles')

        # Verify statistical validity
        assert salary_profile.mean_value > 0
        assert salary_profile.std_dev >= 0

        if hasattr(salary_profile, 'quartiles'):
            q1, q2, q3 = salary_profile.quartiles[:3]
            assert q1 <= q2 <= q3  # Quartiles should be ordered

        # Test correlation analysis if available
        if hasattr(profile_result, 'correlations'):
            correlations = profile_result.correlations
            assert isinstance(correlations, dict)
            for field_pair, corr in correlations.items():
                assert -1 <= corr <= 1

    @pytest.mark.unit
    @pytest.mark.data_processing
    def test_pattern_detection(self):
        """Test pattern detection capabilities."""
        # Create data with specific patterns
        pattern_data = pd.DataFrame({
            'email': ['user1@example.com', 'user2@test.org', 'invalid-email', 'user3@company.net'],
            'phone': ['555-1234', '(555) 567-8901', '555.234.5678', 'invalid-phone'],
            'date': ['2023-01-01', '2023-12-31', 'invalid-date', '2023-06-15'],
            'url': ['https://example.com', 'http://test.org', 'invalid-url', 'https://company.net']
        })

        profile_result = self.profiler.profile_data(pattern_data)

        # Test email pattern detection
        email_profile = profile_result.field_profiles['email']
        if hasattr(email_profile, 'detected_patterns'):
            patterns = email_profile.detected_patterns
            assert any('email' in pattern.lower() for pattern in patterns)

        # Test phone pattern detection
        phone_profile = profile_result.field_profiles['phone']
        if hasattr(phone_profile, 'detected_patterns'):
            patterns = phone_profile.detected_patterns
            assert any('phone' in pattern.lower() for pattern in patterns)

        # Test date pattern detection
        date_profile = profile_result.field_profiles['date']
        if hasattr(date_profile, 'detected_patterns'):
            patterns = date_profile.detected_patterns
            assert any('date' in pattern.lower() for pattern in patterns)

    @pytest.mark.error_handling
    @pytest.mark.data_processing
    def test_invalid_data_handling(self):
        """Test handling of invalid or problematic data."""
        # Test with None input
        with pytest.raises((DataValidationError, TypeError)):
            self.profiler.profile_data(None)

        # Test with empty DataFrame
        empty_df = pd.DataFrame()
        result = self.profiler.profile_data(empty_df)
        assert result.data_quality_score >= 0  # Should handle gracefully

        # Test with single row DataFrame
        single_row = self.high_quality_data.iloc[:1]
        result = self.profiler.profile_data(single_row)
        assert result is not None

        # Test with DataFrame containing only nulls
        null_df = pd.DataFrame({
            'null_column': [None, None, None, None],
            'another_null': [np.nan, np.nan, np.nan, np.nan]
        })
        result = self.profiler.profile_data(null_df)
        assert result is not None
        assert result.data_quality_score <= 50  # Should reflect poor quality

    @pytest.mark.error_handling
    @pytest.mark.data_processing
    def test_extreme_data_values(self):
        """Test handling of extreme or unusual data values."""
        # Create data with extreme values
        extreme_data = pd.DataFrame({
            'huge_numbers': [1e15, 1e20, -1e15, 0],
            'tiny_numbers': [1e-15, 1e-20, -1e-15, 0],
            'long_strings': ['x' * 10000, 'y' * 5000, 'z', ''],
            'special_chars': ['', '🚀🔥💯', '\n\t\r', '\\x00\\x01\\x02'],
            'mixed_types': [1, 'string', 3.14, None]
        })

        # Should handle extreme values without crashing
        result = self.profiler.profile_data(extreme_data)
        assert result is not None

        # Verify profiles were created for all columns
        for column in extreme_data.columns:
            assert column in result.field_profiles

        # Check handling of huge numbers
        huge_profile = result.field_profiles['huge_numbers']
        assert huge_profile.field_type in ['numeric', 'float']

        # Check handling of long strings
        long_profile = result.field_profiles['long_strings']
        assert long_profile.field_type == 'string'
        assert long_profile.max_length >= 5000

    @pytest.mark.integration
    @pytest.mark.data_processing
    def test_standard_generator_integration(self):
        """Test integration with standard generator."""
        # Profile the data
        profile_result = self.profiler.profile_data(self.high_quality_data)

        # Mock standard generator integration
        with patch('src.adri.analysis.contract_generator.ContractGenerator') as mock_generator:
            mock_instance = Mock()
            mock_generator.return_value = mock_instance

            # Simulate using profile for standard generation
            mock_instance.generate_from_profile.return_value = {
                'contracts': {
                    'id': 'generated_standard',
                    'name': 'Generated from Profile'
                }
            }

            # Test integration
            generator = mock_generator()
            standard = generator.generate_from_profile(profile_result)

            mock_generator.assert_called()
            mock_instance.generate_from_profile.assert_called_with(profile_result)
            assert standard['contracts']['id'] == 'generated_standard'

    @pytest.mark.integration
    @pytest.mark.data_processing
    def test_type_inference_integration(self):
        """Test integration with type inference system."""
        profile_result = self.profiler.profile_data(self.high_quality_data)

        # Mock type inference integration
        with patch('src.adri.analysis.type_inference.TypeInference') as mock_inference:
            mock_instance = Mock()
            mock_inference.return_value = mock_instance

            # Simulate type inference using profile data
            mock_instance.infer_types.return_value = {
                'customer_id': 'integer',
                'name': 'string',
                'email': 'email',
                'age': 'integer',
                'salary': 'currency'
            }

            # Test integration
            type_inference = mock_inference()
            inferred_types = type_inference.infer_types(profile_result)

            mock_inference.assert_called()
            mock_instance.infer_types.assert_called_with(profile_result)
            assert 'customer_id' in inferred_types
            assert inferred_types['email'] == 'email'

    @pytest.mark.performance
    @pytest.mark.data_processing
    def test_large_dataset_profiling_performance(self, performance_tester):
        """Test performance with large datasets."""
        # Test with progressively larger datasets
        dataset_sizes = [1000, 5000, 10000]
        performance_results = []

        for size in dataset_sizes:
            large_dataset = performance_tester.create_large_dataset(size)

            start_time = time.time()
            profile_result = self.profiler.profile_data(large_dataset)
            duration = time.time() - start_time

            performance_results.append({
                'size': size,
                'duration': duration,
                'quality_score': profile_result.data_quality_score
            })

            # Verify profiling completed successfully
            assert profile_result is not None
            assert profile_result.data_quality_score >= 0

        # Log performance scaling for monitoring
        if len(performance_results) >= 2:
            ratio_10x = performance_results[-1]['duration'] / performance_results[0]['duration']
            size_ratio = performance_results[-1]['size'] / performance_results[0]['size']
            print(f"Performance scaling: {ratio_10x:.2f}x for {size_ratio}x data increase")

        # Basic performance check - should complete in reasonable time
        for result in performance_results:
            assert result['duration'] < 60, f"Profiling {result['size']} rows took too long: {result['duration']:.2f}s"

    @pytest.mark.performance
    @pytest.mark.data_processing
    def test_wide_dataset_profiling_performance(self, performance_tester):
        """Test performance with wide datasets (many columns)."""
        # Create wide datasets with many columns
        wide_dataset = performance_tester.create_wide_dataset(cols=200, rows=1000)

        start_time = time.time()
        profile_result = self.profiler.profile_data(wide_dataset)
        duration = time.time() - start_time

        # Basic performance check
        assert duration < 120, f"Wide dataset profiling took too long: {duration:.2f}s"

        # Verify all columns were profiled
        assert len(profile_result.field_profiles) == 200

        # Verify each column has a valid profile
        for field_name, field_profile in profile_result.field_profiles.items():
            assert isinstance(field_profile, FieldProfile)
            assert field_profile.field_type in ['string', 'integer', 'numeric', 'date']

    @pytest.mark.performance
    @pytest.mark.data_processing
    def test_concurrent_profiling(self, performance_tester):
        """Test concurrent profiling of multiple datasets."""
        import concurrent.futures
        import threading

        def profile_dataset(dataset_id):
            """Profile a dataset with thread identification."""
            # Create unique dataset for each thread
            data = performance_tester.create_large_dataset(500)

            result = self.profiler.profile_data(data)
            return {
                'dataset_id': dataset_id,
                'thread_id': threading.get_ident(),
                'quality_score': result.data_quality_score,
                'field_count': len(result.field_profiles),
                'timestamp': time.time()
            }

        # Run concurrent profiling
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(profile_dataset, i)
                for i in range(6)
            ]

            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        # Verify concurrent execution completed
        assert len(results) == 6

        # Verify different threads were used
        thread_ids = set(r['thread_id'] for r in results)
        assert len(thread_ids) > 1, "Expected multiple threads"

        # Verify all profiling completed successfully
        for result in results:
            assert result['quality_score'] >= 0
            assert result['field_count'] > 0

    @pytest.mark.unit
    @pytest.mark.data_processing
    def test_data_distribution_analysis(self):
        """Test analysis of data distributions."""
        np.random.seed(42)

        # Create data with known distributions
        distribution_data = pd.DataFrame({
            'normal_dist': np.random.normal(50, 10, 1000),
            'uniform_dist': np.random.uniform(0, 100, 1000),
            'skewed_dist': np.random.exponential(2, 1000),
            'categorical': np.random.choice(['A', 'B', 'C'], 1000, p=[0.5, 0.3, 0.2])
        })

        profile_result = self.profiler.profile_data(distribution_data)

        # Test numeric distribution analysis
        normal_profile = profile_result.field_profiles['normal_dist']
        assert normal_profile.field_type in ['numeric', 'float']

        # Should detect distribution characteristics
        if hasattr(normal_profile, 'skewness'):
            # Normal distribution should have low skewness
            assert abs(normal_profile.skewness) < 1.0

        if hasattr(normal_profile, 'kurtosis'):
            # Normal distribution should have kurtosis close to 3
            assert 2.0 < normal_profile.kurtosis < 4.0

        # Test categorical distribution analysis
        categorical_profile = profile_result.field_profiles['categorical']
        assert categorical_profile.field_type == 'string'

        if hasattr(categorical_profile, 'value_counts'):
            value_counts = categorical_profile.value_counts
            assert 'A' in value_counts
            assert 'B' in value_counts
            assert 'C' in value_counts
            # 'A' should be most frequent (p=0.5)
            assert value_counts['A'] > value_counts['B']
            assert value_counts['A'] > value_counts['C']

    @pytest.mark.unit
    @pytest.mark.data_processing
    def test_missing_value_analysis(self):
        """Test comprehensive missing value analysis."""
        # Create data with various missing patterns
        missing_data = pd.DataFrame({
            'no_missing': range(100),
            'few_missing': [i if i % 20 != 0 else None for i in range(100)],  # 5% missing
            'many_missing': [i if i % 4 != 0 else None for i in range(100)],  # 25% missing
            'mostly_missing': [i if i % 10 == 0 else None for i in range(100)],  # 90% missing
            'all_missing': [None] * 100
        })

        profile_result = self.profiler.profile_data(missing_data)

        # Test missing value patterns
        no_missing_profile = profile_result.field_profiles['no_missing']
        assert no_missing_profile.null_count == 0

        few_missing_profile = profile_result.field_profiles['few_missing']
        assert 4 <= few_missing_profile.null_count <= 6  # Around 5%

        many_missing_profile = profile_result.field_profiles['many_missing']
        assert 23 <= many_missing_profile.null_count <= 27  # Around 25%

        mostly_missing_profile = profile_result.field_profiles['mostly_missing']
        assert 88 <= mostly_missing_profile.null_count <= 92  # Around 90%

        all_missing_profile = profile_result.field_profiles['all_missing']
        assert all_missing_profile.null_count == 100

        # Overall data quality should reflect missing data
        assert profile_result.data_quality_score < 80  # Should be reduced due to missing data

    @pytest.mark.unit
    @pytest.mark.data_processing
    def test_outlier_detection(self):
        """Test outlier detection capabilities."""
        # Create data with outliers
        outlier_data = pd.DataFrame({
            'normal_values': list(range(1, 96)) + [1000, 2000, -500, -1000, 5000],  # 5 outliers in 100 values
            'no_outliers': list(range(50, 150)),  # Normal range
            'string_outliers': ['normal'] * 95 + ['VERY_LONG_UNUSUAL_STRING'] * 5
        })

        profile_result = self.profiler.profile_data(outlier_data)

        # Test numeric outlier detection
        normal_values_profile = profile_result.field_profiles['normal_values']

        if hasattr(normal_values_profile, 'outlier_count'):
            # Should detect the extreme values
            assert normal_values_profile.outlier_count >= 3

        if hasattr(normal_values_profile, 'outliers'):
            outliers = normal_values_profile.outliers
            # Should include extreme values
            assert any(val >= 1000 for val in outliers)
            assert any(val <= -500 for val in outliers)

        # Test non-outlier field
        no_outliers_profile = profile_result.field_profiles['no_outliers']
        if hasattr(no_outliers_profile, 'outlier_count'):
            # Should have few or no outliers
            assert no_outliers_profile.outlier_count <= 2

    @pytest.mark.integration
    @pytest.mark.data_processing
    def test_configuration_integration(self):
        """Test integration with different configurations."""
        # Test minimal configuration
        minimal_config = {
            "sample_size": 100,
            "enable_statistical_analysis": False,
            "enable_pattern_detection": False
        }

        minimal_profiler = DataProfiler(config=minimal_config)
        minimal_result = minimal_profiler.profile_data(self.high_quality_data)
        assert minimal_result is not None

        # Test comprehensive configuration
        comprehensive_config = {
            "sample_size": 10000,
            "enable_statistical_analysis": True,
            "enable_pattern_detection": True,
            "enable_outlier_detection": True,
            "null_threshold": 0.01
        }

        comprehensive_profiler = DataProfiler(config=comprehensive_config)
        comprehensive_result = comprehensive_profiler.profile_data(self.high_quality_data)
        assert comprehensive_result is not None

        # Both should have basic information
        comp_profile = comprehensive_result.field_profiles['age']
        min_profile = minimal_result.field_profiles['age']
        assert comp_profile.field_type == min_profile.field_type

    def teardown_method(self):
        """Cleanup after each test method."""
        pass


@pytest.mark.data_processing
class TestDataProfilerFunctionality:
    """Additional functionality tests for data profiler."""

    def test_profile_dataframe_function(self):
        """Test the module-level profile_dataframe function."""
        data = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie']
        })

        result = profile_dataframe(data)
        assert result is not None
        assert isinstance(result, ProfileResult)
        assert 'id' in result.field_profiles
        assert 'name' in result.field_profiles

    def test_profiler_with_datetime_columns(self):
        """Test profiler handling of datetime columns."""
        data = pd.DataFrame({
            'created_at': pd.date_range('2020-01-01', periods=100, freq='D'),
            'updated_at': pd.date_range('2020-06-01', periods=100, freq='h'),
            'event_time': pd.to_datetime(['2020-01-01 10:00:00'] * 100)
        })

        profiler = DataProfiler()
        result = profiler.profile_data(data)

        assert result is not None
        assert 'created_at' in result.field_profiles
        assert 'updated_at' in result.field_profiles
        assert 'event_time' in result.field_profiles

    def test_profiler_with_boolean_columns(self):
        """Test profiler handling of boolean columns."""
        data = pd.DataFrame({
            'is_active': [True, False, True, True, False] * 20,
            'has_subscription': [True] * 50 + [False] * 50,
            'mixed_bool': [True, False, None, True, False] * 20
        })

        profiler = DataProfiler()
        result = profiler.profile_data(data)

        assert result is not None
        assert 'is_active' in result.field_profiles
        assert 'has_subscription' in result.field_profiles
