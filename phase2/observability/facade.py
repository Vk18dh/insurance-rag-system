"""
phase2.observability.facade
============================
ObservabilityFacade — single public interface used by the Orchestrator.

The Orchestrator calls four lifecycle hooks per pipeline execution:
    on_pipeline_start → on_agent_start → on_agent_end → on_pipeline_end

Everything else (metrics, audit, storage, health, logging) is coordinated
internally. No agent or service from Parts 1–8 is modified.

ObservabilityFactory
--------------------
Constructs the facade from Phase2Settings using dependency injection.
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

from phase2.observability.interfaces.observability_interface import IObservabilityFacade
from phase2.observability.interfaces.observability_interface import (
    ILoggingService, IMetricsService, IAuditService,
    ITracingService, IStorageBackend, IHealthMonitor,
)
from phase2.observability.models.trace_context import TraceContext
from phase2.observability.models.observability_event import AgentExecutionEvent, EventType
from phase2.observability.exceptions import ObservabilityException

logger = logging.getLogger(__name__)


class ObservabilityFacade(IObservabilityFacade):
    """
    Aggregates all observability sub-services behind a single interface.

    Dependencies are injected — the facade itself contains no configuration.

    Thread Safety
    -------------
    _agent_sequences is protected by _seq_lock so concurrent pipeline
    executions (multi-tenant mode) do not corrupt each other's audit data.
    """

    def __init__(
        self,
        logging_svc: ILoggingService,
        metrics_svc: IMetricsService,
        audit_svc: IAuditService,
        tracing_svc: ITracingService,
        storage: IStorageBackend,
        health_monitor: IHealthMonitor,
        environment: str,
    ) -> None:
        self._log = logging_svc
        self._metrics = metrics_svc
        self._audit = audit_svc
        self._tracing = tracing_svc
        self._storage = storage
        self._health = health_monitor
        self._environment = environment

        # Thread-safe agent sequence tracker
        self._agent_sequences: Dict[str, List[str]] = {}
        self._seq_lock = threading.Lock()

    # ------------------------------------------------------------------
    # IObservabilityFacade implementation
    # ------------------------------------------------------------------

    def on_pipeline_start(self, execution_id: str, raw_query: str) -> TraceContext:
        """Called once at the beginning of each pipeline run."""
        try:
            # Use the Orchestrator-supplied execution_id so all IDs match
            trace = TraceContext(execution_id=execution_id)
            self._audit.create_record(execution_id, raw_query, self._environment)
            with self._seq_lock:
                self._agent_sequences[execution_id] = []
            self._log.log_info(
                "Pipeline started.",
                execution_id=execution_id,
                event_type=EventType.PIPELINE_STARTED.value,
            )
            return trace
        except Exception as exc:
            # Observability failures must NEVER propagate to the pipeline
            logger.error("ObservabilityFacade.on_pipeline_start error: %s", exc)
            return TraceContext(execution_id=execution_id)

    def on_agent_start(self, trace: TraceContext, agent_name: str) -> TraceContext:
        """Called just before an agent begins execution."""
        try:
            span = self._tracing.start_span(trace)
            start_ms = time.time() * 1000
            self._metrics.record_agent_start(trace.execution_id, agent_name, start_ms)

            event = AgentExecutionEvent(
                event_type=EventType.AGENT_STARTED,
                execution_id=trace.execution_id,
                agent_name=agent_name,
            )
            self._storage.save_event(event)

            with self._seq_lock:
                self._agent_sequences.setdefault(trace.execution_id, []).append(agent_name)

            self._log.log_info(
                f"Agent started: {agent_name}",
                execution_id=trace.execution_id,
                agent=agent_name,
            )
            return span
        except Exception as exc:
            logger.error("ObservabilityFacade.on_agent_start error: %s", exc)
            return trace

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
        try:
            end_ms = time.time() * 1000
            self._metrics.record_agent_end(
                trace.execution_id, agent_name, end_ms, succeeded, retry_count, timed_out
            )

            event_type = EventType.AGENT_COMPLETED if succeeded else EventType.AGENT_FAILED
            if timed_out:
                event_type = EventType.AGENT_TIMEOUT

            event = AgentExecutionEvent(
                event_type=event_type,
                execution_id=trace.execution_id,
                agent_name=agent_name,
                duration_ms=duration_ms,
                retry_count=retry_count,
                error_message=error_type,
            )
            self._storage.save_event(event)

            level = "info" if succeeded else "error"
            getattr(self._log, f"log_{level}")(
                f"Agent {'completed' if succeeded else 'failed'}: {agent_name} "
                f"({duration_ms:.1f}ms, retries={retry_count})",
                execution_id=trace.execution_id,
                agent=agent_name,
                duration_ms=duration_ms,
            )
        except Exception as exc:
            logger.error("ObservabilityFacade.on_agent_end error: %s", exc)

    def on_pipeline_end(
        self,
        trace: TraceContext,
        overall_status: str,
        warning_count: int = 0,
        citation_count: int = 0,
    ) -> None:
        """Called once when the pipeline finishes. Flushes all stores."""
        try:
            metrics = self._metrics.compile_execution_metrics(trace.execution_id)
            self._storage.save_metrics(metrics)

            with self._seq_lock:
                agent_seq = self._agent_sequences.pop(trace.execution_id, [])

            audit = self._audit.finalise_record(
                execution_id=trace.execution_id,
                agent_sequence=agent_seq,
                warning_count=warning_count,
                citation_count=citation_count,
                overall_status=overall_status,
            )
            self._storage.save_audit_record(audit)

            self._health.record_execution_outcome(
                execution_id=trace.execution_id,
                succeeded=(overall_status == "success"),
                duration_ms=metrics.total_duration_ms,
                had_timeout=metrics.total_timeout_count > 0,
                retry_count=metrics.total_retry_count,
            )

            for alert in self._health.get_pending_alerts():
                self._storage.save_alert(alert)
                self._log.log_warning(
                    f"Health alert: {alert.message}",
                    execution_id=trace.execution_id,
                    metric=alert.metric_name,
                    severity=alert.severity.value,
                )

            self._log.log_info(
                f"Pipeline ended: status={overall_status}, "
                f"total_ms={metrics.total_duration_ms:.1f}",
                execution_id=trace.execution_id,
                event_type=EventType.PIPELINE_COMPLETED.value,
            )
        except Exception as exc:
            logger.error("ObservabilityFacade.on_pipeline_end error: %s", exc)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

class ObservabilityFactory:
    """
    Constructs ObservabilityFacade from Phase2Settings.

    Returns NullObservabilityFacade when observability is disabled so
    the Orchestrator requires no conditional checks.
    """

    @staticmethod
    def create(settings: object) -> IObservabilityFacade:  # type: ignore[return]
        """
        Parameters
        ----------
        settings : Phase2Settings instance (typed as object to avoid circular import).
        """
        obs = getattr(settings, "observability", None)
        if obs is None or not getattr(obs, "enabled", True):
            return NullObservabilityFacade()

        from phase2.observability.logging.logging_service import LoggingService
        from phase2.observability.metrics.metrics_service import MetricsService
        from phase2.observability.audit.audit_service import AuditService
        from phase2.observability.tracing.tracing_service import TracingService
        from phase2.observability.health.health_monitor import HealthMonitor

        logging_svc = LoggingService(
            log_level=obs.log_level,
            log_dir=obs.log_dir,
            log_to_file=obs.log_to_file,
            log_to_console=obs.log_to_console,
            log_format=obs.log_format,
        )
        metrics_svc = MetricsService(
            retrieval_agents=frozenset(obs.retrieval_agent_names),
            reasoning_agents=frozenset(obs.reasoning_agent_names),
            response_agents=frozenset(obs.response_agent_names),
        )
        audit_svc = AuditService(
            salt_env_var=obs.query_hash_salt_env_var,
            environment=settings.environment,  # type: ignore[attr-defined]
        )
        tracing_svc = TracingService()
        health = HealthMonitor(
            failure_rate_threshold=obs.alert_failure_rate_threshold,
            avg_latency_ms_threshold=obs.alert_avg_latency_ms_threshold,
            window_size=obs.health_window_size,
        )

        # Use pathlib for cross-platform path construction
        audit_path = Path(obs.audit_dir)
        if obs.audit_storage_backend == "sqlite":
            from phase2.observability.storage.sqlite_storage import SqliteStorageBackend
            storage: IStorageBackend = SqliteStorageBackend(
                db_path=str(audit_path / "observability.db")
            )
        else:
            from phase2.observability.storage.json_storage import JsonStorageBackend
            storage = JsonStorageBackend(audit_dir=str(audit_path))

        return ObservabilityFacade(
            logging_svc=logging_svc,
            metrics_svc=metrics_svc,
            audit_svc=audit_svc,
            tracing_svc=tracing_svc,
            storage=storage,
            health_monitor=health,
            environment=settings.environment,  # type: ignore[attr-defined]
        )


class NullObservabilityFacade(IObservabilityFacade):
    """
    No-op facade used when observability is disabled in configuration.

    Ensures Orchestrator code requires no conditional checks (Null Object pattern).
    """

    def on_pipeline_start(self, execution_id: str, raw_query: str) -> TraceContext:
        return TraceContext(execution_id=execution_id)

    def on_agent_start(self, trace: TraceContext, agent_name: str) -> TraceContext:
        return trace

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
        pass

    def on_pipeline_end(
        self,
        trace: TraceContext,
        overall_status: str,
        warning_count: int = 0,
        citation_count: int = 0,
    ) -> None:
        pass
