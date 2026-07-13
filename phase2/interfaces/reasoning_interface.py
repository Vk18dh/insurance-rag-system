from abc import ABC, abstractmethod
from typing import List, Dict, Any

from phase2.models.retrieved_chunk import RetrievedChunk
from phase2.models.verification_result import VerificationResult
from phase2.models.reasoning_step import ReasoningStep
from phase2.models.reasoning_chain import ReasoningChain
from phase2.models.explanation import Explanation
from phase2.models.reasoning_result import ReasoningResult


class IClauseInterpreter(ABC):
    """
    Translates raw string evidence from standard RetrievedChunks into explicitly 
    isolated insurance clauses mapping distinct conceptual boundaries (e.g., Free Look vs Lapse).
    """
    @abstractmethod
    def interpret(self, chunks: List[RetrievedChunk], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extracts foundational insurance clauses natively.
        Does NOT build multi-step reasoning.
        """
        pass

class IEvidenceLinker(ABC):
    """
    Determines topological mapping relationships between disjoint clauses 
    (e.g. Clause B legally overrides/supports Clause A).
    """
    @abstractmethod
    def link_evidence(self, clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Yields connected clause groupings or dependency pairs.
        """
        pass

class IReasoningChainBuilder(ABC):
    """
    Drives the core logical progression sequence over linked evidence.
    Constructs an explicit pipeline of `ReasoningStep` objects securely bound without generating final replies.
    """
    @abstractmethod
    def build_chain(self, verification_result: VerificationResult, linked_clauses: List[Dict[str, Any]]) -> ReasoningChain:
        """
        Iteratively constructs a reasoning chain up to a configured maximum depth length.
        """
        pass

class IExplanationService(ABC):
    """
    Maps mechanical ReasoningStep definitions into UX-friendly explanation schemas 
    strictly noting any unsupported dependencies.
    """
    @abstractmethod
    def generate_explanation(self, reasoning_chain: ReasoningChain) -> Explanation:
        """
        Produces detailed string boundaries explicitly highlighting assumptions 
        and mapping logic constraints natively for transparency.
        """
        pass

class IReasoningAgent(ABC):
    """
    Top-Level Agent Orchestrator governing Part 4 workflows.
    Binds the interpreters, linkers, and chain builders synchronously inside protected error bounds.
    """
    @abstractmethod
    def reason(self, verification_result: VerificationResult) -> ReasoningResult:
        """
        Accepts the definitive VerificationResult boundary and resolves directly into 
        a bounded ReasoningResult without ever retrieving external data natively.
        """
        pass
