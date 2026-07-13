from abc import ABC, abstractmethod
from typing import Dict, Any

from phase2.models.reasoning_result import ReasoningResult
from phase2.models.risk_assessment import RiskAssessmentResult

from phase2.models.contradiction_result import ContradictionResult
from phase2.models.contradiction_record import ContradictionRecord
from phase2.models.conflict_level import ConflictLevel
from phase2.models.evidence_alignment import EvidenceAlignment


class IPolicyContextValidator(ABC):
    """Prevents false positives by bounding cross-policy comparisons strictly."""
    @abstractmethod
    def validate_compatibility(self, reasoning_result: ReasoningResult) -> bool:
        pass


class IEvidenceAlignmentService(ABC):
    """Maps clauses anchoring reasoning conclusions to verified chunks securely."""
    @abstractmethod
    def align_evidence(self, reasoning_result: ReasoningResult) -> EvidenceAlignment:
        pass


class IContradictionClassifier(ABC):
    """Parses logical overlap bounds strictly dictating ConflictLevel."""
    @abstractmethod
    def classify(self, llm_payload: Dict[str, Any]) -> ConflictLevel:
        pass


class IContradictionExplainer(ABC):
    """Generates structural boundary mappings extracting LLM explanation bounds safely."""
    @abstractmethod
    def explain(self, llm_payload: Dict[str, Any]) -> str:
        pass


class IConflictResolutionHelper(ABC):
    """Creates routing limits based structurally on conflict density."""
    @abstractmethod
    def recommend(self, conflict_level: ConflictLevel) -> str:
        pass


class IContradictionService(ABC):
    """Orchestrator securely driving independent constraint validators without monolithic dependencies."""
    @abstractmethod
    def detect_contradictions(self, reasoning_result: ReasoningResult, risk_result: RiskAssessmentResult) -> ContradictionResult:
        pass


class IContradictionAgent(ABC):
    """Primary boundary isolating configuration and service injections natively."""
    @abstractmethod
    def process(self, reasoning_result: ReasoningResult, risk_result: RiskAssessmentResult) -> ContradictionResult:
        pass
