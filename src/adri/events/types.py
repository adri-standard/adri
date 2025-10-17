"""
Event system type definitions.

Defines event types and data structures for assessment lifecycle events.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class EventType(Enum):
    """Assessment lifecycle event types."""

    ASSESSMENT_CREATED = "assessment.created"
    ASSESSMENT_STARTED = "assessment.started"
    ASSESSMENT_COMPLETED = "assessment.completed"
    ASSESSMENT_FAILED = "assessment.failed"
    ASSESSMENT_PERSISTED = "assessment.persisted"


@dataclass
class AssessmentEvent:
    """Event published during assessment lifecycle.

    Attributes:
        event_type: Type of event being published
        assessment_id: Unique identifier for the assessment
        timestamp: When the event occurred
        payload: Event-specific data
        metadata: Additional context information
    """

    event_type: EventType
    assessment_id: str
    timestamp: datetime
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the event
        """
        return {
            "event_type": self.event_type.value,
            "assessment_id": self.assessment_id,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "metadata": self.metadata or {},
        }


@dataclass
class AssessmentManifest:
    """Minimal assessment metadata for fast path storage.

    This lightweight structure is written immediately (<10ms) when an
    assessment is created or completed, enabling workflow orchestrators
    to access assessment IDs without waiting for full batch logging.

    Attributes:
        assessment_id: Unique identifier for the assessment
        timestamp: When the assessment occurred
        status: Current status (CREATED, PASSED, BLOCKED, ERROR)
        score: Overall assessment score (0-100)
        standard_name: Name of the standard used
    """

    assessment_id: str
    timestamp: datetime
    status: str
    score: Optional[float] = None
    standard_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the manifest
        """
        return {
            "assessment_id": self.assessment_id,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "score": self.score,
            "standard_name": self.standard_name,
        }
