"""
phase2.models.verification_result
==================================
The final envelope linking the Part 2 `RetrievalResult` directly to the
Part 3 `VerificationReport`. This becomes the single input source 
for the Part 4 Reasoning Agent.
"""
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from phase2.models.retrieval_result import RetrievalResult
from phase2.models.verification_report import VerificationReport


class VerificationResult(BaseModel):
    """
    Top-level contract fulfilling Part 3 execution.
    It encapsulates the unmodified retrieval chunks inside `retrieval_result`
    while appending the rigorous metadata constraints and QA scores via `report`.
    """
    retrieval_result: RetrievalResult = Field(
        ..., 
        description="The strictly unmodified retrieval envelope handed from Part 2."
    )
    report: VerificationReport = Field(
        ...,
        description="The rigorous verification bounds evaluated by Part 3."
    )
    is_valid_for_reasoning: bool = Field(
        ...,
        description="True if the downstream Reasoning Agent should attempt an answer."
    )
    verified_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 UTC timestamp."
    )
    
    def to_reasoning_input(self) -> dict:
        """
        Creates the strictly formatted dictionary defining
        the entry contract for Part 4 processing.
        """
        return {
            "is_valid": self.is_valid_for_reasoning,
            "status": self.report.verification_status.value,
            "query": self.retrieval_result.query_context.normalized_query,
            "evidence_count": len(self.retrieval_result.ranked_evidence),
            "recommendations": self.report.recommendations
        }
