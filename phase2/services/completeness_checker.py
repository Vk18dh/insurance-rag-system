import logging
from typing import List
from phase2.interfaces.verification_interface import ICompletenessChecker
from phase2.models.retrieved_chunk import RetrievedChunk
from phase2.models.query_context import QueryContext

logger = logging.getLogger(__name__)

class CompletenessChecker(ICompletenessChecker):
    """
    Checks evidence volume against minimum heuristic requirements.
    """
    def __init__(self, min_evidence_count: int = 1):
        self.min_evidence_count = min_evidence_count

    def evaluate_completeness(self, chunks: List[RetrievedChunk], query_context: QueryContext) -> str:
        """Determines if the quantity of passing chunks strictly satisfies constraints."""
        if len(chunks) >= self.min_evidence_count:
            return "Complete"
            
        logger.info(f"Evidence evaluated as Incomplete: Found {len(chunks)}, Required {self.min_evidence_count}")
        return "Incomplete"
