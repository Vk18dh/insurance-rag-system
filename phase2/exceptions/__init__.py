"""
phase2.exceptions — Public exception exports.

Part 1: Full exception hierarchy + RecoveryStrategy + handlers.
Part 2: Retrieval-specific exceptions (RetrievalException, etc.).
"""

# Part 1 exceptions (unchanged)
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

# Part 2 exceptions (new)
from phase2.exceptions.retrieval_exception import (
    IndexUnavailableException,
    RankingException,
    RetrievalConfigurationException,
    RetrievalException,
    RetrievalTimeoutException,
    RetrievalValidationException,
)

__all__ = [
    # Part 1 hierarchy
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
    # Part 1 handlers
    "ErrorResponse",
    "RecoveryStrategy",
    "build_error_response",
    "is_retryable",
    "retry_on_transient",
    "safe_agent_call",
    "GlobalExceptionHandler",
    # Part 2 retrieval exceptions
    "RetrievalException",
    "IndexUnavailableException",
    "RetrievalValidationException",
    "RetrievalTimeoutException",
    "RankingException",
    "RetrievalConfigurationException",
    # Part 3 verification exceptions
    "VerificationException",
    "InvalidEvidenceException",
    "MetadataException",
    "CitationException",
    "VerificationConfigurationException",
    "VerificationTimeoutException",
]

from phase2.exceptions.verification_exception import (
    VerificationException,
    InvalidEvidenceException,
    MetadataException,
    CitationException,
    VerificationConfigurationException,
    VerificationTimeoutException,
)
