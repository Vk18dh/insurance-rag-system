import logging
from typing import Dict, Any
from phase2.interfaces.contradiction_interface import IContradictionClassifier
from phase2.models.conflict_level import ConflictLevel
from phase2.exceptions.contradiction_exception import ConflictClassificationException

logger = logging.getLogger(__name__)

class ContradictionClassifier(IContradictionClassifier):
    def classify(self, llm_payload: Dict[str, Any]) -> ConflictLevel:
        """
        Structurally validates and returns severity thresholds securely cleanly avoiding crashes natively.
        """
        try:
            val = llm_payload.get("conflict_level", "LOW")
            return ConflictLevel(val.upper())
        except ValueError:
            logger.warning(f"Fallback triggered mapping conflict parsing bounds natively.")
            return ConflictLevel.LOW
        except Exception as e:
            logger.error(f"Classification validation failed safely natively: {e}")
            raise ConflictClassificationException("Invalid structural bounds for conflict extraction.") from e
