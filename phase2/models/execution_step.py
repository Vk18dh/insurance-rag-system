from pydantic import BaseModel, Field
from typing import Optional
from phase2.models.execution_status import ExecutionStatus

class ExecutionStep(BaseModel):
    """Node logging individual agent executions seamlessly mapping start and end arrays securely."""
    agent_name: str = Field(..., description="Name of the bounding agent or sequence trace natively.")
    status: ExecutionStatus = Field(ExecutionStatus.SUCCESS, description="End state of this specific bound explicitly.")
    start_time_ms: float = Field(0.0, description="Start timestamp tracing isolated loops.")
    end_time_ms: float = Field(0.0, description="End timestamp securely natively.")
    duration_ms: float = Field(0.0, description="Extracted latency limit cleanly.")
    retry_count: int = Field(0, description="Transient retries explicitly consumed matching loops safely.")
    error_message: Optional[str] = Field(None, description="Exception bounds strictly extracted.")
