"""
phase2.exceptions.retrieval_exception
========================================

Custom exception hierarchy for the Retrieval Agent (Phase 2 Part 2).

Design:
    All retrieval exceptions extend Phase2BaseException from Part 1.
    This preserves the single-exception-hierarchy rule from Part 0 and means
    the Orchestrator can catch Phase2BaseException to handle all Phase 2 errors.

Hierarchy:
    Phase2BaseException (Part 1)
    └── RetrievalException                  — Base for all retrieval failures
        ├── IndexUnavailableException       — BM25 or ChromaDB not accessible
        ├── RetrievalValidationException    — Retrieval results failed validation
        ├── RetrievalTimeoutException       — Retrieval exceeded configured timeout
        ├── RankingException                — Ranking service failure
        └── RetrievalConfigurationException — Invalid retrieval configuration

Retry policy (aligned with Part 1 RecoveryStrategy):
    SURFACE  : RetrievalValidationException, RetrievalConfigurationException
    RETRY    : IndexUnavailableException (transient), RetrievalTimeoutException
    DEGRADE  : RankingException (ranking can be skipped, return unranked)
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from phase2.exceptions.query_exception import Phase2BaseException


class RetrievalException(Phase2BaseException):
    """
    Base exception for all Retrieval Agent failures.

    Extends Phase2BaseException so the Orchestrator's single
    except Phase2BaseException clause handles all Phase 2 errors.

    Args:
        message    : Human-readable description.
        error_code : Machine-readable code (default: RETRIEVAL_ERROR).
        context    : Optional structured context dict for diagnostics.
        query_id   : Query ID for correlation with QueryMetadata.
    """

    DEFAULT_ERROR_CODE = "RETRIEVAL_ERROR"
    DEFAULT_MESSAGE = "An error occurred during evidence retrieval."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        query_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code or self.DEFAULT_ERROR_CODE,
            context=context or {},
        )
        if query_id:
            self.context["query_id"] = query_id


class IndexUnavailableException(RetrievalException):
    """
    Raised when the Phase 1 BM25 index or ChromaDB vector index is inaccessible.

    Recovery:
        RETRY — This is a transient infrastructure failure.
        After max_retries exhausted → SURFACE.

    Args:
        index_type : 'bm25' | 'vector' | 'both'
        index_path : File or directory path that was unavailable.
    """

    DEFAULT_ERROR_CODE = "INDEX_UNAVAILABLE"
    DEFAULT_MESSAGE = "Phase 1 retrieval index is unavailable."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        index_type: str = "unknown",
        index_path: Optional[str] = None,
        query_id: Optional[str] = None,
    ) -> None:
        context: Dict[str, Any] = {"index_type": index_type}
        # Never expose actual file system paths in the message — only in context
        # so they don't leak to user-facing error responses.
        if index_path:
            context["index_path_available"] = False  # Don't log the actual path
        super().__init__(
            message=message,
            error_code=self.DEFAULT_ERROR_CODE,
            context=context,
            query_id=query_id,
        )


class RetrievalValidationException(RetrievalException):
    """
    Raised when retrieved evidence fails quality validation.

    Examples:
        - No chunks met the minimum similarity threshold
        - All chunks have incomplete metadata
        - Retrieved count is below minimum required

    Recovery:
        SURFACE — Validation failures are deterministic; retry won't help.

    Args:
        validation_check : Name of the validation check that failed.
        actual_value     : The actual value that failed the check.
        threshold        : The configured threshold that was not met.
    """

    DEFAULT_ERROR_CODE = "RETRIEVAL_VALIDATION_FAILED"
    DEFAULT_MESSAGE = "Retrieved evidence failed quality validation."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        validation_check: str = "unknown",
        actual_value: Any = None,
        threshold: Any = None,
        query_id: Optional[str] = None,
    ) -> None:
        context: Dict[str, Any] = {
            "validation_check": validation_check,
            "actual_value": actual_value,
            "threshold": threshold,
        }
        super().__init__(
            message=message,
            error_code=self.DEFAULT_ERROR_CODE,
            context=context,
            query_id=query_id,
        )


class RetrievalTimeoutException(RetrievalException):
    """
    Raised when Phase 1 retrieval or ranking exceeds the configured timeout.

    Recovery:
        RETRY — Transient. Retried up to max_retries from settings.

    Args:
        operation      : Name of the timed-out operation.
        elapsed_ms     : How long the operation took before timeout (ms).
        timeout_ms     : Configured timeout threshold (ms).
    """

    DEFAULT_ERROR_CODE = "RETRIEVAL_TIMEOUT"
    DEFAULT_MESSAGE = "Retrieval operation exceeded the configured timeout."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        operation: str = "retrieval",
        elapsed_ms: Optional[float] = None,
        timeout_ms: Optional[float] = None,
        query_id: Optional[str] = None,
    ) -> None:
        context: Dict[str, Any] = {
            "operation": operation,
            "elapsed_ms": elapsed_ms,
            "timeout_ms": timeout_ms,
        }
        super().__init__(
            message=message,
            error_code=self.DEFAULT_ERROR_CODE,
            context=context,
            query_id=query_id,
        )


class RankingException(RetrievalException):
    """
    Raised when the ranking service fails to rank retrieved chunks.

    Recovery:
        DEGRADE — Return unranked chunks rather than failing entirely.
                  The Orchestrator decides whether to proceed with unranked evidence.

    Args:
        ranking_step : Which ranking step failed (e.g. 'score_computation').
        chunk_count  : How many chunks were being ranked.
    """

    DEFAULT_ERROR_CODE = "RANKING_FAILED"
    DEFAULT_MESSAGE = "Ranking service failed to rank retrieved evidence."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        ranking_step: str = "unknown",
        chunk_count: int = 0,
        query_id: Optional[str] = None,
    ) -> None:
        context: Dict[str, Any] = {
            "ranking_step": ranking_step,
            "chunk_count": chunk_count,
        }
        super().__init__(
            message=message,
            error_code=self.DEFAULT_ERROR_CODE,
            context=context,
            query_id=query_id,
        )


class RetrievalConfigurationException(RetrievalException):
    """
    Raised when retrieval configuration is invalid or missing.

    Examples:
        - Strategy weights do not sum to a valid range
        - top_k is zero or negative
        - Required config key is missing

    Recovery:
        SURFACE — Configuration errors are deterministic; must be fixed.

    Args:
        config_key : The configuration key that is invalid or missing.
    """

    DEFAULT_ERROR_CODE = "RETRIEVAL_CONFIGURATION_ERROR"
    DEFAULT_MESSAGE = "Invalid or missing retrieval configuration."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        config_key: str = "unknown",
        query_id: Optional[str] = None,
    ) -> None:
        context: Dict[str, Any] = {"config_key": config_key}
        super().__init__(
            message=message,
            error_code=self.DEFAULT_ERROR_CODE,
            context=context,
            query_id=query_id,
        )
