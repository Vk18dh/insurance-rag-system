from pydantic import BaseModel, Field
from typing import List
from phase2.models.conflict_level import ConflictLevel
from phase2.models.contradiction_type import ContradictionType
from phase2.models.evidence_alignment import EvidenceAlignment

class ContradictionRecord(BaseModel):
    """Isolated contradiction event identified across constraints."""
    contradiction_type: ContradictionType = Field(..., description="Type of contradiction mapped natively.")
    conflict_level: ConflictLevel = Field(..., description="Severity bounds for the overlap constraint.")
    evidence_ties: EvidenceAlignment = Field(..., description="Specific references mapping the factual bounds of this conflict natively.")
    risk_factor_ids: List[str] = Field(default_factory=list, description="If applicable, risk variables contributing to this logic overlapping.")
    explanation: str = Field(..., description="A detailed map explaining the inconsistency safely limits without assuming outputs.")
    suggested_interpretation: str = Field("None", description="Recommended logic map safely resolving the clause optionally.")
