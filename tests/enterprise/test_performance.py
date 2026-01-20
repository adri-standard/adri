"""
Comprehensive performance tests for enterprise features.

Tests covering:
- Load testing for enterprise decorator workflows
- Performance baselines for all enterprise components
- Scalability testing with large datasets
- Concurrent operations performance
- Memory usage and resource efficiency
- Bottleneck identification and optimization verification
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock
import gc
import psutil
import os

import pandas as pd
import pytest

from adri_enterprise.decorator import adri_protected
from adri_enterprise.license import get_validator
from adri_enterprise.logging.reasoning import ReasoningLogger
from adri_enterprise.logging.verodat import VerodatLogger


@pytest.mark.performance
class TestEnterpriseDecoratorPerformance:
    """Performance tests for enterprise decorator."""

    def test_decorator_overhead_baseline(
        self,
        performance_baseline,
        clean_license_cache,
        mock_verodat_api_success
    ):
        """Test that enterprise decorator overhead meets baseline."""
        # Small dataset to isolate decorator overhead
        test_data = pd.DataFrame({
            "id": [1, 2, 3],
            "value": [10, 20, 30]
        })

        with patch.dict(os.environ, {'VERODAT_API_KEY': 'overhead-test-key'}):

            @adri_protected(
                contract="test_decorator_overhead",
                reasoning_mode=False,
                verbose=False,
                auto_generate=True
            )
            def minimal_function(data):
                """Minimal function to isolate decorator overhead."""
                return len(data)

            # Warm up (license validation, contract generation)
            minimal_function(test_data)

            # Measure overhead on subsequent calls
            start_time = time.time()
            for _ in range(100):  # Multiple calls to average overhead
                result = minimal_function(test_data)
                assert result == 3
            end_time = time.time()

            # Calculate average overhead per call
            total_time = end_time - start_time
            overhead_per_call = total_time / 100

            # Should meet performance baseline (relaxed for CI environments)
            assert overhead_per_call < performance_baseline['decorator_overhead_max_time'] * 2.0

    def test_large_dataset_performance(
        self,
        clean_license_cache,
        mock_verodat_api_success
    ):
        """Test performance with large datasets."""
        # Create large dataset
        large_data = pd.DataFrame({
            "id": range(10000),
            "value": [i * 1.5 for i in range(10000)],
            "category": [f"cat_{i % 100}" for i in range(10000)],
            "description": [f"Description for record {i}" for i in range(10000)]
        })

        with patch.dict(os.environ, {'VERODAT_API_KEY': 'large-dataset-key'}):

            @adri_protected(
                contract="test_large_dataset_performance",
                reasoning_mode=False,
                verbose=False,
                auto_generate=True
            )
            def process_large_dataset(data):
                """Process large dataset efficiently."""
                # Realistic data processing
                processed = data.copy()
                processed['computed_value'] = processed['value'] * 2
                processed['value_squared'] = processed['value'] ** 2
                return processed.groupby('category')['value'].agg(['mean', 'sum', 'count'])

            # Measure processing time
            start_time = time.time()
            result = process_large_dataset(large_data)
            end_time = time.time()

            # Verify results
            assert len(result) == 100  # 100 categories
            assert all(result['count'] == 100)  # Each category has 100 records

            # Performance should be reasonable for large dataset
            processing_time = end_time - start_time
            assert processing_time < 5.0  # Should complete within 5 seconds

    def test_reasoning_mode_performance_impact(
        self,
        temp_log_dir,
        clean_license_cache,
        mock_verodat_api_success
    ):
        """Test performance impact of reasoning mode."""
        test_data = pd.DataFrame({
            "metric": [1, 2, 3, 4, 5] * 100  # 500 records
        })

        with patch.dict(os.environ, {'VERODAT_API_KEY': 'reasoning-perf-key'}):

            # Test without reasoning mode
            @adri_protected(
                contract="test_no_reasoning_performance",
                reasoning_mode=False,
                verbose=False,
                auto_generate=True
            )
            def no_reasoning_function(data):
                return data['metric'].mean()

            # Test with reasoning mode
            @adri_protected(
                contract="test_with_reasoning_performance",
                reasoning_mode=True,
                verbose=False,
                auto_generate=True
            )
            def with_reasoning_function(data):
                return data['metric'].mean()

            # Warm up both functions
            no_reasoning_function(test_data)
            with_reasoning_function(test_data)

            # Measure performance without reasoning
            start_time = time.time()
            for _ in range(10):
                result1 = no_reasoning_function(test_data)
            no_reasoning_time = time.time() - start_time

            # Measure performance with reasoning
            start_time = time.time()
            for _ in range(10):
                result2 = with_reasoning_function(test_data)
            reasoning_time = time.time() - start_time

            # Results should be identical
            assert result1 == result2 == 3.0

            # Reasoning mode should not add excessive overhead
            overhead_ratio = reasoning_time / no_reasoning_time
            assert overhead_ratio < 3.0  # Less than 3x overhead


@pytest.mark.performance
class TestLicenseValidationPerformance:
    """Performance tests for license validation system."""

    def test_license_validation_speed(
        self,
        performance_baseline,
        clean_license_cache,
        mock_verodat_api_success
    ):
        """Test license validation speed meets baseline."""
        validator = get_validator()

        start_time = time.time()
        license_info = validator.validate_api_key("performance-test-key")
        end_time = time.time()

        validation_time = end_time - start_time

        # Verify successful validation
        assert license_info.is_valid is True

        # Should meet performance baseline
        assert validation_time < performance_baseline['license_validation_max_time']

    def test_license_cache_performance(
        self,
        performance_baseline,
        clean_license_cache,
        mock_verodat_api_success
    ):
        """Test license cache hit performance."""
        validator = get_validator()

        # Initial validation (cache miss)
        validator.validate_api_key("cache-perf-key")

        # Measure cache hit performance
        start_time = time.time()
        for _ in range(1000):  # Many cache hits
            license_info = validator.validate_api_key("cache-perf-key")
            assert license_info.is_valid is True
        end_time = time.time()

        # Calculate average cache hit time
        total_time = end_time - start_time
        avg_cache_time = total_time / 1000

        # Cache hits should be very fast
        assert avg_cache_time < performance_baseline['license_cache_hit_max_time']

    def test_concurrent_license_validation_performance(
        self,
        clean_license_cache,
        mock_verodat_api_success
    ):
        """Test performance with concurrent license validations."""
        def validate_license_concurrent():
            validator = get_validator()
            return validator.validate_api_key("concurrent-validation-key")

        start_time = time.time()

        # Run concurrent validations
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(validate_license_concurrent)
                for _ in range(100)
            ]
            results = [future.result() for future in as_completed(futures)]

        end_time = time.time()

        # All validations should succeed
        assert len(results) == 100
        for result in results:
            assert result.is_valid is True

        # Should complete quickly due to singleton + caching
        total_time = end_time - start_time
        assert total_time < 2.0  # Should complete within 2 seconds

        # API should only be called once
        assert mock_verodat_api_success['get'].call_count == 1


@pytest.mark.performance
class TestReasoningLoggerPerformance:
    """Performance tests for reasoning logger."""

    def test_reasoning_log_write_performance(
        self,
        temp_log_dir,
        performance_baseline
    ):
        """Test reasoning log write performance."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        # Test prompt logging performance
        start_time = time.time()
        for i in range(100):
            logger.log_prompt(
                prompt=f"Performance test prompt {i}",
                assessment_id=f"perf_test_{i:03d}"
            )
        end_time = time.time()

        total_time = end_time - start_time
        avg_time_per_log = total_time / 100

        # Should meet performance baseline
        assert avg_time_per_log < performance_baseline['reasoning_log_write_max_time']

    def test_reasoning_logger_throughput(self, temp_log_dir):
        """Test reasoning logger throughput under load."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        def log_many_steps(count):
            for i in range(count):
                logger.log_reasoning_step(
                    prompt=f"Throughput test prompt {i}",
                    response=f"Throughput test response {i}",
                    assessment_id=f"throughput_{i:04d}"
                )

        start_time = time.time()
        log_many_steps(500)  # 500 reasoning steps
        end_time = time.time()

        total_time = end_time - start_time
        throughput = 500 / total_time

        # Should achieve good throughput
        assert throughput >= 50.0  # At least 50 steps per second

    def test_concurrent_reasoning_logging_performance(self, temp_log_dir):
        """Test concurrent reasoning logging performance."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        def concurrent_log(thread_id):
            results = []
            for i in range(20):
                prompt_id, response_id = logger.log_reasoning_step(
                    prompt=f"Thread {thread_id} prompt {i}",
                    response=f"Thread {thread_id} response {i}",
                    assessment_id=f"concurrent_{thread_id}_{i:02d}"
                )
                results.append((prompt_id, response_id))
            return results

        start_time = time.time()

        # Run concurrent logging
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(concurrent_log, thread_id)
                for thread_id in range(10)
            ]
            thread_results = [future.result() for future in as_completed(futures)]

        end_time = time.time()

        # Verify all operations succeeded
        total_operations = sum(len(results) for results in thread_results)
        assert total_operations == 200  # 10 threads * 20 operations each

        # Performance should be reasonable
        total_time = end_time - start_time
        operations_per_second = total_operations / total_time
        assert operations_per_second >= 20.0  # At least 20 ops per second

    def test_large_data_logging_performance(self, temp_log_dir):
        """Test performance with large reasoning data."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        # Create large structured data
        large_prompt = {
            "system": "Complex data analysis system",
            "user_query": "Analyze this comprehensive dataset",
            "context": {
                "dataset_metadata": {
                    "records": 50000,
                    "fields": ["field_" + str(i) for i in range(200)],
                    "quality_scores": {f"dimension_{i}": 80 + (i % 20) for i in range(50)}
                },
                "processing_history": [
                    {
                        "step": f"processing_step_{i}",
                        "duration": i * 0.5,
                        "status": "completed" if i % 2 == 0 else "pending"
                    }
                    for i in range(100)
                ]
            }
        }

        large_response = {
            "analysis_results": {
                "summary": "Comprehensive analysis of large dataset",
                "findings": [f"Finding {i}: Data pattern detected" for i in range(50)],
                "recommendations": [
                    {
                        "priority": "high" if i < 10 else "medium",
                        "action": f"Recommendation {i}",
                        "impact_score": 90 - (i * 2)
                    }
                    for i in range(30)
                ]
            },
            "detailed_metrics": {
                f"metric_{i}": {
                    "value": i * 1.5,
                    "threshold": i * 1.2,
                    "status": "pass" if i % 3 == 0 else "fail"
                }
                for i in range(200)
            }
        }

        start_time = time.time()
        prompt_id, response_id = logger.log_reasoning_step(
            prompt=large_prompt,
            response=large_response,
            assessment_id="large_data_perf_test"
        )
        end_time = time.time()

        # Should handle large data efficiently
        logging_time = end_time - start_time
        assert logging_time < 1.0  # Should complete within 1 second

        # Verify data was logged correctly
        assert prompt_id.startswith("prompt_")
        assert response_id.startswith("response_")


@pytest.mark.performance
class TestVerodatLoggerPerformance:
    """Performance tests for Verodat logger."""

    def test_verodat_batch_processing_performance(self, performance_baseline):
        """Test Verodat batch processing performance."""
        logger = VerodatLogger(
            api_url="https://test.api.com",
            api_key="batch-perf-key",
            batch_size=50
        )

        # Create batch of assessments
        assessments = [
            {
                "assessment_id": f"batch_perf_{i:04d}",
                "overall_score": 80 + (i % 20),
                "passed": True,
                "dimension_scores": {
                    "validity": 18.0,
                    "completeness": 17.5,
                    "consistency": 16.8
                }
            }
            for i in range(50)
        ]

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            start_time = time.time()

            # Log all assessments (should trigger batch send)
            for assessment in assessments[:-1]:
                logger.log_assessment(assessment)

            # Last assessment triggers batch send
            logger.log_assessment(assessments[-1])

            end_time = time.time()

            processing_time = end_time - start_time

            # Should process batch efficiently
            assert processing_time < 2.0  # Should complete within 2 seconds

            # Should have made one API call for the batch
            assert mock_post.call_count == 1

    def test_verodat_concurrent_logging_performance(self):
        """Test Verodat logger performance with concurrent operations."""
        logger = VerodatLogger(
            api_url="https://test.api.com",
            api_key="concurrent-verodat-key",
            batch_size=1  # Immediate send for concurrent testing
        )

        def concurrent_verodat_log(log_id):
            assessment = {
                "assessment_id": f"concurrent_verodat_{log_id}",
                "overall_score": 85.0,
                "passed": True
            }

            with patch('requests.post') as mock_post:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_post.return_value = mock_response

                return logger.log_assessment(assessment)

        start_time = time.time()

        # Run concurrent Verodat logging
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [
                executor.submit(concurrent_verodat_log, i)
                for i in range(50)
            ]
            results = [future.result() for future in as_completed(futures)]

        end_time = time.time()

        # All operations should succeed
        assert len(results) == 50
        assert all(results)

        # Should complete within reasonable time
        total_time = end_time - start_time
        assert total_time < 10.0  # Should complete within 10 seconds

    def test_verodat_retry_performance_impact(self):
        """Test performance impact of retry logic."""
        logger = VerodatLogger(
            api_url="https://test.api.com",
            api_key="retry-perf-key",
            retry_attempts=3,
            batch_size=1  # Immediate send for testing
        )

        assessment = {
            "assessment_id": "retry_performance_test",
            "overall_score": 88.5
        }

        # Test successful call (no retries)
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            start_time = time.time()
            result = logger.log_assessment(assessment)
            no_retry_time = time.time() - start_time

            assert result is True
            assert mock_post.call_count == 1

        # Create new logger instance for second test (fresh buffer)
        logger2 = VerodatLogger(
            api_url="https://test.api.com",
            api_key="retry-perf-key",
            retry_attempts=3,
            batch_size=1
        )

        # Test with retries (2 failures, then success)
        with patch('requests.post') as mock_post:
            responses = [
                MagicMock(status_code=500),  # Failure
                MagicMock(status_code=502),  # Failure
                MagicMock(status_code=200)   # Success
            ]
            mock_post.side_effect = responses

            start_time = time.time()
            result = logger2.log_assessment(assessment)
            retry_time = time.time() - start_time

            assert result is True
            assert mock_post.call_count == 3

        # Retry overhead should be reasonable
        retry_overhead = retry_time - no_retry_time
        assert retry_overhead < 1.0  # Less than 1 second additional overhead


@pytest.mark.performance
class TestMemoryAndResourcePerformance:
    """Performance tests for memory usage and resource efficiency."""

    def test_memory_usage_enterprise_decorator(
        self,
        clean_license_cache,
        mock_verodat_api_success
    ):
        """Test memory usage of enterprise decorator workflows."""
        process = psutil.Process()

        # Get baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        test_data = pd.DataFrame({
            "id": range(1000),
            "value": [i * 1.5 for i in range(1000)]
        })

        with patch.dict(os.environ, {'VERODAT_API_KEY': 'memory-test-key'}):

            @adri_protected(
                contract="test_memory_usage",
                reasoning_mode=True,
                verbose=False,
                auto_generate=True
            )
            def memory_test_function(data):
                # Process data in a way that should not accumulate memory
                return data.groupby(data.index // 100)['value'].mean()

            # Run multiple iterations to check for memory leaks
            for i in range(50):
                result = memory_test_function(test_data)
                assert len(result) == 10

                # Force garbage collection every 10 iterations
                if i % 10 == 0:
                    gc.collect()

            # Check memory after operations
            gc.collect()
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - baseline_memory

            # Memory increase should be reasonable (less than 100MB)
            assert memory_increase < 100.0

    def test_reasoning_logger_memory_efficiency(self, temp_log_dir):
        """Test memory efficiency of reasoning logger."""
        process = psutil.Process()

        # Get baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        logger = ReasoningLogger(log_dir=temp_log_dir)

        # Log many reasoning steps
        for i in range(500):
            logger.log_reasoning_step(
                prompt=f"Memory test prompt {i}",
                response=f"Memory test response {i}",
                assessment_id=f"memory_test_{i:04d}"
            )

            # Periodic garbage collection
            if i % 100 == 0:
                gc.collect()

        # Check final memory
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - baseline_memory

        # Memory increase should be minimal (logs are written to disk)
        assert memory_increase < 50.0  # Less than 50MB increase

    def test_license_validator_memory_efficiency(
        self,
        clean_license_cache,
        mock_verodat_api_success
    ):
        """Test memory efficiency of license validator."""
        process = psutil.Process()
        validator = get_validator()

        # Get baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform many validations (should use cache)
        for i in range(1000):
            license_info = validator.validate_api_key("memory-efficiency-key")
            assert license_info.is_valid is True

            # Periodic garbage collection
            if i % 200 == 0:
                gc.collect()

        # Check memory usage
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - baseline_memory

        # Memory should not increase significantly (caching is efficient)
        assert memory_increase < 10.0  # Less than 10MB increase


@pytest.mark.performance
class TestScalabilityPerformance:
    """Performance tests for scalability and load handling."""

    def test_high_concurrency_enterprise_workflows(
        self,
        clean_license_cache,
        mock_verodat_api_success
    ):
        """Test scalability with high concurrency."""
        test_data = pd.DataFrame({
            "record_id": range(100),
            "metric": [i * 2.5 for i in range(100)]
        })

        with patch.dict(os.environ, {'VERODAT_API_KEY': 'high-concurrency-key'}):

            @adri_protected(
                contract="test_high_concurrency",
                verbose=False,
                auto_generate=True
            )
            def high_concurrency_workflow(data, worker_id):
                time.sleep(0.01)  # Minimal processing time
                return {
                    'worker_id': worker_id,
                    'result': data['metric'].sum(),
                    'count': len(data)
                }

            def run_workflow(worker_id):
                return high_concurrency_workflow(test_data, worker_id)

            start_time = time.time()

            # High concurrency test
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = [
                    executor.submit(run_workflow, i)
                    for i in range(200)
                ]
                results = [future.result() for future in as_completed(futures)]

            end_time = time.time()

            # All workflows should complete
            assert len(results) == 200
            for result in results:
                assert result['result'] == sum(i * 2.5 for i in range(100))
                assert result['count'] == 100

            # Should handle high concurrency efficiently
            total_time = end_time - start_time
            workflows_per_second = len(results) / total_time
            assert workflows_per_second >= 5.0  # At least 5 workflows/second (adjusted for CI)

    def test_large_scale_logging_performance(self, temp_log_dir):
        """Test performance with large-scale logging operations."""
        reasoning_logger = ReasoningLogger(log_dir=temp_log_dir)
        verodat_logger = VerodatLogger("https://test.api.com", "large-scale-key", batch_size=100)

        start_time = time.time()

        # Large scale logging test
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            for i in range(1000):
                # Log reasoning step
                prompt_id, response_id = reasoning_logger.log_reasoning_step(
                    prompt=f"Large scale test {i}",
                    response=f"Response {i}",
                    assessment_id=f"large_scale_{i:04d}"
                )

                # Log to Verodat every 10th iteration
                if i % 10 == 0:
                    assessment = {
                        "assessment_id": f"large_scale_{i:04d}",
                        "overall_score": 80 + (i % 20),
                        "reasoning_prompt_id": prompt_id,
                        "reasoning_response_id": response_id
                    }
                    verodat_logger.log_assessment(assessment)

            # Flush remaining Verodat batch
            verodat_logger.close()

        end_time = time.time()

        total_time = end_time - start_time
        operations_per_second = 1000 / total_time

        # Should handle large scale operations efficiently
        assert operations_per_second >= 100.0  # At least 100 ops/second

    def test_sustained_load_performance(
        self,
        clean_license_cache,
        mock_verodat_api_success
    ):
        """Test performance under sustained load."""
        test_data = pd.DataFrame({
            "value": range(50)
        })

        with patch.dict(os.environ, {'VERODAT_API_KEY': 'sustained-load-key'}):

            @adri_protected(
                contract="test_sustained_load",
                verbose=False,
                auto_generate=True
            )
            def sustained_load_workflow(data):
                return data['value'].mean()

            # Run sustained load test
            total_operations = 0
            start_time = time.time()

            # Run for a sustained period
            while time.time() - start_time < 3.0:  # 3 seconds
                result = sustained_load_workflow(test_data)
                assert result == 24.5  # Mean of range(50)
                total_operations += 1

            end_time = time.time()
            actual_duration = end_time - start_time

            # Calculate sustained throughput
            sustained_throughput = total_operations / actual_duration

            # Should maintain good throughput under sustained load
            assert sustained_throughput >= 8.0  # At least 8 ops/second (adjusted for CI)
            assert total_operations >= 24  # Should complete at least 24 operations
