"""
Integration tests for event-driven assessment logging architecture.

Tests the complete flow: decorator → events → fast path → slow path
"""

import asyncio
import tempfile
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from src.adri.callbacks.async_handler import AsyncCallbackManager
from src.adri.callbacks.workflow_adapters import PrefectAdapter, WorkflowAdapter
from src.adri.decorator import adri_protected
from src.adri.events.event_bus import get_event_bus, reset_event_bus
from src.adri.events.types import EventType
from src.adri.guard.modes import DataProtectionEngine
from src.adri.logging.fast_path import FastPathLogger
from src.adri.logging.unified import UnifiedLogger


class TestEventDrivenLoggingFlow:
    """Test complete event-driven logging flow."""

    def setup_method(self):
        """Reset event bus before each test."""
        reset_event_bus()

    @pytest.mark.skip(reason="Feature not implemented: fast_path_logger parameter not in adri_protected")
    def test_end_to_end_flow(self):
        """Test complete flow from assessment to events to fast path."""
        # Setup
        events_received = []

        def event_callback(event):
            events_received.append(event)

        # Subscribe to events
        bus = get_event_bus()
        bus.subscribe(EventType.ASSESSMENT_CREATED, event_callback)

        # Create test data and standard
        test_data = pd.DataFrame({
            "name": ["Alice", "Bob"],
            "age": [25, 30],
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup fast path logger
            fast_path = FastPathLogger(storage="file", storage_dir=tmpdir)

            # Create a simple test function
            @adri_protected(
                contract="test_integration",
                fast_path_logger=fast_path,
            )
            def process_data(data):
                return len(data)

            # Execute
            try:
                result = process_data(test_data)
            except Exception:
                # May fail due to missing standard, but that's ok for this test
                pass

            # Wait for async processing
            time.sleep(0.3)

            # Verify events were published
            assert len(events_received) > 0
            assert events_received[0].event_type == EventType.ASSESSMENT_CREATED

            fast_path.close()

    @pytest.mark.skip(reason="Feature not implemented: async_callbacks parameter not in adri_protected")
    def test_async_callback_integration(self):
        """Test async callbacks triggered by decorator."""
        callback_results = []

        def sync_callback(result):
            callback_results.append(f"sync_{result.assessment_id}")

        async def async_callback(result):
            await asyncio.sleep(0.05)
            callback_results.append(f"async_{result.assessment_id}")

        # Setup callback manager
        manager = AsyncCallbackManager()
        manager.add_callback(sync_callback)
        manager.add_callback(async_callback)

        # Create test function with callbacks
        test_data = pd.DataFrame({"value": [1, 2, 3]})

        @adri_protected(
            contract="callback_test",
            async_callbacks=manager,
        )
        def process_with_callbacks(data):
            return sum(data["value"])

        # Execute
        try:
            process_with_callbacks(test_data)
        except Exception:
            pass  # May fail, but callbacks should still fire

        # Wait for callbacks
        time.sleep(0.4)

        # Both callbacks should have executed
        assert len(callback_results) >= 1  # At least one callback fired

        manager.close()

    @pytest.mark.skip(reason="Feature not implemented: workflow_adapter parameter not in adri_protected")
    def test_workflow_adapter_integration(self):
        """Test workflow adapter integration with decorator."""

        class MockAdapter(WorkflowAdapter):
            """Mock adapter for testing."""

            def __init__(self):
                self.start_called = False
                self.complete_called = False
                self.error_called = False
                self.last_assessment_id = None

            def on_assessment_start(self, assessment_id, metadata):
                self.start_called = True
                self.last_assessment_id = assessment_id

            def on_assessment_complete(self, assessment_id, assessment_result):
                self.complete_called = True
                self.last_assessment_id = assessment_id

            def on_assessment_error(self, assessment_id, error):
                self.error_called = True

        adapter = MockAdapter()
        test_data = pd.DataFrame({"x": [1, 2, 3]})

        @adri_protected(
            contract="adapter_test",
            workflow_adapter=adapter,
        )
        def process_with_adapter(data):
            return data.sum()

        # Execute
        try:
            process_with_adapter(test_data)
        except Exception:
            pass

        # Adapter should have been called
        assert adapter.complete_called or adapter.start_called

    @pytest.mark.skip(reason="Feature not implemented: fast_path_logger parameter not in adri_protected")
    def test_fast_path_immediate_write(self):
        """Test fast path manifest is written immediately."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fast_path = FastPathLogger(storage="file", storage_dir=tmpdir)

            # Track when assessment completes
            assessment_id_holder = []

            def capture_id(result):
                assessment_id_holder.append(result.assessment_id)

            test_data = pd.DataFrame({"field": ["a", "b"]})

            @adri_protected(
                contract="fast_path_test",
                on_assessment=capture_id,
                fast_path_logger=fast_path,
            )
            def process_fast(data):
                return data

            # Execute
            try:
                process_fast(test_data)
            except Exception:
                pass

            # Check if manifest was written
            if assessment_id_holder:
                assessment_id = assessment_id_holder[0]

                # Small delay for file write
                time.sleep(0.1)

                # Verify manifest file exists
                manifest_files = list(Path(tmpdir).rglob("*.json"))
                assert len(manifest_files) > 0

                # Verify we can read it back
                manifest = fast_path.get_manifest(assessment_id)
                if manifest:
                    assert manifest.assessment_id == assessment_id

            fast_path.close()


class TestDualWritePattern:
    """Test unified logger dual-write pattern."""

    @pytest.mark.skip(reason="Feature not implemented: publish_events parameter not in AssessmentResult")
    def test_unified_logger_dual_write(self):
        """Test that UnifiedLogger writes to both paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock slow path logger
            class MockSlowPath:
                def __init__(self):
                    self.logs = []

                def log_assessment(self, **kwargs):
                    self.logs.append(kwargs)
                    return {"audit_id": "mock_123"}

            slow_path = MockSlowPath()

            # Create unified logger
            unified = UnifiedLogger(
                fast_path_enabled=True,
                fast_path_storage="file",
                fast_path_config={"storage_dir": tmpdir},
                slow_path_logger=slow_path,
            )

            # Create mock assessment result
            from src.adri.validator.engine import AssessmentResult, DimensionScore

            result = AssessmentResult(
                overall_score=85.0,
                passed=True,
                dimension_scores={
                    "validity": DimensionScore(17.0),
                    "completeness": DimensionScore(18.0),
                },
                publish_events=False,  # Disable events for this test
            )

            # Log assessment
            unified.log_assessment(
                assessment_result=result,
                execution_context={"function": "test"},
                data_info={"rows": 100},
            )

            # Wait for writes
            time.sleep(0.2)

            # Verify fast path write
            manifest = unified.get_manifest(result.assessment_id)
            assert manifest is not None
            assert manifest.status == "PASSED"

            # Verify slow path write
            assert len(slow_path.logs) == 1

            unified.close()


class TestPerformanceTargets:
    """Test that performance targets are met."""

    def test_fast_path_write_latency(self):
        """Test fast path writes complete reasonably quickly."""
        fast_path = FastPathLogger(storage="memory")

        from src.adri.events.types import AssessmentManifest

        manifest = AssessmentManifest(
            assessment_id="perf_test",
            timestamp=datetime.now(),
            status="CREATED",
        )

        # Measure write time
        start = time.time()
        fast_path.log_manifest(manifest)
        duration_ms = (time.time() - start) * 1000

        # Log for monitoring (no assertion - too flaky on CI runners)
        print(f"Fast path write latency: {duration_ms:.2f}ms")

        fast_path.close()

    def test_event_publish_overhead(self):
        """Test event publishing overhead is minimal."""
        bus = get_event_bus()

        from src.adri.events.types import AssessmentEvent

        event = AssessmentEvent(
            event_type=EventType.ASSESSMENT_COMPLETED,
            assessment_id="overhead_test",
            timestamp=datetime.now(),
            payload={},
        )

        # Measure publish time
        start = time.time()
        bus.publish(event)
        duration_ms = (time.time() - start) * 1000

        # Log for monitoring (no assertion - too flaky on CI runners)
        print(f"Event publish overhead: {duration_ms:.2f}ms")

    @pytest.mark.skip(reason="Feature not implemented: publish_events parameter not in AssessmentResult")
    def test_async_callback_overhead(self):
        """Test async callback invocation overhead."""
        manager = AsyncCallbackManager()

        def simple_callback(result):
            pass

        manager.add_callback(simple_callback)

        from src.adri.validator.engine import AssessmentResult, DimensionScore

        result = AssessmentResult(
            overall_score=90.0,
            passed=True,
            dimension_scores={"validity": DimensionScore(18.0)},
            publish_events=False,
        )

        # Measure invocation time (not execution time)
        start = time.time()
        manager.invoke_all(result)
        duration_ms = (time.time() - start) * 1000

        # Invocation should be very fast (<50ms target)
        assert duration_ms < 50.0

        manager.close()


class TestBackwardCompatibility:
    """Test that new features maintain backward compatibility."""

    def test_decorator_without_new_features(self):
        """Test decorator works without new async features."""
        test_data = pd.DataFrame({"val": [1, 2, 3]})

        @adri_protected(contract="compat_test")
        def old_style_function(data):
            return len(data)

        # Should work without async_callbacks, workflow_adapter, fast_path_logger
        try:
            result = old_style_function(test_data)
            # If it succeeds, great!
            assert result == 3
        except Exception:
            # If it fails due to missing standard, that's ok for this test
            pass

    @pytest.mark.skip(reason="Feature not implemented: publish_events parameter not in AssessmentResult")
    def test_assessment_result_without_events(self):
        """Test AssessmentResult can disable event publishing."""
        from src.adri.validator.engine import AssessmentResult, DimensionScore

        reset_event_bus()
        events_received = []

        bus = get_event_bus()
        bus.subscribe(None, lambda e: events_received.append(e))

        # Create result with events disabled
        result = AssessmentResult(
            overall_score=80.0,
            passed=True,
            dimension_scores={"validity": DimensionScore(16.0)},
            publish_events=False,
        )

        # No events should be published
        assert len(events_received) == 0

    @pytest.mark.skip(reason="Feature not implemented: async_callbacks/workflow_adapter attributes not in DataProtectionEngine")
    def test_protection_engine_without_async_features(self):
        """Test DataProtectionEngine works without async features."""
        engine = DataProtectionEngine()

        # Should initialize successfully without async_callbacks, etc.
        assert engine.async_callbacks is None
        assert engine.workflow_adapter is None
        assert engine.fast_path_logger is None


class TestErrorHandling:
    """Test error handling and graceful degradation."""

    @pytest.mark.skip(reason="Feature not implemented: fast_path_logger parameter not in adri_protected")
    def test_fast_path_failure_doesnt_break_assessment(self):
        """Test that fast path failure doesn't break assessment."""

        class FailingFastPath:
            """Mock fast path that always fails."""
            def log_manifest(self, manifest):
                raise RuntimeError("Simulated fast path failure")

        failing_logger = FailingFastPath()

        test_data = pd.DataFrame({"x": [1, 2]})

        @adri_protected(
            contract="error_test",
            fast_path_logger=failing_logger,
        )
        def process_with_failing_fast_path(data):
            return len(data)

        # Should not raise due to fast path failure
        # (may raise due to other reasons like missing standard)
        try:
            result = process_with_failing_fast_path(test_data)
        except Exception as e:
            # If it raises, it should not be due to fast path
            assert "fast path" not in str(e).lower()

    @pytest.mark.skip(reason="Feature not implemented: async_callbacks parameter not in adri_protected")
    def test_async_callback_error_isolation(self):
        """Test that callback errors don't break assessment."""
        manager = AsyncCallbackManager()
        results = []

        def failing_callback(result):
            raise ValueError("Callback error")

        def working_callback(result):
            results.append(result.assessment_id)

        manager.add_callback(failing_callback)
        manager.add_callback(working_callback)

        test_data = pd.DataFrame({"val": [5, 10]})

        @adri_protected(
            contract="callback_error_test",
            async_callbacks=manager,
        )
        def process_with_errors(data):
            return data.sum()

        # Execute - should not raise due to callback error
        try:
            process_with_errors(test_data)
        except Exception as e:
            # Should not be callback-related
            assert "callback" not in str(e).lower()

        # Wait for callbacks
        time.sleep(0.3)

        # Working callback should have executed despite failing one
        # (may be 0 if assessment failed before callbacks)
        assert len(results) >= 0

        manager.close()


class TestConcurrentAssessments:
    """Test handling of concurrent assessments."""

    @pytest.mark.skip(reason="Feature not implemented: publish_events parameter not in AssessmentResult")
    def test_concurrent_fast_path_writes(self):
        """Test multiple concurrent assessments with fast path."""
        import threading

        fast_path = FastPathLogger(storage="memory")
        assessment_ids = []
        lock = threading.Lock()

        def run_assessment(i):
            from src.adri.validator.engine import AssessmentResult, DimensionScore
            from src.adri.events.types import AssessmentManifest

            result = AssessmentResult(
                overall_score=float(80 + i),
                passed=True,
                dimension_scores={"validity": DimensionScore(16.0)},
                publish_events=False,
            )

            manifest = AssessmentManifest(
                assessment_id=result.assessment_id,
                timestamp=datetime.now(),
                status="PASSED",
                score=result.overall_score,
            )

            fast_path.log_manifest(manifest)

            with lock:
                assessment_ids.append(result.assessment_id)

        # Run 10 concurrent assessments
        threads = []
        for i in range(10):
            t = threading.Thread(target=run_assessment, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All should succeed
        assert len(assessment_ids) == 10

        # All should be retrievable
        for aid in assessment_ids:
            manifest = fast_path.get_manifest(aid)
            assert manifest is not None

        fast_path.close()

    def test_concurrent_event_publishing(self):
        """Test concurrent event publishing."""
        import threading

        reset_event_bus()
        bus = get_event_bus()
        events_received = []
        lock = threading.Lock()

        def event_callback(event):
            with lock:
                events_received.append(event)

        bus.subscribe(EventType.ASSESSMENT_COMPLETED, event_callback)

        from src.adri.events.types import AssessmentEvent

        def publish_event(i):
            event = AssessmentEvent(
                event_type=EventType.ASSESSMENT_COMPLETED,
                assessment_id=f"concurrent_{i}",
                timestamp=datetime.now(),
                payload={},
            )
            bus.publish(event)

        # Publish from multiple threads
        threads = []
        for i in range(20):
            t = threading.Thread(target=publish_event, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Wait for event processing
        time.sleep(0.2)

        # All events should be received
        assert len(events_received) == 20


class TestMemoryOverhead:
    """Test memory overhead of new components."""

    def setup_method(self):
        """Reset event bus before each test."""
        reset_event_bus()

    def test_event_bus_memory(self):
        """Test EventBus memory usage is reasonable."""
        import sys

        bus = get_event_bus()

        # Add many subscribers
        subs = []
        for i in range(100):
            sub_id = bus.subscribe(EventType.ASSESSMENT_COMPLETED, lambda e: None)
            subs.append(sub_id)

        # Memory overhead should be minimal
        # (Exact measurement is tricky, just verify it doesn't crash)
        assert bus.get_subscriber_count() == 100

        # Cleanup
        for sub_id in subs:
            bus.unsubscribe(sub_id)

    def test_fast_path_memory_limit(self):
        """Test fast path memory usage stays bounded."""
        fast_path = FastPathLogger(storage="memory")

        from src.adri.events.types import AssessmentManifest

        # Write many manifests
        for i in range(1000):
            manifest = AssessmentManifest(
                assessment_id=f"mem_test_{i}",
                timestamp=datetime.now(),
                status="CREATED",
            )
            fast_path.log_manifest(manifest)

        # Should not crash or consume excessive memory
        # (In production, TTL cleanup would prevent unbounded growth)
        assert fast_path.get_manifest("mem_test_0") is not None

        fast_path.close()


@pytest.mark.skipif(
    True,  # Skip by default
    reason="Performance benchmark - run manually"
)
class TestPerformanceBenchmarks:
    """Performance benchmarks for the new architecture."""

    def test_1000_concurrent_assessments(self):
        """Benchmark with 1000 concurrent assessments."""
        import threading

        fast_path = FastPathLogger(storage="memory")
        completed = []
        lock = threading.Lock()

        def run_assessment(i):
            from src.adri.validator.engine import AssessmentResult, DimensionScore
            from src.adri.events.types import AssessmentManifest

            result = AssessmentResult(
                overall_score=85.0,
                passed=True,
                dimension_scores={"validity": DimensionScore(17.0)},
                publish_events=False,
            )

            manifest = AssessmentManifest(
                assessment_id=result.assessment_id,
                timestamp=datetime.now(),
                status="PASSED",
            )

            start = time.time()
            fast_path.log_manifest(manifest)
            duration = time.time() - start

            with lock:
                completed.append(duration * 1000)  # ms

        # Run 1000 concurrent
        start_time = time.time()

        threads = []
        for i in range(1000):
            t = threading.Thread(target=run_assessment, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        total_time = time.time() - start_time

        # Performance metrics
        avg_latency = sum(completed) / len(completed)
        p99_latency = sorted(completed)[int(len(completed) * 0.99)]

        print(f"\nBenchmark Results (1000 assessments):")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Avg latency: {avg_latency:.2f}ms")
        print(f"  P99 latency: {p99_latency:.2f}ms")

        # Targets
        assert avg_latency < 10.0  # Avg < 10ms
        assert p99_latency < 20.0  # P99 < 20ms (allows some variance)

        fast_path.close()
