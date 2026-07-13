from typing import List, Optional
from pydantic import BaseModel, Field

class SupportingEvidence(BaseModel):
    """Reference tracking mapping a specific verified chunk back to the origin."""
    chunk_id: str
    source_document: str = Field(..., description="Document filename.")
    section_title: Optional[str] = None
    page_number: Optional[str] = None

class ReasoningStep(BaseModel):
    """
    A discrete, indivisible logical inference derived from upstream evidence.
    Tracks causality directly to verified rules.
    """
    step_number: int = Field(..., description="Sequential order in the chain.")
    premise: str = Field(..., description="The logic condition or rule context evaluated.")
    evidence_used: List[SupportingEvidence] = Field(default_factory=list, description="Verified anchors confirming the premise.")
    assumption: Optional[str] = Field(None, description="Flagged deductive leaps not explicitly defined in evidence.")
    conclusion: str = Field(..., description="The factual deduction derived.")
    is_supported: bool = Field(
        ..., 
        description="True if supported by verified evidence. False if orphaned, forcing it to be marked unsupported rather than explicitly inferred."
    )
