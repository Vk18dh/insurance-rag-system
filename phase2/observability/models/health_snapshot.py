"""
phase2.observability.models.health_snapshot
============================================
Point-in-time system health state produced by HealthMonitor.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List

from pydantic import BaseModel, Field


class HealthSnapshot(BaseModel):
    """
    Captures health metrics at a given moment.

    Fields
    ------
    snapshot_id         : UUID of this health check.
    timestamp_utc       : When the snapshot was taken.
    failure_rate        : Fraction of agents that failed (0.0–1.0).
    avg_latency_ms      : Rolling average pipeline latency.
    retry_frequency     : Average retries per pipeline execution.
    timeout_frequency   : Fraction of executions that had at least one timeout.
    total_executions    : Cumulative execution count since startup.
    is_healthy          : True when all thresholds are within configured bounds.
    """

    snapshot_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    failure_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_latency_ms: float = Field(default=0.0, ge=0.0)
    retry_frequency: float = Field(default=0.0, ge=0.0)
    timeout_frequency: float = Field(default=0.0, ge=0.0, le=1.0)
    total_executions: int = Field(default=0, ge=0)
    is_healthy: bool = Field(default=True)
    unhealthy_reasons: List[str] = Field(default_factory=list)
