import json
import logging

from phase2.config.settings import get_settings
from phase2.agents.verification_agent import VerificationAgentFactory
from phase2.models.retrieval_result import RetrievalResult, RetrievalMetrics
from phase2.models.retrieved_chunk import RetrievedChunk, RetrievalSource
from phase2.models.query_context import QueryContext

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def main():
    settings = get_settings()
    
    print("\n" + "="*50)
    print("AI-Driven Insurance Knowledge Assessment System")
    print("Part 3 Verification Agent Integration Check")
    print("="*50 + "\n")

    # 1. Instantiate the dynamically bounded Agent via Factory
    print("[1] Building VerificationAgent dynamically from Phase2Settings...")
    agent = VerificationAgentFactory.create(settings)
    
    # 2. Mock a pristine RetrievalResult payload exactly simulating Part 2 output
    print("[2] Constructing mock RetrievalResult bounds...")
    ctx = QueryContext(original_query="What are the term life benefits?", normalized_query="What are the term life benefits?")
    
    c1 = RetrievedChunk(
        chunk_id="chunk_101",
        text="Term life insurance provides a death benefit if the insured person dies during the specified term.",
        source_document="TermLifePolicy_v2.pdf",
        page_number="5",
        combined_score=0.85,
        retrieval_source=RetrievalSource.VECTOR
    )
    
    c2 = RetrievedChunk(
        chunk_id="chunk_102",
        text="The premium remains level for the entire duration of the term length selected.",
        source_document="TermLifePolicy_v2.pdf",
        page_number="N/A",  # Deliberate Citation degradation 
        combined_score=0.45,
        retrieval_source=RetrievalSource.BM25
    )
    
    rr = RetrievalResult(
        query_context=ctx,
        ranked_evidence=[c1, c2],
        metrics=RetrievalMetrics(total_chunks_retrieved=10, chunks_after_filtering=2),
        retrieval_strategy="factual"
    )
    
    # 3. Fire the pipeline!
    print(f"\n[3] Firing Verification Pipeline on {len(rr.ranked_evidence)} evidence chunks...")
    try:
        vr = agent.verify(rr)
        print("\n" + "="*50)
        print("VERIFICATION RESULT JSON (downstream bounds payload for Reasoning Agent):")
        print("="*50)
        
        output = vr.model_dump(mode="json")
        print(json.dumps(output, indent=2))
        
        print("\n✅ Integration successful.")
        print(f"Overall Reasoning Valid Status: {vr.is_valid_for_reasoning}")
    except Exception as e:
        print(f"\n❌ Integration failed: {e}")

if __name__ == "__main__":
    main()
