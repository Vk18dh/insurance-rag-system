"""
phase2.models.retrieval_metrics
================================

Performance and quality metrics for a single Retrieval Agent execution.

Stored in RetrievalResult and used for:
    - Orchestrator diagnostics
    - Performance monitoring
    - Retrieval confidence signals for downstream agents
    - Audit logging

All timing values are in milliseconds. All score values are in [0, 1].
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RetrievalMetrics(BaseModel):
    """
    Comprehensive metrics for a single retrieval execution cycle.

    Contains timing, chunk counts, score distributions, and a computed
    retrieval_confidence value that downstream agents use to adjust their
    processing strategy.

    Timeline:
        retrieval_started_at → Phase 1 calls begin
        retrieval_ended_at   → Phase 1 calls complete
        ranking_ended_at     → ranking complete
        validation_ended_at  → validation complete

    Args:
        metrics_id     : UUID for correlation with audit logs.
        query_id       : Copied from QueryMetadata.query_id for correlation.
        strategy_used  : Which retrieval strategy was selected (e.g. 'policy_specific').
    """

    metrics_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="UUID for correlation with audit log entries.",
    )
    query_id: Optional[str] = Field(
        default=None,
        description="QueryMetadata.query_id — copied for cross-agent correlation.",
    )

    # ── Strategy ──────────────────────────────────────────────────────────────
    strategy_used: str = Field(
        default="default",
        description="Name of retrieval strategy selected (e.g. 'policy_specific', 'regulatory').",
    )
    bm25_weight_used: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="BM25 weight applied during this retrieval.",
    )
    vector_weight_used: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Vector weight applied during this retrieval.",
    )

    # ── Timing (milliseconds) ─────────────────────────────────────────────────
    retrieval_start_ms: Optional[float] = Field(
        default=None, description="Monotonic clock value when Phase 1 calls began (ms)."
    )
    retrieval_end_ms: Optional[float] = Field(
        default=None, description="Monotonic clock value when Phase 1 calls completed (ms)."
    )
    ranking_end_ms: Optional[float] = Field(
        default=None, description="Monotonic clock value when ranking completed (ms)."
    )
    validation_end_ms: Optional[float] = Field(
        default=None, description="Monotonic clock value when validation completed (ms)."
    )
    total_duration_ms: Optional[float] = Field(
        default=None, description="Total end-to-end Retrieval Agent duration (ms)."
    )

    # ── Chunk counts ──────────────────────────────────────────────────────────
    bm25_chunks_retrieved: int = Field(
        default=0, ge=0, description="Number of chunks returned by BM25 search."
    )
    vector_chunks_retrieved: int = Field(
        default=0, ge=0, description="Number of chunks returned by vector search."
    )
    chunks_before_dedup: int = Field(
        default=0, ge=0, description="Total chunks before duplicate removal."
    )
    chunks_after_dedup: int = Field(
        default=0, ge=0, description="Chunks remaining after duplicate removal."
    )
    chunks_after_ranking: int = Field(
        default=0, ge=0, description="Final number of ranked chunks returned."
    )
    duplicates_removed: int = Field(
        default=0, ge=0, description="Number of duplicate chunks detected and removed."
    )

    # ── Score summaries ───────────────────────────────────────────────────────
    avg_bm25_score: float = Field(
        default=0.0, ge=0.0, description="Mean BM25 score across retrieved chunks."
    )
    avg_vector_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Mean cosine similarity score."
    )
    avg_combined_score: float = Field(
        default=0.0, ge=0.0, description="Mean combined hybrid score."
    )
    avg_ranking_score: float = Field(
        default=0.0, ge=0.0, description="Mean final ranking score."
    )
    top_chunk_score: float = Field(
        default=0.0, ge=0.0, description="Highest ranking score in the result set."
    )

    # ── Quality signals ───────────────────────────────────────────────────────
    retrieval_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description=(
            "Composite retrieval confidence [0, 1]. "
            "Computed from top_chunk_score, avg_combined_score, and chunk coverage. "
            "Downstream agents (Verification Agent) use this to scale their confidence."
        ),
    )
    metadata_completeness_ratio: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Fraction of returned chunks with complete metadata.",
    )
    validation_passed: bool = Field(
        default=True,
        description="False if any validation check failed.",
    )
    warning_count: int = Field(
        default=0, ge=0, description="Number of non-fatal validation warnings."
    )

    # ── Timestamp ─────────────────────────────────────────────────────────────
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 UTC timestamp when this metrics object was created.",
    )

    # =========================================================================
    # Derived property helpers
    # =========================================================================

    def retrieval_duration_ms(self) -> Optional[float]:
        """Phase 1 call duration only (excluding ranking and validation)."""
        if self.retrieval_start_ms is not None and self.retrieval_end_ms is not None:
            return self.retrieval_end_ms - self.retrieval_start_ms
        return None

    def ranking_duration_ms(self) -> Optional[float]:
        """Ranking-only duration."""
        if self.retrieval_end_ms is not None and self.ranking_end_ms is not None:
            return self.ranking_end_ms - self.retrieval_end_ms
        return None

    def to_summary_dict(self) -> Dict[str, Any]:
        """
        Return a concise dict for structured logging.

        Excludes raw timing internals — safe for log emission.
        """
        return {
            "metrics_id": self.metrics_id,
            "query_id": self.query_id,
            "strategy": self.strategy_used,
            "chunks_final": self.chunks_after_ranking,
            "duplicates_removed": self.duplicates_removed,
            "top_score": round(self.top_chunk_score, 4),
            "retrieval_confidence": round(self.retrieval_confidence, 4),
            "total_ms": round(self.total_duration_ms or 0.0, 1),
            "validation_passed": self.validation_passed,
            "warnings": self.warning_count,
        }
