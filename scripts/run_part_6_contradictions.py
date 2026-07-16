import os
import sys
import logging
from unittest.mock import MagicMock

# 1. Mount Configuration bounds reliably
from phase2.config.settings import get_settings

# 2. Mount Offline Logic Boundaries bypassing APIs locally
from phase2.interfaces.query_agent_interface import ILLMAnalyzer

class OfflineLLM(ILLMAnalyzer):
    def analyse(self, prompt: str) -> dict:
        """Isolated LLM Stub returning Pydantic bounds seamlessly."""
        if "Determine conclusions" in prompt:
            # Mock Reasoning payload
            return {
                "steps": [
                    {
                        "step_number": 1,
                        "observation": "Waiting period states 30 days.",
                        "conclusion": "The policy requires a 30-day waiting gap.",
                        "confidence": 0.95,
                        "evidence_ids": ["chk_1"],
                        "flags": []
                    }
                ],
                "explanation": "Extracted limits successfully.",
                "confidence": 0.95
            }
        
        if "operational, legal, and compliance risks" in prompt:
            # Mock Risk Payload
            return {
                  "ambiguity": {
                    "is_ambiguous": False,
                    "ambiguous_steps": [],
                    "ambiguity_type": "None",
                    "description": "Insufficient Evidence"
                  },
                  "legal_sensitivity": {
                    "is_sensitive": False,
                    "sensitive_steps": [],
                    "legal_category": "None",
                    "description": "Insufficient Evidence"
                  },
                  "exclusions": {
                    "has_exclusions": True,
                    "excluded_steps": [1],
                    "exclusion_type": "Waiting Period",
                    "description": "Coverage halts precisely for 30 days initially."
                  },
                  "regulatory": {
                    "has_regulatory_concerns": False,
                    "regulatory_steps": [],
                    "concern_type": "None",
                    "description": "Insufficient Evidence"
                  },
                  "high_risk": {
                    "is_high_risk_query": False,
                    "risk_level": "MEDIUM",
                    "justification": "Exclusion clauses apply bounding overlaps natively."
                  }
            }
            
        if "contradiction" in prompt or "Contradiction Detection" in prompt or "conflicting regulatory clauses" in prompt or "REASONING_BLOCK" in prompt:
            # Mock Contradiction Payload
            return {
                "contradictions": [
                    {
                        "type": "Exclusion",
                        "conflict_level": "HIGH",
                        "explanation": "Claim overrides overlap with waiting periods dynamically mapped inside clause constraints natively."
                    }
                ]
            }
            
        return {}

# 3. Mount Pipeline
from phase2.agents.query_agent import QueryUnderstandingAgentFactory
from phase2.agents.retrieval_agent import RetrievalAgentFactory
from phase2.agents.verification_agent import VerificationAgentFactory
from phase2.agents.reasoning_agent import ReasoningAgentFactory
from phase2.agents.risk_agent import RiskAgentFactory
from phase2.agents.contradiction_agent import ContradictionAgentFactory

from phase2.interfaces.query_agent_interface import IQueryProcessingService
from phase2.models.query_context import QueryContext
from phase2.models.query_metadata import QueryMetadata

class OfflineQueryService(IQueryProcessingService):
    def process(self, str_query: str) -> QueryContext:
        ctx = QueryContext.model_construct(
            original_query=str_query,
            metadata=QueryMetadata.model_construct(query_id="TEST_Q"),
            intent=MagicMock(),
            entities=MagicMock(),
            classification=MagicMock(),
            ambiguity=MagicMock()
        )
        return ctx
    def validate_only(self, query: str) -> bool: return True

from phase2.models.retrieval_result import RetrievalResult, RetrievalMetrics
from phase2.models.retrieved_chunk import RetrievedChunk

class OfflineRetrievalService:
    class MockRetriever:
        def is_available(self): return True
    def __init__(self):
        self._retriever = self.MockRetriever()
        
    def retrieve(self, **kwargs) -> dict:
        chunk = RetrievedChunk.model_construct(
            chunk_id="chk_1",
            text="The standard health policy carries a 30-day waiting period for illnesses.",
            source=MagicMock(),
            combined_score=0.9
        )
        return {
            "chunks": [chunk],
            "bm25_count": 1,
            "vector_count": 0,
            "total_time_ms": 10.0,
            "bm25_time_ms": 5.0,
            "vector_time_ms": 5.0
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    settings = get_settings()
    llm = OfflineLLM()
    retriever_svc = OfflineRetrievalService()
    
    # Instantiate Pipeline Agents natively traversing interfaces
    query_svc = OfflineQueryService()
    query_agent = QueryUnderstandingAgentFactory.create(settings, query_svc)
    retrieval_agent = RetrievalAgentFactory.create(settings, retriever_svc)
    verification_agent = VerificationAgentFactory.create(settings)
    reasoning_agent = ReasoningAgentFactory.create(settings, llm)
    risk_agent = RiskAgentFactory.create(settings, llm)
    contradiction_agent = ContradictionAgentFactory.create(settings, llm)
    
    query = "Does the policy cover illness on exactly day 15?"
    
    print(f"\n=========================================")
    print(f"PIPELINE: CONTRADICTION EVALUATION TRACE")
    print(f"=========================================\n")
    
    try:
        print("[1] Running Query Agent...")
        ctx = query_agent.process(query)
        
        print("[2] Running Retrieval Agent...")
        ret_res = retrieval_agent.retrieve(ctx)
        
        print("[3] Running Verification Agent...")
        val_res = verification_agent.verify(ret_res)
        
        print("[4] Running Reasoning Agent...")
        reason_res = reasoning_agent.reason(val_res)
        
        print("[5] Running Risk Agent...")
        risk_res = risk_agent.evaluate(reason_res)
        
        print("[6] Running Contradiction Detection Agent...")
        contra_res = contradiction_agent.process(reason_res, risk_res)
        
        print(f"\n=========================================")
        print(f"CONTRADICTION ASSESSMENT RESULT:")
        print(f"Metrics (total executed): {contra_res.metrics.total_contradictions_found} conflicts safely extracted.")
        print(f"Time Taken: {contra_res.metrics.extraction_time_ms:.2f}ms")
        if contra_res.contradictions:
            c = contra_res.contradictions[0]
            print(f"Top Trace [Level: {c.conflict_level.value}]: {c.explanation}")
            print(f"Recommendation: {c.suggested_interpretation}")
        else:
            print("No logical constraints collided natively securely.")
            
        print(f"=========================================\n")
        
    except Exception as e:
        import traceback
        with open("final_error.txt", "w") as f:
            f.write(traceback.format_exc())
        print(f"ERROR: {e} | Dumped isolated limits gracefully to final_error.txt")
        exit(1)
