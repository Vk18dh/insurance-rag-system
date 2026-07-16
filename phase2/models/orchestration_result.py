from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from phase2.models.execution_status import ExecutionStatus
from phase2.models.execution_step import ExecutionStep
from phase2.models.workflow_metrics import WorkflowMetrics

# Dynamic imported type placeholders ensuring compatibility natively decoupling exact dependencies smoothly
from phase2.models.query_context import QueryContext
from phase2.models.retrieval_result import RetrievalResult
from phase2.models.verification_result import VerificationResult
from phase2.models.reasoning_result import ReasoningResult
from phase2.models.risk_assessment import RiskAssessmentResult
from phase2.models.contradiction_result import ContradictionResult
from phase2.models.final_response import FinalResponse

class SharedContext(BaseModel):
    """Maintains SharedExecutionContext tracking properties independently avoiding memory overlap natively."""
    query_context: Optional[QueryContext] = None
    retrieval_result: Optional[RetrievalResult] = None
    verification_result: Optional[VerificationResult] = None
    reasoning_result: Optional[ReasoningResult] = None
    risk_result: Optional[RiskAssessmentResult] = None
    contradiction_result: Optional[ContradictionResult] = None
    final_response: Optional[FinalResponse] = None

class OrchestrationResult(BaseModel):
    """Root trace returning the completely executed Context natively strictly mapping cleanly sequentially."""
    request_id: str = Field(..., description="Unique traceability token securely tracking correlation ID natively.")
    overall_status: ExecutionStatus = Field(..., description="Ultimate workflow execution limits natively bound.")
    metrics: WorkflowMetrics = Field(default_factory=WorkflowMetrics)
    execution_history: List[ExecutionStep] = Field(default_factory=list, description="Ordered map explicitly tracing constraints.")
    shared_context: SharedContext = Field(default_factory=SharedContext)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
