from pydantic import BaseModel, Field

class ContradictionMetrics(BaseModel):
    extraction_time_ms: float = Field(0.0, description="Total ms evaluating the LLM constraints reliably.")
    total_contradictions_found: int = Field(0, description="Amount of isolated conflicts structurally identified.")
    false_positives_prevented: int = Field(0, description="Number of instances safely discarded natively due to policy bounds mapping mismatch.")
