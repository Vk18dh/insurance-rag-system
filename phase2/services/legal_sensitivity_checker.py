from typing import Dict, Any
from phase2.interfaces.risk_agent_interface import ILegalSensitivityChecker
from phase2.models.legal_warning import LegalWarning
from phase2.exceptions.risk_exception import LegalSensitivityException

import logging
logger = logging.getLogger(__name__)

class LegalSensitivityChecker(ILegalSensitivityChecker):
    """Parses legal boundaries from synchronized outputs."""
    def check(self, json_payload: Dict[str, Any]) -> LegalWarning:
        try:
            core = json_payload.get("legal_sensitivity", {})
            return LegalWarning(
                detected=core.get("is_sensitive", False),
                affected_step_numbers=core.get("sensitive_steps", []),
                legal_category=core.get("legal_category", "None"),
                description=core.get("description", "Secure logic bound limit")
            )
        except Exception as e:
            logger.error(f"Failed to map Legal Sensitivity organically: {e}")
            raise LegalSensitivityException("Failed to decode Legal schema natively.") from e
