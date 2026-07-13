"""
phase2.exceptions.query_exception
===================================

Custom exception hierarchy for the Query Understanding Agent.

All exceptions inherit from Phase2BaseException so callers can catch
the entire Phase 2 exception surface with one except clause while
still enabling precise sub-type handling.

Hierarchy:
    Phase2BaseException
    └── QueryException
        ├── QueryValidationException
        ├── QueryProcessingException
        │   ├── IntentDetectionException
        │   ├── EntityExtractionException
        │   ├── QueryClassificationException
        │   └── AmbiguityDetectionException
        ├── QueryTimeoutException
        ├── QueryConfigurationException
        └── QuerySecurityException
"""

from __future__ import annotations

from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------
class Phase2BaseException(Exception):
    """
    Root exception for all Phase 2 errors.

    Attributes:
        message    : Human-readable error description.
        error_code : Optional machine-readable error code for API responses.
        context    : Optional diagnostic key-value pairs.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "PHASE2_ERROR"
        self.context: Dict[str, Any] = context or {}

    def to_dict(self) -> Dict[str, Any]:
        """Serialise exception to a dict safe for API error responses."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.error_code}, msg={self.message!r})"


# ---------------------------------------------------------------------------
# Query root
# ---------------------------------------------------------------------------
class QueryException(Phase2BaseException):
    """Base exception for all Query Understanding Agent errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code or "QUERY_ERROR", context)


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------
class QueryValidationException(QueryException):
    """
    Raised when user input fails validation before processing begins.

    Scenarios: empty query, whitespace-only, oversized, invalid encoding,
    malicious Unicode, prompt injection attempt.
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        ctx = context or {}
        if field:
            ctx["field"] = field
        super().__init__(message, "QUERY_VALIDATION_ERROR", ctx)


# ---------------------------------------------------------------------------
# Processing errors
# ---------------------------------------------------------------------------
class QueryProcessingException(QueryException):
    """
    Raised when the NLP processing pipeline encounters an unexpected failure.

    Parent class for all step-specific processing exceptions.
    """

    def __init__(
        self,
        message: str,
        step: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        ctx = context or {}
        if step:
            ctx["step"] = step
        super().__init__(message, "QUERY_PROCESSING_ERROR", ctx)


class IntentDetectionException(QueryProcessingException):
    """Raised when intent detection fails or returns an unusable result."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, step="intent_detection", context=context)
        self.error_code = "INTENT_DETECTION_ERROR"


class EntityExtractionException(QueryProcessingException):
    """Raised when entity extraction fails."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, step="entity_extraction", context=context)
        self.error_code = "ENTITY_EXTRACTION_ERROR"


class QueryClassificationException(QueryProcessingException):
    """Raised when query structural classification fails."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, step="classification", context=context)
        self.error_code = "CLASSIFICATION_ERROR"


class AmbiguityDetectionException(QueryProcessingException):
    """Raised when ambiguity detection fails."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, step="ambiguity_detection", context=context)
        self.error_code = "AMBIGUITY_DETECTION_ERROR"


# ---------------------------------------------------------------------------
# Timeout
# ---------------------------------------------------------------------------
class QueryTimeoutException(QueryException):
    """
    Raised when query processing exceeds the configured timeout.

    Includes the operation name and elapsed time for diagnostics.
    """

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        elapsed_ms: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        ctx = context or {}
        if operation:
            ctx["operation"] = operation
        if elapsed_ms is not None:
            ctx["elapsed_ms"] = elapsed_ms
        super().__init__(message, "QUERY_TIMEOUT_ERROR", ctx)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
class QueryConfigurationException(QueryException):
    """
    Raised at startup when required configuration is missing or invalid.

    Triggers fast-fail behaviour — the application should not start with
    invalid configuration.
    """

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        ctx = context or {}
        if config_key:
            ctx["config_key"] = config_key
        super().__init__(message, "QUERY_CONFIG_ERROR", ctx)


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
class QuerySecurityException(QueryException):
    """
    Raised when a security violation is detected in user input.

    Examples: prompt injection attempt, oversized payload, malicious Unicode.
    Never expose internal details of the detection logic in the error message.
    """

    def __init__(
        self,
        message: str = "Request rejected for security reasons.",
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, "QUERY_SECURITY_ERROR", context)
