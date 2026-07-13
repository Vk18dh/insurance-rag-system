from pydantic import BaseModel, Field

class RiskProcessingMetrics(BaseModel):
    """Captures performance telemetry preventing logic loop anomalies."""
    execution_time_ms: float = Field(..., ge=0.0)
    risk_factors_detected: int = Field(..., ge=0)
