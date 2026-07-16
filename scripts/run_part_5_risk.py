"""
Run Script for Phase 2 Part 5 (Risk Agent).
Demonstrates linking Part 1 (Query) -> Part 2 (Retrieval) -> Part 3 (Verification) -> Part 4 (Reasoning) -> Part 5 (Risk)
using an offline mock LLM and offline Retrieval mapping seamlessly.
"""

import logging
import time

# Use the offline integrations explicitly to prevent API Key halts mapping tests organically.
from phase2.config.settings import get_settings
from phase2.agents.query_agent import QueryUnderstandingAgentFactory
from phase2.agents.retrieval_agent import RetrievalAgentFactory
from phase2.agents.verification_agent import VerificationAgentFactory
from phase2.agents.reasoning_agent import ReasoningAgentFactory
from phase2.agents.risk_agent import RiskAgentFactory

# Offline stubs for testing Native Integration Boundaries!
class OfflineLLM:
    def analyse(self, prompt: str) -> dict:
        # Step 1: Mock Query Agent Context
        if "Intent" in prompt or "entities" in prompt:
            return {
                "intent": "exclusions",
                "confidence": 0.95,
                "entities": {"policy_feature": ["waiting period"]}
            }
        
        # Step 4: Mock Reasoning Chain
        if "Determine conclusions" in prompt:
            return {
                "steps": [
                    {
                        "step_number": 1,
                        "evidence_references": ["EVIDENCE_1"],
                        "conclusion": "The policy states a 30-day waiting period.",
                        "is_supported": True
                    }
                ]
            }
        
        # Step 5: Mock Risk Assessment
        if "operational, legal, and compliance risks" in prompt:
            return {
                  "ambiguity": {
                    "is_ambiguous": False
                  },
                  "legal_sensitivity": {
                    "is_sensitive": True,
                    "sensitive_steps": [1],
                    "legal_category": "Claim Rejection",
                    "description": "Waiting period enforcement could lead to rejection."
                  },
                  "exclusions": {
                    "has_exclusions": True,
                    "excluded_steps": [1],
                    "exclusion_type": "Waiting Period",
                    "description": "30-day wait applies."
                  },
                  "regulatory": {
                    "has_regulatory_concerns": False
                  },
                  "high_risk": {
                    "is_high_risk_query": False,
                    "risk_level": "MEDIUM",
                    "justification": "Standard exclusion."
                  }
            }
            
        return {}
        
from phase2.models.retrieved_chunk import RetrievedChunk, RetrievalSource
from phase2.models.retrieval_result import RetrievalResult, RetrievalMetrics

class OfflineRetrievalService:
    class MockRetriever:
        def is_available(self): return True
        
    def __init__(self):
        self._retriever = self.MockRetriever()
        
    def retrieve(self, **kwargs) -> dict:
        from unittest.mock import MagicMock
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

from phase2.models.query_context import QueryContext
from phase2.models.query_metadata import QueryMetadata
from phase2.interfaces.query_agent_interface import IQueryProcessingService

class OfflineQueryService(IQueryProcessingService):
    def process(self, str_query: str) -> QueryContext:
        from unittest.mock import MagicMock
        ctx = QueryContext.model_construct(
            original_query=str_query,
            metadata=QueryMetadata.model_construct(query_id="TEST_Q"),
            intent=MagicMock(),
            entities=MagicMock(),
            classification=MagicMock(),
            ambiguity=MagicMock()
        )
        return ctx
    def validate_only(self, query: str) -> bool:
        return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    settings = get_settings()
    llm = OfflineLLM()
    retriever_svc = OfflineRetrievalService()
    
    # Instantiate Pipeline Agents
    query_svc = OfflineQueryService()
    query_agent = QueryUnderstandingAgentFactory.create(settings, query_svc)
    retrieval_agent = RetrievalAgentFactory.create(settings, retriever_svc)
    verification_agent = VerificationAgentFactory.create(settings)
    reasoning_agent = ReasoningAgentFactory.create(settings, llm)
    risk_agent = RiskAgentFactory.create(settings, llm)
    
    query = "Does the policy cover illness on exactly day 15?"
    
    print(f"\n=========================================")
    print(f"PIPELINE: EVALUATING '{query}'")
    print(f"=========================================\n")
    
    time.sleep(0.5)
    
    # 1. Query
    print(f"[1] Running Query Agent...")
    ctx = query_agent.process(query)
    
    # 2. Retrieval
    print(f"[2] Running Retrieval Agent...")
    ret_res = retrieval_agent.retrieve(ctx)
    
    # 3. Verification
    print(f"[3] Running Verification Agent...")
    ver_res = verification_agent.verify(ret_res)
    
    # 4. Reasoning
    print(f"[4] Running Reasoning Agent...")
    reason_res = reasoning_agent.reason(ver_res)
    
    # 5. Risk
    print(f"[5] Running Risk Agent...")
    try:
        risk_res = risk_agent.evaluate(reason_res)
    except Exception as e:
        import traceback
        with open("final_error.txt", "w") as f:
            f.write(traceback.format_exc())
        print("ERROR DUMPED TO final_error.txt")
        exit(1)
    
    print(f"\n=========================================")
    print(f"RISK ASSESSMENT RESULT:")
    print(f"=========================================")
    print(f"Overall Risk Level: {risk_res.overall_risk_level.value}")
    print(f"Is Ambiguous: {risk_res.ambiguity_report.detected}")
    print(f"Legal Warnings: {risk_res.legal_warnings.detected} ({risk_res.legal_warnings.legal_category})")
    print(f"Exclusions Found: {risk_res.exclusions_identified.detected} ({risk_res.exclusions_identified.exclusion_type})")
    print(f"Regulatory Flags: {risk_res.regulatory_warnings.detected}")
    print(f"Escalation Recommended: {risk_res.escalation.escalation_required}")
    print(f"=========================================\n")
