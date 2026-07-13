import pytest
from unittest.mock import Mock, MagicMock

from phase2.config.settings import build_settings
from phase2.agents.reasoning_agent import ReasoningAgentFactory
from phase2.models.verification_result import VerificationResult
from phase2.models.verification_report import VerificationStatus, VerificationReport
from phase2.models.validation_metrics import ValidationMetrics
from phase2.models.retrieval_result import RetrievalResult, RetrievalMetrics
from phase2.models.query_context import QueryContext
from phase2.models.retrieved_chunk import RetrievedChunk, RetrievalSource
from phase2.interfaces.query_agent_interface import ILLMAnalyzer
from phase2.exceptions.reasoning_exception import InvalidVerificationException

@pytest.fixture
def valid_verification_result():
    # Build robust pipeline mock context
    query_ctx = QueryContext(original_query="What is the free look period?")
    ret_metrics = RetrievalMetrics(chunks_retrieved=1)
    chunk = RetrievedChunk(
        chunk_id="free_look_1",
        text="The free look period is 15 days.",
        source_document="doc.pdf",
        section_title="Free Look",
        page_number="1",
        bm25_score=0.9,
        vector_score=0.9,
        combined_score=0.9,
        retrieval_source=RetrievalSource.VECTOR,
        metadata_complete=True,
        raw_metadata={}
    )
    
    ret_res = RetrievalResult(
        query_context=query_ctx,
        ranked_evidence=[chunk],
        metrics=ret_metrics,
        warnings=[],
        is_valid=True
    )
    
    v_report = VerificationReport(
        verification_status=VerificationStatus.PASSED,
        validation_metrics=ValidationMetrics(
            total_chunks_processed=1,
            chunks_with_citations=1,
            chunks_with_conflicts=0,
            overall_evidence_score=0.9
        ),
        warnings=[],
        procedural_recommendations=[]
    )
    
    return VerificationResult(
        retrieval_result=ret_res,
        report=v_report,
        is_valid_for_reasoning=True,
        metrics=None
    )

class MockLLMAnalyzer(ILLMAnalyzer):
    def analyse(self, payload: str) -> dict:
        return {
            "reasoning_steps": [
                {
                    "premise": "Free look applies to all new policies.",
                    "evidence_used_ids": ["EVIDENCE_1"],
                    "assumption": "",
                    "conclusion": "The user has 15 days to cancel."
                }
            ]
        }

def test_reasoning_agent_succesful_flow(valid_verification_result):
    settings = build_settings()
    llm = MockLLMAnalyzer()
    
    agent = ReasoningAgentFactory.create(settings, llm)
    
    result = agent.reason(valid_verification_result)
    
    # Assert Result Bounds
    assert result.metrics.total_steps == 1
    assert result.reasoning_chain.is_complete is True
    assert result.reasoning_chain.steps[0].is_supported is True
    assert "15 days to cancel" in result.explanation.reasoning_summary

def test_reasoning_agent_blocks_invalid_verification(valid_verification_result):
    valid_verification_result.is_valid_for_reasoning = False
    
    settings = build_settings()
    llm = MockLLMAnalyzer()
    agent = ReasoningAgentFactory.create(settings, llm)
    
    with pytest.raises(InvalidVerificationException):
        agent.reason(valid_verification_result)
