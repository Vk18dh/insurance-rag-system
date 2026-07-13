from typing import Dict, Any
from phase2.interfaces.risk_agent_interface import IRiskAmbiguityDetector
from phase2.models.ambiguity_report import AmbiguityReport
from phase2.exceptions.risk_exception import AmbiguityException

import logging
logger = logging.getLogger(__name__)

class AmbiguityDetector(IRiskAmbiguityDetector):
    """Parses ambiguity factors securely without standalone LLM bloat."""
    def detect(self, json_payload: Dict[str, Any]) -> AmbiguityReport:
        try:
            core = json_payload.get("ambiguity", {})
            return AmbiguityReport(
                detected=core.get("is_ambiguous", False),
                affected_step_numbers=core.get("ambiguous_steps", []),
                ambiguity_type=core.get("ambiguity_type", "None"),
                description=core.get("description", "Secure logic bound limit")
            )
        except Exception as e:
            logger.error(f"Failed to map Ambiguity checks organically: {e}")
            raise AmbiguityException("Failed to decode Ambiguity schema natively.") from e
