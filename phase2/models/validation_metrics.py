"""
phase2.models.validation_metrics
=================================
Aggregated metrics from the structured verification pass.
"""
from pydantic import BaseModel, Field

class ValidationMetrics(BaseModel):
    """
    Quantitative metrics indicating the throughput and attrition
    of retrieved chunks during the verification sequence.
    """
    total_chunks_evaluated: int = Field(
        default=0, ge=0, 
        description="Total chunks provided by the Retriever Agent."
    )
    chunks_passed_relevance: int = Field(
        default=0, ge=0, 
        description="Chunks exceeding the minimum relevance threshold."
    )
    chunks_with_valid_citations: int = Field(
        default=0, ge=0, 
        description="Chunks possessing strictly valid document locations."
    )
    metadata_integrity_score: float = Field(
        default=0.0, ge=0.0, le=1.0, 
        description="Aggregate integrity score of structural metadata across all chunks."
    )
    structural_consistencies_found: int = Field(
        default=0, ge=0,
        description="Count of structural inconsistencies detected."
    )
    overall_evidence_completeness: str = Field(
        default="Incomplete",
        description="Discrete status: 'Complete' or 'Incomplete'."
    )
    execution_time_ms: float = Field(
        default=0.0, ge=0.0,
        description="Total verification step execution time in milliseconds."
    )
