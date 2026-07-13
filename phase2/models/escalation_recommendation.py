from pydantic import BaseModel, Field

class EscalationRecommendation(BaseModel):
    """Recommends whether Human-in-the-Loop interventions are mandatory downstream."""
    escalation_required: bool = Field(..., description="True if escalation is highly recommended.")
    recommended_action: str = Field(..., description="E.g., 'Recommend expert review'")
    reasoning: str = Field(..., description="Why the escalation is raised.")
