from typing import Dict, Any
from phase2.interfaces.risk_agent_interface import IRegulatoryChecker
from phase2.models.regulatory_warning import RegulatoryWarning
from phase2.exceptions.risk_exception import RegulatoryException

import logging
logger = logging.getLogger(__name__)

class RegulatoryChecker(IRegulatoryChecker):
    """Verifies regulatory boundary conditions securely."""
    def check(self, json_payload: Dict[str, Any]) -> RegulatoryWarning:
        try:
            core = json_payload.get("regulatory", {})
            return RegulatoryWarning(
                detected=core.get("has_regulatory_concerns", False),
                affected_step_numbers=core.get("regulatory_steps", []),
                concern_type=core.get("concern_type", "None"),
                description=core.get("description", "Secure logic bound limit")
            )
        except Exception as e:
            logger.error(f"Failed to map Regulatory tracks organically: {e}")
            raise RegulatoryException("Failed to decode Regulatory schema natively.") from e
