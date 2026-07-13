"""
phase2.models.response_metadata

Tracks agent latency, confidence, and system identifiers smoothly safely.
"""
from typing import Optional
from pydantic import BaseModel, Field

class ResponseMetadata(BaseModel):
    """
    Telemetry boundaries securely wrapping execution mapping statistics dynamically safely.
    """
    request_id: str = Field(..., description="Unique tracer ID for the request.")
    total_processing_time_ms: float = Field(..., description="Total time taken to generate the final response.")
    agent_version: str = Field(..., description="Version of the Response Builder agent natively configured.")
    confidence_score: Optional[float] = Field(None, description="Aggregated confidence score (Placeholder for Future Phase 3 HITL mapping).")
