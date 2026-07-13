"""
phase2.observability.health.health_monitor
==========================================
Concrete IHealthMonitor implementation.

Evaluates rolling system health against configurable thresholds.
All thresholds and window size are injected — never hardcoded.
"""

from __future__ import annotations

import threading
from collections import deque
from typing import Deque, List, Tuple

from phase2.observability.interfaces.observability_interface import IHealthMonitor
from phase2.observability.models.health_snapshot import HealthSnapshot
from phase2.observability.models.alert_event import AlertEvent, AlertSeverity
from phase2.observability.exceptions import HealthMonitorException


class HealthMonitor(IHealthMonitor):
    """
    Thread-safe rolling health evaluator.

    Parameters
    ----------
    failure_rate_threshold     : Maximum tolerable fraction of failed executions.
    avg_latency_ms_threshold   : Maximum tolerable average latency in ms.
    window_size                : Rolling window size (number of executions to track).
    """

    def __init__(
        self,
        failure_rate_threshold: float,
        avg_latency_ms_threshold: float,
        window_size: int = 100,
    ) -> None:
        if window_size < 1:
            raise HealthMonitorException(
                f"window_size must be >= 1, got {window_size}"
            )
        self._failure_rate_threshold = failure_rate_threshold
        self._avg_latency_threshold = avg_latency_ms_threshold

        # Rolling window: each entry is (succeeded, duration_ms, had_timeout, retries)
        self._window: Deque[Tuple[bool, float, bool, int]] = deque(maxlen=window_size)
        self._pending_alerts: List[AlertEvent] = []
        self._lock = threading.Lock()
        self._total_executions = 0

    # ------------------------------------------------------------------
    # IHealthMonitor implementation
    # ------------------------------------------------------------------

    def record_execution_outcome(
        self,
        execution_id: str,
        succeeded: bool,
        duration_ms: float,
        had_timeout: bool,
        retry_count: int,
    ) -> None:
        with self._lock:
            self._window.append((succeeded, duration_ms, had_timeout, retry_count))
            self._total_executions += 1
            self._evaluate(execution_id)

    def get_health_snapshot(self) -> HealthSnapshot:
        with self._lock:
            return self._compute_snapshot()

    def get_pending_alerts(self) -> List[AlertEvent]:
        with self._lock:
            alerts = list(self._pending_alerts)
            self._pending_alerts.clear()
            return alerts

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _compute_snapshot(self) -> HealthSnapshot:
        """Must be called with self._lock held."""
        if not self._window:
            return HealthSnapshot(total_executions=self._total_executions)

        n = len(self._window)
        failures = sum(1 for s, _, _, _ in self._window if not s)
        failure_rate = failures / n
        avg_latency = sum(d for _, d, _, _ in self._window) / n
        timeouts = sum(1 for _, _, t, _ in self._window if t)
        timeout_freq = timeouts / n
        avg_retries = sum(r for _, _, _, r in self._window) / n

        unhealthy: List[str] = []
        if failure_rate > self._failure_rate_threshold:
            unhealthy.append(
                f"failure_rate={failure_rate:.2%} > threshold={self._failure_rate_threshold:.2%}"
            )
        if avg_latency > self._avg_latency_threshold:
            unhealthy.append(
                f"avg_latency={avg_latency:.1f}ms > threshold={self._avg_latency_threshold:.1f}ms"
            )

        return HealthSnapshot(
            failure_rate=failure_rate,
            avg_latency_ms=avg_latency,
            retry_frequency=avg_retries,
            timeout_frequency=timeout_freq,
            total_executions=self._total_executions,
            is_healthy=len(unhealthy) == 0,
            unhealthy_reasons=unhealthy,
        )

    def _evaluate(self, execution_id: str) -> None:
        """Generate alert events when thresholds are breached. Called with lock held."""
        snapshot = self._compute_snapshot()

        if snapshot.failure_rate > self._failure_rate_threshold:
            self._pending_alerts.append(AlertEvent(
                execution_id=execution_id,
                severity=AlertSeverity.HIGH,
                metric_name="failure_rate",
                observed=snapshot.failure_rate,
                threshold=self._failure_rate_threshold,
                message=(
                    f"Pipeline failure rate {snapshot.failure_rate:.2%} exceeds "
                    f"threshold {self._failure_rate_threshold:.2%}."
                ),
            ))

        if snapshot.avg_latency_ms > self._avg_latency_threshold:
            self._pending_alerts.append(AlertEvent(
                execution_id=execution_id,
                severity=AlertSeverity.MEDIUM,
                metric_name="avg_latency_ms",
                observed=snapshot.avg_latency_ms,
                threshold=self._avg_latency_threshold,
                message=(
                    f"Average pipeline latency {snapshot.avg_latency_ms:.1f}ms exceeds "
                    f"threshold {self._avg_latency_threshold:.1f}ms."
                ),
            ))
