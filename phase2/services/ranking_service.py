"""
phase2.services.ranking_service
==================================

Evidence re-ranking service for the Retrieval Agent.

Design:
    WeightedRankingService implements IRankingService and ranks RetrievedChunk
    objects using a configurable multi-signal scoring formula:

        ranking_score = (
            retrieval_score_weight * normalised_combined_score
          + keyword_overlap_weight * keyword_overlap_ratio
          + metadata_completeness_weight * metadata_completeness_score
        )

    All weights come from RankingSettings in Phase2Settings.
    The formula is additive and extensible — future signals (BM25/vector
    independently, entity overlap, policy_names boost) can be added without
    changing the interface.

    Implements IRankingService — can be replaced with an LLM re-ranker in
    future parts by providing a different IRankingService implementation.

Thread safety:
    WeightedRankingService is stateless. Parallel calls are safe.
"""

from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional, Set

from phase2.exceptions.retrieval_exception import RankingException
from phase2.interfaces.retrieval_interface import IRankingService
from phase2.models.retrieved_chunk import RetrievedChunk
from phase2.logging.logger import get_logger

logger = get_logger(__name__)


class WeightedRankingService(IRankingService):
    """
    Multi-signal weighted ranking for retrieved evidence chunks.

    Ranking signals:
        1. normalised_combined_score  — Phase 1 hybrid retrieval quality.
        2. keyword_overlap_ratio      — token overlap between query and chunk text.
        3. metadata_completeness      — 1.0 if source_document + page_number are valid.

    All signal weights are injected from settings — zero hardcoded constants.

    Args:
        retrieval_score_weight       : Weight for the normalised combined_score signal.
        keyword_overlap_weight       : Weight for query-text token overlap signal.
        metadata_completeness_weight : Weight for metadata completeness signal.
        min_ranking_score            : Minimum ranking_score to include in the output.
                                       Chunks below this are filtered out.
    """

    def __init__(
        self,
        retrieval_score_weight: float,
        keyword_overlap_weight: float,
        metadata_completeness_weight: float,
        min_ranking_score: float = 0.0,
    ) -> None:
        total = retrieval_score_weight + keyword_overlap_weight + metadata_completeness_weight
        if not (0.0 < total <= 3.0):
            raise RankingException(
                f"Sum of ranking weights must be in (0, 3.0], got {total:.3f}.",
                ranking_step="weight_validation",
            )
        if min_ranking_score < 0.0:
            raise RankingException(
                "min_ranking_score must be >= 0.0.",
                ranking_step="weight_validation",
            )

        self._retrieval_w    = retrieval_score_weight
        self._keyword_w      = keyword_overlap_weight
        self._metadata_w     = metadata_completeness_weight
        self._min_score      = min_ranking_score

    # =========================================================================
    # IRankingService implementation
    # =========================================================================

    def rank(
        self,
        chunks: List[RetrievedChunk],
        query: str,
        strategy_context: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedChunk]:
        """
        Rank chunks using the weighted multi-signal formula.

        Args:
            chunks           : Merged, deduplicated chunks from RetrievalService.
            query            : Normalised query string for keyword overlap.
            strategy_context : Optional strategy info (currently unused; reserved
                               for future entity-boost and policy-boost signals).

        Returns:
            Chunks sorted by ranking_score descending.
            Each chunk's `ranking_score` and `rank` fields are populated.
            Chunks with ranking_score < min_ranking_score are removed.

        Raises:
            RankingException : If any ranking step fails.
        """
        if not chunks:
            logger.debug("Ranking received empty chunk list — returning empty.")
            return []

        start = time.monotonic()

        try:
            query_tokens = self._tokenize(query)
            normalised   = self._normalise_combined_scores(chunks)
            scored       = self._compute_scores(normalised, query_tokens)
            filtered     = [c for c in scored if c.ranking_score >= self._min_score]
            filtered.sort(key=lambda c: c.ranking_score, reverse=True)

            # Assign 1-indexed rank
            for i, chunk in enumerate(filtered, 1):
                object.__setattr__(chunk, "rank", i)

        except RankingException:
            raise
        except Exception as exc:
            raise RankingException(
                f"Ranking failed: {type(exc).__name__}: {exc}",
                ranking_step="score_computation",
                chunk_count=len(chunks),
            ) from exc

        elapsed_ms = (time.monotonic() - start) * 1000
        logger.info(
            "Ranking completed",
            extra={
                "input_count": len(chunks),
                "output_count": len(filtered),
                "filtered_out": len(chunks) - len(filtered),
                "top_score": round(filtered[0].ranking_score, 4) if filtered else 0.0,
                "elapsed_ms": round(elapsed_ms, 1),
            },
        )

        return filtered

    # =========================================================================
    # Private helpers
    # =========================================================================

    def _compute_scores(
        self,
        chunks: List[RetrievedChunk],
        query_tokens: Set[str],
    ) -> List[RetrievedChunk]:
        """Compute ranking_score for each chunk and set the field."""
        for chunk in chunks:
            retrieval_signal    = chunk.combined_score  # already normalised
            keyword_signal      = self._keyword_overlap(chunk.text, query_tokens)
            metadata_signal     = 1.0 if chunk.metadata_complete else 0.0

            score = (
                self._retrieval_w * retrieval_signal
                + self._keyword_w * keyword_signal
                + self._metadata_w * metadata_signal
            )
            object.__setattr__(chunk, "ranking_score", round(score, 6))

        return chunks

    @staticmethod
    def _normalise_combined_scores(chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        """Min-max normalise combined_score to [0, 1] for the ranking formula."""
        scores = [c.combined_score for c in chunks]
        min_s, max_s = min(scores), max(scores)
        spread = max_s - min_s if max_s != min_s else 1.0
        for chunk in chunks:
            norm = (chunk.combined_score - min_s) / spread
            object.__setattr__(chunk, "combined_score", norm)
        return chunks

    @staticmethod
    def _keyword_overlap(text: str, query_tokens: Set[str]) -> float:
        """
        Compute the ratio of query tokens that appear in the chunk text.

        Returns:
            float in [0, 1] — 0.0 if no overlap, 1.0 if all query tokens appear.
        """
        if not query_tokens:
            return 0.0
        chunk_tokens = set(re.findall(r"\b[a-z0-9]+\b", text.lower()))
        overlap = query_tokens.intersection(chunk_tokens)
        return len(overlap) / len(query_tokens)

    @staticmethod
    def _tokenize(text: str) -> Set[str]:
        """Simple lowercase tokeniser (stopword removal omitted for speed)."""
        return set(re.findall(r"\b[a-z0-9]{3,}\b", text.lower()))
