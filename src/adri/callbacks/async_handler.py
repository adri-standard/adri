"""
Async callback handler implementation.

Manages execution of sync and async callbacks with proper isolation and error handling.
"""

import asyncio
import inspect
import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional

from .types import CallbackType

logger = logging.getLogger(__name__)


class AsyncCallbackManager:
    """Manages sync and async callback execution.

    Provides thread-safe callback registration and execution with proper
    error isolation. Sync callbacks run in a thread pool, async callbacks
    run in an asyncio event loop.

    Usage:
        manager = AsyncCallbackManager(thread_pool_size=4)

        # Register callbacks
        def sync_callback(result):
            print(f"Sync: {result.assessment_id}")

        async def async_callback(result):
            await send_notification(result)

        manager.add_callback(sync_callback)
        manager.add_callback(async_callback)

        # Invoke all callbacks
        manager.invoke_all(assessment_result)

        # Cleanup
        manager.close()
    """

    def __init__(self, thread_pool_size: int = 4, enable_async: bool = True):
        """Initialize callback manager.

        Args:
            thread_pool_size: Size of thread pool for sync callbacks
            enable_async: Whether to enable async callback support
        """
        self.thread_pool_size = thread_pool_size
        self.enable_async = enable_async

        # Thread pool for sync callbacks
        self._executor = ThreadPoolExecutor(
            max_workers=thread_pool_size, thread_name_prefix="adri_callback_"
        )

        # Asyncio event loop for async callbacks (created on demand)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._loop_ready = threading.Event()

        # Callback registry
        self._callbacks: Dict[str, CallbackType] = {}
        self._lock = threading.RLock()

        # Track if manager is closed
        self._closed = False

        logger.debug(
            f"Initialized AsyncCallbackManager with {thread_pool_size} threads, "
            f"async_enabled={enable_async}"
        )

    def add_callback(self, callback: CallbackType) -> str:
        """Register a callback (sync or async).

        Args:
            callback: Callback function to register

        Returns:
            Callback ID for later removal

        Raises:
            ValueError: If callback is not callable
            RuntimeError: If manager is closed
        """
        if self._closed:
            raise RuntimeError("Cannot add callback to closed manager")

        if not callable(callback):
            raise ValueError("Callback must be callable")

        callback_id = str(uuid.uuid4())

        with self._lock:
            self._callbacks[callback_id] = callback

        callback_type = "async" if inspect.iscoroutinefunction(callback) else "sync"
        logger.debug(f"Registered {callback_type} callback: {callback_id}")

        return callback_id

    def remove_callback(self, callback_id: str) -> bool:
        """Remove a registered callback.

        Args:
            callback_id: ID returned from add_callback()

        Returns:
            True if callback was found and removed, False otherwise
        """
        with self._lock:
            if callback_id in self._callbacks:
                del self._callbacks[callback_id]
                logger.debug(f"Removed callback: {callback_id}")
                return True

        logger.warning(f"Callback not found: {callback_id}")
        return False

    def invoke_all(self, assessment_result: Any) -> None:
        """Invoke all registered callbacks with assessment result.

        Callbacks are executed asynchronously and errors are caught
        and logged to prevent one callback from affecting others.

        Args:
            assessment_result: AssessmentResult to pass to callbacks
        """
        if self._closed:
            logger.warning("Cannot invoke callbacks on closed manager")
            return

        with self._lock:
            callbacks = list(self._callbacks.items())

        if not callbacks:
            logger.debug("No callbacks registered")
            return

        logger.debug(f"Invoking {len(callbacks)} callbacks")

        for callback_id, callback in callbacks:
            try:
                if inspect.iscoroutinefunction(callback):
                    # Async callback
                    self._invoke_async_callback(
                        callback_id, callback, assessment_result
                    )
                else:
                    # Sync callback
                    self._invoke_sync_callback(callback_id, callback, assessment_result)
            except Exception as e:
                logger.error(
                    f"Error invoking callback {callback_id}: {e}", exc_info=True
                )

    def _invoke_sync_callback(
        self, callback_id: str, callback: CallbackType, assessment_result: Any
    ) -> None:
        """Execute sync callback in thread pool."""

        def run_callback():
            try:
                callback(assessment_result)
                logger.debug(f"Sync callback {callback_id} completed")
            except Exception as e:
                logger.error(
                    f"Error in sync callback {callback_id}: {e}", exc_info=True
                )

        self._executor.submit(run_callback)

    def _invoke_async_callback(
        self, callback_id: str, callback: CallbackType, assessment_result: Any
    ) -> None:
        """Execute async callback in event loop."""
        if not self.enable_async:
            logger.warning(f"Async callback {callback_id} skipped (async disabled)")
            return

        # Ensure event loop is running
        if self._loop is None:
            self._start_event_loop()

        # Wait for loop to be ready (with timeout)
        if not self._loop_ready.wait(timeout=5.0):
            logger.error("Event loop not ready, skipping async callback")
            return

        # Schedule callback in event loop
        async def run_callback():
            try:
                await callback(assessment_result)
                logger.debug(f"Async callback {callback_id} completed")
            except Exception as e:
                logger.error(
                    f"Error in async callback {callback_id}: {e}", exc_info=True
                )

        # Schedule in event loop (thread-safe)
        asyncio.run_coroutine_threadsafe(run_callback(), self._loop)

    def _start_event_loop(self) -> None:
        """Start asyncio event loop in background thread."""
        with self._lock:
            if self._loop is not None:
                return

            def run_loop():
                """Event loop runner."""
                asyncio.set_event_loop(self._loop)
                self._loop_ready.set()
                logger.debug("Async event loop started")
                try:
                    self._loop.run_forever()
                except Exception as e:
                    logger.error(f"Event loop error: {e}", exc_info=True)
                finally:
                    logger.debug("Async event loop stopped")

            # Create new event loop
            self._loop = asyncio.new_event_loop()

            # Start loop in background thread
            self._loop_thread = threading.Thread(
                target=run_loop, name="adri_async_loop", daemon=True
            )
            self._loop_thread.start()

    def get_callback_count(self) -> int:
        """Get number of registered callbacks.

        Returns:
            Number of registered callbacks
        """
        with self._lock:
            return len(self._callbacks)

    def clear_callbacks(self) -> None:
        """Remove all registered callbacks."""
        with self._lock:
            count = len(self._callbacks)
            self._callbacks.clear()
            logger.debug(f"Cleared {count} callbacks")

    def close(self) -> None:
        """Shutdown callback manager and cleanup resources."""
        if self._closed:
            return

        logger.debug("Closing AsyncCallbackManager")
        self._closed = True

        # Shutdown thread pool
        self._executor.shutdown(wait=True)
        logger.debug("Thread pool shutdown complete")

        # Stop event loop if running
        if self._loop is not None and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
            if self._loop_thread is not None:
                self._loop_thread.join(timeout=5.0)
            logger.debug("Event loop shutdown complete")

        # Clear callbacks
        self.clear_callbacks()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __del__(self):
        """Cleanup on deletion."""
        if not self._closed:
            self.close()
