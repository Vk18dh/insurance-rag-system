import logging
from typing import List
from phase2.interfaces.verification_interface import IConsistencyChecker
from phase2.models.retrieved_chunk import RetrievedChunk

logger = logging.getLogger(__name__)

class ConsistencyChecker(IConsistencyChecker):
    """
    Performs deterministic boundary checks to ensure retrieved evidence chunks
    do not contain impossible or corrupted metadata overlapping conflicts.
    """
    def check_metadata_consistency(self, chunks: List[RetrievedChunk]) -> int:
        inconsistencies = 0
        seen_chunks = {}
        
        for chunk in chunks:
            if chunk.chunk_id in seen_chunks:
                # If chunk ID is identical, text and source must perfectly align.
                existing = seen_chunks[chunk.chunk_id]
                if existing.source_document != chunk.source_document:
                    logger.warning(f"Inconsistent metadata: Chunk ID '{chunk.chunk_id}' maps to multiple distinct source docs.")
                    inconsistencies += 1
            else:
                seen_chunks[chunk.chunk_id] = chunk

            # Empty text bounding fault
            if not chunk.text or len(chunk.text.strip()) == 0:
                logger.warning(f"Inconsistent metadata: Chunk ID '{chunk.chunk_id}' contains zero byte text.")
                inconsistencies += 1

        return inconsistencies
