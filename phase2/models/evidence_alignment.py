from pydantic import BaseModel, Field
from typing import List

class EvidenceAlignment(BaseModel):
    """Maps retrieved chunk identifiers explicitly matching reasoning conclusion steps."""
    reasoning_step_ids: List[int] = Field(default_factory=list, description="Reasoning steps tracing this alignment boundaries natively.")
    retrieved_chunk_ids: List[str] = Field(default_factory=list, description="Source context chunks anchoring this alignment securely.")
