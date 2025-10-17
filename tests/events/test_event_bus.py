"""
Tests for EventBus pub/sub functionality.

Verifies thread-safe event publishing and subscription with proper error isolation.
"""

import threading
import time
from datetime import datetime
from unittest.mock import Mock

import pytest

from src.adri.events.event_bus import EventBus, get_event_bus, reset_event_bus
from src.adri.events.types import AssessmentEvent, EventType


class TestEventBusBasics:
    """Test basic EventBus functionality."""

    def setup_method(self):
        """Reset event bus before each test."""
        reset_event_bus()

    def test_subscribe_and_publish(self):
        """Test basic subscribe and publish flow."""
        bus = EventBus()
        received_events = []

        def callback(event):
            received_events.append(event)

        # Subscribe to ASSESSMENT_COMPLETED events
        sub_id = bus.subscribe(EventType.ASSESSMENT_COMPLETED, callback)
        assert sub_id is not None

        # Publish an event
        event = AssessmentEvent(
            event_type=EventType.ASSESSMENT_COMPLETED,
            assessment_id="test_123",
            timestamp=datetime.now(),
            payload={"score": 95.0},
        )
        bus.publish(event)

        # Verify callback was invoked
        assert len(received_events) == 1
        assert received_events[0].assessment_id == "test_123"
        assert received_events[0].payload["score"] == 95.0

    def test_multiple_subscribers(self):
        """Test multiple subscribers for same event type."""
        bus = EventBus()
        callback1_events = []
        callback2_events = []

        def callback1(event):
            callback1_events.append(event)

        def callback2(event):
            callback2_events.append(event)

        # Subscribe both callbacks
        bus.subscribe(EventType.ASSESSMENT_CREATED, callback1)
        bus.subscribe(EventType.ASSESSMENT_CREATED, callback2)

        # Publish event
        event = AssessmentEvent(
            event_type=EventType.ASSESSMENT_CREATED,
            assessment_id="test_456",
            timestamp=datetime.now(),
            payload={},
        )
        bus.publish(event)

        # Both callbacks should receive the event
        assert len(callback1_events) == 1
        assert len(callback2_events) == 1
        assert callback1_events[0].assessment_id == "test_456"
        assert callback2_events[0].assessment_id == "test_456"

    def test_unsubscribe(self):
        """Test unsubscribing from events."""
        bus = EventBus()
        received_events = []

        def callback(event):
            received_events.append(event)

        # Subscribe and then unsubscribe
        sub_id = bus.subscribe(EventType.ASSESSMENT_COMPLETED, callback)
        assert bus.unsubscribe(sub_id) is True

        # Publish event - should not be received
        event = AssessmentEvent(
            event_type=EventType.ASSESSMENT_COMPLETED,
            assessment_id="test_789",
            timestamp=datetime.now(),
            payload={},
        )
        bus.publish(event)

        assert len(received_events) == 0

    def test_unsubscribe_nonexistent(self):
        """Test unsubscribing with invalid ID."""
        bus = EventBus()
        assert bus.unsubscribe("invalid_id") is False

    def test_event_filtering(self):
        """Test that subscribers only receive subscribed event types."""
        bus = EventBus()
        created_events = []
        completed_events = []

        def created_callback(event):
            created_events.append(event)

        def completed_callback(event):
            completed_events.append(event)

        # Subscribe to different event types
        bus.subscribe(EventType.ASSESSMENT_CREATED, created_callback)
        bus.subscribe(EventType.ASSESSMENT_COMPLETED, completed_callback)

        # Publish CREATED event
        bus.publish(
            AssessmentEvent(
                event_type=EventType.ASSESSMENT_CREATED,
                assessment_id="created_1",
                timestamp=datetime.now(),
                payload={},
            )
        )

        # Publish COMPLETED event
        bus.publish(
            AssessmentEvent(
                event_type=EventType.ASSESSMENT_COMPLETED,
                assessment_id="completed_1",
                timestamp=datetime.now(),
                payload={},
            )
        )

        # Verify filtering
        assert len(created_events) == 1
        assert len(completed_events) == 1
        assert created_events[0].assessment_id == "created_1"
        assert completed_events[0].assessment_id == "completed_1"

    def test_subscribe_to_all_events(self):
        """Test subscribing to all event types."""
        bus = EventBus()
        all_events = []

        def all_callback(event):
            all_events.append(event)

        # Subscribe to all events (None type)
        bus.subscribe(None, all_callback)

        # Publish different event types
        bus.publish(
            AssessmentEvent(
                event_type=EventType.ASSESSMENT_CREATED,
                assessment_id="test_1",
                timestamp=datetime.now(),
                payload={},
            )
        )
        bus.publish(
            AssessmentEvent(
                event_type=EventType.ASSESSMENT_COMPLETED,
                assessment_id="test_2",
                timestamp=datetime.now(),
                payload={},
            )
        )

        # Should receive both events
        assert len(all_events) == 2
        assert all_events[0].event_type == EventType.ASSESSMENT_CREATED
        assert all_events[1].event_type == EventType.ASSESSMENT_COMPLETED


