import logging
from phase2.interfaces.contradiction_interface import IConflictResolutionHelper
from phase2.models.conflict_level import ConflictLevel

logger = logging.getLogger(__name__)

class ConflictResolutionHelper(IConflictResolutionHelper):
    def __init__(self, conflict_thresholds: list = None):
        self._mapping = {}
        thresholds = conflict_thresholds or [
            "CRITICAL -> Halt automated generation. Regulatory clarification or human review explicitly required.",
            "HIGH -> Expert review suggested. Clauses significantly overlap.",
            "MEDIUM -> Additional verification recommended optionally mapping fallback rules securely.",
            "LOW -> No action necessary. Maintain response delivery safely."
        ]
        for threshold in thresholds:
            if "->" in threshold:
                lvl, rule = threshold.split("->", 1)
                try:
                    self._mapping[ConflictLevel(lvl.strip().upper())] = rule.strip()
                except ValueError:
                    continue
                    
    def recommend(self, conflict_level: ConflictLevel) -> str:
        """
        Provides programmatic routing strategies natively matched to explicitly identified constraints reliably.
        """
        return self._mapping.get(conflict_level, "No action")
