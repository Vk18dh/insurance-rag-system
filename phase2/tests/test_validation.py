"""
phase2.tests.test_validation
================================

Unit tests for RetrievalValidationService.

Coverage:
    - Empty retrieval → RetrievalValidationException (FATAL)
    - Low chunk count → MEDIUM warning
    - Low similarity score → HIGH warning
    - Incomplete metadata → LOW warning
    - Missing page numbers → MEDIUM warning (when require_page_numbers=True)
    - Single source → LOW warning
    - Clean retrieval → empty warnings list
    - Configuration validation
"""

from __future__ import annotations

import pytest

from phase2.models.retrieved_chunk import RetrievedChunk, RetrievalSource
from phase2.models.query_context import QueryContext
from phase2.models.query_metadata import QueryMetadata
from phase2.models.intent import IntentResult, IntentType
from phase2.services.retrieval_validation_service import RetrievalValidationService
from phase2.exceptions.retrieval_exception import RetrievalValidationException


# ===========================================================================
# Test helpers
# ===========================================================================

def make_chunk(
    chunk_id: str = "c1",
    text: str = "Policy benefit details.",
    combined_score: float = 0.7,
    source_document: str = "policy.pdf",
    page_number: str = "5",
    metadata_complete: bool = True,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        text=text,
        combined_score=combined_score,
        bm25_score=0.3,
        vector_score=0.7,
        source_document=source_document,
        page_number=page_number,
        metadata_complete=metadata_complete,
    )


def make_context(query_id: str = "test-001") -> QueryContext:
    metadata = QueryMetadata(query_id=query_id)
    intent = IntentResult(intent=IntentType.GENERAL_INQUIRY, confidence=0.8)
    return QueryContext(
        original_query="What are the policy benefits?",
        metadata=metadata,
        intent=intent,
    )


def make_service(
    min_chunks: int = 1,
    min_score: float = 0.1,
    max_incomplete_ratio: float = 0.5,
    require_pages: bool = False,
) -> RetrievalValidationService:
    return RetrievalValidationService(
        min_chunks_required=min_chunks,
        min_similarity_score=min_score,
        max_incomplete_metadata_ratio=max_incomplete_ratio,
        require_page_numbers=require_pages,
    )


# ===========================================================================
# Fatal check: empty retrieval
# ===========================================================================

class TestEmptyRetrieval:
    def test_empty_chunks_raises_validation_exception(self):
        svc = make_service()
        ctx = make_context()
        with pytest.raises(RetrievalValidationException) as exc_info:
            svc.validate([], ctx)
        assert exc_info.value.error_code == "RETRIEVAL_VALIDATION_FAILED"

    def test_exception_has_correct_validation_check(self):
        svc = make_service()
        ctx = make_context()
        with pytest.raises(RetrievalValidationException) as exc_info:
            svc.validate([], ctx)
        assert exc_info.value.context.get("validation_check") == "empty_retrieval"


# ===========================================================================
# Clean retrieval — no warnings
# ===========================================================================

class TestCleanRetrieval:
    def test_good_chunks_produce_no_warnings(self):
        svc = make_service(min_chunks=1, min_score=0.1)
        chunks = [
            make_chunk("c1", combined_score=0.8),
            make_chunk("c2", combined_score=0.6),
        ]
        ctx = make_context()
        warnings = svc.validate(chunks, ctx)
        assert warnings == []

    def test_returns_list_not_none(self):
        svc = make_service()
        chunks = [make_chunk()]
        ctx = make_context()
        result = svc.validate(chunks, ctx)
        assert isinstance(result, list)


# ===========================================================================
# Low chunk count
# ===========================================================================

class TestLowChunkCount:
    def test_below_min_chunks_produces_medium_warning(self):
        svc = make_service(min_chunks=5)
        chunks = [make_chunk()]
        ctx = make_context()
        warnings = svc.validate(chunks, ctx)
        codes = [w.code for w in warnings]
        assert "LOW_CHUNK_COUNT" in codes

    def test_low_chunk_warning_is_medium_severity(self):
        svc = make_service(min_chunks=5)
        chunks = [make_chunk()]
        ctx = make_context()
        warnings = svc.validate(chunks, ctx)
        w = next(w for w in warnings if w.code == "LOW_CHUNK_COUNT")
        assert w.severity == "MEDIUM"


# ===========================================================================
# Low similarity score
# ===========================================================================

