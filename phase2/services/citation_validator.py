import logging
from phase2.interfaces.verification_interface import ICitationValidator
from phase2.models.retrieved_chunk import RetrievedChunk

logger = logging.getLogger(__name__)

class CitationValidator(ICitationValidator):
    """
    Concrete implementation enforcing exact bounds on source attributions.
    """
    def __init__(self, require_page_numbers: bool = False):
        self.require_page_numbers = require_page_numbers

    def validate_citations(self, chunk: RetrievedChunk) -> float:
        """
        Validates citation completeness without fetching databases.
        Scores strictly 1.0 (perfect), 0.5 (partial), or 0.0 (unusable).
        """
        score = 1.0
        
        # Absolute critical bounds
        if not chunk.source_document or chunk.source_document.lower() == "unknown" or not chunk.chunk_id:
            logger.warning(f"Chunk missing critical citation anchors: {chunk.chunk_id}")
            return 0.0
            
        # Optional bounds depending on configuration strictness
        if self.require_page_numbers and (not chunk.page_number or chunk.page_number.strip().upper() == "N/A"):
            logger.info(f"Chunk penalized for missing page_number: {chunk.chunk_id}")
            score -= 0.5
            
        return max(0.0, score)
