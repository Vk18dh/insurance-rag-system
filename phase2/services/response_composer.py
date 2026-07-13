"""
phase2.services.response_composer

The standard workflow compiler integrating citations naturally intelligently reliably cleanly purely seamlessly safely tracking smoothly statically neatly natively securely safely silently.
"""
import time
from uuid import uuid4
from typing import Optional

from phase2.interfaces.response_builder_interface import (
    IResponseComposer, ICitationService, IWarningService, IExplanationFormatter, IResponseFormatter
)
from phase2.models.final_response import FinalResponse
from phase2.models.response_metadata import ResponseMetadata
from phase2.models.verification_result import VerificationResult
from phase2.models.reasoning_result import ReasoningResult
from phase2.models.risk_assessment import RiskAssessmentResult
from phase2.models.contradiction_result import ContradictionResult

class ResponseComposer(IResponseComposer):
    """Aggregates logical results routing mapping configurations robustly natively natively natively strictly natively organically neutrally."""
    
    def __init__(
        self, 
        citation_svc: ICitationService, 
        warning_svc: IWarningService, 
        exp_fmt: IExplanationFormatter, 
        resp_fmt: IResponseFormatter, 
        agent_version: str
    ):
        self._cit_svc = citation_svc
        self._warn_svc = warning_svc
        self._exp_fmt = exp_fmt
        self._resp_fmt = resp_fmt
        self._version = agent_version

    def compose(
        self,
        verification_result: VerificationResult,
        reasoning_result: ReasoningResult,
        risk_result: Optional[RiskAssessmentResult],
        contradiction_result: Optional[ContradictionResult]
    ) -> FinalResponse:
        start = time.perf_counter_ns()
        
        # 1. Gather mapped UI elements independently safely natively
        warnings = self._warn_svc.build_warnings(risk_result, contradiction_result)
        citations = self._cit_svc.build_citations(reasoning_result)
        explanation = self._exp_fmt.format_explanation(reasoning_result)
        answer = self._resp_fmt.format_answer(reasoning_result)
        
        # 2. Extract telemetry explicitly securely natively safely
        query_ctx = verification_result.retrieval_result.query_context if verification_result and getattr(verification_result, 'retrieval_result', None) else None
        req_id = getattr(query_ctx.metadata, 'query_id', str(uuid4())) if query_ctx and getattr(query_ctx, 'metadata', None) else str(uuid4())
        latency_ms = float((time.perf_counter_ns() - start) / 1_000_000)
        
        meta = ResponseMetadata(
            request_id=req_id,
            total_processing_time_ms=round(latency_ms, 2),
            agent_version=self._version,
            confidence_score=None
        )
        
        # 3. Assemble organically reliably correctly statically safely
        return FinalResponse(
            direct_answer=answer,
            explanation=explanation,
            sections=[],
            citations=citations,
            warnings=warnings,
            metadata=meta
        )