class TestLowSimilarity:
    def test_low_top_score_produces_high_warning(self):
        svc = make_service(min_score=0.8)
        chunks = [make_chunk(combined_score=0.1)]
        ctx = make_context()
        warnings = svc.validate(chunks, ctx)
        codes = [w.code for w in warnings]
        assert "LOW_SIMILARITY_SCORE" in codes

    def test_low_similarity_warning_is_high_severity(self):
        svc = make_service(min_score=0.9)
        chunks = [make_chunk(combined_score=0.2)]
        ctx = make_context()
        warnings = svc.validate(chunks, ctx)
        w = next(w for w in warnings if w.code == "LOW_SIMILARITY_SCORE")
        assert w.severity == "HIGH"

    def test_score_above_threshold_no_warning(self):
        svc = make_service(min_score=0.3)
        chunks = [make_chunk(combined_score=0.9)]
        ctx = make_context()
        warnings = svc.validate(chunks, ctx)
        codes = [w.code for w in warnings]
        assert "LOW_SIMILARITY_SCORE" not in codes


# ===========================================================================
# Incomplete metadata
# ===========================================================================

class TestIncompleteMetadata:
    def test_high_incomplete_ratio_produces_low_warning(self):
        svc = make_service(max_incomplete_ratio=0.3)
        chunks = [
            make_chunk("c1", metadata_complete=False),
            make_chunk("c2", metadata_complete=False),
            make_chunk("c3", metadata_complete=True),
        ]
        ctx = make_context()
        warnings = svc.validate(chunks, ctx)
        codes = [w.code for w in warnings]
        assert "INCOMPLETE_METADATA" in codes

    def test_all_complete_no_warning(self):
        svc = make_service(max_incomplete_ratio=0.5)
        chunks = [make_chunk("c1"), make_chunk("c2")]
        ctx = make_context()
        warnings = svc.validate(chunks, ctx)
        codes = [w.code for w in warnings]
        assert "INCOMPLETE_METADATA" not in codes


# ===========================================================================
# Missing page numbers
# ===========================================================================

class TestMissingPageNumbers:
    def test_all_missing_pages_with_require_true_produces_warning(self):
        svc = make_service(require_pages=True)
        chunks = [
            make_chunk("c1", page_number="N/A"),
            make_chunk("c2", page_number="N/A"),
        ]
        ctx = make_context()
        warnings = svc.validate(chunks, ctx)
        codes = [w.code for w in warnings]
        assert "MISSING_PAGE_NUMBERS" in codes

    def test_missing_pages_with_require_false_no_warning(self):
        svc = make_service(require_pages=False)
        chunks = [make_chunk("c1", page_number="N/A")]
        ctx = make_context()
        warnings = svc.validate(chunks, ctx)
        codes = [w.code for w in warnings]
        assert "MISSING_PAGE_NUMBERS" not in codes


# ===========================================================================
# Single source
# ===========================================================================

class TestSingleSource:
    def test_all_from_same_source_with_many_chunks_produces_warning(self):
        svc = make_service()
        chunks = [
            make_chunk(f"c{i}", source_document="single_doc.pdf")
            for i in range(5)
        ]
        ctx = make_context()
        warnings = svc.validate(chunks, ctx)
        codes = [w.code for w in warnings]
        assert "SINGLE_SOURCE" in codes

    def test_multiple_sources_no_single_source_warning(self):
        svc = make_service()
        chunks = [
            make_chunk("c1", source_document="doc_a.pdf"),
            make_chunk("c2", source_document="doc_b.pdf"),
            make_chunk("c3", source_document="doc_c.pdf"),
            make_chunk("c4", source_document="doc_d.pdf"),
        ]
        ctx = make_context()
        warnings = svc.validate(chunks, ctx)
        codes = [w.code for w in warnings]
        assert "SINGLE_SOURCE" not in codes

    def test_single_chunk_does_not_trigger_single_source_warning(self):
        # Single source warning only fires for > 2 chunks
        svc = make_service()
        chunks = [make_chunk("c1", source_document="solo.pdf")]
        ctx = make_context()
        warnings = svc.validate(chunks, ctx)
        codes = [w.code for w in warnings]
        assert "SINGLE_SOURCE" not in codes


# ===========================================================================
# Multiple warnings at once
# ===========================================================================

class TestMultipleWarnings:
    def test_multiple_issues_produce_multiple_warnings(self):
        svc = make_service(min_chunks=10, min_score=0.9, max_incomplete_ratio=0.1)
        chunks = [
            make_chunk("c1", combined_score=0.05, metadata_complete=False),
        ]
        ctx = make_context()
        warnings = svc.validate(chunks, ctx)
        # Expect: LOW_CHUNK_COUNT + LOW_SIMILARITY_SCORE + INCOMPLETE_METADATA
        codes = {w.code for w in warnings}
        assert "LOW_CHUNK_COUNT" in codes
        assert "LOW_SIMILARITY_SCORE" in codes
        assert "INCOMPLETE_METADATA" in codes
