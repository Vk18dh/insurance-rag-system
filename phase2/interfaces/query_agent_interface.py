"""
phase2.interfaces.query_agent_interface
========================================

Abstract contracts for every component of the Query Understanding pipeline.

Design rationale:
    - Coding to an interface (not a concrete class) enables the Orchestrator to
      swap implementations without any structural changes (Open/Closed Principle).
    - Enables dependency injection and mock substitution in tests.
    - All future alternative agents, LLM providers, normalizers, etc. must
      implement the same contracts.

Classes:
    ILLMAnalyzer        — Abstract base for LLM/NLP analysis backends
                          (Gemini, OpenAI, Claude, Local, Offline).
    IQueryProcessingService — Abstract base for the query processing service.
    IQueryAgent         — Abstract base class for the Query Understanding Agent.
    ITextNormalizer     — Abstract base class for text normalisation strategies.
    IIntentDetector     — Abstract base class for intent detection strategies.
    IEntityExtractor    — Abstract base class for entity extraction strategies.
    IQueryClassifier    — Abstract base class for query classification strategies.
    IAmbiguityDetector  — Abstract base class for ambiguity detection strategies.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


# ---------------------------------------------------------------------------
# Forward-import types via string annotations to avoid circular imports.
# Concrete files import from phase2.models explicitly.
# ---------------------------------------------------------------------------
from phase2.models.intent import IntentResult
from phase2.models.query_context import ExtractedEntities, QueryContext
from phase2.models.query_metadata import AmbiguityInfo, QueryClassification


# ===========================================================================
# ILLMAnalyzer — Abstract backend for single-pass LLM/NLP analysis
# ===========================================================================
class ILLMAnalyzer(ABC):
    """
    Abstract base class for all LLM/NLP analysis backends.

    Implementations may use:
        - Google Gemini (GeminiQueryAnalyzer)
        - OpenAI GPT (future)
        - Anthropic Claude (future)
        - Local/HuggingFace model (future)
        - Rule-based offline fallback (FallbackQueryAnalyzer)

    The active implementation is selected via ``settings.llm.provider``.
    All downstream adapters (IIntentDetector, IEntityExtractor, etc.) depend
    on this interface — never on a concrete analyzer class.

    Contract:
        ``analyse()`` must return a dict with the following top-level keys:
            - intent        : dict with keys primary, secondary, confidence, explanation
            - entities      : dict with entity category lists
            - classification: str matching a QueryClassification value
            - ambiguity     : dict with is_ambiguous, ambiguity_type, etc.
            - language      : BCP-47 language code (e.g. 'en')
    """

    @abstractmethod
    def analyse(self, normalized_query: str) -> Dict[str, Any]:
        """
        Perform a single-pass analysis of the normalised query.

        Args:
            normalized_query: The cleaned, normalised query text.

        Returns:
            Dict with keys: intent, entities, classification, ambiguity, language.

        Raises:
            QueryProcessingException: On model or parsing failure.
            QueryTimeoutException   : When analysis exceeds the configured timeout.
        """
        ...


# ===========================================================================
# IQueryProcessingService — Abstract contract for the processing service
# ===========================================================================
class IQueryProcessingService(ABC):
    """
    Abstract base class for the Query Processing Service.

    Separating this behind an interface allows:
        - MockQueryProcessingService in tests without concrete binding.
        - CachedQueryProcessingService with Redis in production.
        - StreamingQueryProcessingService for future streaming pipelines.

    QueryUnderstandingAgent depends on this interface, never on the
    concrete QueryProcessingService class.
    """

    @abstractmethod
    def process(self, raw_query: str) -> QueryContext:
        """
        Run the full Query Understanding pipeline on a raw user query.

        Args:
            raw_query: Exact, unmodified user input string.

        Returns:
            QueryContext: Fully populated context ready for the Retrieval Agent.

        Raises:
            QueryValidationException : On invalid input.
            QuerySecurityException   : On security violation.
            QueryProcessingException : On NLP pipeline failure.
            QueryTimeoutException    : On processing timeout.
        """
        ...

    @abstractmethod
    def validate_only(self, raw_query: str) -> bool:
        """
        Validate input without running the full pipeline.

        Args:
            raw_query: Raw user input string.

        Returns:
            bool: True if valid.

        Raises:
            QueryValidationException: On invalid input.
            QuerySecurityException  : On security violation.
        """
        ...


# ===========================================================================
# IQueryAgent — Top-level contract
# ===========================================================================
class IQueryAgent(ABC):
    """
    Abstract base class defining the public contract of the Query Understanding Agent.

    Implementors must process a raw user query through the full pipeline:
    validation → normalisation → intent detection → entity extraction →
    classification → ambiguity detection → metadata generation.

    The Orchestrator depends on this interface, NOT on any concrete class.
    Concrete implementations are injected via the constructor of the Orchestrator.

    Usage::

        class ConcreteQueryAgent(IQueryAgent):
            def process(self, raw_query: str) -> QueryContext:
                ...

        orchestrator = Orchestrator(query_agent=ConcreteQueryAgent(...))
    """

    @abstractmethod
    def process(self, raw_query: str) -> QueryContext:
        """
        Process a raw user query through the full Query Understanding pipeline.

        This is the single entry-point called by the Orchestrator.
        Implementations must be stateless with respect to user data —
        all state lives inside the returned QueryContext.

        Args:
            raw_query: The exact, unmodified string received from the user interface.

        Returns:
            QueryContext: Fully populated context object ready for the
                          Retrieval Agent.

        Raises:
            QueryValidationException : When the query fails input validation.
            QueryProcessingException : When processing fails due to a model or
                                       service error.
            QueryTimeoutException    : When processing exceeds the configured
                                       timeout.
        """
        ...

    @abstractmethod
    def validate(self, raw_query: str) -> bool:
        """
        Perform input validation on a raw query without running the full pipeline.

        Useful for early rejection at the API layer before allocating processing
        resources.

        Args:
            raw_query: Raw user input string.

        Returns:
            bool: True when the query is valid and can be processed.

        Raises:
            QueryValidationException: On invalid input with structured error detail.
        """
        ...

    @abstractmethod
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Return structured metadata about this agent implementation.

        Used by the Orchestrator for logging, health checks, and diagnostics.

        Returns:
            Dict containing at minimum:
                - 'name'       : str  — human-readable agent name
                - 'version'    : str  — semver version string
                - 'model'      : str  — LLM/NLP model in use (from config)
                - 'capabilities': list — list of supported processing steps
        """
        ...


