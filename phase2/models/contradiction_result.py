from pydantic import BaseModel, Field
from typing import List
from phase2.models.contradiction_record import ContradictionRecord
from phase2.models.contradiction_metrics import ContradictionMetrics
from phase2.models.reasoning_result import ReasoningResult
from phase2.models.risk_assessment import RiskAssessmentResult

class ContradictionResult(BaseModel):
    """Final wrapped boundary isolating all logical conflicts explicitly."""
    reasoning_source: ReasoningResult = Field(..., description="Base origin of the logic traces securely boundaries.")
    risk_source: RiskAssessmentResult = Field(..., description="Origin of flagged overlaps natively bounding variables.")
    contradictions: List[ContradictionRecord] = Field(default_factory=list, description="Collection of conflicts natively identified.")
    overall_confidence: float = Field(..., description="Confidence from 0.0 to 1.0 locating explicit boundaries flawlessly.", ge=0.0, le=1.0)
    recommendation: str = Field("No action", description="High-level suggested routing or human fallback limits.")
    metrics: ContradictionMetrics = Field(default_factory=ContradictionMetrics)
    
    @property
    def has_critical_conflict(self) -> bool:
        from phase2.models.conflict_level import ConflictLevel
        return any(c.conflict_level == ConflictLevel.CRITICAL for c in self.contradictions)
