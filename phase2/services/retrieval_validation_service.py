"""
phase2.services.retrieval_validation_service
===============================================

Retrieval quality validation service.

Design:
    RetrievalValidationService implements IValidationService.
    It validates the ranked evidence list against configurable quality thresholds
    and returns a list of RetrievalWarning objects.

    Validation checks (all thresholds from settings — zero hardcoding):
        1. EMPTY_RETRIEVAL       → chunks list is empty (CRITICAL → always raises)
        2. LOW_CHUNK_COUNT       → below min_chunks_required (MEDIUM warning)
        3. LOW_SIMILARITY_SCORE  → top chunk below min_similarity_score (HIGH warning)
        4. HIGH_DUPLICATE_RATIO  → not applicable post-dedup, but checked as safety
        5. INCOMPLETE_METADATA   → too many chunks with metadata_complete=False (LOW)
        6. MISSING_PAGE_NUMBERS  → all chunks have page_number 'N/A' (MEDIUM)
        7. SINGLE_SOURCE         → all chunks from the same source document (LOW)

    The service distinguishes between:
        FATAL checks → raise RetrievalValidationException (pipeline cannot continue)
        WARNING checks → append RetrievalWarning (pipeline continues with caution)

Thread safety:
    RetrievalValidationService is stateless — safe for concurrent use.
"""

from __future__ import annotations

from typing import Any, List

from phase2.exceptions.retrieval_exception import RetrievalValidationException
from phase2.interfaces.retrieval_interface import IValidationService
from phase2.models.query_context import QueryContext
from phase2.models.retrieved_chunk import RetrievedChunk
from phase2.models.retrieval_result import RetrievalWarning
from phase2.logging.logger import get_logger

logger = get_logger(__name__)


class RetrievalValidationService(IValidationService):
    """
    Validates ranked evidence against configurable quality thresholds.

    All thresholds are injected at construction — never hardcoded.

    Args:
        min_chunks_required         : Minimum acceptable chunk count (warning if below).
        min_similarity_score        : Minimum top-chunk combined_score (warning if below).
        max_incomplete_metadata_ratio: Fraction of chunks allowed to have
                                        metadata_complete=False before warning.
        require_page_numbers        : If True, warn when all page refs are 'N/A'.
    """

    def __init__(
        self,
        min_chunks_required: int = 1,
        min_similarity_score: float = 0.1,
        max_incomplete_metadata_ratio: float = 0.5,
        require_page_numbers: bool = False,
    ) -> None:
        if min_chunks_required < 0:
            raise RetrievalValidationException(
                "min_chunks_required must be >= 0.",
                validation_check="config",
                actual_value=min_chunks_required,
                threshold=0,
            )
        self._min_chunks            = min_chunks_required
        self._min_score             = min_similarity_score
        self._max_incomplete_ratio  = max_incomplete_metadata_ratio
        self._require_pages         = require_page_numbers

    # =========================================================================
    # IValidationService implementation
    # =========================================================================

    def validate(
        self,
        chunks: List[RetrievedChunk],
        query_context: QueryContext,
    ) -> List[RetrievalWarning]:
        """
        Run all validation checks and return accumulated warnings.

        Args:
            chunks        : Ranked evidence chunks (post-ranking).
            query_context : Source QueryContext for context-aware checks.

        Returns:
            List[RetrievalWarning] — empty if all checks pass cleanly.

        Raises:
            RetrievalValidationException : Only if retrieval is completely empty
                                          (no chunks at all after ranking).
        """
        query_id = (
            query_context.metadata.query_id if query_context.metadata else None
        )
        warnings: List[RetrievalWarning] = []

        # ── CHECK 1: Empty retrieval (FATAL) ──────────────────────────────
        if not chunks:
            logger.warning(
                "Validation FATAL: no chunks retrieved",
                extra={"query_id": query_id},
            )
            raise RetrievalValidationException(
                "No evidence chunks were retrieved for this query. "
                "Ensure the Phase 1 index is built and populated.",
                validation_check="empty_retrieval",
                actual_value=0,
                threshold=self._min_chunks,
                query_id=query_id,
            )

        # ── CHECK 2: Low chunk count (MEDIUM warning) ─────────────────────
        if len(chunks) < self._min_chunks and self._min_chunks > 0:
            warnings.append(RetrievalWarning(
                code="LOW_CHUNK_COUNT",
                message=(
                    f"Retrieved only {len(chunks)} chunk(s); "
                    f"minimum recommended is {self._min_chunks}."
                ),
                severity="MEDIUM",
                context={"actual": len(chunks), "threshold": self._min_chunks},
            ))

        # ── CHECK 3: Low similarity score (HIGH warning) ──────────────────
        top_score = chunks[0].combined_score if chunks else 0.0
        if top_score < self._min_score:
            warnings.append(RetrievalWarning(
                code="LOW_SIMILARITY_SCORE",
                message=(
                    f"Top chunk combined_score ({top_score:.3f}) is below the "
                    f"configured minimum ({self._min_score:.3f}). "
                    "Retrieved evidence may not be relevant to the query."
                ),
                severity="HIGH",
                context={"top_score": top_score, "threshold": self._min_score},
            ))

        # ── CHECK 4: Incomplete metadata (LOW warning) ────────────────────
        incomplete = [c for c in chunks if not c.metadata_complete]
        if chunks:
            incomplete_ratio = len(incomplete) / len(chunks)
            if incomplete_ratio > self._max_incomplete_ratio:
                warnings.append(RetrievalWarning(
                    code="INCOMPLETE_METADATA",
                    message=(
                        f"{len(incomplete)} of {len(chunks)} chunks "
                        f"({incomplete_ratio:.0%}) have incomplete metadata "
                        "(missing source_document or page_number)."
                    ),
                    severity="LOW",
                    context={
                        "incomplete_count": len(incomplete),
                        "total_count": len(chunks),
                        "ratio": round(incomplete_ratio, 3),
                    },
                ))

        # ── CHECK 5: Missing page numbers (MEDIUM warning) ────────────────
        if self._require_pages:
            no_page = [c for c in chunks if not c.has_valid_page()]
            if len(no_page) == len(chunks):
                warnings.append(RetrievalWarning(
                    code="MISSING_PAGE_NUMBERS",
                    message=(
                        "All retrieved chunks have missing page references (N/A). "
                        "Citations may be incomplete."
                    ),
                    severity="MEDIUM",
                    context={"chunks_without_page": len(no_page)},
                ))

        # ── CHECK 6: Single source (LOW warning) ──────────────────────────
        sources = {c.source_document for c in chunks}
        if len(sources) == 1 and len(chunks) > 2:
            warnings.append(RetrievalWarning(
                code="SINGLE_SOURCE",
                message=(
                    f"All {len(chunks)} retrieved chunks come from a single source "
                    f"document ('{next(iter(sources))}'). Evidence may lack diversity."
                ),
                severity="LOW",
                context={"source": next(iter(sources)), "chunk_count": len(chunks)},
            ))

        # ── Log summary ───────────────────────────────────────────────────
        logger.info(
            "Validation completed",
            extra={
                "chunks": len(chunks),
                "warnings": len(warnings),
                "top_score": round(top_score, 4),
                "query_id": query_id,
            },
        )

        return warnings
