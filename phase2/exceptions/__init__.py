"""
phase2.exceptions — Public API exports.

    from phase2.exceptions import (
        Phase2BaseException, QueryValidationException, ...
        ErrorResponse, build_error_response, retry_on_transient,
        safe_agent_call, GlobalExceptionHandler, is_retryable,
    )
"""

from phase2.exceptions.query_exception import (
    AmbiguityDetectionException,
    EntityExtractionException,
    IntentDetectionException,
    Phase2BaseException,
    QueryClassificationException,
    QueryConfigurationException,
    QueryException,
    QueryProcessingException,
    QuerySecurityException,
    QueryTimeoutException,
    QueryValidationException,
)
from phase2.exceptions.handlers import (
    ErrorResponse,
    GlobalExceptionHandler,
    RecoveryStrategy,
    build_error_response,
    is_retryable,
    retry_on_transient,
    safe_agent_call,
)

__all__ = [
    # Hierarchy
    "Phase2BaseException",
    "QueryException",
    "QueryValidationException",
    "QueryProcessingException",
    "IntentDetectionException",
    "EntityExtractionException",
    "QueryClassificationException",
    "AmbiguityDetectionException",
    "QueryTimeoutException",
    "QueryConfigurationException",
    "QuerySecurityException",
    # Handlers
    "ErrorResponse",
    "RecoveryStrategy",
    "build_error_response",
    "is_retryable",
    "retry_on_transient",
    "safe_agent_call",
    "GlobalExceptionHandler",
]