class TestEventBusErrorHandling:
    """Test error handling and isolation."""

    def setup_method(self):
        """Reset event bus before each test."""
        reset_event_bus()

    def test_error_isolation(self):
        """Test that errors in one subscriber don't affect others."""
        bus = EventBus()
        successful_events = []

        def failing_callback(event):
            raise ValueError("Simulated error")

        def successful_callback(event):
            successful_events.append(event)

        # Subscribe both callbacks
        bus.subscribe(EventType.ASSESSMENT_COMPLETED, failing_callback)
        bus.subscribe(EventType.ASSESSMENT_COMPLETED, successful_callback)

        # Publish event - successful callback should still work
        event = AssessmentEvent(
            event_type=EventType.ASSESSMENT_COMPLETED,
            assessment_id="test_error",
            timestamp=datetime.now(),
            payload={},
        )
        bus.publish(event)

        # Successful callback should have received the event
        assert len(successful_events) == 1
        assert successful_events[0].assessment_id == "test_error"


class TestEventBusThreadSafety:
    """Test thread safety of EventBus."""

    def setup_method(self):
        """Reset event bus before each test."""
        reset_event_bus()

    def test_concurrent_publish(self):
        """Test publishing from multiple threads simultaneously."""
        bus = EventBus()
        received_events = []
        lock = threading.Lock()

        def callback(event):
            with lock:
                received_events.append(event)

        bus.subscribe(EventType.ASSESSMENT_COMPLETED, callback)

        # Publish from multiple threads
        def publish_event(i):
            event = AssessmentEvent(
                event_type=EventType.ASSESSMENT_COMPLETED,
                assessment_id=f"test_{i}",
                timestamp=datetime.now(),
                payload={},
            )
            bus.publish(event)

        threads = []
        for i in range(10):
            t = threading.Thread(target=publish_event, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All events should be received
        assert len(received_events) == 10

    def test_concurrent_subscribe_unsubscribe(self):
        """Test subscribing/unsubscribing from multiple threads."""
        bus = EventBus()
        subscription_ids = []
        lock = threading.Lock()

        def subscribe_worker():
            sub_id = bus.subscribe(
                EventType.ASSESSMENT_COMPLETED, lambda e: None
            )
            with lock:
                subscription_ids.append(sub_id)

        # Subscribe from multiple threads
        threads = []
        for _ in range(5):
            t = threading.Thread(target=subscribe_worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All subscriptions should succeed
        assert len(subscription_ids) == 5

        # Unsubscribe all
        for sub_id in subscription_ids:
            assert bus.unsubscribe(sub_id) is True


class TestEventBusSingleton:
    """Test singleton behavior of get_event_bus()."""

    def setup_method(self):
        """Reset event bus before each test."""
        reset_event_bus()

    def test_singleton_instance(self):
        """Test that get_event_bus returns same instance."""
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2

    def test_singleton_thread_safe(self):
        """Test singleton is thread-safe."""
        instances = []
        lock = threading.Lock()

        def get_instance():
            bus = get_event_bus()
            with lock:
                instances.append(id(bus))

        threads = []
        for _ in range(10):
            t = threading.Thread(target=get_instance)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All threads should get same instance
        assert len(set(instances)) == 1

    def test_reset_singleton(self):
        """Test resetting singleton creates new instance."""
        bus1 = get_event_bus()
        reset_event_bus()
        bus2 = get_event_bus()
        assert bus1 is not bus2


class TestEventBusPerformance:
    """Test EventBus performance characteristics."""

    def setup_method(self):
        """Reset event bus before each test."""
        reset_event_bus()

    def test_publish_latency(self):
        """Test that event publishing has low latency (<5ms target)."""
        bus = EventBus()
        callback_times = []

        def callback(event):
            callback_times.append(time.time())

        bus.subscribe(EventType.ASSESSMENT_COMPLETED, callback)

        # Publish event and measure latency
        start_time = time.time()
        event = AssessmentEvent(
            event_type=EventType.ASSESSMENT_COMPLETED,
            assessment_id="perf_test",
            timestamp=datetime.now(),
            payload={},
        )
        bus.publish(event)

        latency_ms = (time.time() - start_time) * 1000

        # Should be very fast (<5ms for local pub/sub)
        assert latency_ms < 5.0
        assert len(callback_times) == 1

    def test_subscriber_count(self):
        """Test getting subscriber counts."""
        bus = EventBus()

        # No subscribers initially
        assert bus.get_subscriber_count() == 0
        assert bus.get_subscriber_count(EventType.ASSESSMENT_COMPLETED) == 0

        # Add subscribers
        bus.subscribe(EventType.ASSESSMENT_COMPLETED, lambda e: None)
        bus.subscribe(EventType.ASSESSMENT_COMPLETED, lambda e: None)
        bus.subscribe(EventType.ASSESSMENT_CREATED, lambda e: None)

        # Check counts
        assert bus.get_subscriber_count(EventType.ASSESSMENT_COMPLETED) == 2
        assert bus.get_subscriber_count(EventType.ASSESSMENT_CREATED) == 1
        assert bus.get_subscriber_count() == 3

    def test_clear_subscribers(self):
        """Test clearing all subscribers."""
        bus = EventBus()

        # Add subscribers
        bus.subscribe(EventType.ASSESSMENT_COMPLETED, lambda e: None)
        bus.subscribe(EventType.ASSESSMENT_CREATED, lambda e: None)
        assert bus.get_subscriber_count() == 2

        # Clear
        bus.clear_subscribers()
        assert bus.get_subscriber_count() == 0
