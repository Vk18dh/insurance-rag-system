from typing import List, Dict, Any
from pydantic import BaseModel, Field

class Explanation(BaseModel):
    """
    Human-readable structured trace derived securely from the ReasoningChain.
    Prepares format for auditors or user-facing UI components without acting as a conversational reply.
    """
    reasoning_summary: str = Field(
        ..., 
        description="A clear, high-level summary of the logical path taken."
    )
    clause_interpretation: str = Field(
        ..., 
        description="Context detailing how the specific rules (e.g., Free Look Period) were contextualized."
    )
    assumptions_flagged: List[str] = Field(
        default_factory=list,
        description="List of detected logic leaps strictly mapped for transparency."
    )
    confidence_inputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Telemetry metadata informing future Confidence Agents (e.g. ambiguity variance). Should NOT be a final percentage."
    )
