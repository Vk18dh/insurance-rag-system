"""
phase2.observability.interfaces.observability_interface
=========================================================
Abstract contracts for every observability service.

Design rules (Part 0 — Interface Segregation Principle):
  - Each interface has exactly one responsibility.
  - No implementation details leak through these contracts.
  - All concrete services must implement the relevant interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from phase2.observability.models.observability_event import AgentExecutionEvent, EventType
from phase2.observability.models.audit_record import AuditRecord
from phase2.observability.models.execution_metrics import ExecutionMetrics, AgentMetrics
from phase2.observability.models.trace_context import TraceContext
from phase2.observability.models.health_snapshot import HealthSnapshot
from phase2.observability.models.alert_event import AlertEvent


# ---------------------------------------------------------------------------
# ILoggingService
# ---------------------------------------------------------------------------

class ILoggingService(ABC):
    """Emits structured log entries at configurable severity levels."""

    @abstractmethod
    def log_info(self, message: str, execution_id: Optional[str] = None, **kwargs: object) -> None:
        """Emit an INFO-level structured log entry."""

    @abstractmethod
    def log_warning(self, message: str, execution_id: Optional[str] = None, **kwargs: object) -> None:
        """Emit a WARNING-level structured log entry."""

    @abstractmethod
    def log_error(self, message: str, execution_id: Optional[str] = None, **kwargs: object) -> None:
        """Emit an ERROR-level structured log entry."""

    @abstractmethod
    def log_debug(self, message: str, execution_id: Optional[str] = None, **kwargs: object) -> None:
        """Emit a DEBUG-level structured log entry."""


# ---------------------------------------------------------------------------
# IMetricsService
# ---------------------------------------------------------------------------

class IMetricsService(ABC):
    """Records per-agent and per-request performance metrics."""

    @abstractmethod
    def record_agent_start(self, execution_id: str, agent_name: str, start_time_ms: float) -> None:
        """Mark the start of an agent execution."""

    @abstractmethod
    def record_agent_end(
        self,
        execution_id: str,
        agent_name: str,
        end_time_ms: float,
        succeeded: bool,
        retry_count: int = 0,
        timed_out: bool = False,
    ) -> None:
        """Mark the completion of an agent execution."""

    @abstractmethod
    def compile_execution_metrics(self, execution_id: str) -> ExecutionMetrics:
        """Return aggregated metrics for a completed execution."""


# ---------------------------------------------------------------------------
# IAuditService
# ---------------------------------------------------------------------------

class IAuditService(ABC):
    """Stores masked, hashed audit records for compliance and debugging."""

    @abstractmethod
    def create_record(self, execution_id: str, raw_query: str, environment: str) -> AuditRecord:
        """Initialise an audit record. Hashes the raw_query immediately."""

    @abstractmethod
    def finalise_record(
        self,
        execution_id: str,
        agent_sequence: List[str],
        warning_count: int,
        citation_count: int,
        overall_status: str,
        retrieved_doc_ids: Optional[List[str]] = None,
        exception_types: Optional[List[str]] = None,
    ) -> AuditRecord:
        """Populate completion fields and persist the record."""

    @abstractmethod
    def get_record(self, execution_id: str) -> Optional[AuditRecord]:
        """Retrieve an audit record by execution ID."""


# ---------------------------------------------------------------------------
# ITracingService
# ---------------------------------------------------------------------------

class ITracingService(ABC):
    """Assigns and propagates distributed trace identifiers."""

    @abstractmethod
    def start_trace(self) -> TraceContext:
        """Create a new root TraceContext for a pipeline execution."""

    @abstractmethod
    def start_span(self, parent: TraceContext) -> TraceContext:
        """Create a child span inheriting the parent execution_id."""


# ---------------------------------------------------------------------------
# IStorageBackend
# ---------------------------------------------------------------------------

class IStorageBackend(ABC):
    """Persists observability events and audit records to a durable store."""

    @abstractmethod
    def save_event(self, event: AgentExecutionEvent) -> None:
        """Persist a single agent execution event."""

    @abstractmethod
    def save_audit_record(self, record: AuditRecord) -> None:
        """Persist an audit record."""

    @abstractmethod
    def save_metrics(self, metrics: ExecutionMetrics) -> None:
        """Persist aggregated execution metrics."""

    @abstractmethod
    def save_alert(self, alert: AlertEvent) -> None:
        """Persist an alert event."""


# ---------------------------------------------------------------------------
# IHealthMonitor
# ---------------------------------------------------------------------------

class IHealthMonitor(ABC):
    """Evaluates system health and emits alerts when thresholds are breached."""

    @abstractmethod
    def record_execution_outcome(
        self,
        execution_id: str,
        succeeded: bool,
        duration_ms: float,
        had_timeout: bool,
        retry_count: int,
    ) -> None:
        """Register the outcome of one pipeline execution."""

    @abstractmethod
    def get_health_snapshot(self) -> HealthSnapshot:
        """Return the current system health state."""

    @abstractmethod
    def get_pending_alerts(self) -> List[AlertEvent]:
        """Return alerts that have not yet been consumed."""


# ---------------------------------------------------------------------------
# IObservabilityFacade
# ---------------------------------------------------------------------------

class IObservabilityFacade(ABC):
    """
    Single entry point for the Orchestrator.

    The Orchestrator calls only:
        facade.on_pipeline_start(...)
        facade.on_agent_start(...)
        facade.on_agent_end(...)
        facade.on_pipeline_end(...)

    All internal service coordination is hidden behind this facade.
    """

    @abstractmethod
    def on_pipeline_start(self, execution_id: str, raw_query: str) -> TraceContext:
        """Called once at the beginning of a pipeline run."""

    @abstractmethod
    def on_agent_start(self, trace: TraceContext, agent_name: str) -> TraceContext:
        """Called just before an agent begins execution."""

    @abstractmethod
    def on_agent_end(
        self,
        trace: TraceContext,
        agent_name: str,
        duration_ms: float,
        succeeded: bool,
        retry_count: int = 0,
        timed_out: bool = False,
        error_type: Optional[str] = None,
    ) -> None:
        """Called immediately after an agent finishes (success or failure)."""

    @abstractmethod
    def on_pipeline_end(
        self,
        trace: TraceContext,
        overall_status: str,
        warning_count: int = 0,
        citation_count: int = 0,
    ) -> None:
        """Called once when the pipeline finishes. Flushes storage."""
