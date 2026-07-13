from typing import List
from pydantic import BaseModel, Field

from phase2.models.reasoning_result import ReasoningResult
from phase2.models.risk_level import RiskLevel
from phase2.models.legal_warning import LegalWarning
from phase2.models.ambiguity_report import AmbiguityReport
from phase2.models.regulatory_warning import RegulatoryWarning
from phase2.models.exclusion_warning import ExclusionWarning
from phase2.models.escalation_recommendation import EscalationRecommendation
from phase2.models.risk_processing_metrics import RiskProcessingMetrics

class RiskAssessmentResult(BaseModel):
    """
    Absolute container traversing downstream towards the Contradiction Detection Agent (Part 6).
    Summarizes all operational faults mapped precisely over the `ReasoningResult`.
    """
    reasoning_source: ReasoningResult = Field(
        ..., 
        description="Immutable snapshot of the previous agent's boundaries seamlessly passed through."
    )
    overall_risk_level: RiskLevel = Field(...)
    
    ambiguity_report: AmbiguityReport = Field(...)
    legal_warnings: LegalWarning = Field(...)
    regulatory_warnings: RegulatoryWarning = Field(...)
    exclusions_identified: ExclusionWarning = Field(...)
    
    escalation: EscalationRecommendation = Field(...)
    metrics: RiskProcessingMetrics = Field(...)
