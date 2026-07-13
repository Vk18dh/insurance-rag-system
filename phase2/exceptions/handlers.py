"""
phase2.exceptions.handlers
============================

Graceful exception handling utilities for Phase 2 agents.

Provides:
    - retry_on_transient()  — Decorator for retrying transient failures
                              with configurable back-off (from settings).
    - safe_agent_call()     — Context manager that catches all exceptions,
                              logs them, and returns a structured error instead
                              of crashing the pipeline.
    - ErrorResponse         — Typed structured error safe for API serialisation.
    - build_error_response()— Converts any Phase2 or unexpected exception into
                              an ErrorResponse without exposing internals.
    - GlobalExceptionHandler— Centralised handler that classifies exceptions
                              and decides whether to retry, surface, or recover.

All retry/timeout values come from settings (injected) — never hardcoded.

Design:
    Retry policy:  ONLY transient failures (network, LLM timeout, DB hiccup).
    Never retry:   QueryValidationException, QuerySecurityException,
                   QueryConfigurationException (deterministic failures).
"""

from __future__ import annotations

import functools
import logging
import time
from contextlib import contextmanager
from enum import Enum
from typing import Any, Callable, Generator, Optional, Type, Tuple

from phase2.exceptions.query_exception import (
    Phase2BaseException,
    QueryConfigurationException,
    QueryProcessingException,
    QuerySecurityException,
    QueryTimeoutException,
    QueryValidationException,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# RecoveryStrategy — typed enum for pipeline recovery decisions
# ---------------------------------------------------------------------------
class RecoveryStrategy(str, Enum):
    """
    Typed recovery strategy returned by GlobalExceptionHandler.classify().

    Using a StrEnum (str + Enum) means callers can compare with plain strings
    for backwards compatibility while gaining type safety and IDE completion.

    Values:
        SURFACE : Return safe error response to user immediately.
        RETRY   : The Orchestrator may retry the failed step.
        DEGRADE : Continue pipeline with degraded/partial output.
    """
    SURFACE = "surface"
    RETRY = "retry"
    DEGRADE = "degrade"


# ---------------------------------------------------------------------------
# Exceptions that should NEVER be retried — deterministic failures
# ---------------------------------------------------------------------------
_NON_RETRYABLE: Tuple[Type[Exception], ...] = (
    QueryValidationException,
    QuerySecurityException,
    QueryConfigurationException,
)


# ===========================================================================
# ErrorResponse — structured API-safe error model
# ===========================================================================

class ErrorResponse:
    """
    Serialisable, API-safe error representation.

    Never exposes: stack traces, internal paths, API keys, or raw exceptions.
    Always includes: error_code, user_message, query_id (for log correlation).

    Attributes:
        error_code    : Machine-readable code (e.g. 'QUERY_VALIDATION_ERROR').
        user_message  : Safe, user-facing message (no internals).
        query_id      : Optional query UUID for log correlation.
        retryable     : Whether the client may retry the request.
        details       : Optional structured details (safe for external display).
    """

    def __init__(
        self,
        error_code: str,
        user_message: str,
        query_id: Optional[str] = None,
        retryable: bool = False,
        details: Optional[dict] = None,
    ) -> None:
        self.error_code = error_code
        self.user_message = user_message
        self.query_id = query_id
        self.retryable = retryable
        self.details: dict = details or {}

    def to_dict(self) -> dict:
        """Serialise to a dict safe for JSON API response bodies."""
        return {
            "error_code": self.error_code,
            "message": self.user_message,
            "query_id": self.query_id,
            "retryable": self.retryable,
            "details": self.details,
        }

    def __repr__(self) -> str:
        return f"ErrorResponse(code={self.error_code}, retryable={self.retryable})"


# ===========================================================================
# build_error_response — converts any exception to ErrorResponse
# ===========================================================================

def build_error_response(
    exc: Exception,
    query_id: Optional[str] = None,
) -> ErrorResponse:
    """
    Convert any exception into a safe, structured ErrorResponse.

    Business rule: NEVER include raw exception messages, stack traces,
    internal paths, or configuration details in the response.

    Args:
        exc      : The caught exception.
        query_id : Optional query UUID for log correlation.

    Returns:
        ErrorResponse: Safe, structured error object.
    """
    if isinstance(exc, QuerySecurityException):
        return ErrorResponse(
            error_code=exc.error_code,
            user_message="Your request could not be processed for security reasons.",
            query_id=query_id,
            retryable=False,
        )

    if isinstance(exc, QueryValidationException):
        return ErrorResponse(
            error_code=exc.error_code,
            user_message="The query is invalid. Please check your input and try again.",
            query_id=query_id,
            retryable=False,
            details={"field": exc.context.get("field", "query")},
        )

    if isinstance(exc, QueryTimeoutException):
        return ErrorResponse(
            error_code=exc.error_code,
            user_message="The request timed out. Please try again shortly.",
            query_id=query_id,
            retryable=True,
        )

    if isinstance(exc, QueryConfigurationException):
        # Configuration errors must never expose config values to end users
        logger.critical(
            "Configuration error exposed at API boundary: %s", exc.error_code
        )
        return ErrorResponse(
            error_code="INTERNAL_ERROR",
            user_message="A system configuration error occurred. Please contact support.",
            query_id=query_id,
            retryable=False,
        )

    if isinstance(exc, QueryProcessingException):
        return ErrorResponse(
            error_code=exc.error_code,
            user_message="We could not process your query at this time. Please try again.",
            query_id=query_id,
            retryable=True,
        )

    if isinstance(exc, Phase2BaseException):
        return ErrorResponse(
            error_code=exc.error_code,
            user_message="An unexpected error occurred. Please try again.",
            query_id=query_id,
            retryable=False,
        )

    # Unknown exception — log with full info but return generic safe message
    logger.exception("Unknown exception type reached build_error_response: %s", type(exc).__name__)
    return ErrorResponse(
        error_code="UNKNOWN_ERROR",
        user_message="An unexpected error occurred. Please try again later.",
        query_id=query_id,
        retryable=False,
    )


def is_retryable(exc: Exception) -> bool:
    """
    Return True when an exception represents a transient failure worth retrying.

    Args:
        exc: The caught exception.

    Returns:
        bool: True if the operation should be retried.
    """
    return not isinstance(exc, _NON_RETRYABLE)


# ===========================================================================
# retry_on_transient — decorator for resilient external calls
# ===========================================================================

def retry_on_transient(
    max_retries: int,
    base_delay_seconds: float,
    max_delay_seconds: float,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """
    Decorator that retries a function on transient failures using exponential back-off.

    Non-retryable exceptions (QueryValidationException, QuerySecurityException,
    QueryConfigurationException) are always re-raised immediately without retry.

    Args:
        max_retries       : Maximum number of retry attempts (from settings).
        base_delay_seconds: Initial back-off delay in seconds (from settings).
        max_delay_seconds : Cap on back-off delay (from settings).
        exceptions        : Tuple of exception types that trigger a retry.
                            Defaults to (Exception,) — catch all.

    Returns:
        Callable: Decorated function with retry logic.

    Example::

        @retry_on_transient(max_retries=3, base_delay_seconds=1.0, max_delay_seconds=8.0)
        def call_llm(query: str) -> str:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Optional[Exception] = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except _NON_RETRYABLE as exc:
                    # Deterministic failures — never retry
                    raise
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_retries:
                        break
                    delay = min(base_delay_seconds * (2 ** (attempt - 1)), max_delay_seconds)
                    logger.warning(
                        "Transient failure in %s (attempt %d/%d) — retrying in %.1fs: %s",
                        func.__qualname__, attempt, max_retries, delay, exc,
                    )
                    time.sleep(delay)

            raise QueryProcessingException(
                f"{func.__qualname__} failed after {max_retries} attempts.",
                step=func.__qualname__,
                context={"last_error": str(last_exc)},
            ) from last_exc

        return wrapper
    return decorator


# ===========================================================================
# safe_agent_call — context manager for graceful pipeline recovery
# ===========================================================================

@contextmanager
def safe_agent_call(
    agent_name: str,
    query_id: Optional[str] = None,
    reraise: bool = True,
) -> Generator[None, None, None]:
    """
    Context manager that wraps an agent call with structured logging and
    optional recovery.

    Usage::

        with safe_agent_call("QueryUnderstandingAgent", query_id="abc"):
            context = agent.process(query)

    Args:
        agent_name: Human-readable name for log messages.
        query_id  : Optional query UUID for log correlation.
        reraise   : If True (default), re-raise Phase2BaseException after logging.
                    If False, swallow and allow pipeline to continue with degraded output.

    Yields:
        None.

    Raises:
        Phase2BaseException: Re-raised when reraise=True and an exception occurs.
    """
    try:
        yield
    except _NON_RETRYABLE as exc:
        logger.warning(
            "[%s] Non-retryable exception (query_id=%s): %s — %s",
            agent_name, query_id or "N/A", exc.error_code, exc.message,
        )
        raise  # Non-retryable errors must always propagate
    except Phase2BaseException as exc:
        logger.error(
            "[%s] Agent exception (query_id=%s): %s — %s",
            agent_name, query_id or "N/A", exc.error_code, exc.message,
        )
        if reraise:
            raise
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "[%s] Unhandled exception (query_id=%s): %s",
            agent_name, query_id or "N/A", type(exc).__name__,
        )
        if reraise:
            raise QueryProcessingException(
                "Unexpected failure in agent execution.",
                step=agent_name,
                context={"error_type": type(exc).__name__},
            ) from exc


# ===========================================================================
# GlobalExceptionHandler — Orchestrator-level classifier
# ===========================================================================

class GlobalExceptionHandler:
    """
    Centralised exception classifier used by the Orchestrator.

    Classifies every exception into one of three categories:
        - SURFACE  : Return safe error response to user immediately.
        - RETRY    : The Orchestrator may retry the failed step.
        - DEGRADE  : Continue pipeline with degraded/partial output.

    Args:
        max_retries: From settings — maximum retries the Orchestrator will attempt.
    """

    SURFACE = RecoveryStrategy.SURFACE.value
    RETRY = RecoveryStrategy.RETRY.value
    DEGRADE = RecoveryStrategy.DEGRADE.value

    def __init__(self, max_retries: int) -> None:
        if max_retries < 0:
            raise QueryConfigurationException(
                "max_retries must be >= 0",
                config_key="llm.max_retries",
            )
        self._max_retries = max_retries

    def classify(self, exc: Exception, attempt: int) -> RecoveryStrategy:
        """
        Classify an exception into a pipeline recovery strategy.

        Args:
            exc    : The caught exception.
            attempt: Current attempt number (1-indexed).

        Returns:
            RecoveryStrategy: Typed strategy — SURFACE, RETRY, or DEGRADE.
        """
        # Security and validation issues must surface immediately
        if isinstance(exc, (QuerySecurityException, QueryValidationException)):
            return RecoveryStrategy.SURFACE

        # Config errors are fatal — surface immediately
        if isinstance(exc, QueryConfigurationException):
            return RecoveryStrategy.SURFACE

        # Transient processing errors — retry if attempts remain
        if isinstance(exc, (QueryProcessingException, QueryTimeoutException)):
            if attempt <= self._max_retries:
                return RecoveryStrategy.RETRY
            return RecoveryStrategy.SURFACE

        # Any other Phase2 exception after exhausting retries
        if isinstance(exc, Phase2BaseException):
            return RecoveryStrategy.DEGRADE if attempt > self._max_retries else RecoveryStrategy.RETRY

        # Unknown exceptions — surface safely
        return RecoveryStrategy.SURFACE
