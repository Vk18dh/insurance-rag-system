import logging
from phase2.config.settings import Phase2Settings
from phase2.interfaces.contradiction_interface import IContradictionAgent, IContradictionService
from phase2.interfaces.query_agent_interface import ILLMAnalyzer

from phase2.models.reasoning_result import ReasoningResult
from phase2.models.risk_assessment import RiskAssessmentResult
from phase2.models.contradiction_result import ContradictionResult

from phase2.exceptions.handlers import safe_agent_call

logger = logging.getLogger(__name__)

class ContradictionAgent(IContradictionAgent):
    """
    Central logic execution boundary orchestrating Part 6 constraints flawlessly.
    """
    def __init__(self, settings: Phase2Settings, contradiction_service: IContradictionService):
        self._settings = settings
        self._contradiction_service = contradiction_service

    def process(self, reasoning_result: ReasoningResult, risk_result: RiskAssessmentResult) -> ContradictionResult:
        logger.info("Contradiction agent analysis initiated natively securely.")
        with safe_agent_call("ContradictionAgent", reraise=True):
            return self._contradiction_service.detect_contradictions(reasoning_result, risk_result)


class ContradictionAgentFactory:
    """
    Dependency Injection root resolving Singleton services without structural bloat safely.
    """
    @staticmethod
    def create(settings: Phase2Settings, llm_analyzer: ILLMAnalyzer) -> IContradictionAgent:
        from phase2.services.policy_context_validator import PolicyContextValidator
        from phase2.services.evidence_alignment_service import EvidenceAlignmentService
        from phase2.services.contradiction_classifier import ContradictionClassifier
        from phase2.services.contradiction_explainer import ContradictionExplainer
        from phase2.services.conflict_resolution_helper import ConflictResolutionHelper
        from phase2.services.contradiction_service import ContradictionService
        
        ctx_val = PolicyContextValidator()
        align_svc = EvidenceAlignmentService()
        classifier = ContradictionClassifier()
        explainer = ContradictionExplainer()
        try:
            pt_path = settings.contradiction.prompt_template_path
            categories = settings.contradiction.supported_contradiction_categories
            thresholds = settings.contradiction.conflict_thresholds
        except AttributeError:
            pt_path = "phase2/prompts/contradiction_detection_prompt.txt"
            categories = ["Logical", "Regulatory", "Clause", "Coverage", "Eligibility", "Benefit", "Exclusion"]
            thresholds = [
                "CRITICAL -> HALT",
                "HIGH -> REVIEW"
            ]

        resolver = ConflictResolutionHelper(thresholds)
        
        svc = ContradictionService(
            llm_analyzer=llm_analyzer,
            prompt_template_path=pt_path,
            context_validator=ctx_val,
            alignment_service=align_svc,
            classifier=classifier,
            explainer=explainer,
            resolution_helper=resolver,
            supported_categories=categories
        )
        return ContradictionAgent(settings, svc)
