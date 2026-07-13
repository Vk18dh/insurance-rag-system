"""
phase2.interfaces.verification_interface
========================================
Defines formal abstraction layers for the Verification Agent and its subsystems.
"""
from abc import ABC, abstractmethod
from typing import List

from phase2.models.retrieved_chunk import RetrievedChunk
from phase2.models.query_context import QueryContext
from phase2.models.retrieval_result import RetrievalResult
from phase2.models.verification_report import VerificationReport
from phase2.models.verification_result import VerificationResult


class IRelevanceChecker(ABC):
    """Protocol for checking chunk topical relevance against user query intent."""
    @abstractmethod
    def evaluate_relevance(self, chunk: RetrievedChunk, query_context: QueryContext) -> float:
        """Returns a scalar score [0.0 - 1.0] evaluating strict alignment."""
        pass


class ICitationValidator(ABC):
    """Protocol for strict evidence citation/pointer verification."""
    @abstractmethod
    def validate_citations(self, chunk: RetrievedChunk) -> float:
        """Returns a scalar score [0.0 - 1.0] indicating citation integrity."""
        pass


class IConsistencyChecker(ABC):
    """Protocol ensuring evidence chunks do not structurally conflict in metadata bounds."""
    @abstractmethod
    def check_metadata_consistency(self, chunks: List[RetrievedChunk]) -> int:
        """Returns the integer count of detected structural inconsistencies."""
        pass


class ICompletenessChecker(ABC):
    """Protocol defining whether retrieved data collectively satisfies the query type."""
    @abstractmethod
    def evaluate_completeness(self, chunks: List[RetrievedChunk], query_context: QueryContext) -> str:
        """Returns categorical completeness evaluation e.g., 'Complete', 'Incomplete'."""
        pass


class IEvidenceValidator(ABC):
    """Protocol for the top-level service orchestrating all subsystem validation passes."""
    @abstractmethod
    def validate_evidence(self, retrieval_result: RetrievalResult) -> VerificationReport:
        """Compiles scores, rules, and citations across all chunks into a structured VerificationReport."""
        pass


class IVerificationAgent(ABC):
    """Protocol for the core Verification orchestrator."""
    @abstractmethod
    def verify(self, retrieval_result: RetrievalResult) -> VerificationResult:
        """Entry point consuming raw RetrievalResults and issuing bounding VerificationResults."""
        pass
