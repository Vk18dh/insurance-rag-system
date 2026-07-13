"""
phase2.observability.tracing.tracing_service
=============================================
Concrete ITracingService implementation.

Assigns UUID v4 execution IDs and creates child spans for per-agent tracing.
"""

from __future__ import annotations

from phase2.observability.interfaces.observability_interface import ITracingService
from phase2.observability.models.trace_context import TraceContext


class TracingService(ITracingService):
    """Creates and propagates trace contexts across the pipeline."""

    def start_trace(self) -> TraceContext:
        """Generate a new root TraceContext for a pipeline execution."""
        return TraceContext()

    def start_span(self, parent: TraceContext) -> TraceContext:
        """Create a child span that inherits the parent's execution_id."""
        return parent.child_span()
