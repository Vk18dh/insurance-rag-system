"""
phase2.observability.metrics.metrics_service
=============================================
Concrete IMetricsService implementation.

Thread-safe in-memory metrics accumulator.
All state is keyed by execution_id and flushed after each pipeline run.

Agent role classification (retrieval / reasoning / response) is injected
at construction time — no agent names are hardcoded in this module.
"""

from __future__ import annotations

import threading
import time
from typing import Dict, FrozenSet, List, Optional

from phase2.observability.interfaces.observability_interface import IMetricsService
from phase2.observability.models.execution_metrics import AgentMetrics, ExecutionMetrics
from phase2.observability.exceptions import MetricsException


class MetricsService(IMetricsService):
    """
    Thread-safe, in-memory metrics store.

    Parameters
    ----------
    retrieval_agents  : Names of agents classified as retrieval workers.
    reasoning_agents  : Names of agents classified as reasoning workers.
    response_agents   : Names of agents classified as response workers.

    All three sets default to empty — callers that care about per-segment
    timing should inject the appropriate sets from configuration.
    """

    def __init__(
        self,
        retrieval_agents: Optional[FrozenSet[str]] = None,
        reasoning_agents: Optional[FrozenSet[str]] = None,
        response_agents: Optional[FrozenSet[str]] = None,
    ) -> None:
        self._retrieval_agents: FrozenSet[str] = retrieval_agents or frozenset()
        self._reasoning_agents: FrozenSet[str] = reasoning_agents or frozenset()
        self._response_agents: FrozenSet[str] = response_agents or frozenset()

        self._lock = threading.Lock()
        self._in_progress: Dict[str, List[Dict]] = {}
        self._pipeline_start: Dict[str, float] = {}

    # ------------------------------------------------------------------
    # IMetricsService implementation
    # ------------------------------------------------------------------

    def record_agent_start(
        self, execution_id: str, agent_name: str, start_time_ms: float
    ) -> None:
        with self._lock:
            if execution_id not in self._in_progress:
                self._in_progress[execution_id] = []
                self._pipeline_start[execution_id] = start_time_ms
            self._in_progress[execution_id].append(
                {
                    "agent_name": agent_name,
                    "start_time_ms": start_time_ms,
                    "end_time_ms": None,
                    "duration_ms": None,
                    "retry_count": 0,
                    "timed_out": False,
                    "succeeded": False,
                }
            )

    def record_agent_end(
        self,
        execution_id: str,
        agent_name: str,
        end_time_ms: float,
        succeeded: bool,
        retry_count: int = 0,
        timed_out: bool = False,
    ) -> None:
        with self._lock:
            bucket = self._in_progress.get(execution_id)
            if bucket is None:
                raise MetricsException(
                    f"No metrics context for execution_id={execution_id}"
                )
            for entry in reversed(bucket):
                if entry["agent_name"] == agent_name and entry["end_time_ms"] is None:
                    entry["end_time_ms"] = end_time_ms
                    entry["duration_ms"] = end_time_ms - entry["start_time_ms"]
                    entry["succeeded"] = succeeded
                    entry["retry_count"] = retry_count
                    entry["timed_out"] = timed_out
                    return
            raise MetricsException(
                f"Open metrics entry not found for agent={agent_name} "
                f"execution={execution_id}"
            )

    def compile_execution_metrics(self, execution_id: str) -> ExecutionMetrics:
        with self._lock:
            bucket = self._in_progress.pop(execution_id, [])
            pipeline_start = self._pipeline_start.pop(execution_id, None)

        agent_metrics = [AgentMetrics(**e) for e in bucket]

        now_ms = time.time() * 1000
        total_ms = (now_ms - pipeline_start) if pipeline_start else 0.0

        total_retries = sum(m.retry_count for m in agent_metrics)
        total_timeouts = sum(1 for m in agent_metrics if m.timed_out)

        retrieval_ms = sum(
            m.duration_ms or 0.0
            for m in agent_metrics if m.agent_name in self._retrieval_agents
        )
        reasoning_ms = sum(
            m.duration_ms or 0.0
            for m in agent_metrics if m.agent_name in self._reasoning_agents
        )
        response_ms = sum(
            m.duration_ms or 0.0
            for m in agent_metrics if m.agent_name in self._response_agents
        )

        # Optional memory snapshot via psutil (best-effort)
        memory_mb: Optional[float] = None
        try:
            import psutil  # type: ignore[import]
            memory_mb = psutil.Process().memory_info().rss / (1024 * 1024)
        except ImportError:
            pass

        return ExecutionMetrics(
            execution_id=execution_id,
            total_duration_ms=total_ms,
            agent_metrics=agent_metrics,
            total_retry_count=total_retries,
            total_timeout_count=total_timeouts,
            retrieval_duration_ms=retrieval_ms or None,
            reasoning_duration_ms=reasoning_ms or None,
            response_generation_duration_ms=response_ms or None,
            memory_rss_mb=memory_mb,
        )
