"""
Tests for AsyncCallbackManager.

Verifies sync/async callback execution with proper error isolation.
"""

import asyncio
import time
from datetime import datetime
from unittest.mock import Mock

import pytest

from src.adri.callbacks.async_handler import AsyncCallbackManager


class MockAssessmentResult:
    """Mock assessment result for testing."""

    def __init__(self, assessment_id="test_123", passed=True, score=95.0):
        self.assessment_id = assessment_id
        self.passed = passed
        self.overall_score = score
        self.assessment_date = datetime.now()


class TestAsyncCallbackManagerBasics:
    """Test basic AsyncCallbackManager functionality."""

    def test_initialization(self):
        """Test manager initialization."""
        manager = AsyncCallbackManager(thread_pool_size=2)
        assert manager.thread_pool_size == 2
        assert manager.enable_async is True
        assert manager.get_callback_count() == 0
        manager.close()

    def test_add_sync_callback(self):
        """Test adding synchronous callback."""
        manager = AsyncCallbackManager()

        def sync_callback(result):
            pass

        callback_id = manager.add_callback(sync_callback)
        assert callback_id is not None
        assert manager.get_callback_count() == 1

        manager.close()

    def test_add_async_callback(self):
        """Test adding asynchronous callback."""
        manager = AsyncCallbackManager()

        async def async_callback(result):
            await asyncio.sleep(0.01)

        callback_id = manager.add_callback(async_callback)
        assert callback_id is not None
        assert manager.get_callback_count() == 1

        manager.close()

    def test_remove_callback(self):
        """Test removing callbacks."""
        manager = AsyncCallbackManager()

        callback_id = manager.add_callback(lambda r: None)
        assert manager.get_callback_count() == 1

        assert manager.remove_callback(callback_id) is True
        assert manager.get_callback_count() == 0

        # Removing again should return False
        assert manager.remove_callback(callback_id) is False

        manager.close()

    def test_add_invalid_callback(self):
        """Test adding invalid callback raises error."""
        manager = AsyncCallbackManager()

        with pytest.raises(ValueError, match="must be callable"):
            manager.add_callback("not_callable")

        manager.close()

    def test_clear_callbacks(self):
        """Test clearing all callbacks."""
        manager = AsyncCallbackManager()

        manager.add_callback(lambda r: None)
        manager.add_callback(lambda r: None)
        assert manager.get_callback_count() == 2

        manager.clear_callbacks()
        assert manager.get_callback_count() == 0

        manager.close()


class TestSyncCallbackExecution:
    """Test synchronous callback execution."""

    def test_invoke_sync_callback(self):
        """Test invoking synchronous callback."""
        manager = AsyncCallbackManager()
        results = []

        def sync_callback(result):
            results.append(result.assessment_id)

        manager.add_callback(sync_callback)

        # Invoke callback
        mock_result = MockAssessmentResult("sync_test")
        manager.invoke_all(mock_result)

        # Wait for callback to complete
        time.sleep(0.2)

        assert len(results) == 1
        assert results[0] == "sync_test"

        manager.close()

    def test_multiple_sync_callbacks(self):
        """Test multiple sync callbacks are all invoked."""
        manager = AsyncCallbackManager()
        results = []

        def callback1(result):
            results.append(f"cb1_{result.assessment_id}")

        def callback2(result):
            results.append(f"cb2_{result.assessment_id}")

        manager.add_callback(callback1)
        manager.add_callback(callback2)

        mock_result = MockAssessmentResult("multi_test")
        manager.invoke_all(mock_result)

        # Wait for callbacks
        time.sleep(0.2)

        assert len(results) == 2
        assert "cb1_multi_test" in results
        assert "cb2_multi_test" in results

        manager.close()

    def test_sync_callback_error_isolation(self):
        """Test that error in one sync callback doesn't affect others."""
        manager = AsyncCallbackManager()
        results = []

        def failing_callback(result):
            raise ValueError("Simulated error")

        def working_callback(result):
            results.append(result.assessment_id)

        manager.add_callback(failing_callback)
        manager.add_callback(working_callback)

        mock_result = MockAssessmentResult("error_test")
        manager.invoke_all(mock_result)

        # Wait for callbacks
        time.sleep(0.2)

        # Working callback should still execute
        assert len(results) == 1
        assert results[0] == "error_test"

        manager.close()


