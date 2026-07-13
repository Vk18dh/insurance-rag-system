from typing import List, Dict, Any
from phase2.interfaces.reasoning_interface import IClauseInterpreter
from phase2.models.retrieved_chunk import RetrievedChunk

import logging

logger = logging.getLogger(__name__)

class ClauseInterpreter(IClauseInterpreter):
    """
    Parses and sanitizes retrieval text chunks into indexed, flattened 
    clause dictionaries preventing uncontrolled LLM context string bloat.
    """
    def __init__(self, max_chunk_length: int = 1000):
        self.max_chunk_length = max_chunk_length

    def interpret(self, chunks: List[RetrievedChunk], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Maps raw chunks securely into formatted target boundaries.
        Optimized to drop arbitrary metadata that confuses logic synthesis.
        """
        interpreted = []
        for c in chunks:
            text_val = c.text.strip()
            if len(text_val) > self.max_chunk_length:
                text_val = text_val[:self.max_chunk_length] + "... [TRUNCATED]"
                
            interpreted.append({
                "chunk_id": c.chunk_id,
                "source": c.source_document,
                "domain_context": c.section_title or "General Policy",
                "clause_text": text_val
            })
        logger.info("Clauses interpreted successfully", extra={"chunks_processed": len(chunks), "clauses_extracted": len(interpreted)})
        return interpreted
