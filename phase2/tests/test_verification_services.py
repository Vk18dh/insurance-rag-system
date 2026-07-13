import pytest
from phase2.models.retrieved_chunk import RetrievedChunk, RetrievalSource
from phase2.models.query_context import QueryContext
from phase2.services.citation_validator import CitationValidator
from phase2.services.completeness_checker import CompletenessChecker
from phase2.services.consistency_checker import ConsistencyChecker
from phase2.services.relevance_checker import RelevanceChecker
from phase2.services.evidence_validator import EvidenceValidator
from phase2.models.retrieval_result import RetrievalResult, RetrievalMetrics

def test_citation_validator():
    validator = CitationValidator(require_page_numbers=True)
    
    # Perfect chunk
    c1 = RetrievedChunk(chunk_id="1", text="valid", source_document="doc.pdf", page_number="12", combined_score=0.9, retrieval_source=RetrievalSource.BM25)
    assert validator.validate_citations(c1) == 1.0
    
    # Missing page
    c2 = RetrievedChunk(chunk_id="2", text="valid", source_document="doc.pdf", combined_score=0.9, retrieval_source=RetrievalSource.BM25)
    assert validator.validate_citations(c2) == 0.5
    
    # Missing doc
    c3 = RetrievedChunk(chunk_id="3", text="valid", page_number="12", combined_score=0.9, retrieval_source=RetrievalSource.BM25)
    assert validator.validate_citations(c3) == 0.0

def test_relevance_checker():
    checker = RelevanceChecker(min_relevance_score=0.5)
    q = QueryContext(original_query="test", normalized_query="test")
    
    c_pass = RetrievedChunk(chunk_id="1", text="test", source_document="a", combined_score=0.8, retrieval_source=RetrievalSource.VECTOR)
    c_fail = RetrievedChunk(chunk_id="2", text="test", source_document="b", combined_score=0.2, retrieval_source=RetrievalSource.VECTOR)
    
    assert checker.evaluate_relevance(c_pass, q) == 0.8
    assert checker.evaluate_relevance(c_fail, q) == 0.2

def test_consistency_checker():
    checker = ConsistencyChecker()
    
    c1 = RetrievedChunk(chunk_id="chunk1", text="hello", source_document="doc1.pdf", combined_score=0.8, retrieval_source=RetrievalSource.VECTOR)
    # Different doc but same ID = inconsistency!
    c2 = RetrievedChunk(chunk_id="chunk1", text="hello", source_document="doc2.pdf", combined_score=0.8, retrieval_source=RetrievalSource.VECTOR)
    
    assert checker.check_metadata_consistency([c1, c2]) == 1

def test_completeness_checker():
    checker = CompletenessChecker(min_evidence_count=2)
    q = QueryContext(original_query="test", normalized_query="test")
    
    c = RetrievedChunk(chunk_id="1", text="valid", source_document="doc.pdf", combined_score=0.9, retrieval_source=RetrievalSource.BM25)
    
    assert checker.evaluate_completeness([c], q) == "Incomplete"
    assert checker.evaluate_completeness([c, c], q) == "Complete"

def test_evidence_validator_full_integration():
    cit = CitationValidator(require_page_numbers=False)
    rel = RelevanceChecker(min_relevance_score=0.3)
    con = ConsistencyChecker()
    comp = CompletenessChecker(min_evidence_count=1)
    
    val = EvidenceValidator(cit, rel, con, comp, strict_metadata=True)
    
    c_good = RetrievedChunk(chunk_id="c1", text="useful fact", source_document="policy.pdf", combined_score=0.9, retrieval_source=RetrievalSource.VECTOR)
    
    ctx = QueryContext(original_query="What is the policy?", normalized_query="What is the policy?")
    metrics = RetrievalMetrics()
    rr = RetrievalResult(query_context=ctx, ranked_evidence=[c_good], metrics=metrics, retrieval_strategy="fallback")
    
    report = val.validate_evidence(rr)
    assert report.verification_status.value == "passed"
    assert report.validation_metrics.chunks_passed_relevance == 1
    assert report.validation_metrics.chunks_with_valid_citations == 1
    assert len(report.evidence_scores) == 1
    assert report.evidence_scores[0].chunk_id == "c1"
