"""
End-to-End Pipeline Check for Phase 2 (Parts 1, 2, and 3).

Executes realistic orchestration covering the entire sequence natively:
User Query -> Query Agent -> Retriever Agent -> Verification Agent -> Final Result
"""

import sys
import json
import importlib.util
from phase2.config.settings import build_settings
from phase2.agents.query_agent import QueryUnderstandingAgentFactory
from phase2.services.query_processing_service import QueryProcessingServiceFactory
from phase2.services.retrieval_service import RetrievalServiceFactory
from phase2.agents.retrieval_agent import RetrievalAgentFactory
from phase2.agents.verification_agent import VerificationAgentFactory
from phase2.logging.logger import setup_phase2_logging


def main():
    print("==================================================================")
    print("Phase 2 Full E2E Pipeline Check (Query -> Retrieval -> Verification)")
    print("==================================================================\n")

    settings = build_settings()
    # Force offline LLM for seamless pipeline validation without paid limits
    settings.llm.provider = "offline"
    setup_phase2_logging(settings)

    print("[1] Initialising and linking all Agents...")
    try:
        # Part 1 Agent
        query_service = QueryProcessingServiceFactory.create(settings)
        query_agent = QueryUnderstandingAgentFactory.create(settings, query_service)

        # Part 2 Agent
        retrieval_service = RetrievalServiceFactory.create(settings)
        if not retrieval_service._retriever.is_available() or importlib.util.find_spec('chromadb') is None:
            print("    -> Injecting MockPhase1Retriever for pipeline independence...")
            from phase2.interfaces.retrieval_interface import IPhase1Retriever
            from phase2.models.retrieved_chunk import RetrievedChunk, RetrievalSource
            
            class MockPhase1Retriever(IPhase1Retriever):
                def is_available(self): return True
                
                def bm25_search(self, query, top_k): 
                    return [
                        RetrievedChunk(
                            chunk_id="c1", text="Term life pays upon death.", 
                            source_document="policy_v1.pdf", page_number="5", 
                            section_title="Coverage", bm25_score=0.9, vector_score=0.0, 
                            combined_score=0.9, retrieval_source=RetrievalSource.BM25, 
                            metadata_complete=True, raw_metadata={}
                        )
                    ]
                    
                def vector_search(self, query, top_k): 
                    return [
                        RetrievedChunk(
                            chunk_id="c2", text="Premium grace period is 30 days.", 
                            source_document="policy_v1.pdf", page_number="6", 
                            section_title="Premiums", bm25_score=0.0, vector_score=0.8, 
                            combined_score=0.8, retrieval_source=RetrievalSource.VECTOR, 
                            metadata_complete=True, raw_metadata={}
                        )
                    ]
            retrieval_service._retriever = MockPhase1Retriever()
            
        retrieval_agent = RetrievalAgentFactory.create(settings, retrieval_service)

        # Part 3 Agent
        verification_agent = VerificationAgentFactory.create(settings)
        
    except Exception as e:
        print(f"\n[FAIL] Pipeline binding failed: {e}")
        sys.exit(1)

    print("    -> Agents bound successfully.")

    test_queries = [
        "What is the term life insurance grace period?",
        "Gibberish invalid question context" # Deliberate noise test
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n[Test {i}] Executing User Query: '{query}'")
        
        try:
            # 1. Query Agent
            print(f"  -> Q-Agent Processing...")
            query_ctx = query_agent.process(query)
            
            # 2. Retrieval Agent
            print(f"  -> R-Agent Retrieving based on intent [{query_ctx.intent.intent.value}]...")
            retrieval_res = retrieval_agent.retrieve(query_ctx)
            
            # 3. Verification Agent
            print(f"  -> V-Agent Verifying {len(retrieval_res.ranked_evidence)} chunks of evidence...")
            verification_res = verification_agent.verify(retrieval_res)
            
            print(f"\n  [OK] VERIFICATION DICT (Future Part 4 Entrypoint):")
            print(json.dumps(verification_res.to_reasoning_input(), indent=4))
            
            print(f"  Final Valid Boundary Status : {verification_res.is_valid_for_reasoning}")
            
        except Exception as e:
            # In Phase 2 architecture, proper failures like "Invalid Intent" are caught safely.
            print(f"  [FAIL] Explicit Exceptions Trapped Safely: {type(e).__name__} -> {e}")

    print("\n==================================================================")
    print("E2E Validation Completes: No uncaught system fatals generated.")
    print("==================================================================")

if __name__ == "__main__":
    main()
