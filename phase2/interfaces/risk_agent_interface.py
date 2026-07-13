from abc import ABC, abstractmethod
from typing import Dict, Any

from phase2.models.reasoning_result import ReasoningResult
from phase2.models.risk_assessment import RiskAssessmentResult

from phase2.models.ambiguity_report import AmbiguityReport
from phase2.models.legal_warning import LegalWarning
from phase2.models.exclusion_warning import ExclusionWarning
from phase2.models.regulatory_warning import RegulatoryWarning
from phase2.models.escalation_recommendation import EscalationRecommendation

class IRiskAmbiguityDetector(ABC):
    """Abstract Strategy: Extracts ambiguity metrics from structured JSON envelopes."""
    @abstractmethod
    def detect(self, json_payload: Dict[str, Any]) -> AmbiguityReport:
        pass

class ILegalSensitivityChecker(ABC):
    """Abstract Strategy: Extracts legal bounds from structured JSON envelopes."""
    @abstractmethod
    def check(self, json_payload: Dict[str, Any]) -> LegalWarning:
        pass

class IExclusionChecker(ABC):
    """Abstract Strategy: Extracts exclusion bounds from structured JSON envelopes."""
    @abstractmethod
    def check(self, json_payload: Dict[str, Any]) -> ExclusionWarning:
        pass

class IRegulatoryChecker(ABC):
    """Abstract Strategy: Extracts regulatory boundaries from structured JSON envelopes."""
    @abstractmethod
    def check(self, json_payload: Dict[str, Any]) -> RegulatoryWarning:
        pass

class IEscalationService(ABC):
    """Abstract Strategy: Extracts high-risk operational evaluations and evaluates escalation."""
    @abstractmethod
    def evaluate(self, json_payload: Dict[str, Any]) -> EscalationRecommendation:
        pass

class IRiskAssessmentService(ABC):
    """
    Abstract Orchestrator: Fires the unified LLM prompt, secures the JSON envelope natively,
    and coordinates parsing delegates.
    """
    @abstractmethod
    def assess_risk(self, reasoning_result: ReasoningResult) -> RiskAssessmentResult:
        pass

class IRiskAgent(ABC):
    """
    Abstract Agent: Safely binds `VerificationResult` boundaries and mounts standard logging limits.
    """
    @abstractmethod
    def evaluate(self, reasoning_result: ReasoningResult) -> RiskAssessmentResult:
        pass