# ===========================================================================
# ITextNormalizer — Strategy interface for text normalisation
# ===========================================================================
class ITextNormalizer(ABC):
    """
    Abstract base class for text normalisation strategies.

    Separating normalisation behind an interface allows swapping
    basic regex normalisation for a language-model-powered approach
    without changing the service layer.

    All implementations must preserve:
        - Insurance terminology
        - Policy names
        - Numbers and amounts
        - Abbreviations (e.g. 'UIN', 'IRDAI', 'LIC')
    """

    @abstractmethod
    def normalize(self, text: str) -> str:
        """
        Normalise the input text.

        Args:
            text: Raw text to normalise.

        Returns:
            str: Normalised text suitable for downstream NLP processing.

        Raises:
            QueryValidationException: If text is invalid or empty.
        """
        ...


# ===========================================================================
# IIntentDetector — Strategy interface for intent classification
# ===========================================================================
class IIntentDetector(ABC):
    """
    Abstract base class for intent detection strategies.

    Implementations may use:
        - LLM-based zero-shot classification (default)
        - Fine-tuned text classifiers
        - Keyword-matching fallback (for offline/test environments)

    The active implementation is selected via configuration.
    Business logic never hardcodes 'if intent == X'.
    """

    @abstractmethod
    def detect(self, normalized_query: str) -> IntentResult:
        """
        Detect the primary intent of the normalised query.

        Args:
            normalized_query: The cleaned, normalised query text.

        Returns:
            IntentResult: Typed intent result with confidence score.

        Raises:
            QueryProcessingException: On model or service failure.
            QueryTimeoutException   : When detection exceeds configured timeout.
        """
        ...


# ===========================================================================
# IEntityExtractor — Strategy interface for entity extraction
# ===========================================================================
class IEntityExtractor(ABC):
    """
    Abstract base class for insurance entity extraction strategies.

    Implementations may use:
        - LLM-based structured extraction (default)
        - spaCy NER pipeline
        - Rule-based regex extraction (for offline/test environments)

    The active implementation is selected via configuration.
    No policy names or entity types are hardcoded in business logic.
    """

    @abstractmethod
    def extract(self, normalized_query: str) -> ExtractedEntities:
        """
        Extract insurance entities from the normalised query.

        Args:
            normalized_query: The cleaned, normalised query text.

        Returns:
            ExtractedEntities: Typed container of all extracted entity groups.

        Raises:
            QueryProcessingException: On model or service failure.
            QueryTimeoutException   : When extraction exceeds configured timeout.
        """
        ...


# ===========================================================================
# IQueryClassifier — Strategy interface for structural query classification
# ===========================================================================
class IQueryClassifier(ABC):
    """
    Abstract base class for query structural classification strategies.

    Classification determines the *type* of the query
    (factual, comparative, regulatory, etc.) to help the Retrieval Agent
    choose the most appropriate retrieval strategy.
    """

    @abstractmethod
    def classify(self, normalized_query: str, intent: IntentResult) -> QueryClassification:
        """
        Classify the structural type of the query.

        Args:
            normalized_query: The cleaned, normalised query text.
            intent          : Already-detected intent result.

        Returns:
            QueryClassification: The structural category of the query.

        Raises:
            QueryProcessingException: On classification failure.
        """
        ...


# ===========================================================================
# IAmbiguityDetector — Strategy interface for ambiguity detection
# ===========================================================================
class IAmbiguityDetector(ABC):
    """
    Abstract base class for ambiguity detection strategies.

    A query is ambiguous when essential context is missing, making it
    impossible to retrieve the correct evidence without clarification.

    Implementations may use:
        - LLM-based reasoning
        - Rule-based checks against extracted entities
        - Statistical thresholds on intent confidence
    """

    @abstractmethod
    def detect(
        self,
        normalized_query: str,
        intent: IntentResult,
        entities: ExtractedEntities,
    ) -> AmbiguityInfo:
        """
        Determine whether the query is ambiguous.

        Args:
            normalized_query: The cleaned, normalised query text.
            intent          : Already-detected intent result.
            entities        : Already-extracted entities.

        Returns:
            AmbiguityInfo: Structured ambiguity signal.

        Raises:
            QueryProcessingException: On detection failure.
        """
        ...
