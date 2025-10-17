"""
Event bus implementation.

Thread-safe pub/sub message bus for assessment lifecycle events.
"""

import logging
import threading
import uuid
from typing import Callable, Dict, Optional

from .types import AssessmentEvent, EventType

logger = logging.getLogger(__name__)


class EventBus:
    """Thread-safe pub/sub event bus for assessment events.

    Provides a singleton event bus that allows components to publish
    and subscribe to assessment lifecycle events. Supports both sync
    and async subscribers with proper error isolation.

    Usage:
        bus = get_event_bus()

        # Subscribe to events
        subscription_id = bus.subscribe(
            EventType.ASSESSMENT_COMPLETED,
            lambda event: print(f"Assessment {event.assessment_id} completed")
        )

        # Publish events
        bus.publish(AssessmentEvent(
            event_type=EventType.ASSESSMENT_COMPLETED,
            assessment_id="adri_20250110_123456_abc123",
            timestamp=datetime.now(),
            payload={"score": 95.0}
        ))

        # Unsubscribe when done
        bus.unsubscribe(subscription_id)
    """

    def __init__(self):
        """Initialize event bus with empty subscriber registry."""
        self._subscribers: Dict[EventType, Dict[str, Callable]] = {}
        self._lock = threading.RLock()
        self._all_subscribers: Dict[str, Callable] = {}  # Subscribe to all events

    def subscribe(
        self,
        event_type: Optional[EventType],
        callback: Callable[[AssessmentEvent], None],
    ) -> str:
        """Subscribe to events of a specific type.

        Args:
            event_type: Type of event to subscribe to, or None for all events
            callback: Function to call when event occurs

        Returns:
            Subscription ID for later unsubscribe

        Example:
            >>> bus = get_event_bus()
            >>> sub_id = bus.subscribe(
            ...     EventType.ASSESSMENT_COMPLETED,
            ...     lambda e: print(f"Done: {e.assessment_id}")
            ... )
        """
        subscription_id = str(uuid.uuid4())

        with self._lock:
            if event_type is None:
                # Subscribe to all events
                self._all_subscribers[subscription_id] = callback
            else:
                # Subscribe to specific event type
                if event_type not in self._subscribers:
                    self._subscribers[event_type] = {}
                self._subscribers[event_type][subscription_id] = callback

        logger.debug(
            f"Subscribed {subscription_id} to "
            f"{'all events' if event_type is None else event_type.value}"
        )
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a subscription.

        Args:
            subscription_id: ID returned from subscribe()

        Returns:
            True if subscription was found and removed, False otherwise

        Example:
            >>> bus.unsubscribe(sub_id)
            True
        """
        with self._lock:
            # Check all-events subscribers
            if subscription_id in self._all_subscribers:
                del self._all_subscribers[subscription_id]
                logger.debug(f"Unsubscribed {subscription_id} from all events")
                return True

            # Check event-specific subscribers
            for event_type, subscribers in self._subscribers.items():
                if subscription_id in subscribers:
                    del subscribers[subscription_id]
                    logger.debug(
                        f"Unsubscribed {subscription_id} from {event_type.value}"
                    )
                    return True

        logger.warning(f"Subscription {subscription_id} not found")
        return False

    def publish(self, event: AssessmentEvent) -> None:
        """Publish an event to all subscribers.

        Delivers the event to all subscribers interested in this event type
        or all events. Errors in individual subscribers are caught and logged
        to prevent one subscriber from affecting others.

        Args:
            event: Event to publish

        Example:
            >>> bus.publish(AssessmentEvent(
            ...     event_type=EventType.ASSESSMENT_CREATED,
            ...     assessment_id="adri_20250110_123456_abc123",
            ...     timestamp=datetime.now(),
            ...     payload={"standard": "invoice_standard"}
            ... ))
        """
        with self._lock:
            # Get subscribers for this specific event type
            subscribers = self._subscribers.get(event.event_type, {}).copy()
            # Add all-events subscribers
            subscribers.update(self._all_subscribers.copy())

        if not subscribers:
            logger.debug(
                f"No subscribers for {event.event_type.value}, "
                f"assessment_id={event.assessment_id}"
            )
            return

        # Notify subscribers outside of lock to prevent deadlocks
        logger.debug(
            f"Publishing {event.event_type.value} to {len(subscribers)} subscribers, "
            f"assessment_id={event.assessment_id}"
        )

        for subscription_id, callback in subscribers.items():
            try:
                callback(event)
            except Exception as e:
                logger.error(
                    f"Error in subscriber {subscription_id} for "
                    f"{event.event_type.value}: {e}",
                    exc_info=True,
                )

    def get_subscriber_count(self, event_type: Optional[EventType] = None) -> int:
        """Get number of subscribers for an event type.

        Args:
            event_type: Event type to count, or None for total count

        Returns:
            Number of subscribers
        """
        with self._lock:
            if event_type is None:
                # Total count across all types plus all-events subscribers
                total = len(self._all_subscribers)
                for subscribers in self._subscribers.values():
                    total += len(subscribers)
                return total
            else:
                return len(self._subscribers.get(event_type, {}))

    def clear_subscribers(self) -> None:
        """Remove all subscribers. Mainly for testing."""
        with self._lock:
            self._subscribers.clear()
            self._all_subscribers.clear()
            logger.debug("Cleared all event bus subscribers")


# Singleton instance
_event_bus_instance: Optional[EventBus] = None
_event_bus_lock = threading.Lock()


def get_event_bus() -> EventBus:
    """Get singleton EventBus instance.

    Returns:
        Singleton EventBus instance

    Example:
        >>> bus = get_event_bus()
        >>> bus.subscribe(EventType.ASSESSMENT_COMPLETED, my_callback)
    """
    global _event_bus_instance

    if _event_bus_instance is None:
        with _event_bus_lock:
            if _event_bus_instance is None:
                _event_bus_instance = EventBus()
                logger.debug("Created singleton EventBus instance")

    return _event_bus_instance


def reset_event_bus() -> None:
    """Reset singleton instance. Mainly for testing."""
    global _event_bus_instance

    with _event_bus_lock:
        if _event_bus_instance is not None:
            _event_bus_instance.clear_subscribers()
        _event_bus_instance = None
        logger.debug("Reset EventBus singleton")
