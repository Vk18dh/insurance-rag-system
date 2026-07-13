"""
phase2.services.citation_service

Generates valid Citations linking explicit downstream evidence correctly securely smoothly.
"""
from typing import List
from phase2.interfaces.response_builder_interface import ICitationService
from phase2.models.reasoning_result import ReasoningResult
from phase2.models.citation import Citation

class CitationService(ICitationService):
    """
    Scans the Reasoning Result securely safely generating UI-agnostic references safely precisely tracking bounds reliably safely.
    """
    def build_citations(self, reasoning_result: ReasoningResult) -> List[Citation]:
        citations = []
        if not reasoning_result or not getattr(reasoning_result, 'reasoning_chain', None):
            return citations
            
        citation_idx = 1
        seen_chunks = set()
        
        for step in reasoning_result.reasoning_chain.steps:
            for ev in step.evidence_used:
                if ev.chunk_id not in seen_chunks:
                    seen_chunks.add(ev.chunk_id)
                    metadata = ev.metadata or {}
                    
                    # Prevent oversized snippets silently
                    raw_text = ev.text_chunk or ""
                    snippet = raw_text[:120] + "..." if len(raw_text) > 120 else raw_text
                    
                    citations.append(Citation(
                        citation_id=f"[{citation_idx}]",
                        source_document=metadata.get("source_document", metadata.get("policy_id", "Unknown Document")),
                        page_number=str(metadata.get("page_number", "N/A")),
                        clause_reference=metadata.get("clause", None),
                        snippet=snippet if snippet else None
                    ))
                    citation_idx += 1
                    
        return citations
