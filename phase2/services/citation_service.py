"""
phase2.services.citation_service

Generates valid Citations linking explicit downstream evidence correctly securely smoothly.
"""
from typing import List
from phase2.interfaces.response_builder_interface import ICitationService
from phase2.models.reasoning_result import ReasoningResult
from phase2.models.citation import Citation
from phase2.models.verification_result import VerificationResult
import logging

logger = logging.getLogger(__name__)

class CitationService(ICitationService):
    """
    Scans the Reasoning Result securely safely generating UI-agnostic references safely precisely tracking bounds reliably safely.
    """
    def build_citations(self, reasoning_result: ReasoningResult, verification_result: VerificationResult) -> List[Citation]:
        citations = []
        if not reasoning_result or not getattr(reasoning_result, 'reasoning_chain', None):
            return citations
            
        # Build lookup table for chunks
        chunk_lookup = {}
        if verification_result and verification_result.retrieval_result and getattr(verification_result.retrieval_result, 'ranked_evidence', None):
            for chunk in verification_result.retrieval_result.ranked_evidence:
                if isinstance(chunk, dict):
                    c_id = chunk.get('chunk_id')
                    c_text = chunk.get('text')
                else:
                    c_id = getattr(chunk, 'chunk_id', None)
                    c_text = getattr(chunk, 'text', None)
                
                if c_id and c_text:
                    c_id = str(c_id).strip()
                    chunk_lookup[c_id] = c_text
                    logger.info(f"Loaded chunk_id {c_id} into lookup table with text length {len(c_text)}")
            
        citation_idx = 1
        seen_chunks = set()
        
        for step in reasoning_result.reasoning_chain.steps:
            for ev in step.evidence_used:
                ev_id = str(ev.chunk_id).strip()
                if ev_id not in seen_chunks:
                    seen_chunks.add(ev_id)
                    
                    # Extract snippet
                    snippet = chunk_lookup.get(ev_id, None)
                    if snippet is None:
                        logger.warning(f"Could not find snippet for chunk_id {ev_id}. Available in lookup: {list(chunk_lookup.keys())}")
                    elif len(snippet) > 250:
                        snippet = snippet[:247] + "..."
                        
                    citations.append(Citation(
                        citation_id=f"[{citation_idx}]",
                        source_document=getattr(ev, 'source_document', 'Unknown Document'),
                        page_number=str(getattr(ev, 'page_number', 'N/A')),
                        clause_reference=getattr(ev, 'section_title', None),
                        snippet=snippet
                    ))
                    citation_idx += 1
                    
        return citations
