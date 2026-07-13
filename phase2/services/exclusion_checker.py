from typing import Dict, Any
from phase2.interfaces.risk_agent_interface import IExclusionChecker
from phase2.models.exclusion_warning import ExclusionWarning
from phase2.exceptions.risk_exception import RiskException

import logging
logger = logging.getLogger(__name__)

class ExclusionChecker(IExclusionChecker):
    """Maps suicide exclusions, waiting periods, etc."""
    def check(self, json_payload: Dict[str, Any]) -> ExclusionWarning:
        try:
            core = json_payload.get("exclusions", {})
            return ExclusionWarning(
                detected=core.get("has_exclusions", False),
                affected_step_numbers=core.get("excluded_steps", []),
                exclusion_type=core.get("exclusion_type", "None"),
                description=core.get("description", "Secure logic bound limit")
            )
        except Exception as e:
            logger.error(f"Failed to map Exclusion limits organically: {e}")
            raise RiskException("Failed to decode Exclusion schema natively.") from e
