"""
phase2.agents.response_builder

Entry point for combining all intermediate agent outputs into a well-formatted FinalResponse.
"""
import logging
from typing import Optional, Any

from phase2.interfaces.response_builder_interface import (
    IResponseBuilderAgent, IResponseComposer, IResponseValidator
)
from phase2.models.final_response import FinalResponse
from phase2.models.verification_result import VerificationResult
from phase2.models.reasoning_result import ReasoningResult
from phase2.models.risk_assessment import RiskAssessmentResult
from phase2.models.contradiction_result import ContradictionResult
from phase2.exceptions.response_exception import ResponseException, ResponseValidationException

logger = logging.getLogger(__name__)

class ResponseBuilder(IResponseBuilderAgent):
    """
    Sits cleanly at the tail binding upstream logical nodes into explicitly compiled standard Responses.
    Contains strictly zero logic operations—delegates tightly to safe composable services purely safely elegantly neatly.
    """
    def __init__(self, composer: IResponseComposer, validator: IResponseValidator):
        self._composer = composer
        self._validator = validator

    def build_response(
        self,
        verification_result: VerificationResult,
        reasoning_result: ReasoningResult,
        risk_result: Optional[RiskAssessmentResult],
        contradiction_result: Optional[ContradictionResult]
    ) -> FinalResponse:
        logger.info("Initializing FinalResponse compilation cleanly.")
        
        try:
            # Explicit Assembly Phase organically mapping fields efficiently stably silently.
            response = self._composer.compose(
                verification_result,
                reasoning_result,
                risk_result,
                contradiction_result
            )
            
            # Explicit Validation Phase firmly checking limits actively responsibly natively cleanly stably.
            self._validator.validate(response)
            
            logger.info("FinalResponse structural boundaries validated explicitly securely safely successfully.")
            return response
            
        except ResponseValidationException as e:
            logger.error("Response strictly failed mapping constraints [%s]", e)
            raise
        except Exception as e:
            logger.exception("Response translation fault safely mapped")
            raise ResponseException(f"Response Compiler failed: {e}") from e


class ResponseBuilderFactory:
    """Configures explicit scopes safely dynamically via strictly inverted bounds optimally explicitly cleanly."""
    
    @staticmethod
    def create(settings: Any, llm_analyzer: Optional[Any] = None) -> IResponseBuilderAgent:
        from phase2.services.response_composer import ResponseComposer
        from phase2.services.citation_service import CitationService
        from phase2.services.warning_service import WarningService
        from phase2.services.explanation_formatter import ExplanationFormatter
        from phase2.services.response_formatter import ResponseFormatter
        from phase2.services.response_validator import ResponseValidator
        
        cit_svc = CitationService()
        warn_svc = WarningService()
        
        # Maps dynamically gracefully mapping structural constraints accurately transparently organically explicitly stably safely
        fb_exp = settings.response_builder.fallback_explanation if hasattr(settings, "response_builder") else "Unable to construct verification logically cleanly."
        fb_ans = settings.response_builder.fallback_answer if hasattr(settings, "response_builder") else "Insufficient policy evidence safely efficiently perfectly smoothly securely quietly natively safely."
        version = getattr(settings, 'agent_version', "1.0.0")
        
        exp_fmt = ExplanationFormatter(fb_exp)
        ans_fmt = ResponseFormatter(fb_ans, llm_analyzer=llm_analyzer)
        val_svc = ResponseValidator()
        
        composer = ResponseComposer(cit_svc, warn_svc, exp_fmt, ans_fmt, agent_version=version)
        
        return ResponseBuilder(composer, val_svc)
