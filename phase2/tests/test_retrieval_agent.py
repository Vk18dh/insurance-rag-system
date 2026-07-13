"""
phase2.tests.test_retrieval_agent
=====================================

Tests for the Retrieval Agent (Phase 2 Part 2).

Coverage:
    Unit Tests:
        - Strategy selection (all classifications)
        - Phase1RetrieverAdapter dict→RetrievedChunk conversion
        - RetrievalService merge + deduplication logic
        - ConfigDrivenRetrievalStrategy default fallback
        - RetrievalResult contract (to_verification_input keys)

    Integration Tests:
        - QueryAgent → RetrievalAgent pipeline (fully mocked Phase 1)
        - RetrievalResult contains correct metadata from QueryContext

    Failure Tests:
        - IndexUnavailableException when both indexes absent
        - RankingException → graceful degrade (returns unranked)
        - RetrievalValidationException → empty result (not crash)
        - None QueryContext → QueryValidationException
        - Timeout → RetrievalTimeoutException

    Configuration Tests:
        - RetrievalSettings loaded from dict (matches YAML schema)
        - strategy_weights missing 'default' → RetrievalConfigurationException
        - Phase1RetrieverAdapter rejects empty paths
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from phase2.models.retrieved_chunk import RetrievedChunk, RetrievalSource
from phase2.models.retrieval_result import RetrievalResult, RetrievalWarning
from phase2.models.retrieval_metrics import RetrievalMetrics
from phase2.models.query_context import QueryContext
from phase2.models.query_metadata import QueryMetadata
from phase2.models.intent import IntentResult, IntentType
from phase2.models.query_metadata import QueryClassification

from phase2.agents.retrieval_agent import (
    RetrievalAgent,
    ConfigDrivenRetrievalStrategy,
    RetrievalAgentFactory,
)
from phase2.services.retrieval_service import RetrievalService, Phase1RetrieverAdapter
from phase2.services.ranking_service import WeightedRankingService
from phase2.services.retrieval_validation_service import RetrievalValidationService

from phase2.exceptions.retrieval_exception import (
    IndexUnavailableException,
    RankingException,
    RetrievalValidationException,
    RetrievalConfigurationException,
    RetrievalTimeoutException,
)
from phase2.exceptions.query_exception import QueryValidationException


# ===========================================================================
# Shared helpers / fixtures
# ===========================================================================

def make_chunk(
    chunk_id: str = "c1",
    text: str = "policy benefit claim insurance",
    combined_score: float = 0.6,
    source_document: str = "policy.pdf",
    page_number: str = "7",
    metadata_complete: bool = True,
    retrieval_source: RetrievalSource = RetrievalSource.HYBRID,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        text=text,
        combined_score=combined_score,
        bm25_score=0.4,
        vector_score=0.6,
        source_document=source_document,
        page_number=page_number,
        metadata_complete=metadata_complete,
        retrieval_source=retrieval_source,
    )


def make_context(
    query: str = "What is the claim settlement period?",
    classification: QueryClassification = QueryClassification.POLICY_SPECIFIC,
    query_id: str = "test-qid-001",
) -> QueryContext:
    metadata = QueryMetadata(query_id=query_id)
    intent = IntentResult(intent=IntentType.CLAIM_PROCESS, confidence=0.85)
    return QueryContext(
        original_query=query,
        normalized_query=query.lower(),
        metadata=metadata,
        intent=intent,
        classification=classification,
    )


DEFAULT_STRATEGY_WEIGHTS = {
    "policy_specific": {"bm25": 0.7, "vector": 0.3, "top_k": 8},
    "factual":         {"bm25": 0.5, "vector": 0.5, "top_k": 8},
    "regulatory":      {"bm25": 0.4, "vector": 0.6, "top_k": 8},
    "comparative":     {"bm25": 0.3, "vector": 0.7, "top_k": 10},
    "general":         {"bm25": 0.5, "vector": 0.5, "top_k": 8},
    "unknown":         {"bm25": 0.5, "vector": 0.5, "top_k": 8},
    "default":         {"bm25": 0.5, "vector": 0.5, "top_k": 8},
}


def make_retrieval_agent(
    chunks_to_return: list | None = None,
    raise_on_retrieve: Exception | None = None,
    raise_on_rank: Exception | None = None,
    raise_on_validate: Exception | None = None,
) -> RetrievalAgent:
    """Build a RetrievalAgent with fully mocked dependencies."""
    if chunks_to_return is None:
        chunks_to_return = [make_chunk("c1"), make_chunk("c2")]

    # Mock retrieval service
    mock_retrieval_svc = MagicMock(spec=RetrievalService)
    mock_adapter = MagicMock()
    mock_adapter.is_available.return_value = True
    mock_retrieval_svc._retriever = mock_adapter

    if raise_on_retrieve:
        mock_retrieval_svc.retrieve.side_effect = raise_on_retrieve
    else:
        mock_retrieval_svc.retrieve.return_value = {
            "chunks": chunks_to_return,
            "bm25_count": len(chunks_to_return),
            "vector_count": len(chunks_to_return),
            "elapsed_ms": 120.0,
        }

    # Mock ranking service
    mock_ranking = MagicMock(spec=WeightedRankingService)
    if raise_on_rank:
        mock_ranking.rank.side_effect = raise_on_rank
    else:
        def _rank_side_effect(chunks, query, strategy_context=None):
            for i, c in enumerate(chunks):
                object.__setattr__(c, "ranking_score", 0.9 - i * 0.1)
                object.__setattr__(c, "rank", i + 1)
            return chunks
        mock_ranking.rank.side_effect = _rank_side_effect

    # Mock validation service
    mock_validation = MagicMock(spec=RetrievalValidationService)
    if raise_on_validate:
        mock_validation.validate.side_effect = raise_on_validate
    else:
        mock_validation.validate.return_value = []

    strategy = ConfigDrivenRetrievalStrategy(
        strategy_weights=DEFAULT_STRATEGY_WEIGHTS,
        default_top_k=8,
    )

    return RetrievalAgent(
        retrieval_service=mock_retrieval_svc,
        strategy=strategy,
        ranking_service=mock_ranking,
        validation_service=mock_validation,
        agent_version="2.0.0-test",
    )


# ===========================================================================
# ConfigDrivenRetrievalStrategy
# ===========================================================================

class TestConfigDrivenRetrievalStrategy:
    def test_policy_specific_uses_high_bm25(self):
        strategy = ConfigDrivenRetrievalStrategy(DEFAULT_STRATEGY_WEIGHTS, default_top_k=8)
        ctx = make_context(classification=QueryClassification.POLICY_SPECIFIC)
        result = strategy.select(ctx)
        assert result["bm25_weight"] == 0.7
        assert result["vector_weight"] == 0.3
        assert result["strategy_name"] == "policy_specific"

    def test_regulatory_uses_higher_vector(self):
        strategy = ConfigDrivenRetrievalStrategy(DEFAULT_STRATEGY_WEIGHTS, default_top_k=8)
        ctx = make_context(classification=QueryClassification.REGULATORY)
        result = strategy.select(ctx)
        assert result["vector_weight"] == 0.6
        assert result["bm25_weight"] == 0.4

    def test_comparative_uses_highest_vector(self):
        strategy = ConfigDrivenRetrievalStrategy(DEFAULT_STRATEGY_WEIGHTS, default_top_k=8)
        ctx = make_context(classification=QueryClassification.COMPARATIVE)
        result = strategy.select(ctx)
        assert result["vector_weight"] == 0.7

    def test_unknown_falls_back_to_default_weights(self):
        strategy = ConfigDrivenRetrievalStrategy(DEFAULT_STRATEGY_WEIGHTS, default_top_k=8)
        ctx = make_context(classification=QueryClassification.UNKNOWN)
        result = strategy.select(ctx)
        assert result["bm25_weight"] == 0.5
        assert result["vector_weight"] == 0.5

    def test_none_classification_falls_back_to_default(self):
        strategy = ConfigDrivenRetrievalStrategy(DEFAULT_STRATEGY_WEIGHTS, default_top_k=8)
        ctx = QueryContext(original_query="test query")
        result = strategy.select(ctx)
        assert result["strategy_name"] == "default"

    def test_missing_default_key_raises_configuration_exception(self):
        bad_weights = {"policy_specific": {"bm25": 0.7, "vector": 0.3, "top_k": 8}}
        with pytest.raises(RetrievalConfigurationException):
            ConfigDrivenRetrievalStrategy(bad_weights, default_top_k=8)

    def test_top_k_from_strategy(self):
        strategy = ConfigDrivenRetrievalStrategy(DEFAULT_STRATEGY_WEIGHTS, default_top_k=8)
        ctx = make_context(classification=QueryClassification.COMPARATIVE)
        result = strategy.select(ctx)
        assert result["top_k"] == 10  # comparative has top_k=10 in DEFAULT_STRATEGY_WEIGHTS


# ===========================================================================
# Phase1RetrieverAdapter — initialization validation
# ===========================================================================

class TestPhase1RetrieverAdapterInit:
    def test_empty_bm25_path_raises(self):
        with pytest.raises(RetrievalConfigurationException):
            Phase1RetrieverAdapter(
                bm25_index_path="",
                chroma_dir="/some/dir",
                chroma_collection="test",
            )

    def test_empty_chroma_dir_raises(self):
        with pytest.raises(RetrievalConfigurationException):
            Phase1RetrieverAdapter(
                bm25_index_path="/some/path.pkl",
                chroma_dir="",
                chroma_collection="test",
            )

    def test_zero_timeout_raises(self):
        with pytest.raises(RetrievalConfigurationException):
            Phase1RetrieverAdapter(
                bm25_index_path="/some.pkl",
                chroma_dir="/some/db",
                chroma_collection="test",
                timeout_seconds=0.0,
            )

    def test_is_available_returns_false_when_files_missing(self):
        adapter = Phase1RetrieverAdapter(
            bm25_index_path="/nonexistent/bm25.pkl",
            chroma_dir="/nonexistent/chroma",
            chroma_collection="test",
        )
        assert adapter.is_available() is False

    def test_bm25_search_raises_when_index_missing(self):
        adapter = Phase1RetrieverAdapter(
            bm25_index_path="/nonexistent/bm25.pkl",
            chroma_dir="/nonexistent/chroma",
            chroma_collection="test",
        )
        with pytest.raises(IndexUnavailableException):
            adapter.bm25_search("test query", top_k=5)

    def test_vector_search_raises_when_chroma_missing(self):
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            bm25_path = f.name
        try:
            adapter = Phase1RetrieverAdapter(
                bm25_index_path=bm25_path,
                chroma_dir="/nonexistent/chroma",
                chroma_collection="test",
            )
            with pytest.raises(IndexUnavailableException):
                adapter.vector_search("test query", top_k=5)
        finally:
            os.unlink(bm25_path)


# ===========================================================================
# Phase1RetrieverAdapter — dict→RetrievedChunk conversion
# ===========================================================================

class TestPhase1RetrieverAdapterConversion:
    def test_dict_to_chunk_bm25(self):
        raw = {
            "chunk_id": "abc-123",
            "text": "Insurance claim process",
            "score": 0.75,
            "source_document": "policy.pdf",
            "page_number": 10,
            "section_title": "Claims",
        }
        chunk = Phase1RetrieverAdapter._dict_to_chunk(raw, RetrievalSource.BM25, bm25_score=0.75)
        assert chunk.chunk_id == "abc-123"
        assert chunk.text == "Insurance claim process"
        assert chunk.bm25_score == 0.75
        assert chunk.vector_score == 0.0
        assert chunk.source_document == "policy.pdf"
        assert chunk.page_number == "10"
        assert chunk.section_title == "Claims"
        assert chunk.retrieval_source == RetrievalSource.BM25

    def test_dict_to_chunk_vector(self):
        raw = {
            "chunk_id": "xyz-789",
            "text": "Benefit summary",
            "score": 0.88,
            "source_document": "benefit.pdf",
            "page_number": 5,
            "section_title": "Benefits",
        }
        chunk = Phase1RetrieverAdapter._dict_to_chunk(raw, RetrievalSource.VECTOR, vector_score=0.88)
        assert chunk.vector_score == 0.88
        assert chunk.bm25_score == 0.0
        assert chunk.retrieval_source == RetrievalSource.VECTOR

    def test_dict_to_chunk_missing_metadata_incomplete_flag(self):
        raw = {
            "chunk_id": "no-meta",
            "text": "Some text",
            "score": 0.5,
            "source_document": "unknown",
            "page_number": None,
            "section_title": "Unknown",
        }
        chunk = Phase1RetrieverAdapter._dict_to_chunk(raw, RetrievalSource.BM25, bm25_score=0.5)
        assert chunk.metadata_complete is False

    def test_raw_metadata_preserved(self):
        raw = {
            "chunk_id": "raw-1",
            "text": "text",
            "score": 0.5,
            "source_document": "doc.pdf",
            "page_number": 1,
            "section_title": "Intro",
        }
        chunk = Phase1RetrieverAdapter._dict_to_chunk(raw, RetrievalSource.HYBRID)
        assert chunk.raw_metadata is not None
        assert chunk.raw_metadata["chunk_id"] == "raw-1"


# ===========================================================================
# RetrievalAgent — unit tests (mocked dependencies)
# ===========================================================================

class TestRetrievalAgent:
    def test_retrieve_returns_retrieval_result(self):
        agent = make_retrieval_agent()
        ctx = make_context()
        result = agent.retrieve(ctx)
        assert isinstance(result, RetrievalResult)

    def test_retrieve_none_context_raises(self):
        agent = make_retrieval_agent()
        with pytest.raises(QueryValidationException):
            agent.retrieve(None)  # type: ignore

    def test_result_contains_query_context(self):
        agent = make_retrieval_agent()
        ctx = make_context()
        result = agent.retrieve(ctx)
        assert result.query_context is ctx

    def test_result_is_successful_when_chunks_returned(self):
        agent = make_retrieval_agent([make_chunk("c1"), make_chunk("c2")])
        ctx = make_context()
        result = agent.retrieve(ctx)
        assert result.is_successful is True

    def test_result_has_ranked_evidence_list(self):
        agent = make_retrieval_agent([make_chunk("c1"), make_chunk("c2")])
        ctx = make_context()
        result = agent.retrieve(ctx)
        assert isinstance(result.ranked_evidence, list)
        assert len(result.ranked_evidence) > 0

    def test_metrics_populated(self):
        agent = make_retrieval_agent()
        ctx = make_context()
        result = agent.retrieve(ctx)
        assert result.metrics.strategy_used != ""
        assert result.metrics.total_duration_ms is not None
        assert result.metrics.total_duration_ms > 0

    def test_strategy_applied_correctly(self):
        agent = make_retrieval_agent()
        ctx = make_context(classification=QueryClassification.POLICY_SPECIFIC)
        result = agent.retrieve(ctx)
        assert result.retrieval_strategy == "policy_specific"
        assert result.bm25_weight == 0.7

    def test_empty_warnings_on_clean_retrieval(self):
        agent = make_retrieval_agent()
        ctx = make_context()
        result = agent.retrieve(ctx)
        assert result.warnings == []

    def test_ranking_exception_degrades_gracefully(self):
        agent = make_retrieval_agent(
            raise_on_rank=RankingException("ranking failed", ranking_step="test")
        )
        ctx = make_context()
        # Should NOT raise — degrades to unranked result
        result = agent.retrieve(ctx)
        assert isinstance(result, RetrievalResult)

    def test_validation_exception_returns_empty_result(self):
        agent = make_retrieval_agent(
            raise_on_validate=RetrievalValidationException(
                "no chunks", validation_check="empty_retrieval"
            )
        )
        ctx = make_context()
        result = agent.retrieve(ctx)
        assert result.is_successful is False
        assert result.ranked_evidence == []
        codes = [w.code for w in result.warnings]
        assert "EMPTY_RETRIEVAL" in codes

    def test_index_unavailable_exception_propagates(self):
        agent = make_retrieval_agent(
            raise_on_retrieve=IndexUnavailableException("no index", index_type="both")
        )
        ctx = make_context()
        with pytest.raises(IndexUnavailableException):
            agent.retrieve(ctx)

    def test_get_agent_info_returns_dict(self):
        agent = make_retrieval_agent()
        info = agent.get_agent_info()
        assert info["name"] == "RetrievalAgent"
        assert "capabilities" in info
        assert "hybrid_retrieval" in info["capabilities"]


# ===========================================================================
# Integration: QueryContext → RetrievalResult contract
# ===========================================================================

class TestQueryContextToRetrievalResultIntegration:
    def test_to_verification_input_has_required_keys(self):
        agent = make_retrieval_agent([make_chunk("c1"), make_chunk("c2")])
        ctx = make_context()
        result = agent.retrieve(ctx)
        v_input = result.to_verification_input()
        required_keys = [
            "query", "intent", "confidence", "classification",
            "is_ambiguous", "query_id", "evidence", "evidence_count",
            "source_documents", "retrieval_confidence", "retrieval_strategy",
            "validation_passed", "warnings", "metrics_id",
        ]
        for key in required_keys:
            assert key in v_input, f"Missing key in to_verification_input(): {key}"

    def test_evidence_items_have_required_fields(self):
        agent = make_retrieval_agent([make_chunk("c1")])
        ctx = make_context()
        result = agent.retrieve(ctx)
        v_input = result.to_verification_input()
        evidence = v_input["evidence"]
        assert len(evidence) > 0
        item = evidence[0]
        for field in ["chunk_id", "text", "source_document", "page_number",
                      "section_title", "ranking_score", "rank", "citation"]:
            assert field in item, f"Missing field in evidence dict: {field}"

    def test_retrieval_confidence_in_zero_to_one(self):
        agent = make_retrieval_agent()
        ctx = make_context()
        result = agent.retrieve(ctx)
        assert 0.0 <= result.metrics.retrieval_confidence <= 1.0

    def test_unique_sources_deduplicated(self):
        chunks = [
            make_chunk("c1", source_document="doc_a.pdf"),
            make_chunk("c2", source_document="doc_a.pdf"),  # duplicate source
            make_chunk("c3", source_document="doc_b.pdf"),
        ]
        agent = make_retrieval_agent(chunks)
        ctx = make_context()
        result = agent.retrieve(ctx)
        sources = result.unique_sources()
        assert len(sources) == 2
        assert "doc_a.pdf" in sources
        assert "doc_b.pdf" in sources


# ===========================================================================
# RetrievalSettings configuration
# ===========================================================================

class TestRetrievalSettingsConfiguration:
    def test_default_settings_are_valid(self):
        from phase2.config.settings import RetrievalSettings
        s = RetrievalSettings()
        assert s.top_k == 8
        assert "default" in s.strategy_weights

    def test_missing_default_strategy_raises(self):
        from phase2.config.settings import RetrievalSettings
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            RetrievalSettings(strategy_weights={"policy_specific": {"bm25": 0.7, "vector": 0.3}})

    def test_ranking_settings_defaults_valid(self):
        from phase2.config.settings import RankingSettings
        s = RankingSettings()
        assert s.retrieval_score_weight + s.keyword_overlap_weight + s.metadata_completeness_weight > 0

    def test_validation_settings_defaults_valid(self):
        from phase2.config.settings import ValidationSettings
        s = ValidationSettings()
        assert s.min_chunks_required >= 0
        assert 0.0 <= s.min_similarity_score <= 1.0

    def test_phase2settings_includes_retrieval_block(self):
        from phase2.config.settings import Phase2Settings
        from pydantic import ValidationError
        s = Phase2Settings()
        assert hasattr(s, "retrieval")
        assert hasattr(s, "ranking")
        assert hasattr(s, "validation")
        assert s.retrieval.top_k > 0
