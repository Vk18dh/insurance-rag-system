import logging
from phase2.config.settings import Phase2Settings
from phase2.interfaces.risk_agent_interface import IRiskAgent, IRiskAssessmentService
from phase2.interfaces.query_agent_interface import ILLMAnalyzer

from phase2.models.reasoning_result import ReasoningResult
from phase2.models.risk_assessment import RiskAssessmentResult
from phase2.exceptions.handlers import safe_agent_call

from phase2.services.ambiguity_detector import AmbiguityDetector
from phase2.services.legal_sensitivity_checker import LegalSensitivityChecker
from phase2.services.exclusion_checker import ExclusionChecker
from phase2.services.regulatory_checker import RegulatoryChecker
from phase2.services.escalation_service import EscalationService
from phase2.services.risk_assessment_service import RiskAssessmentService

logger = logging.getLogger(__name__)

class RiskAgent(IRiskAgent):
    """
    Core executor bounding the Reasoning logic evaluations into
    structured operational risk artifacts cleanly preventing hallucinated metadata.
    """
    def __init__(self, assessment_service: IRiskAssessmentService):
        self._assessment_service = assessment_service

    def evaluate(self, reasoning_result: ReasoningResult) -> RiskAssessmentResult:
        """Evaluates logic securely routing exceptions through handlers."""
        query_id = getattr(reasoning_result.verification_source.retrieval_result.query_context, "query_id", "Unknown")
        logger.info(f"Risk evaluation initiated securely for Query [{query_id}]")
        
        with safe_agent_call("RiskAgent", query_id=query_id, reraise=True):
            risk_result = self._assessment_service.assess_risk(reasoning_result)
            logger.info(
                f"Risk bounds processed securely generating a [{risk_result.overall_risk_level.value}] Level Assessment",
                extra={"query_id": query_id, "metrics": risk_result.metrics.model_dump()}
            )
            return risk_result


class RiskAgentFactory:
    """Safely encapsulates Dependency Bounds tying Settings and Configs."""
    @staticmethod
    def create(settings: Phase2Settings, llm_analyzer: ILLMAnalyzer) -> IRiskAgent:
        ambiguity_svc = AmbiguityDetector()
        legal_svc = LegalSensitivityChecker()
        exclusion_svc = ExclusionChecker()
        reg_svc = RegulatoryChecker()
        escalation_svc = EscalationService()
        
        assessment_svc = RiskAssessmentService(
            llm_analyzer=llm_analyzer,
            prompt_template_path=settings.risk.prompt_template_path,
            ambiguity_detector=ambiguity_svc,
            legal_checker=legal_svc,
            exclusion_checker=exclusion_svc,
            regulatory_checker=reg_svc,
            escalation_service=escalation_svc,
            supported_risk_categories=settings.risk.supported_risk_categories
        )
        
        return RiskAgent(assessment_svc)
