"""
phase2.models.retrieval_result
================================

The structured output of the Retrieval Agent.

Design:
    RetrievalResult is the single object passed from the Retrieval Agent to all
    downstream agents (Verification Agent, Reasoning Agent, etc.).

    It contains:
        - The original QueryContext (unchanged, for context propagation)
        - Ranked evidence chunks (RetrievedChunk list)
        - RetrievalMetrics (timing, quality, confidence)
        - Validation warnings (non-fatal issues found during retrieval)
        - Retrieval strategy metadata

    Never returns raw lists. All evidence is wrapped in this typed container.

Part 3 (Verification Agent) integration contract:
    The Verification Agent consumes:
        result.ranked_evidence          → List[RetrievedChunk] (primary input)
        result.query_context            → QueryContext (for query-evidence alignment)
        result.metrics.retrieval_confidence → float (to scale verification intensity)
        result.to_verification_input()  → typed Dict for the verification pipeline
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from phase2.models.query_context import QueryContext
from phase2.models.retrieved_chunk import RetrievedChunk
from phase2.models.retrieval_metrics import RetrievalMetrics


class RetrievalWarning(BaseModel):
    """
    A non-fatal warning raised during retrieval validation.

    Warnings do NOT stop the pipeline. They signal potential quality issues
    that downstream agents should be aware of.

    Severity levels:
        LOW    — informational, no downstream impact expected
        MEDIUM — downstream agents should proceed with additional caution
        HIGH   — retrieval quality may be insufficient for confident answers
    """

    code: str = Field(..., description="Machine-readable warning code (e.g. 'LOW_CHUNK_COUNT').")
    message: str = Field(..., description="Human-readable description of the issue.")
    severity: str = Field(
        default="MEDIUM",
        description="Warning severity: LOW | MEDIUM | HIGH.",
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional structured context for the warning (e.g. threshold, actual value).",
    )


class RetrievalResult(BaseModel):
    """
    Primary output of the Retrieval Agent.

    This is the single strongly-typed object returned by RetrievalAgent.retrieve().
    It functions as the integration contract between the Retrieval Agent (Part 2)
    and all downstream agents (Part 3 Verification Agent, Part 4 Reasoning Agent, etc.).

    Fields:
        query_context       : Original QueryContext from Part 1 (unmodified).
        ranked_evidence     : Ranked, deduplicated, validated RetrievedChunk list.
        metrics             : Full performance and quality metrics.
        warnings            : Non-fatal issues. Empty list if retrieval was clean.
        retrieval_strategy  : Name of the strategy used (for audit/diagnostics).
        is_successful       : True when at least one valid chunk was retrieved.
        fallback_used       : True when a fallback retrieval strategy was applied.
    """

    # ── Context propagation ───────────────────────────────────────────────────
    query_context: QueryContext = Field(
        ...,
        description="The QueryContext from Part 1. Passed through unchanged.",
    )

    # ── Evidence ──────────────────────────────────────────────────────────────
    ranked_evidence: List[RetrievedChunk] = Field(
        default_factory=list,
        description=(
            "Ranked, deduplicated, validated evidence chunks. "
            "Ordered by ranking_score descending. The Verification Agent "
            "iterates this list to assess evidence quality."
        ),
    )

    # ── Diagnostics ───────────────────────────────────────────────────────────
    metrics: RetrievalMetrics = Field(
        default_factory=RetrievalMetrics,
        description="Full retrieval performance and quality metrics.",
    )
    warnings: List[RetrievalWarning] = Field(
        default_factory=list,
        description="Non-fatal validation warnings. Empty on clean retrieval.",
    )

    # ── Strategy metadata ─────────────────────────────────────────────────────
    retrieval_strategy: str = Field(
        default="default",
        description="Name of the retrieval strategy applied (from settings).",
    )
    bm25_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="BM25 weight actually used during retrieval.",
    )
    vector_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Vector weight actually used during retrieval.",
    )

    # ── Status ────────────────────────────────────────────────────────────────
    is_successful: bool = Field(
        default=False,
        description="True when at least one valid chunk was retrieved and validated.",
    )
    fallback_used: bool = Field(
        default=False,
        description="True when the default fallback strategy was applied instead "
                    "of the query-specific strategy.",
    )

    # =========================================================================
    # Helper methods
    # =========================================================================

    def has_evidence(self) -> bool:
        """Return True when at least one ranked evidence chunk is available."""
        return len(self.ranked_evidence) > 0

    def top_chunks(self, n: int = 5) -> List[RetrievedChunk]:
        """
        Return the top-n ranked evidence chunks.

        Chunks are already ordered by ranking_score descending.

        Args:
            n: Maximum number of chunks to return.

        Returns:
            List of up to n RetrievedChunk objects.
        """
        return self.ranked_evidence[:n]

    def unique_sources(self) -> List[str]:
        """Return a deduplicated list of source document filenames."""
        seen = set()
        sources = []
        for chunk in self.ranked_evidence:
            if chunk.source_document not in seen:
                seen.add(chunk.source_document)
                sources.append(chunk.source_document)
        return sources

    def has_warnings(self) -> bool:
        """Return True if any warnings were raised during retrieval."""
        return len(self.warnings) > 0

    def high_severity_warnings(self) -> List[RetrievalWarning]:
        """Return only HIGH severity warnings."""
        return [w for w in self.warnings if w.severity == "HIGH"]

    def to_verification_input(self) -> Dict[str, Any]:
        """
        Produce the integration contract for the Verification Agent (Part 3).

        The Verification Agent will consume this dict to assess evidence quality
        and align retrieved evidence with the user's query intent.

        Returns:
            Dict with: query_context fields, evidence list, metrics summary,
                       warnings, source documents, retrieval_confidence.

        Note:
            This is the Part 3 integration contract — equivalent to
            QueryContext.to_retrieval_input() in Part 1.
        """
        return {
            # Query context
            "query": self.query_context.normalized_query or self.query_context.original_query,
            "intent": self.query_context.intent.intent.value if self.query_context.intent else None,
            "confidence": self.query_context.intent.confidence if self.query_context.intent else 0.0,
            "classification": (
                self.query_context.classification.value
                if self.query_context.classification else None
            ),
            "is_ambiguous": (
                self.query_context.ambiguity.is_ambiguous
                if self.query_context.ambiguity else False
            ),
            "query_id": (
                self.query_context.metadata.query_id
                if self.query_context.metadata else None
            ),
            # Evidence
            "evidence": [chunk.to_evidence_dict() for chunk in self.ranked_evidence],
            "evidence_count": len(self.ranked_evidence),
            "source_documents": self.unique_sources(),
            # Quality signals
            "retrieval_confidence": self.metrics.retrieval_confidence,
            "retrieval_strategy": self.retrieval_strategy,
            "validation_passed": self.metrics.validation_passed,
            "warnings": [
                {"code": w.code, "severity": w.severity, "message": w.message}
                for w in self.warnings
            ],
            # Retrieval metadata
            "metrics_id": self.metrics.metrics_id,
        }
