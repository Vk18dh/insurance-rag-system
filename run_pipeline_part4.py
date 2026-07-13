import asyncio
import logging
from typing import Dict, Any

from phase2.config.settings import get_settings
from phase2.exceptions.handlers import safe_agent_call
from phase2.models.query_context import QueryContext
from phase2.models.retrieval_result import RetrievalResult
from phase2.models.verification_result import VerificationResult
from phase2.models.reasoning_result import ReasoningResult

from phase2.agents.query_agent import QueryUnderstandingAgentFactory
from phase2.agents.retrieval_agent import RetrievalAgentFactory
from phase2.agents.verification_agent import VerificationAgentFactory
from phase2.agents.reasoning_agent import ReasoningAgentFactory

# Dummy/Offline LLM Analyzer to prevent Google API charges during integration
from phase2.interfaces.query_agent_interface import ILLMAnalyzer
class OfflineAnalyzer(ILLMAnalyzer):
    def analyse(self, payload: str) -> dict:
        # Check if doing Part 1 Query or Part 4 Reasoning based on payload
        if "reasoning guidelines" in payload.lower() or "steps" in payload:
            return {
                "reasoning_steps": [
                    {
                        "premise": "Free look period rules apply.",
                        "evidence_used_ids": ["EVIDENCE_1"],
                        "assumption": "",
                        "conclusion": "The user has 15 days."
                    }
                ]
            }
        else:
            return {
                "understanding": {
                    "primary_intent": "policy_information",
                    "confidence_score": 0.9,
                    "entities": {},
                    "query_classification": "factual",
                    "requires_multi_document": False,
                    "suggested_actions": [],
                    "reasoning": "Offline test."
                }
            }

async def run_e2e_pipeline(test_query: str):
    logging.basicConfig(level=logging.INFO)
async def run_e2e_pipeline(test_query: str):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Pipeline_Integration")
    
    settings = get_settings()
    llm = OfflineAnalyzer()
    
    reasoning_agent = ReasoningAgentFactory.create(settings, llm)
    
    logger.info(f"--- Starting Pipeline for Query: {test_query} ---")
    
    # 1. Build VerificationResult mock payload cleanly
    query_ctx = QueryContext(original_query=test_query)
    from phase2.models.retrieved_chunk import RetrievedChunk, RetrievalSource
    chunk = RetrievedChunk(
        chunk_id="chunk1",
        text="Free look period is 15 days.",
        source_document="doc.pdf",
        section_title="Free look",
        page_number="1",
        bm25_score=0.9, vector_score=0.9, combined_score=0.9,
        retrieval_source=RetrievalSource.VECTOR,
        metadata_complete=True, raw_metadata={}
    )
    
    from phase2.models.retrieval_result import RetrievalMetrics
    retrieval_res = RetrievalResult(
        query_context=query_ctx,
        ranked_evidence=[chunk],
        metrics=RetrievalMetrics(chunks_retrieved=1),
        warnings=[],
        is_valid=True
    )
    
    from phase2.models.verification_report import VerificationReport, VerificationStatus
    from phase2.models.validation_metrics import ValidationMetrics
    v_report = VerificationReport(
        verification_status=VerificationStatus.PASSED,
        validation_metrics=ValidationMetrics(
            total_chunks_processed=1, chunks_with_citations=1, chunks_with_conflicts=0, overall_evidence_score=0.9
        ),
        ranked_evidence=[chunk],
        warnings=[],
        procedural_recommendations=[]
    )
    
    verification_res = VerificationResult(
        retrieval_result=retrieval_res,
        report=v_report,
        is_valid_for_reasoning=True,
        metrics=None
    )
    
    # 2. Native Continuity Test: Verify -> Reason Linkage
    logger.info("Passing VerificationResult into ReasoningAgent...")
    reasoning_res = reasoning_agent.reason(verification_res)
    
    logger.info("--- Pipeline Completed Successfully ---")
    logger.info(f"Reasoning Summary:\n{reasoning_res.explanation.reasoning_summary}")
    logger.info(f"Total Logic Steps: {reasoning_res.metrics.total_steps}")
    
if __name__ == "__main__":
    asyncio.run(run_e2e_pipeline("What is the free look period?"))
