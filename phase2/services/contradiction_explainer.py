import logging
from typing import Dict, Any
from phase2.interfaces.contradiction_interface import IContradictionExplainer

logger = logging.getLogger(__name__)

class ContradictionExplainer(IContradictionExplainer):
    def explain(self, llm_payload: Dict[str, Any]) -> str:
        """
        Maps dictionary justifications cleanly without injecting logic loops natively.
        """
        try:
            return str(llm_payload.get("explanation", "Insufficient Evidence"))
        except Exception as e:
            logger.error(f"Explanation map failed securely parsing strings natively: {e}")
            return "Insufficient Evidence"
