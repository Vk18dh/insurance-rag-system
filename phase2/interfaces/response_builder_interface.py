"""
phase2.interfaces.response_builder_interface

Defines base Abstract interfaces for all Response Builder components mapping strictly natively securely cleanly.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from phase2.models.final_response import FinalResponse
from phase2.models.citation import Citation
from phase2.models.warning import ResponseWarning
from phase2.models.response_section import ResponseSection

from phase2.models.verification_result import VerificationResult
from phase2.models.reasoning_result import ReasoningResult
from phase2.models.risk_assessment import RiskAssessmentResult
from phase2.models.contradiction_result import ContradictionResult


class ICitationService(ABC):
    """Generates structural citations mapping directly back to Verification boundaries natively cleanly."""
    @abstractmethod
    def build_citations(self, reasoning_result: ReasoningResult) -> List[Citation]:
        """Extract citations enforcing traceability smoothly scaling bounds explicitly safely natively."""
        pass


class IWarningService(ABC):
    """Transposes risk anomalies and logic contradictions cleanly into user-observable UI Warnings."""
    @abstractmethod
    def build_warnings(
        self,
        risk_result: Optional[RiskAssessmentResult],
        contradiction_result: Optional[ContradictionResult]
    ) -> List[ResponseWarning]:
        """Generate structured Warnings safely naturally converting internal risk mappings securely cleanly."""
        pass


class IExplanationFormatter(ABC):
    """Maps reasoning limits to neutral UI-agnostic explanatory formats dynamically."""
    @abstractmethod
    def format_explanation(self, reasoning_result: ReasoningResult) -> str:
        """Constructs string layout mapping evidence chains implicitly tracing limits stably safely cleanly."""
        pass


class IResponseFormatter(ABC):
    """Extracts direct answers seamlessly tracking grammar boundaries dynamically matching defaults natively."""
    @abstractmethod
    def format_answer(self, reasoning_result: ReasoningResult) -> str:
        """Constructs explicitly tracked natural answers handling fallbacks smoothly exactly dynamically."""
        pass


class IResponseValidator(ABC):
    """Gates payload enforcing safety preventing malformatted injections securely neatly explicitly accurately."""
    @abstractmethod
    def validate(self, response: FinalResponse) -> None:
        """Raises exceptions natively if fields fail schema requirements strictly safely explicitly smoothly."""
        pass


class IResponseComposer(ABC):
    """Drives internal dependency mapping aggregating chunks efficiently gracefully correctly properly implicitly."""
    @abstractmethod
    def compose(
        self,
        verification_result: VerificationResult,
        reasoning_result: ReasoningResult,
        risk_result: Optional[RiskAssessmentResult],
        contradiction_result: Optional[ContradictionResult]
    ) -> FinalResponse:
        """Integrates dependencies reliably smoothly securely explicitly mapping outputs gracefully natively safely."""
        pass


class IResponseBuilderAgent(ABC):
    """Sits stably mapping the top level agent boundary routing safely across the pipeline cleanly explicitly."""
    @abstractmethod
    def build_response(
        self,
        verification_result: VerificationResult,
        reasoning_result: ReasoningResult,
        risk_result: Optional[RiskAssessmentResult],
        contradiction_result: Optional[ContradictionResult]
    ) -> FinalResponse:
        """Builds FinalResponse tracking logic natively securely gracefully perfectly implicitly reliably exactly."""
        pass
