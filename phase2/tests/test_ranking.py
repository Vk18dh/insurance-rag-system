"""
phase2.tests.test_ranking
============================

Unit tests for WeightedRankingService.

Coverage:
    - Correct ranking_score formula
    - Rank assignment (1-indexed)
    - Normalisation of combined_score
    - Keyword overlap calculation
    - Metadata completeness signal
    - min_ranking_score filtering
    - Empty input handling
    - Invalid weights validation
    - RankingException propagation
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from phase2.models.retrieved_chunk import RetrievedChunk, RetrievalSource
from phase2.services.ranking_service import WeightedRankingService
from phase2.exceptions.retrieval_exception import RankingException


# ===========================================================================
# Helpers
# ===========================================================================

def make_chunk(
    chunk_id: str = "c1",
    text: str = "Insurance policy covers claim submission process.",
    combined_score: float = 0.5,
    bm25_score: float = 0.3,
    vector_score: float = 0.7,
    source_document: str = "policy.pdf",
    page_number: str = "12",
    metadata_complete: bool = True,
    retrieval_source: RetrievalSource = RetrievalSource.HYBRID,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        text=text,
        combined_score=combined_score,
        bm25_score=bm25_score,
        vector_score=vector_score,
        source_document=source_document,
        page_number=page_number,
        metadata_complete=metadata_complete,
        retrieval_source=retrieval_source,
    )


def make_service(
    retrieval_w: float = 0.6,
    keyword_w: float = 0.2,
    metadata_w: float = 0.2,
    min_score: float = 0.0,
) -> WeightedRankingService:
    return WeightedRankingService(
        retrieval_score_weight=retrieval_w,
        keyword_overlap_weight=keyword_w,
        metadata_completeness_weight=metadata_w,
        min_ranking_score=min_score,
    )


# ===========================================================================
# Initialisation
# ===========================================================================

class TestWeightedRankingServiceInit:
    def test_valid_weights_accepted(self):
        svc = make_service()
        assert svc is not None

    def test_all_zero_weights_raises(self):
        with pytest.raises(RankingException):
            WeightedRankingService(
                retrieval_score_weight=0.0,
                keyword_overlap_weight=0.0,
                metadata_completeness_weight=0.0,
            )

    def test_negative_min_score_raises(self):
        with pytest.raises(RankingException):
            WeightedRankingService(
                retrieval_score_weight=0.6,
                keyword_overlap_weight=0.2,
                metadata_completeness_weight=0.2,
                min_ranking_score=-0.1,
            )


# ===========================================================================
# Empty input
# ===========================================================================

class TestEmptyInput:
    def test_empty_chunks_returns_empty_list(self):
        svc = make_service()
        result = svc.rank([], query="claim submission")
        assert result == []


# ===========================================================================
# Ranking score formula
# ===========================================================================

class TestRankingScoreFormula:
    def test_single_chunk_gets_nonzero_score(self):
        svc = make_service()
        chunk = make_chunk(text="claim submission process")
        result = svc.rank([chunk], query="claim submission")
        assert len(result) == 1
        assert result[0].ranking_score > 0.0

    def test_rank_assigned_starting_from_1(self):
        svc = make_service()
        chunks = [
            make_chunk("c1", combined_score=0.9),
            make_chunk("c2", combined_score=0.5),
            make_chunk("c3", combined_score=0.1),
        ]
        result = svc.rank(chunks, query="insurance claim")
        ranks = [c.rank for c in result]
        assert ranks == [1, 2, 3]

    def test_chunks_sorted_descending_by_ranking_score(self):
        svc = make_service()
        chunks = [
            make_chunk("c1", text="completely unrelated text xyz", combined_score=0.3),
            make_chunk("c2", text="insurance claim policy document", combined_score=0.9),
        ]
        result = svc.rank(chunks, query="insurance claim policy")
        assert result[0].ranking_score >= result[1].ranking_score

    def test_metadata_complete_score_higher(self):
        svc = make_service(retrieval_w=0.4, keyword_w=0.2, metadata_w=0.4)
        complete = make_chunk("c1", metadata_complete=True, combined_score=0.5)
        incomplete = make_chunk("c2", metadata_complete=False, combined_score=0.5)
        result = svc.rank([complete, incomplete], query="test")
        # Complete metadata chunk should rank higher (same retrieval score, metadata differs)
        assert result[0].chunk_id == "c1"

    def test_high_keyword_overlap_boosts_score(self):
        svc = make_service(retrieval_w=0.3, keyword_w=0.5, metadata_w=0.2)
        high_overlap = make_chunk(
            "c1", text="claim settlement process insurance benefit", combined_score=0.5
        )
        low_overlap = make_chunk(
            "c2", text="unrelated agricultural topic banana fruit", combined_score=0.5
        )
        result = svc.rank([high_overlap, low_overlap], query="claim settlement insurance")
        assert result[0].chunk_id == "c1"


# ===========================================================================
# min_ranking_score filtering
# ===========================================================================

class TestMinRankingScoreFilter:
    def test_chunks_below_threshold_removed(self):
        svc = make_service(
            retrieval_w=0.0, keyword_w=0.0, metadata_w=1.0, min_score=0.5
        )
        # metadata_complete=False → score = 0.0, should be filtered
        chunk_low = make_chunk("low", metadata_complete=False)
        # metadata_complete=True → score = 1.0, should pass
        chunk_high = make_chunk("high", metadata_complete=True)
        result = svc.rank([chunk_low, chunk_high], query="test")
        chunk_ids = [c.chunk_id for c in result]
        assert "high" in chunk_ids
        assert "low" not in chunk_ids

    def test_zero_min_score_returns_all(self):
        svc = make_service(min_score=0.0)
        chunks = [make_chunk("c1"), make_chunk("c2"), make_chunk("c3")]
        result = svc.rank(chunks, query="insurance")
        assert len(result) == 3


# ===========================================================================
# Score normalisation
# ===========================================================================

class TestScoreNormalisation:
    def test_all_same_score_chunks_ranked_by_other_signals(self):
        svc = make_service(retrieval_w=0.0, keyword_w=0.5, metadata_w=0.5)
        chunks = [
            make_chunk("c1", text="insurance claim policy", combined_score=0.5, metadata_complete=True),
            make_chunk("c2", text="banana fruit market", combined_score=0.5, metadata_complete=False),
        ]
        result = svc.rank(chunks, query="insurance claim policy")
        # c1 should rank higher: better keyword overlap AND metadata complete
        assert result[0].chunk_id == "c1"


# ===========================================================================
# Strategy context (reserved parameter)
# ===========================================================================

class TestStrategyContext:
    def test_strategy_context_accepted_without_error(self):
        svc = make_service()
        chunk = make_chunk()
        result = svc.rank([chunk], query="test", strategy_context={"strategy_name": "regulatory"})
        assert len(result) == 1
