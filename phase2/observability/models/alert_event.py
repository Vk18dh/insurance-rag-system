"""
phase2.observability.models.alert_event
=========================================
Alert emitted when a health threshold is breached.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    """Classification of alert urgency."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertEvent(BaseModel):
    """
    Notification that a monitored threshold has been exceeded.

    Fields
    ------
    alert_id    : Unique identifier.
    execution_id: Trace ID that triggered the alert (None for global alerts).
    severity    : Urgency level.
    metric_name : Which metric breached a threshold.
    observed    : The observed value.
    threshold   : The configured limit.
    message     : Human-readable description (no PII).
    timestamp   : UTC time of alert creation.
    """

    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str | None = Field(default=None)
    severity: AlertSeverity = Field(..., description="Alert urgency level.")
    metric_name: str = Field(..., description="Name of the breached metric.")
    observed: float = Field(..., description="Observed metric value.")
    threshold: float = Field(..., description="Configured threshold value.")
    message: str = Field(..., description="Human-readable alert description.")
    timestamp_utc: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
