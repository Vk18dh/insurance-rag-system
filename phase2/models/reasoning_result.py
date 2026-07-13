from pydantic import BaseModel, Field

from phase2.models.verification_result import VerificationResult
from phase2.models.reasoning_chain import ReasoningChain
from phase2.models.explanation import Explanation
from phase2.models.reasoning_metrics import ReasoningMetrics

class ReasoningResult(BaseModel):
    """
    The definitive container summarizing Part 4 outputs. 
    It is the exclusive, structured artifact passed asynchronously downstream to the Risk Agent (Part 5).
    """
    verification_source: VerificationResult = Field(
        ..., 
        description="Strict reference to the immutable verified input ensuring origin provenance."
    )
    reasoning_chain: ReasoningChain = Field(
        ..., 
        description="The mechanical step-by-step logic sequence traversed."
    )
    explanation: Explanation = Field(
        ..., 
        description="Human-readable synthesis intended for UX translation."
    )
    metrics: ReasoningMetrics = Field(
        ..., 
        description="Quality heuristics surrounding latency and LLM integrity."
    )
    
    def to_risk_input(self) -> dict:
        """
        Formats downstream payloads exclusively, explicitly ensuring 
        zero leakage of raw irrelevant LLM text context to the Risk boundaries.
        """
        return {
            "query_id": getattr(self.verification_source.retrieval_result.query_context, "query_id", "Unknown"),
            "unsupported_steps": self.reasoning_chain.has_unsupported_deductions,
            "assumption_count": self.reasoning_chain.total_assumptions,
            "metrics": self.metrics.model_dump(),
            "chain_length": len(self.reasoning_chain.steps)
        }