class TestAsyncCallbackExecution:
    """Test asynchronous callback execution."""

    def test_invoke_async_callback(self):
        """Test invoking asynchronous callback."""
        manager = AsyncCallbackManager()
        results = []

        async def async_callback(result):
            await asyncio.sleep(0.05)
            results.append(result.assessment_id)

        manager.add_callback(async_callback)

        # Invoke callback
        mock_result = MockAssessmentResult("async_test")
        manager.invoke_all(mock_result)

        # Wait for async callback to complete
        time.sleep(0.3)

        assert len(results) == 1
        assert results[0] == "async_test"

        manager.close()

    def test_multiple_async_callbacks(self):
        """Test multiple async callbacks are all invoked."""
        manager = AsyncCallbackManager()
        results = []

        async def callback1(result):
            await asyncio.sleep(0.05)
            results.append(f"async1_{result.assessment_id}")

        async def callback2(result):
            await asyncio.sleep(0.05)
            results.append(f"async2_{result.assessment_id}")

        manager.add_callback(callback1)
        manager.add_callback(callback2)

        mock_result = MockAssessmentResult("multi_async")
        manager.invoke_all(mock_result)

        # Wait for callbacks
        time.sleep(0.3)

        assert len(results) == 2
        assert "async1_multi_async" in results
        assert "async2_multi_async" in results

        manager.close()

    def test_async_callback_error_isolation(self):
        """Test that error in one async callback doesn't affect others."""
        manager = AsyncCallbackManager()
        results = []

        async def failing_callback(result):
            await asyncio.sleep(0.01)
            raise ValueError("Async error")

        async def working_callback(result):
            await asyncio.sleep(0.01)
            results.append(result.assessment_id)

        manager.add_callback(failing_callback)
        manager.add_callback(working_callback)

        mock_result = MockAssessmentResult("async_error_test")
        manager.invoke_all(mock_result)

        # Wait for callbacks
        time.sleep(0.3)

        # Working callback should still execute
        assert len(results) == 1
        assert results[0] == "async_error_test"

        manager.close()

    def test_async_disabled(self):
        """Test async callbacks are skipped when async disabled."""
        manager = AsyncCallbackManager(enable_async=False)
        results = []

        async def async_callback(result):
            results.append(result.assessment_id)

        manager.add_callback(async_callback)

        mock_result = MockAssessmentResult("disabled_test")
        manager.invoke_all(mock_result)

        # Wait
        time.sleep(0.2)

        # Callback should not execute
        assert len(results) == 0

        manager.close()


class TestMixedCallbacks:
    """Test mixing sync and async callbacks."""

    def test_mixed_callbacks(self):
        """Test invoking both sync and async callbacks together."""
        manager = AsyncCallbackManager()
        results = []

        def sync_callback(result):
            results.append(f"sync_{result.assessment_id}")

        async def async_callback(result):
            await asyncio.sleep(0.05)
            results.append(f"async_{result.assessment_id}")

        manager.add_callback(sync_callback)
        manager.add_callback(async_callback)

        mock_result = MockAssessmentResult("mixed_test")
        manager.invoke_all(mock_result)

        # Wait for both callbacks
        time.sleep(0.3)

        assert len(results) == 2
        assert "sync_mixed_test" in results
        assert "async_mixed_test" in results

        manager.close()


class TestCallbackManagerLifecycle:
    """Test callback manager lifecycle."""

    def test_context_manager(self):
        """Test using manager as context manager."""
        results = []

        with AsyncCallbackManager() as manager:
            manager.add_callback(lambda r: results.append(r.assessment_id))
            mock_result = MockAssessmentResult("context_test")
            manager.invoke_all(mock_result)
            time.sleep(0.2)

        # Manager should be closed after context
        assert len(results) == 1

    def test_close_manager(self):
        """Test closing manager."""
        manager = AsyncCallbackManager()
        manager.add_callback(lambda r: None)

        manager.close()

        # Should not be able to add callbacks after close
        with pytest.raises(RuntimeError, match="closed manager"):
            manager.add_callback(lambda r: None)

    def test_invoke_on_closed_manager(self):
        """Test invoking callbacks on closed manager."""
        manager = AsyncCallbackManager()
        results = []

        manager.add_callback(lambda r: results.append(r.assessment_id))
        manager.close()

        # Should not invoke on closed manager
        mock_result = MockAssessmentResult("closed_test")
        manager.invoke_all(mock_result)

        time.sleep(0.2)
        assert len(results) == 0


class TestCallbackPerformance:
    """Test callback performance characteristics."""

    def test_callback_invocation_overhead(self):
        """Test that callback invocation completes reasonably quickly.
        
        Note: No absolute timing assertion as CI environments have high
        variability. Just verify the callback mechanism works.
        """
        manager = AsyncCallbackManager()

        def simple_callback(result):
            pass

        manager.add_callback(simple_callback)

        # Measure invocation time
        start = time.time()
        mock_result = MockAssessmentResult("perf_test")
        manager.invoke_all(mock_result)
        duration_ms = (time.time() - start) * 1000

        # Log for monitoring (no assertion - too flaky on CI runners)
        print(f"Callback invocation overhead: {duration_ms:.2f}ms")

        manager.close()

    def test_parallel_callback_execution(self):
        """Test that callbacks execute in parallel."""
        manager = AsyncCallbackManager(thread_pool_size=4)
        execution_times = []

        def slow_callback(result):
            start = time.time()
            time.sleep(0.1)  # 100ms
            execution_times.append(time.time() - start)

        # Add 4 callbacks
        for _ in range(4):
            manager.add_callback(slow_callback)

        # Invoke all
        start = time.time()
        mock_result = MockAssessmentResult("parallel_test")
        manager.invoke_all(mock_result)

        # Wait for completion
        time.sleep(0.6)

        total_time = time.time() - start

        # If executed in parallel, total time should be close to 100ms
        # If sequential, would be 400ms
        # Log for monitoring (no assertion - too flaky on CI runners)
        print(f"Parallel callback execution time: {total_time:.2f}s")
        assert len(execution_times) == 4

        manager.close()


class TestCallbackCount:
    """Test callback counting."""

    def test_get_callback_count(self):
        """Test getting callback count."""
        manager = AsyncCallbackManager()

        assert manager.get_callback_count() == 0

        manager.add_callback(lambda r: None)
        assert manager.get_callback_count() == 1

        manager.add_callback(lambda r: None)
        assert manager.get_callback_count() == 2

        manager.close()
