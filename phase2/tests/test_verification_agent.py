import pytest
from phase2.agents.verification_agent import VerificationAgent
from phase2.models.retrieval_result import RetrievalResult, RetrievalMetrics
from phase2.models.query_context import QueryContext
from phase2.models.retrieved_chunk import RetrievedChunk, RetrievalSource
from phase2.services.citation_validator import CitationValidator
from phase2.services.completeness_checker import CompletenessChecker
from phase2.services.consistency_checker import ConsistencyChecker
from phase2.services.evidence_validator import EvidenceValidator
from phase2.services.relevance_checker import RelevanceChecker

@pytest.fixture
def verification_agent():
    ev = EvidenceValidator(
        CitationValidator(),
        RelevanceChecker(0.3),
        ConsistencyChecker(),
        CompletenessChecker(1),
        strict_metadata=False
    )
    return VerificationAgent(evidence_validator=ev)

def test_verification_agent_accepts_retrieval_result(verification_agent):
    c1 = RetrievedChunk(chunk_id="c1", text="stuff", source_document="doc.pdf", combined_score=0.9, retrieval_source=RetrievalSource.BM25)
    rr = RetrievalResult(
        query_context=QueryContext(original_query="test", normalized_query="test"),
        ranked_evidence=[c1],
        metrics=RetrievalMetrics(),
        retrieval_strategy="fallback"
    )
    
    result = verification_agent.verify(rr)
    assert result.is_valid_for_reasoning is True
    assert result.report.verification_status.value == "passed"
    assert result.retrieval_result.query_context.normalized_query == "test"

def test_verification_agent_rejects_invalid_inputs(verification_agent):
    with pytest.raises(ValueError):
        verification_agent.verify("Not a RetrievalResult object")

def test_verification_agent_degraded_on_empty(verification_agent):
    rr = RetrievalResult(
        query_context=QueryContext(original_query="test", normalized_query="test"),
        ranked_evidence=[],
        metrics=RetrievalMetrics(),
        retrieval_strategy="fallback"
    )
    result = verification_agent.verify(rr)
    assert result.is_valid_for_reasoning is False
    assert result.report.verification_status.value == "failed"
