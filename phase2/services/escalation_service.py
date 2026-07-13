from typing import Dict, Any
from phase2.interfaces.risk_agent_interface import IEscalationService
from phase2.models.escalation_recommendation import EscalationRecommendation
from phase2.exceptions.risk_exception import RiskException

import logging
logger = logging.getLogger(__name__)

class EscalationService(IEscalationService):
    """Calculates escalation logic seamlessly out of parsed arrays."""
    def evaluate(self, json_payload: Dict[str, Any]) -> EscalationRecommendation:
        try:
            # First map the high_risk dict natively.
            core = json_payload.get("high_risk", {})
            
            # Simple heuristic matching boolean boundaries.
            is_high = core.get("is_high_risk_query", False)
            return EscalationRecommendation(
                escalation_required=is_high,
                recommended_action="Strongly recommend compliance review" if is_high else "No escalation required",
                reasoning=core.get("justification", "Stable logic scope detected")
            )
        except Exception as e:
            logger.error(f"Failed to map Escalation routes organically: {e}")
            raise RiskException("Failed to decode Escalation bounds natively.") from e
