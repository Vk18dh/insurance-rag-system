from pydantic import BaseModel, Field

class ReasoningMetrics(BaseModel):
    """
    Performance and quality metrics telemetry isolating the 
    efficiency and thoroughness of the LLM execution pipeline.
    """
    reasoning_completeness: float = Field(
        ..., 
        ge=0.0, le=1.0, 
        description="Internal measure of query objective fulfillment."
    )
    evidence_coverage_ratio: float = Field(
        ..., 
        ge=0.0, le=1.0, 
        description="Percentage of verified evidence chunks actually incorporated into the chain."
    )
    logical_consistency_score: float = Field(
        ..., 
        ge=0.0, le=1.0, 
        description="Scored integrity ensuring internal steps do not contradict."
    )
    processing_time_ms: float = Field(
        ..., 
        ge=0.0,
        description="Performance tracing for pipeline optimization tracking."
    )
    total_steps: int = Field(
        ..., 
        ge=0,
        description="Length of the ReasoningChain."
    )
