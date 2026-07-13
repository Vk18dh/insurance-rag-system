import logging
from phase2.interfaces.verification_interface import IRelevanceChecker
from phase2.models.retrieved_chunk import RetrievedChunk
from phase2.models.query_context import QueryContext

logger = logging.getLogger(__name__)

class RelevanceChecker(IRelevanceChecker):
    """
    Algorithmic strict bounds checking ensuring a chunk genuinely relates
    to the query. It leverages the Part 2 hybrid score internally.
    """
    def __init__(self, min_relevance_score: float = 0.3):
        self.min_relevance_score = min_relevance_score

    def evaluate_relevance(self, chunk: RetrievedChunk, query_context: QueryContext) -> float:
        """
        Passively computes semantic relevance.
        Since no LLM generation occurs here, we utilize the Part 2 ranking metrics natively.
        """
        relevance = chunk.combined_score
        
        if relevance < self.min_relevance_score:
            logger.debug(f"Chunk '{chunk.chunk_id}' scored {relevance:.2f} (Below threshold {self.min_relevance_score})")

        return max(0.0, min(1.0, relevance))
