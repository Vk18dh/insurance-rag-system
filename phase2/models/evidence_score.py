"""
phase2.models.evidence_score
==============================
Evidence scoring per individual chunk for the Verification Agent.
"""
from pydantic import BaseModel, Field

class EvidenceScore(BaseModel):
    """
    Score components for an individual retrieved chunk.
    These scores reflect the quality, relevance, and citation integrity 
    of the chunk without invoking any generative reasoning.
    """
    chunk_id: str = Field(
        ..., 
        description="The unique identifier of the chunk being scored."
    )
    semantic_relevance: float = Field(
        default=0.0, ge=0.0, le=1.0, 
        description="Score indicating topical alignment with the query intent."
    )
    bm25_contribution: float = Field(
        default=0.0, ge=0.0, le=1.0, 
        description="Score indicating exact keyword matching relevance."
    )
    metadata_completeness_score: float = Field(
        default=0.0, ge=0.0, le=1.0, 
        description="Score reflecting the presence of necessary metadata fields."
    )
    citation_quality: float = Field(
        default=0.0, ge=0.0, le=1.0, 
        description="Score reflecting validity and completeness of citation pointers."
    )
    overall_confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, 
        description="The final computed confidence of this specific chunk."
    )
    penalties: float = Field(
        default=0.0, ge=0.0, 
        description="Point deductions applied due to structural inconsistencies."
    )
