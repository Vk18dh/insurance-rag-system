"""
phase2.observability.models.observability_event
================================================
Base event model and per-agent execution event.

All events are immutable once created (frozen=True).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Enumeration of every observable lifecycle event."""

    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_RETRY = "agent_retry"
    AGENT_TIMEOUT = "agent_timeout"
    AGENT_FAILED = "agent_failed"
    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_COMPLETED = "pipeline_completed"
    PIPELINE_FAILED = "pipeline_failed"
    WARNING_EMITTED = "warning_emitted"
    ALERT_EMITTED = "alert_emitted"


class ObservabilityEvent(BaseModel):
    """
    Base class for every observability event emitted during pipeline execution.

    Fields
    ------
    event_id        : Unique identifier for this event.
    event_type      : Lifecycle classification.
    execution_id    : Distributed trace ID shared across the entire request.
    agent_name      : Name of the agent that produced this event (None for pipeline events).
    timestamp_utc   : UTC timestamp at event creation.
    extra           : Arbitrary structured metadata (never contains PII or secrets).
    """

    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique event identifier (UUID v4).",
    )
    event_type: EventType = Field(..., description="Lifecycle event type.")
    execution_id: str = Field(..., description="Distributed trace execution ID.")
    agent_name: Optional[str] = Field(
        default=None, description="Agent that produced this event."
    )
    timestamp_utc: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC wall-clock time of event creation.",
    )
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary JSON-safe metadata. Must never contain secrets or PII.",
    )

    model_config = {"frozen": True}


class AgentExecutionEvent(ObservabilityEvent):
    """
    Specialised event for a single agent execution step.

    Additional fields
    -----------------
    duration_ms     : Wall-clock duration (populated on completion events; None on start).
    retry_count     : Number of retries attempted before this event.
    error_message   : Sanitised error description (never a raw stack trace in production).
    """

    duration_ms: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Execution duration in milliseconds (set on completion).",
    )
    retry_count: int = Field(default=0, ge=0, description="Retry attempts made.")
    error_message: Optional[str] = Field(
        default=None,
        description="Sanitised error summary; never a raw exception traceback.",
    )
