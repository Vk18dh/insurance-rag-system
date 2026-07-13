"""
phase2.agents.query_agent
===========================

Concrete implementation of IQueryAgent — the Query Understanding Agent.

This is the primary entry-point called by the Phase 2 Orchestrator for every
user query. It wraps QueryProcessingService (Stage 4) with:
    - Agent-level validation
    - Structured logging (start, end, timing, decisions)
    - Graceful error handling and recovery
    - Agent metadata/health reporting (for Orchestrator diagnostics)
    - Context-level error accumulation (non-fatal errors stored in QueryContext)

Design:
    QueryUnderstandingAgent receives ONE dependency — QueryProcessingService —
    through its constructor. It never creates or imports concrete LLM clients.
    All LLM/NLP strategy wiring happens in the factory/config layer (Stage 6).

Orchestrator integration contract:
    orchestrator.process(query)
        └─▶ QueryUnderstandingAgent.process(query) → QueryContext
                └─▶ QueryProcessingService.process(query) → QueryContext

The Orchestrator always calls IQueryAgent.process() — never the concrete class.

Part 2 integration:
    The returned QueryContext.to_retrieval_input() provides the exact dict
    that the Retrieval Agent (Part 2) will consume.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict

from phase2.exceptions.query_exception import (
    Phase2BaseException,
    QueryConfigurationException,
    QueryProcessingException,
    QuerySecurityException,
    QueryValidationException,
)
from phase2.interfaces.query_agent_interface import IQueryAgent, IQueryProcessingService
from phase2.models.query_context import QueryContext
from phase2.services.query_processing_service import QueryProcessingService

logger = logging.getLogger(__name__)


class QueryUnderstandingAgent(IQueryAgent):
    """
    Concrete Query Understanding Agent.

    Responsibilities:
        1. Accept a raw user query from the Orchestrator.
        2. Delegate to QueryProcessingService for the full NLP pipeline.
        3. Handle and log all exceptions without crashing the pipeline.
        4. Return a fully populated QueryContext or raise structured exceptions.

    This class contains NO business logic — it is a thin orchestration wrapper
    around QueryProcessingService that adds agent-level concerns:
        - timing
        - structured logging
        - top-level exception management
        - agent metadata reporting

    Args:
        service        : Injected QueryProcessingService instance.
        agent_name     : Human-readable name for logging (from settings).
        agent_version  : Semver version string (from settings).
        log_query_preview_length: Max chars of query to log (privacy guard, from settings).
    """

    def __init__(
        self,
        service: IQueryProcessingService,
        agent_name: str,
        agent_version: str,
        log_query_preview_length: int,
    ) -> None:
        if not isinstance(service, IQueryProcessingService):
            raise QueryConfigurationException(
                "QueryUnderstandingAgent requires an IQueryProcessingService instance.",
                config_key="query_agent.service",
            )
        if log_query_preview_length <= 0:
            raise QueryConfigurationException(
                "log_query_preview_length must be positive.",
                config_key="query_agent.log_query_preview_length",
            )

        self._service = service
        self._agent_name = agent_name
        self._agent_version = agent_version
        self._log_preview_len = log_query_preview_length

        logger.info(
            "QueryUnderstandingAgent initialised (name=%s, version=%s)",
            agent_name,
            agent_version,
        )

    # =========================================================================
    # IQueryAgent implementation
    # =========================================================================

    def process(self, raw_query: str) -> QueryContext:
        """
        Process a raw user query through the full Query Understanding pipeline.

        Called exclusively by the Orchestrator. Never called by other agents.

        Pipeline stages (delegated to QueryProcessingService):
            1. Security check
            2. Input validation
            3. Normalisation
            4. Intent detection
            5. Entity extraction
            6. Query classification
            7. Ambiguity detection
            8. Metadata stamping

        Args:
            raw_query: Exact, unmodified string received from the user interface.

        Returns:
            QueryContext: Fully populated context ready for the Retrieval Agent.
                          Contains all intent, entity, classification, and ambiguity
                          information that Part 2 will consume via to_retrieval_input().

        Raises:
            QueryValidationException : Input failed validation (caller should surface to user).
            QuerySecurityException   : Security violation detected (caller must NOT retry).
            QueryProcessingException : NLP pipeline failure after all retries.
        """
        start_ns = time.perf_counter_ns()
        preview = self._safe_preview(raw_query)

        logger.info(
            "[%s] Query received | preview=%r | length=%s",
            self._agent_name,
            preview,
            len(raw_query) if isinstance(raw_query, str) else "N/A",
        )

        try:
            context = self._service.process(raw_query)

            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            logger.info(
                "[%s] Processing complete | query_id=%s | intent=%s | "
                "confidence=%.2f | entities=%d | classification=%s | "
                "ambiguous=%s | elapsed=%.1f ms",
                self._agent_name,
                context.metadata.query_id if context.metadata else "N/A",
                context.intent.intent.value if context.intent else "None",
                context.intent.confidence if context.intent else 0.0,
                len(context.entities.all_entities_flat()) if context.entities else 0,
                context.classification.value if context.classification else "None",
                context.ambiguity.is_ambiguous if context.ambiguity else False,
                elapsed_ms,
            )
            return context

        except QuerySecurityException as exc:
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            logger.warning(
                "[%s] Security violation rejected | code=%s | elapsed=%.1f ms",
                self._agent_name, exc.error_code, elapsed_ms,
            )
            raise  # Must NOT be swallowed — caller surfaces to user

        except QueryValidationException as exc:
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            logger.warning(
                "[%s] Validation failure | code=%s | msg=%s | elapsed=%.1f ms",
                self._agent_name, exc.error_code, exc.message, elapsed_ms,
            )
            raise  # Must NOT be swallowed — user needs to correct input

        except QueryProcessingException as exc:
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            logger.error(
                "[%s] Processing failure | code=%s | step=%s | msg=%s | elapsed=%.1f ms",
                self._agent_name,
                exc.error_code,
                exc.context.get("step", "unknown"),
                exc.message,
                elapsed_ms,
            )
            raise

        except Phase2BaseException as exc:
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            logger.error(
                "[%s] Unexpected Phase2 exception | code=%s | msg=%s | elapsed=%.1f ms",
                self._agent_name, exc.error_code, exc.message, elapsed_ms,
            )
            raise QueryProcessingException(
                f"Query understanding failed unexpectedly: {exc.message}",
                step="query_agent",
                context={"original_code": exc.error_code},
            ) from exc

        except Exception as exc:  # noqa: BLE001 — catch-all at agent boundary
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            logger.exception(
                "[%s] Unhandled exception | type=%s | elapsed=%.1f ms",
                self._agent_name, type(exc).__name__, elapsed_ms,
            )
            raise QueryProcessingException(
                "Query understanding encountered an unexpected error. "
                "Please try again or contact support.",
                step="query_agent",
                context={"error_type": type(exc).__name__},
            ) from exc

    def validate(self, raw_query: str) -> bool:
        """
        Validate input without running the full pipeline.

        Used by the API layer for early rejection (before consuming LLM quota).

        Args:
            raw_query: Raw user input string.

        Returns:
            bool: True when the query passes all validation checks.

        Raises:
            QueryValidationException: On invalid input with structured error detail.
            QuerySecurityException  : On security violation.
        """
        logger.debug(
            "[%s] Validate-only call | preview=%r",
            self._agent_name, self._safe_preview(raw_query),
        )
        return self._service.validate_only(raw_query)

    def get_agent_info(self) -> Dict[str, Any]:
        """
        Return structured metadata about this agent for Orchestrator diagnostics.

        Used for health checks, logging, and introspection.

        Returns:
            Dict with: name, version, capabilities, status.
        """
        return {
            "name": self._agent_name,
            "version": self._agent_version,
            "type": "QueryUnderstandingAgent",
            "capabilities": [
                "input_validation",
                "text_normalisation",
                "intent_detection",
                "entity_extraction",
                "query_classification",
                "ambiguity_detection",
                "metadata_generation",
            ],
            "status": "ready",
            "integration": {
                "input": "raw_query (str)",
                "output": "QueryContext",
                "retrieval_contract": "QueryContext.to_retrieval_input()",
            },
        }

    # =========================================================================
    # Private helpers
    # =========================================================================

    def _safe_preview(self, raw_query: Any) -> str:
        """
        Return a safely truncated, non-null preview string for logging.

        Never logs the full query — protects user privacy.

        Args:
            raw_query: The raw input (may be any type if misused by caller).

        Returns:
            str: Truncated string preview for log output.
        """
        if not isinstance(raw_query, str):
            return f"<non-string: {type(raw_query).__name__}>"
        if not raw_query:
            return "<empty>"
        return raw_query[: self._log_preview_len].replace("\n", " ")


# ===========================================================================
# Agent Factory
# ===========================================================================
class QueryUnderstandingAgentFactory:
    """
    Factory that assembles a production-ready QueryUnderstandingAgent from
    injected settings and a ready QueryProcessingService.

    Usage (called from Orchestrator or main application init):

        settings = load_settings()
        service  = QueryProcessingServiceFactory.create(settings)
        agent    = QueryUnderstandingAgentFactory.create(settings, service)
        context  = agent.process(user_query)

    Args:
        settings: Settings object from phase2.config.settings (Stage 6).
        service : Already-constructed QueryProcessingService instance.
    """

    @staticmethod
    def create(
        settings: Any,
        service: IQueryProcessingService,
    ) -> QueryUnderstandingAgent:
        """
        Build a QueryUnderstandingAgent with values from settings.

        Args:
            settings : Configuration settings (phase2.config.settings).
            service  : Wired QueryProcessingService.

        Returns:
            QueryUnderstandingAgent: Ready to process queries.
        """
        return QueryUnderstandingAgent(
            service=service,
            agent_name=settings.query_agent.agent_name,
            agent_version=settings.agent_version,
            log_query_preview_length=settings.query_agent.log_query_preview_length,
        )
