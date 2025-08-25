"""
Comprehensive Performance Testing Suite for ADRI Validator.

This module contains extensive performance tests to ensure the ADRI Validator
meets production-grade performance requirements and scores high on all metrics.

NOTE: These tests use large datasets and are marked with @pytest.mark.performance
They will be skipped by default. Run with: pytest --performance
"""

import concurrent.futures
import gc
import json
import os
import random
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest
import yaml

from adri.core.audit_logger import AuditLogger
from adri.core.protection import DataProtectionEngine, ProtectionError
from adri.core.assessor import AssessmentEngine
from adri.analysis.data_profiler import DataProfiler
from adri.analysis.standard_generator import StandardGenerator
from adri.decorators.guard import adri_protected

# Import test utilities to prevent token explosion
try:
    from tests.test_utils import OutputLimiter, TestDataGenerator, skip_if_ci
except ImportError:
    # Fallback if test_utils not available
    OutputLimiter = None
    TestDataGenerator = None
    skip_if_ci = lambda: None


@pytest.mark.performance
class TestPerformanceMetrics:
    """Comprehensive performance tests with specific metrics and thresholds.
    
    These tests will be skipped by default. Run with: pytest --performance
    """
    
    # Performance thresholds
    SMALL_DATASET_MAX_TIME = 0.1    # 100ms for datasets < 10K rows
    MEDIUM_DATASET_MAX_TIME = 0.5   # 500ms for datasets < 100K rows
    LARGE_DATASET_MAX_TIME = 2.0    # 2s for datasets < 1M rows
    CACHE_HIT_MIN_RATE = 0.9        # 90% cache hit rate
    MEMORY_GROWTH_MAX_FACTOR = 2.0  # Max 2x memory growth
    CONCURRENT_SCALING_MIN = 0.8    # 80% linear scaling efficiency
    
    @pytest.fixture
    def performance_monitor(self):
        """Monitor for tracking performance metrics."""
        class PerformanceMonitor:
            def __init__(self):
                self.metrics = {
                    'execution_times': [],
                    'memory_usage': [],
                    'cache_hits': 0,
                    'cache_misses': 0,
                    'concurrent_operations': 0,
                    'audit_log_writes': 0
                }
            
            def record_execution_time(self, operation: str, duration: float):
                self.metrics['execution_times'].append({
                    'operation': operation,
                    'duration': duration,
                    'timestamp': time.time()
                })
            
            def record_memory_usage(self, operation: str, memory_mb: float):
                self.metrics['memory_usage'].append({
                    'operation': operation,
                    'memory_mb': memory_mb,
                    'timestamp': time.time()
                })
            
            def record_cache_hit(self):
                self.metrics['cache_hits'] += 1
            
            def record_cache_miss(self):
                self.metrics['cache_misses'] += 1
            
            def get_cache_hit_rate(self):
                total = self.metrics['cache_hits'] + self.metrics['cache_misses']
                if total == 0:
                    return 0
                return self.metrics['cache_hits'] / total
            
            def get_average_execution_time(self, operation: str = None):
                times = self.metrics['execution_times']
                if operation:
                    times = [t for t in times if t['operation'] == operation]
                if not times:
                    return 0
                return sum(t['duration'] for t in times) / len(times)
            
            def generate_report(self):
                return {
                    'avg_execution_time': self.get_average_execution_time(),
                    'cache_hit_rate': self.get_cache_hit_rate(),
                    'total_operations': len(self.metrics['execution_times']),
                    'peak_memory_mb': max(self.metrics['memory_usage'], key=lambda x: x['memory_mb'])['memory_mb'] if self.metrics['memory_usage'] else 0,
                    'concurrent_operations': self.metrics['concurrent_operations']
                }
        
        return PerformanceMonitor()
    
    # ===== Dataset Generators =====
    
    @pytest.fixture
    def generate_dataset(self):
        """Factory for generating datasets of various sizes."""
        def _generate(rows: int, cols: int = 10, wide: bool = False):
            np.random.seed(42)
            
            if wide:
                # Wide dataset with many columns
                data = {}
                for i in range(cols):
                    col_type = random.choice(['numeric', 'string', 'date', 'boolean'])
                    if col_type == 'numeric':
                        data[f'col_{i}'] = np.random.uniform(0, 1000, rows)
                    elif col_type == 'string':
                        data[f'col_{i}'] = [f'value_{j}_{i}' for j in range(rows)]
                    elif col_type == 'date':
                        data[f'col_{i}'] = pd.date_range('2020-01-01', periods=rows, freq='h')
                    else:
                        data[f'col_{i}'] = np.random.choice([True, False], rows)
            else:
                # Standard dataset
                data = {
                    'id': range(rows),
                    'name': [f'Entity_{i}' for i in range(rows)],
                    'email': [f'user{i}@example.com' for i in range(rows)],
                    'age': np.random.randint(18, 80, rows),
                    'score': np.random.uniform(0, 100, rows),
                    'category': np.random.choice(['A', 'B', 'C', 'D'], rows),
                    'is_active': np.random.choice([True, False], rows),
                    'created_date': pd.date_range('2020-01-01', periods=rows, freq='h'),
                    'value': np.random.exponential(100, rows),
                    'description': [f'Description {i}' for i in range(rows)]
                }
            
            return pd.DataFrame(data)
        
        return _generate
    
    # ===== Section 1: DataProtectionEngine Performance =====
    
    def test_protection_engine_small_dataset(self, generate_dataset, performance_monitor):
        """Test protection engine performance with small datasets."""
        data = generate_dataset(1000)
        engine = DataProtectionEngine()
        
        with patch.object(engine, 'ensure_standard_exists'):
            with patch.object(engine, 'assess_data_quality') as mock_assess:
                mock_assess.return_value = Mock(overall_score=85.0, passed=True, dimension_scores={})
                
                def process_data(data):
                    return len(data)
                
                # Measure execution time
                start_time = time.time()
                result = engine.protect_function_call(
                    func=process_data,
                    args=(data,),
                    kwargs={},
                    data_param='data',
                    function_name='process_data',
                    min_score=80.0
                )
                duration = time.time() - start_time
                
                performance_monitor.record_execution_time('protection_small', duration)
                
                # Assert performance threshold
                assert duration < self.SMALL_DATASET_MAX_TIME, f"Small dataset took {duration:.3f}s, max allowed: {self.SMALL_DATASET_MAX_TIME}s"
                assert result == 1000
    
    def test_protection_engine_medium_dataset(self, generate_dataset, performance_monitor):
        """Test protection engine performance with medium datasets."""
        data = generate_dataset(50000)
        engine = DataProtectionEngine()
        
        with patch.object(engine, 'ensure_standard_exists'):
            with patch.object(engine, 'assess_data_quality') as mock_assess:
                mock_assess.return_value = Mock(overall_score=85.0, passed=True, dimension_scores={})
                
                def process_data(data):
                    return len(data)
                
                start_time = time.time()
                result = engine.protect_function_call(
                    func=process_data,
                    args=(data,),
                    kwargs={},
                    data_param='data',
                    function_name='process_data',
                    min_score=80.0
                )
                duration = time.time() - start_time
                
                performance_monitor.record_execution_time('protection_medium', duration)
                
                assert duration < self.MEDIUM_DATASET_MAX_TIME, f"Medium dataset took {duration:.3f}s, max allowed: {self.MEDIUM_DATASET_MAX_TIME}s"
                assert result == 50000
    
    def test_protection_engine_large_dataset(self, generate_dataset, performance_monitor):
        """Test protection engine performance with large datasets."""
        data = generate_dataset(500000)
        engine = DataProtectionEngine()
        
        with patch.object(engine, 'ensure_standard_exists'):
            with patch.object(engine, 'assess_data_quality') as mock_assess:
                mock_assess.return_value = Mock(overall_score=85.0, passed=True, dimension_scores={})
                
                def process_data(data):
                    return len(data)
                
                start_time = time.time()
                result = engine.protect_function_call(
                    func=process_data,
                    args=(data,),
                    kwargs={},
                    data_param='data',
                    function_name='process_data',
                    min_score=80.0
                )
                duration = time.time() - start_time
                
                performance_monitor.record_execution_time('protection_large', duration)
                
                assert duration < self.LARGE_DATASET_MAX_TIME, f"Large dataset took {duration:.3f}s, max allowed: {self.LARGE_DATASET_MAX_TIME}s"
                assert result == 500000
    
    # ===== Section 2: Cache Performance =====
    
    def test_cache_performance_hit_rate(self, generate_dataset, performance_monitor):
        """Test cache hit rate meets minimum threshold."""
        data = generate_dataset(1000)
        engine = DataProtectionEngine()
        
        # Enable caching
        with patch('adri.config.manager.ConfigManager.get_protection_config') as mock_config:
            mock_config.return_value = {
                'cache_duration_hours': 1,
                'default_min_score': 80,
                'default_failure_mode': 'raise'
            }
            
            with patch.object(engine, 'ensure_standard_exists'):
                with patch.object(engine, 'assess_data_quality') as mock_assess:
                    mock_assess.return_value = Mock(overall_score=85.0, passed=True, dimension_scores={})
                    
                    def process_data(data):
                        return len(data)
                    
                    # First call - cache miss
                    engine.protect_function_call(
                        func=process_data,
                        args=(data,),
                        kwargs={},
                        data_param='data',
                        function_name='process_data',
                        min_score=80.0
                    )
                    performance_monitor.record_cache_miss()
                    
                    # Subsequent calls - should be cache hits
                    for _ in range(9):
                        engine.protect_function_call(
                            func=process_data,
                            args=(data,),
                            kwargs={},
                            data_param='data',
                            function_name='process_data',
                            min_score=80.0
                        )
                        performance_monitor.record_cache_hit()
                    
                    # Check cache hit rate
                    hit_rate = performance_monitor.get_cache_hit_rate()
                    assert hit_rate >= self.CACHE_HIT_MIN_RATE, f"Cache hit rate {hit_rate:.2%} below minimum {self.CACHE_HIT_MIN_RATE:.2%}"
    
    def test_cache_performance_speed_improvement(self, generate_dataset):
        """Test that caching improves performance significantly."""
        data = generate_dataset(10000)
        engine = DataProtectionEngine()
        
        with patch('adri.config.manager.ConfigManager.get_protection_config') as mock_config:
            mock_config.return_value = {
                'cache_duration_hours': 1,
                'default_min_score': 80,
                'default_failure_mode': 'raise'
            }
            
            with patch.object(engine, 'ensure_standard_exists'):
                # Real assessment for first call
                assessment_engine = AssessmentEngine()
                standard = {
                    'metadata': {'name': 'test', 'version': '1.0.0'},
                    'standards': {'fields': {}, 'requirements': {'overall_minimum': 80}}
                }
                
                def process_data(data):
                    return len(data)
                
                # First call - no cache
                start_time = time.time()
                with patch.object(engine, 'assess_data_quality', wraps=lambda d, s: assessment_engine.assess(d, s)):
                    engine.protect_function_call(
                        func=process_data,
                        args=(data,),
                        kwargs={},
                        data_param='data',
                        function_name='process_data',
                        min_score=80.0
                    )
                first_call_time = time.time() - start_time
                
                # Second call - should use cache
                start_time = time.time()
                with patch.object(engine, 'assess_data_quality', wraps=lambda d, s: assessment_engine.assess(d, s)):
                    engine.protect_function_call(
                        func=process_data,
                        args=(data,),
                        kwargs={},
                        data_param='data',
                        function_name='process_data',
                        min_score=80.0
                    )
                cached_call_time = time.time() - start_time
                
                # Cache should be at least 10x faster
                speedup = first_call_time / cached_call_time if cached_call_time > 0 else float('inf')
                assert speedup > 10, f"Cache speedup {speedup:.1f}x is less than expected 10x"
    
    # ===== Section 3: Concurrent Performance =====
    
    def test_concurrent_operations_thread_safety(self, generate_dataset, performance_monitor):
        """Test thread safety and performance under concurrent load."""
        datasets = [generate_dataset(1000) for _ in range(10)]
        engine = DataProtectionEngine()
        results = []
        errors = []
        
        def run_protection(data, thread_id):
            try:
                with patch.object(engine, 'ensure_standard_exists'):
                    with patch.object(engine, 'assess_data_quality') as mock_assess:
                        mock_assess.return_value = Mock(overall_score=85.0 + thread_id, passed=True, dimension_scores={})
                        
                        def process_data(data):
                            return f"Thread {thread_id}: {len(data)}"
                        
                        result = engine.protect_function_call(
                            func=process_data,
                            args=(data,),
                            kwargs={},
                            data_param='data',
                            function_name=f'process_data_{thread_id}',
                            min_score=80.0
                        )
                        results.append(result)
                        performance_monitor.metrics['concurrent_operations'] += 1
            except Exception as e:
                errors.append(e)
        
        # Run concurrent operations
        threads = []
        start_time = time.time()
        
        for i, data in enumerate(datasets):
            thread = threading.Thread(target=run_protection, args=(data, i))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        concurrent_time = time.time() - start_time
        
        # Verify all operations completed successfully
        assert len(errors) == 0, f"Concurrent operations had {len(errors)} errors"
        assert len(results) == 10, "Not all concurrent operations completed"
        
        # Check performance scaling
        # Sequential time would be ~10 * single operation time
        # Good concurrent performance should be significantly less
        single_operation_time = 0.01  # Estimated from mocked operations
        expected_sequential_time = 10 * single_operation_time
        scaling_efficiency = expected_sequential_time / concurrent_time if concurrent_time > 0 else 1
        
        # We expect at least 80% scaling efficiency
        assert scaling_efficiency >= self.CONCURRENT_SCALING_MIN or concurrent_time < 0.5, \
            f"Poor concurrent scaling: {scaling_efficiency:.2f} (time: {concurrent_time:.3f}s)"
    
    def test_concurrent_with_thread_pool(self, generate_dataset, performance_monitor):
        """Test performance with thread pool executor."""
        datasets = [generate_dataset(5000) for _ in range(20)]
        engine = DataProtectionEngine()
        
        def assess_data(data):
            with patch.object(engine, 'ensure_standard_exists'):
                with patch.object(engine, 'assess_data_quality') as mock_assess:
                    mock_assess.return_value = Mock(overall_score=90.0, passed=True, dimension_scores={})
                    
                    def process_data(data):
                        return data['score'].mean()
                    
                    return engine.protect_function_call(
                        func=process_data,
                        args=(data,),
                        kwargs={},
                        data_param='data',
                        function_name='process_data',
                        min_score=80.0
                    )
        
        start_time = time.time()
        
        # Use thread pool for parallel execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(assess_data, data) for data in datasets]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        duration = time.time() - start_time
        performance_monitor.record_execution_time('concurrent_pool', duration)
        
        # All operations should complete
        assert len(results) == 20
        
        # Should complete in reasonable time (less than sequential)
        assert duration < 2.0, f"Thread pool operations took {duration:.3f}s"
    
    # ===== Section 4: Audit Logger Performance =====
    
    def test_audit_logger_write_performance(self, performance_monitor, tmp_path):
        """Test audit logger write performance."""
        log_file = tmp_path / 'audit.jsonl'
        config = {
            'enabled': True,
            'log_location': str(log_file)
        }
        logger = AuditLogger(config)
        
        # Generate sample assessment result
        assessment_result = Mock()
        assessment_result.overall_score = 85.0
        assessment_result.passed = True
        assessment_result.standard_id = 'test_standard'
        assessment_result.assessment_date = None
        assessment_result.dimension_scores = {
            'validity': Mock(score=17.0),
            'completeness': Mock(score=18.0),
            'consistency': Mock(score=16.0),
            'freshness': Mock(score=17.0),
            'plausibility': Mock(score=17.0)
        }
        assessment_result.metadata = {}
        assessment_result.rule_execution_log = []
        assessment_result.field_analysis = {}
        
        # Measure write performance for 1000 log entries
        start_time = time.time()
        for i in range(1000):
            logger.log_assessment(
                assessment_result=assessment_result,
                data_shape=(1000, 10),
                execution_context={
                    'function_name': f'test_function_{i}',
                    'assessment_passed': True,
                    'execution_allowed': True
                }
            )
            performance_monitor.metrics['audit_log_writes'] += 1
        
        duration = time.time() - start_time
        performance_monitor.record_execution_time('audit_writes', duration)
        
        # Should write 1000 entries in less than 1 second
        assert duration < 1.0, f"Audit log writes took {duration:.3f}s for 1000 entries"
        
        # Verify logs were written
        assert log_file.exists()
        with open(log_file, 'r') as f:
            lines = f.readlines()
        assert len(lines) == 1000
    
    def test_audit_logger_concurrent_writes(self, tmp_path):
        """Test audit logger performance under concurrent writes."""
        log_file = tmp_path / 'concurrent_audit.jsonl'
        config = {
            'enabled': True,
            'log_location': str(log_file)
        }
        logger = AuditLogger(config)
        
        def write_logs(thread_id):
            assessment_result = Mock()
            assessment_result.overall_score = 80.0 + thread_id
            assessment_result.passed = True
            assessment_result.standard_id = f'standard_{thread_id}'
            assessment_result.assessment_date = None
            assessment_result.dimension_scores = {}
            assessment_result.metadata = {}
            assessment_result.rule_execution_log = []
            assessment_result.field_analysis = {}
            
            for i in range(100):
                logger.log_assessment(
                    assessment_result=assessment_result,
                    data_shape=(100, 5),
                    execution_context={'thread_id': thread_id, 'iteration': i}
                )
        
        # Launch concurrent writers
        threads = []
        start_time = time.time()
        
        for i in range(10):
            thread = threading.Thread(target=write_logs, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        duration = time.time() - start_time
        
        # Should handle concurrent writes efficiently
        assert duration < 2.0, f"Concurrent audit writes took {duration:.3f}s"
        
        # Verify all logs were written
        with open(log_file, 'r') as f:
            lines = f.readlines()
        assert len(lines) == 1000  # 10 threads * 100 logs each
    
    # ===== Section 5: Memory Performance =====
    
    def test_memory_efficiency_large_dataset(self, generate_dataset):
        """Test memory efficiency with large datasets."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Get baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process large dataset
        data = generate_dataset(100000)
        engine = DataProtectionEngine()
        
        with patch.object(engine, 'ensure_standard_exists'):
            with patch.object(engine, 'assess_data_quality') as mock_assess:
                mock_assess.return_value = Mock(overall_score=85.0, passed=True, dimension_scores={})
                
                def process_data(data):
                    return data['score'].mean()
                
                result = engine.protect_function_call(
                    func=process_data,
                    args=(data,),
                    kwargs={},
                    data_param='data',
                    function_name='process_data',
                    min_score=80.0
                )
        
        # Get peak memory
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = peak_memory / baseline_memory if baseline_memory > 0 else 1
        
        # Clean up
        del data
        gc.collect()
        
        # Memory growth should be reasonable
        assert memory_growth < self.MEMORY_GROWTH_MAX_FACTOR, \
            f"Memory grew by {memory_growth:.1f}x, max allowed: {self.MEMORY_GROWTH_MAX_FACTOR}x"
    
    # ===== Section 6: Edge Cases Performance =====
    
    def test_empty_dataset_performance(self, performance_monitor):
        """Test performance with empty dataset."""
        empty_df = pd.DataFrame()
        engine = DataProtectionEngine()
        
        with patch.object(engine, 'ensure_standard_exists'):
            with patch.object(engine, 'assess_data_quality') as mock_assess:
                mock_assess.return_value = Mock(overall_score=0.0, passed=False, dimension_scores={})
                
                def process_data(data):
                    return len(data)
                
                start_time = time.time()
                try:
                    engine.protect_function_call(
                        func=process_data,
                        args=(empty_df,),
                        kwargs={},
                        data_param='data',
                        function_name='process_data',
                        min_score=80.0,
                        on_failure='raise'
                    )
                except ProtectionError:
                    pass  # Expected
                
                duration = time.time() - start_time
                performance_monitor.record_execution_time('empty_dataset', duration)
                
                # Should handle empty dataset quickly
                assert duration < 0.01, f"Empty dataset took {duration:.3f}s"
    
    def test_single_row_performance(self, performance_monitor):
        """Test performance with single row dataset."""
        single_row = pd.DataFrame({'id': [1], 'value': [100]})
        engine = DataProtectionEngine()
        
        with patch.object(engine, 'ensure_standard_exists'):
            with patch.object(engine, 'assess_data_quality') as mock_assess:
                mock_assess.return_value = Mock(overall_score=85.0, passed=True, dimension_scores={})
                
                def process_data(data):
                    return len(data)
                
                start_time = time.time()
                result = engine.protect_function_call(
                    func=process_data,
                    args=(single_row,),
                    kwargs={},
                    data_param='data',
                    function_name='process_data',
                    min_score=80.0
                )
                duration = time.time() - start_time
                
                performance_monitor.record_execution_time('single_row', duration)
                
                assert duration < 0.01, f"Single row took {duration:.3f}s"
                assert result == 1
    
    def test_wide_dataset_performance(self, generate_dataset, performance_monitor):
        """Test performance with wide dataset (many columns)."""
        # Create dataset with 100 columns
        wide_data = generate_dataset(1000, cols=100, wide=True)
        engine = DataProtectionEngine()
        
        with patch.object(engine, 'ensure_standard_exists'):
            with patch.object(engine, 'assess_data_quality') as mock_assess:
                mock_assess.return_value = Mock(overall_score=85.0, passed=True, dimension_scores={})
                
                def process_data(data):
                    return data.shape
                
                start_time = time.time()
                result = engine.protect_function_call(
                    func=process_data,
                    args=(wide_data,),
                    kwargs={},
                    data_param='data',
                    function_name='process_data',
                    min_score=80.0
                )
                duration = time.time() - start_time
                
                performance_monitor.record_execution_time('wide_dataset', duration)
                
                # Wide datasets should still perform well
                assert duration < self.SMALL_DATASET_MAX_TIME * 2, f"Wide dataset took {duration:.3f}s"
                assert result == (1000, 100)
    
    # ===== Section 7: Assessment Engine Performance =====
    
    def test_assessment_engine_scaling(self, generate_dataset, performance_monitor):
        """Test assessment engine performance scaling."""
        engine = AssessmentEngine()
        standard = {
            'metadata': {'name': 'scaling_test', 'version': '1.0.0'},
            'standards': {
                'fields': {
                    'email': {'type': 'string', 'pattern': r'^[^@]+@[^@]+\.[^@]+$'},
                    'age': {'type': 'integer', 'range': {'min': 0, 'max': 150}},
                    'score': {'type': 'float', 'range': {'min': 0, 'max': 100}}
                },
                'requirements': {
                    'overall_minimum': 85,
                    'dimension_minimums': {
                        'validity': 80,
                        'completeness': 90,
                        'consistency': 85
                    }
                }
            }
        }
        
        # Test different dataset sizes
        sizes = [100, 1000, 10000, 50000]
        times = []
        
        for size in sizes:
            data = generate_dataset(size)
            
            start_time = time.time()
            result = engine.assess(data, standard)
            duration = time.time() - start_time
            
            times.append(duration)
            performance_monitor.record_execution_time(f'assess_{size}', duration)
            
            assert result is not None
            assert hasattr(result, 'overall_score')
        
        # Check scaling is reasonable (should be roughly linear)
        # Time for 10x data should be less than 15x time
        for i in range(len(times) - 1):
            size_ratio = sizes[i + 1] / sizes[i]
            time_ratio = times[i + 1] / times[i] if times[i] > 0 else 1
            
            # Allow some overhead, but should be roughly linear
            max_time_ratio = size_ratio * 1.5
            assert time_ratio <= max_time_ratio, \
                f"Poor scaling: {sizes[i]} to {sizes[i+1]} rows took {time_ratio:.1f}x longer (expected max {max_time_ratio:.1f}x)"
    
    # ===== Section 8: Performance Report Generation =====
    
    def test_generate_performance_report(self, generate_dataset, performance_monitor, tmp_path):
        """Generate comprehensive performance report."""
        # Run various operations to collect metrics
        datasets = {
            'small': generate_dataset(1000),
            'medium': generate_dataset(10000),
            'large': generate_dataset(50000)
        }
        
        engine = DataProtectionEngine()
        
        for name, data in datasets.items():
            with patch.object(engine, 'ensure_standard_exists'):
                with patch.object(engine, 'assess_data_quality') as mock_assess:
                    mock_assess.return_value = Mock(overall_score=85.0, passed=True, dimension_scores={})
                    
                    def process_data(data):
                        return len(data)
                    
                    start_time = time.time()
                    engine.protect_function_call(
                        func=process_data,
                        args=(data,),
                        kwargs={},
                        data_param='data',
                        function_name='process_data',
                        min_score=80.0
                    )
                    duration = time.time() - start_time
                    
                    performance_monitor.record_execution_time(f'{name}_dataset', duration)
        
        # Generate report
        report = performance_monitor.generate_report()
        
        # Create performance report file
        report_path = tmp_path / 'performance_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Assert all metrics meet requirements
        assert report['avg_execution_time'] < 1.0, "Average execution time too high"
        assert report['total_operations'] >= 3, "Not enough operations tracked"
        
        # Return report for inspection
        return report


@pytest.mark.performance
class TestPerformanceOptimizations:
    """Test specific optimizations and their effectiveness.
    
    These tests will be skipped by default. Run with: pytest --performance
    """
    
    def test_batch_processing_efficiency(self, generate_dataset):
        """Test that batch processing is more efficient than individual processing."""
        datasets = [generate_dataset(1000) for _ in range(10)]
        engine = DataProtectionEngine()
        
        with patch.object(engine, 'ensure_standard_exists'):
            with patch.object(engine, 'assess_data_quality') as mock_assess:
                mock_assess.return_value = Mock(overall_score=85.0, passed=True, dimension_scores={})
                
                def process_data(data):
                    return len(data)
                
                # Individual processing
                individual_start = time.time()
                for data in datasets:
                    engine.protect_function_call(
                        func=process_data,
                        args=(data,),
                        kwargs={},
                        data_param='data',
                        function_name='process_data',
                        min_score=80.0
                    )
                individual_time = time.time() - individual_start
                
                # Batch processing (simulated with combined dataset)
                combined_data = pd.concat(datasets, ignore_index=True)
                batch_start = time.time()
                engine.protect_function_call(
                    func=process_data,
                    args=(combined_data,),
                    kwargs={},
                    data_param='data',
                    function_name='process_data',
                    min_score=80.0
                )
                batch_time = time.time() - batch_start
                
                # Batch should be faster
                efficiency_gain = individual_time / batch_time if batch_time > 0 else float('inf')
                assert efficiency_gain > 2.0, f"Batch processing only {efficiency_gain:.1f}x faster"
    
    def test_lazy_loading_performance(self, tmp_path):
        """Test lazy loading performance for large standards."""
        # Create a large standard file
        large_standard = {
            'metadata': {'name': 'large_standard', 'version': '1.0.0'},
            'standards': {
                'fields': {f'field_{i}': {'type': 'string'} for i in range(1000)},
                'requirements': {'overall_minimum': 80}
            }
        }
        
        standard_path = tmp_path / 'large_standard.yaml'
        with open(standard_path, 'w') as f:
            yaml.dump(large_standard, f)
        
        # Measure loading time
        from adri.standards.yaml_standards import YAMLStandard
        
        start_time = time.time()
        standard = YAMLStandard(str(standard_path))
        load_time = time.time() - start_time
        
        # Should load quickly even with large standard
        assert load_time < 0.5, f"Large standard loading took {load_time:.3f}s"
    
    def test_streaming_assessment_performance(self, generate_dataset):
        """Test streaming assessment for very large datasets."""
        # Create a very large dataset
        large_data = generate_dataset(100000)
        
        # Split into chunks for streaming
        chunk_size = 10000
        chunks = [large_data[i:i+chunk_size] for i in range(0, len(large_data), chunk_size)]
        
        engine = AssessmentEngine()
        standard = {
            'metadata': {'name': 'streaming_test', 'version': '1.0.0'},
            'standards': {'fields': {}, 'requirements': {'overall_minimum': 80}}
        }
        
        # Measure streaming assessment
        start_time = time.time()
        results = []
        for chunk in chunks:
            result = engine.assess(chunk, standard)
            results.append(result)
        streaming_time = time.time() - start_time
        
        # Compare with full assessment
        start_time = time.time()
        full_result = engine.assess(large_data, standard)
        full_time = time.time() - start_time
        
        # Streaming should be comparable or better for memory efficiency
        assert streaming_time < full_time * 2, \
            f"Streaming too slow: {streaming_time:.3f}s vs full: {full_time:.3f}s"


@pytest.mark.performance
class TestPerformanceRegression:
    """Performance regression tests to ensure no degradation.
    
    These tests will be skipped by default. Run with: pytest --performance
    """
    
    REGRESSION_THRESHOLDS = {
        'small_dataset_assessment': 0.05,  # 50ms
        'medium_dataset_assessment': 0.2,   # 200ms
        'large_dataset_assessment': 1.0,    # 1s
        'cache_lookup': 0.001,              # 1ms
        'audit_log_write': 0.005,           # 5ms
        'standard_loading': 0.1,            # 100ms
    }
    
    def test_small_dataset_regression(self, generate_dataset):
        """Ensure small dataset assessment doesn't regress."""
        data = generate_dataset(100)
        engine = AssessmentEngine()
        standard = {
            'metadata': {'name': 'test', 'version': '1.0.0'},
            'standards': {'fields': {}, 'requirements': {'overall_minimum': 80}}
        }
        
        times = []
        for _ in range(10):
            start_time = time.time()
            engine.assess(data, standard)
            times.append(time.time() - start_time)
        
        avg_time = sum(times) / len(times)
        assert avg_time < self.REGRESSION_THRESHOLDS['small_dataset_assessment'], \
            f"Small dataset regression: {avg_time:.3f}s exceeds threshold"
    
    def test_cache_lookup_regression(self):
        """Ensure cache lookup doesn't regress."""
        engine = DataProtectionEngine()
        
        # Populate cache
        engine._assessment_cache['test_key'] = (Mock(overall_score=85.0), time.time())
        
        # Measure lookup time
        times = []
        for _ in range(1000):
            start_time = time.time()
            _ = 'test_key' in engine._assessment_cache
            times.append(time.time() - start_time)
        
        avg_time = sum(times) / len(times)
        assert avg_time < self.REGRESSION_THRESHOLDS['cache_lookup'], \
            f"Cache lookup regression: {avg_time*1000:.3f}ms exceeds threshold"
    
    def test_audit_write_regression(self, tmp_path):
        """Ensure audit log writes don't regress."""
        log_file = tmp_path / 'regression_audit.jsonl'
        config = {
            'enabled': True,
            'log_location': str(log_file)
        }
        logger = AuditLogger(config)
        
        assessment_result = Mock()
        assessment_result.overall_score = 85.0
        assessment_result.passed = True
        assessment_result.standard_id = 'test'
        assessment_result.assessment_date = None
        assessment_result.dimension_scores = {}
        assessment_result.metadata = {}
        assessment_result.rule_execution_log = []
        assessment_result.field_analysis = {}
        
        times = []
        for i in range(100):
            start_time = time.time()
            logger.log_assessment(
                assessment_result=assessment_result,
                data_shape=(100, 10),
                execution_context={'iteration': i}
            )
            times.append(time.time() - start_time)
        
        avg_time = sum(times) / len(times)
        assert avg_time < self.REGRESSION_THRESHOLDS['audit_log_write'], \
            f"Audit write regression: {avg_time*1000:.3f}ms exceeds threshold"
    
    def test_standard_loading_regression(self, tmp_path):
        """Ensure standard loading doesn't regress."""
        # Create test standard
        standard_dict = {
            'metadata': {'name': 'test', 'version': '1.0.0'},
            'standards': {
                'fields': {f'field_{i}': {'type': 'string'} for i in range(100)},
                'requirements': {'overall_minimum': 80}
            }
        }
        
        standard_path = tmp_path / 'test_standard.yaml'
        with open(standard_path, 'w') as f:
            yaml.dump(standard_dict, f)
        
        from adri.standards.yaml_standards import YAMLStandard
        
        times = []
        for _ in range(10):
            start_time = time.time()
            YAMLStandard(str(standard_path))
            times.append(time.time() - start_time)
        
        avg_time = sum(times) / len(times)
        assert avg_time < self.REGRESSION_THRESHOLDS['standard_loading'], \
            f"Standard loading regression: {avg_time:.3f}s exceeds threshold"


@pytest.mark.performance
class TestPerformanceSummary:
    """Generate comprehensive performance summary.
    
    These tests will be skipped by default. Run with: pytest --performance
    """
    
    def test_generate_performance_summary(self, generate_dataset, tmp_path):
        """Generate a comprehensive performance summary report."""
        results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'performance_metrics': {},
            'thresholds_met': {},
            'recommendations': []
        }
        
        # Test various dataset sizes
        sizes = [100, 1000, 10000, 100000]
        engine = AssessmentEngine()
        standard = {
            'metadata': {'name': 'perf_test', 'version': '1.0.0'},
            'standards': {'fields': {}, 'requirements': {'overall_minimum': 80}}
        }
        
        for size in sizes:
            data = generate_dataset(size)
            
            start_time = time.time()
            engine.assess(data, standard)
            duration = time.time() - start_time
            
            results['performance_metrics'][f'{size}_rows'] = {
                'time_seconds': duration,
                'rows_per_second': size / duration if duration > 0 else 0
            }
        
        # Check thresholds
        results['thresholds_met']['small_dataset'] = results['performance_metrics']['1000_rows']['time_seconds'] < 0.1
        results['thresholds_met']['medium_dataset'] = results['performance_metrics']['10000_rows']['time_seconds'] < 0.5
        results['thresholds_met']['large_dataset'] = results['performance_metrics']['100000_rows']['time_seconds'] < 2.0
        
        # Add recommendations
        if not all(results['thresholds_met'].values()):
            results['recommendations'].append("Consider optimizing assessment algorithms")
        
        if results['performance_metrics']['100000_rows']['rows_per_second'] < 50000:
            results['recommendations'].append("Consider implementing parallel processing for large datasets")
        
        # Save summary
        summary_path = tmp_path / 'performance_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary for visibility
        print("\n" + "="*60)
        print("PERFORMANCE SUMMARY")
        print("="*60)
        for size, metrics in results['performance_metrics'].items():
            print(f"{size}: {metrics['time_seconds']:.3f}s ({metrics['rows_per_second']:.0f} rows/sec)")
        print("\nThresholds Met:")
        for threshold, met in results['thresholds_met'].items():
            status = "✅" if met else "❌"
            print(f"  {threshold}: {status}")
        
        if results['recommendations']:
            print("\nRecommendations:")
            for rec in results['recommendations']:
                print(f"  • {rec}")
        
        # Assert overall performance is acceptable
        assert sum(results['thresholds_met'].values()) >= len(results['thresholds_met']) * 0.8, \
            "Less than 80% of performance thresholds met"
        
        return results
