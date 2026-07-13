"""
phase2.services.warning_service

Maps agent anomalies explicitly securely cleanly smoothly accurately precisely into Warning schemas securely smoothly efficiently securely.
"""
from typing import List, Optional
from phase2.interfaces.response_builder_interface import IWarningService
from phase2.models.risk_assessment import RiskAssessmentResult
from phase2.models.contradiction_result import ContradictionResult
from phase2.models.warning import ResponseWarning, WarningSeverity

class WarningService(IWarningService):
    """Generates standard alerts capturing risk severity and legal contradictions natively seamlessly effectively safely."""
    
    def build_warnings(self, risk_result: Optional[RiskAssessmentResult], contradiction_result: Optional[ContradictionResult]) -> List[ResponseWarning]:
        warnings: List[ResponseWarning] = []
        
        if risk_result and risk_result.risk_level.value not in ("none", "low"):
            warnings.append(ResponseWarning(
                severity=WarningSeverity.HIGH if risk_result.risk_level.value == "high" else WarningSeverity.MEDIUM,
                message=risk_result.explanation,
                source_agent="RiskAssessmentAgent"
            ))
            
        if contradiction_result and contradiction_result.overall_contradiction:
            warnings.append(ResponseWarning(
                severity=WarningSeverity.CRITICAL if contradiction_result.requires_escalation else WarningSeverity.HIGH,
                message=f"Contradiction identified: {contradiction_result.explanation}",
                source_agent="ContradictionAgent"
            ))
            
        return warnings
