"""
phase2.models.final_response

Defines FinalResponse Pydantic boundaries.
"""
from typing import List, Optional
from pydantic import BaseModel, Field

from phase2.models.citation import Citation
from phase2.models.warning import ResponseWarning
from phase2.models.response_section import ResponseSection
from phase2.models.response_metadata import ResponseMetadata

class FinalResponse(BaseModel):
    """
    The strictly typed ultimate return boundary serialized fully into JSON via FastAPI for Frontend consumption.
    Never mutates upstream results directly organically ensuring explainability boundaries accurately securely natively.
    """
    direct_answer: str = Field(..., description="The concise, direct string answer generated for the user question.")
    explanation: str = Field(..., description="Detailed markdown reasoning summary logically supporting the direct answer natively.")
    sections: List[ResponseSection] = Field(default_factory=list, description="Additional explicit structured sections dynamically mapped.")
    citations: List[Citation] = Field(default_factory=list, description="List of verified citations natively mapped to text footnotes accurately.")
    warnings: List[ResponseWarning] = Field(default_factory=list, description="Explicit UI warnings capturing risks or contradictions stably safely.")
    metadata: ResponseMetadata = Field(..., description="Telemetry and execution tracking bounds accurately mapping overhead natively.")
