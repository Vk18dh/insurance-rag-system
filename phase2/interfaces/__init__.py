"""
phase2.interfaces — Public interface exports.

Part 1 interfaces are already defined in query_agent_interface.py.
Part 2 adds: retrieval_interface.py with IPhase1Retriever, IRetrievalStrategy,
IRankingService, IValidationService, IRetrievalAgent.
"""

# Part 1 interfaces (unchanged)
from phase2.interfaces.query_agent_interface import (
    IAmbiguityDetector,
    IEntityExtractor,
    IIntentDetector,
    ILLMAnalyzer,
    IQueryAgent,
    IQueryClassifier,
    IQueryProcessingService,
    ITextNormalizer,
)

# Part 2 interfaces (new)
from phase2.interfaces.retrieval_interface import (
    IPhase1Retriever,
    IRankingService,
    IRetrievalAgent,
    IRetrievalStrategy,
    IValidationService,
)

__all__ = [
    # Part 1
    "IAmbiguityDetector",
    "IEntityExtractor",
    "IIntentDetector",
    "ILLMAnalyzer",
    "IQueryAgent",
    "IQueryClassifier",
    "IQueryProcessingService",
    "ITextNormalizer",
    # Part 2
    "IPhase1Retriever",
    "IRankingService",
    "IRetrievalAgent",
    "IRetrievalStrategy",
    "IValidationService",
]
