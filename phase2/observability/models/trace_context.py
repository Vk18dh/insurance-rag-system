"""
phase2.observability.models.trace_context
==========================================
Distributed trace carrier assigned at pipeline start and inherited by every agent event.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class TraceContext(BaseModel):
    """
    Holds the identifiers that link every event in one pipeline execution.

    Fields
    ------
    execution_id : Top-level trace ID (UUID v4) — the same for all events in one request.
    span_id      : Per-agent span identifier (UUID v4).
    parent_span_id: Parent span for nested calls (None at pipeline root).
    sampled      : Whether this trace is sampled for storage.
    """

    execution_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Pipeline-level trace identifier.",
    )
    span_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Per-agent span identifier.",
    )
    parent_span_id: str | None = Field(default=None)
    sampled: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def child_span(self) -> "TraceContext":
        """Return a new child TraceContext inheriting this execution_id."""
        return TraceContext(
            execution_id=self.execution_id,
            parent_span_id=self.span_id,
            sampled=self.sampled,
        )
