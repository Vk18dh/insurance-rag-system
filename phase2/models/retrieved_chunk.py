"""
phase2.models.retrieved_chunk
===============================

Typed model for a single evidence chunk returned by the Phase 1 retriever.

Design:
    RetrievedChunk is the single integration boundary between Phase 1 (which
    returns raw dicts) and Phase 2 (which operates on typed Pydantic models).

    The Phase1RetrieverAdapter converts Phase 1 dicts to RetrievedChunk objects.
    No other module in Phase 2 ever accesses Phase 1 dicts directly.

Fields:
    chunk_id          : str    — Unique ID assigned by Phase 1 indexer.
    text              : str    — Chunk content (verbatim from Phase 1).
    source_document   : str    — Filename of the source PDF.
    page_number       : str    — Page reference (str to handle 'N/A' from Phase 1).
    section_title     : str    — Section heading from the source document.
    bm25_score        : float  — Raw BM25 relevance score (0 if not retrieved by BM25).
    vector_score      : float  — Cosine similarity score (0 if not retrieved by vector).
    combined_score    : float  — Weighted hybrid score used for initial ordering.
    retrieval_source  : RetrievalSource — Which system returned this chunk.
    rank              : int    — 1-indexed rank after final ranking stage.
    ranking_score     : float  — Final score assigned by the ranking service.
    metadata_complete : bool   — True when all mandatory metadata fields are present.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator


class RetrievalSource(str, Enum):
    """
    Indicates which retrieval backend(s) returned this chunk.

    Used for audit logging and ranking signal computation.
    StrEnum: values compare equal to plain strings (e.g. 'bm25').
    """
    BM25   = "bm25"
    VECTOR = "vector"
    HYBRID = "hybrid"   # chunk returned by both BM25 and vector


class RetrievedChunk(BaseModel):
    """
    Strongly-typed representation of a single retrieved evidence chunk.

    Produced exclusively by Phase1RetrieverAdapter.
    Consumed by: DuplicateRemovalService, ReRankingService, RetrievalValidationService,
                 and ultimately packaged into RetrievalResult.

    Immutable after construction — all fields should be set at instantiation.
    """

    # ── Identity ──────────────────────────────────────────────────────────────
    chunk_id: str = Field(
        ...,
        description="Unique chunk identifier (UUID from Phase 1 indexer).",
    )
    text: str = Field(
        ...,
        min_length=1,
        description="Verbatim chunk text as stored in the Phase 1 index.",
    )

    # ── Source metadata ───────────────────────────────────────────────────────
    source_document: str = Field(
        default="unknown",
        description="Filename of the originating source PDF.",
    )
    page_number: str = Field(
        default="N/A",
        description="Page reference string (may be 'N/A' for metadata-incomplete chunks).",
    )
    section_title: str = Field(
        default="Unknown",
        description="Section heading from the source document.",
    )

    # ── Retrieval scores ──────────────────────────────────────────────────────
    bm25_score: float = Field(
        default=0.0,
        ge=0.0,
        description="Raw BM25 relevance score. 0.0 if chunk was not retrieved by BM25.",
    )
    vector_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Cosine similarity score [0, 1]. 0.0 if not retrieved by vector search.",
    )
    combined_score: float = Field(
        default=0.0,
        ge=0.0,
        description="Weighted hybrid score used for initial ordering before re-ranking.",
    )

    # ── Source ────────────────────────────────────────────────────────────────
    retrieval_source: RetrievalSource = Field(
        default=RetrievalSource.HYBRID,
        description="Which retrieval backend returned this chunk.",
    )

    # ── Post-ranking ──────────────────────────────────────────────────────────
    rank: int = Field(
        default=0,
        ge=0,
        description="1-indexed rank after re-ranking. 0 = not yet ranked.",
    )
    ranking_score: float = Field(
        default=0.0,
        ge=0.0,
        description="Final composite score assigned by the ranking service.",
    )

    # ── Quality flags ─────────────────────────────────────────────────────────
    metadata_complete: bool = Field(
        default=True,
        description="False when any mandatory metadata field (source_document, page_number) "
                    "is missing or 'unknown'/'N/A'.",
    )

    # ── Raw pass-through ──────────────────────────────────────────────────────
    raw_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Original metadata dict from Phase 1 (preserved for auditability).",
    )

    # =========================================================================
    # Validators
    # =========================================================================

    @field_validator("chunk_id")
    @classmethod
    def validate_chunk_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("chunk_id must not be empty.")
        return v.strip()

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Chunk text must not be empty.")
        return v

    # =========================================================================
    # Helper methods
    # =========================================================================

    def has_valid_page(self) -> bool:
        """Return True if page_number is a real page reference (not 'N/A' or empty)."""
        return bool(self.page_number and self.page_number.strip() not in ("N/A", "n/a", "", "None"))

    def is_policy_specific(self) -> bool:
        """Return True if the chunk has a known source document."""
        return self.source_document.lower() not in ("unknown", "", "n/a")

    def citation(self) -> str:
        """
        Return a human-readable citation string for display.

        Example: 'Jeevan_Shagun.pdf — Page 12 (Free Look Period)'
        """
        return (
            f"{self.source_document} — Page {self.page_number} ({self.section_title})"
        )

    def to_evidence_dict(self) -> Dict[str, Any]:
        """
        Return a minimal dict for downstream agents (Verification Agent).

        Contains only the fields needed for evidence assessment.
        """
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "source_document": self.source_document,
            "page_number": self.page_number,
            "section_title": self.section_title,
            "ranking_score": self.ranking_score,
            "rank": self.rank,
            "retrieval_source": self.retrieval_source.value,
            "citation": self.citation(),
        }
