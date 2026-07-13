"""
phase2.interfaces.retrieval_interface
========================================

Abstract Base Classes (ABCs) for the Retrieval Agent and its dependencies.

Design:
    All interfaces follow the same ABC pattern established in Part 1's
    query_agent_interface.py. Every concrete implementation depends only on
    ABCs, never on concrete classes (Dependency Inversion Principle).

    The hierarchy:
        IPhase1Retriever   — wraps Phase 1 raw search functions
        IRetrievalStrategy — selects retrieval weights per query type
        IRankingService    — ranks a list of RetrievedChunk objects
        IValidationService — validates retrieval quality
        IRetrievalAgent    — top-level agent contract

    All ABCs use @abstractmethod + strict type hints, matching Part 1 style.

Integration with Part 1:
    - IQueryAgent (Part 1) → IRetrievalAgent (Part 2) are siblings in the
      agent hierarchy — both consumed by the Orchestrator.
    - IRetrievalAgent.retrieve() accepts QueryContext from Part 1 directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from phase2.models.query_context import QueryContext
from phase2.models.retrieved_chunk import RetrievedChunk
from phase2.models.retrieval_result import RetrievalResult


# ===========================================================================
# IPhase1Retriever
# ===========================================================================

class IPhase1Retriever(ABC):
    """
    Interface for the Phase 1 retrieval adapter.

    Implementations must wrap Phase 1's bm25_search and vector_search functions
    and return typed RetrievedChunk objects.

    This interface is the ONLY point of contact between Phase 2 and Phase 1.
    No other Part 2 class may import from app.py or Phase 1 directly.

    Methods:
        bm25_search(query, top_k)    → List[RetrievedChunk]
        vector_search(query, top_k)  → List[RetrievedChunk]
        is_available()               → bool (both indexes reachable)
    """

    @abstractmethod
    def bm25_search(self, query: str, top_k: int) -> List[RetrievedChunk]:
        """
        Execute BM25 keyword search against the Phase 1 index.

        Args:
            query  : Normalised query string from QueryContext.
            top_k  : Maximum number of chunks to return.

        Returns:
            List of RetrievedChunk with bm25_score populated.
            Returns empty list if index is unavailable (may raise IndexUnavailableException).

        Raises:
            IndexUnavailableException : BM25 index file not found or unreadable.
        """
        ...

    @abstractmethod
    def vector_search(self, query: str, top_k: int) -> List[RetrievedChunk]:
        """
        Execute cosine-similarity vector search against ChromaDB.

        Args:
            query  : Normalised query string from QueryContext.
            top_k  : Maximum number of chunks to return.

        Returns:
            List of RetrievedChunk with vector_score populated.

        Raises:
            IndexUnavailableException : ChromaDB directory not found.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check whether both Phase 1 indexes are accessible.

        Returns:
            True if both BM25 index file and ChromaDB directory exist.
        """
        ...


# ===========================================================================
# IRetrievalStrategy
# ===========================================================================

class IRetrievalStrategy(ABC):
    """
    Interface for retrieval strategy selection.

    Given a QueryContext, determines the retrieval configuration:
    - BM25 weight
    - Vector weight
    - top_k override
    - strategy name (for logging)

    Implementations read weight maps from settings — all weights are
    configuration-driven. No hardcoded values in implementations.
    """

    @abstractmethod
    def select(self, query_context: QueryContext) -> Dict[str, Any]:
        """
        Select a retrieval strategy based on the query classification and intent.

        Args:
            query_context : Validated QueryContext from Part 1.

        Returns:
            Dict with keys:
                strategy_name : str   — human-readable strategy label
                bm25_weight   : float — weight for BM25 retrieval [0, 1]
                vector_weight : float — weight for vector retrieval [0, 1]
                top_k         : int   — number of chunks to retrieve

        Note:
            bm25_weight + vector_weight do not need to sum to 1.0.
            They are applied independently during score computation.
        """
        ...


# ===========================================================================
# IRankingService
# ===========================================================================

class IRankingService(ABC):
    """
    Interface for evidence re-ranking.

    Receives a list of merged, deduplicated RetrievedChunk objects after
    Phase 1 retrieval and returns them sorted by a composite ranking score.

    The ranking formula is configurable (see RankingSettings in Phase2Settings).
    The interface allows future replacement with LLM-based re-rankers.
    """

    @abstractmethod
    def rank(
        self,
        chunks: List[RetrievedChunk],
        query: str,
        strategy_context: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedChunk]:
        """
        Rank a list of RetrievedChunk objects.

        Args:
            chunks           : Deduplicated chunks from Phase 1.
            query            : Normalised query string (for keyword overlap scoring).
            strategy_context : Optional dict from IRetrievalStrategy.select() for
                               strategy-aware ranking.

        Returns:
            The same chunks sorted by ranking_score descending.
            Each chunk's `ranking_score` and `rank` fields are updated in-place.

        Raises:
            RankingException : If ranking fails for any reason.
        """
        ...


# ===========================================================================
# IValidationService
# ===========================================================================

class IValidationService(ABC):
    """
    Interface for retrieval quality validation.

    Validates the final ranked evidence list and produces warnings and/or
    raises a RetrievalValidationException if quality is critically insufficient.

    Validation checks are controlled entirely by settings (ValidationSettings).
    No thresholds are hardcoded in implementations.
    """

    @abstractmethod
    def validate(
        self,
        chunks: List[RetrievedChunk],
        query_context: QueryContext,
    ) -> List[Any]:
        """
        Validate retrieved and ranked evidence.

        Args:
            chunks        : The fully ranked evidence list.
            query_context : QueryContext for context-aware validation.

        Returns:
            List of RetrievalWarning objects (empty list = all checks passed).

        Raises:
            RetrievalValidationException : If a critical validation check fails
                                          (e.g., zero valid chunks after ranking).
        """
        ...


# ===========================================================================
# IRetrievalAgent
# ===========================================================================

class IRetrievalAgent(ABC):
    """
    Top-level interface for the Retrieval Agent.

    Mirrors IQueryAgent from Part 1. The Orchestrator holds a reference to
    IRetrievalAgent and calls retrieve() without knowing the concrete class.

    Implementations must:
        1. Validate the QueryContext (non-None, is_query_understood()).
        2. Select a retrieval strategy.
        3. Call IPhase1Retriever to get chunks.
        4. Merge, deduplicate, rank, and validate.
        5. Return a RetrievalResult.

    Security:
        Never accept raw query strings — only validated QueryContext objects.
    """

    @abstractmethod
    def retrieve(self, query_context: QueryContext) -> RetrievalResult:
        """
        Execute the full retrieval pipeline for a validated query.

        Args:
            query_context : Validated QueryContext from the Query Understanding Agent.
                            Must have is_query_understood() == True.

        Returns:
            RetrievalResult containing ranked evidence, metrics, and warnings.

        Raises:
            RetrievalException          : Generic retrieval failure.
            IndexUnavailableException   : Phase 1 indexes not accessible.
            RetrievalTimeoutException   : Retrieval exceeded timeout.
            QueryValidationException    : QueryContext is invalid or null.
        """
        ...

    @abstractmethod
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Return agent metadata for health checks and diagnostics.

        Returns:
            Dict with: name, version, status, phase1_available, capabilities.
        """
        ...
