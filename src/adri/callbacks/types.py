"""
Callback type definitions.

Defines protocol types for sync and async callbacks.
"""

from typing import Any, Awaitable, Protocol, Union


class SyncCallback(Protocol):
    """Synchronous callback protocol.

    Callbacks implementing this protocol are called in a thread pool
    to avoid blocking the main assessment flow.

    Example:
        def my_callback(assessment_result):
            print(f"Assessment {assessment_result.assessment_id} completed")
            # Send to external system, update database, etc.
    """

    def __call__(self, assessment_result: Any) -> None:
        """Execute callback with assessment result.

        Args:
            assessment_result: AssessmentResult object from completed assessment
        """
        ...


class AsyncCallback(Protocol):
    """Asynchronous callback protocol.

    Callbacks implementing this protocol are awaited in an asyncio event loop.
    Ideal for async HTTP requests, async database operations, etc.

    Example:
        async def my_async_callback(assessment_result):
            async with aiohttp.ClientSession() as session:
                await session.post(
                    "https://api.example.com/assessments",
                    json=assessment_result.to_dict()
                )
    """

    def __call__(self, assessment_result: Any) -> Awaitable[None]:
        """Execute async callback with assessment result.

        Args:
            assessment_result: AssessmentResult object from completed assessment

        Returns:
            Awaitable that completes when callback finishes
        """
        ...


# Union type for callbacks that can be either sync or async
CallbackType = Union[SyncCallback, AsyncCallback]
