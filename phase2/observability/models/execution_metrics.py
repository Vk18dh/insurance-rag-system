"""
phase2.observability.models.execution_metrics
==============================================
Per-agent and per-request performance metrics.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AgentMetrics(BaseModel):
    """Timing and reliability metrics for a single agent invocation."""

    agent_name: str = Field(..., description="Agent identifier.")
    start_time_ms: float = Field(..., ge=0.0, description="Epoch milliseconds at start.")
    end_time_ms: Optional[float] = Field(default=None, description="Epoch milliseconds at end.")
    duration_ms: Optional[float] = Field(
        default=None, ge=0.0, description="Wall-clock duration."
    )
    retry_count: int = Field(default=0, ge=0)
    timed_out: bool = Field(default=False)
    succeeded: bool = Field(default=False)


class ExecutionMetrics(BaseModel):
    """
    Aggregated metrics for one complete pipeline execution.

    Fields
    ------
    execution_id        : Links back to the distributed trace.
    total_duration_ms   : End-to-end pipeline latency.
    agent_metrics       : Per-agent breakdown.
    total_retry_count   : Sum of all retries across all agents.
    total_timeout_count : Number of agents that timed out.
    memory_rss_mb       : Resident set size at pipeline completion (optional).
    """

    execution_id: str = Field(..., description="Distributed trace ID.")
    total_duration_ms: float = Field(default=0.0, ge=0.0)
    agent_metrics: List[AgentMetrics] = Field(default_factory=list)
    total_retry_count: int = Field(default=0, ge=0)
    total_timeout_count: int = Field(default=0, ge=0)
    memory_rss_mb: Optional[float] = Field(
        default=None, ge=0.0, description="RSS memory in MB at completion."
    )
    retrieval_duration_ms: Optional[float] = Field(default=None)
    reasoning_duration_ms: Optional[float] = Field(default=None)
    response_generation_duration_ms: Optional[float] = Field(default=None)
