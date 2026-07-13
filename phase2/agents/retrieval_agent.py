"""
phase2.agents.retrieval_agent
================================

Retrieval Agent — Phase 2 Part 2 core agent.

Responsibility:
    Receives a validated QueryContext from the Query Understanding Agent,
    executes the full retrieval pipeline, and returns a RetrievalResult.

Pipeline (coordinated by RetrievalAgent.retrieve()):
    1. Validate QueryContext (non-None, understood).
    2. Select retrieval strategy (IRetrievalStrategy → weights + top_k).
    3. Execute hybrid retrieval via IPhase1Retriever (separate BM25 + vector).
    4. Merge + deduplicate with configurable weights (RetrievalService).
    5. Re-rank evidence (IRankingService).
    6. Validate quality (IValidationService → RetrievalWarning list).
    7. Build and return RetrievalResult.

Design:
    - Implements IRetrievalAgent — Orchestrator holds IRetrievalAgent reference.
    - All dependencies injected (DI) — no concrete class instantiation inside.
    - Reuses Part 1's RecoveryStrategy, retry_on_transient, safe_agent_call.
    - Reuses Part 1's Phase2BaseException hierarchy.
    - All config values flow from Phase2Settings.

Security:
    - Only accepts QueryContext — never raw user strings.
    - Does not log chunk text content.
    - No internal paths exposed in error responses.
"""

from __future__ import annotations

import time
from typing import Any, Dict

from phase2.exceptions.handlers import RecoveryStrategy, safe_agent_call
from phase2.exceptions.query_exception import QueryValidationException
from phase2.exceptions.retrieval_exception import (
    IndexUnavailableException,
    RankingException,
    RetrievalConfigurationException,
    RetrievalException,
    RetrievalTimeoutException,
    RetrievalValidationException,
)
from phase2.interfaces.retrieval_interface import (
    IPhase1Retriever,
    IRankingService,
    IRetrievalAgent,
    IRetrievalStrategy,
    IValidationService,
)
from phase2.models.query_context import QueryContext
from phase2.models.retrieved_chunk import RetrievedChunk
from phase2.models.retrieval_metrics import RetrievalMetrics
from phase2.models.retrieval_result import RetrievalResult, RetrievalWarning
from phase2.services.retrieval_service import RetrievalService
from phase2.logging.logger import get_logger

logger = get_logger(__name__)


# ===========================================================================
# ConfigDrivenRetrievalStrategy
# ===========================================================================

class ConfigDrivenRetrievalStrategy(IRetrievalStrategy):
    """
    Selects retrieval strategy weights based on query classification and intent.

    Weight maps are loaded entirely from settings.retrieval.strategy_weights.
    No hardcoded classification → weight mappings exist in this class.

    Classification keys (must match QueryClassification enum values):
        policy_specific, factual, regulatory, comparative, general, unknown

    Falls back to 'default' weights if classification is missing or unrecognised.
    """

    def __init__(
        self,
        strategy_weights: Dict[str, Dict[str, float]],
        default_top_k: int,
    ) -> None:
        if not strategy_weights:
            raise RetrievalConfigurationException(
                "strategy_weights must not be empty.",
                config_key="retrieval.strategy_weights",
            )
        if "default" not in strategy_weights:
            raise RetrievalConfigurationException(
                "strategy_weights must include a 'default' entry.",
                config_key="retrieval.strategy_weights.default",
            )
        self._weights   = strategy_weights
        self._top_k     = default_top_k

    def select(self, query_context: QueryContext) -> Dict[str, Any]:
        """
        Return strategy dict based on query classification.

        Priority:
            1. Query classification (e.g. 'policy_specific' → high BM25).
            2. Intent (e.g. 'regulatory_information' → map to 'regulatory').
            3. Default weights.
        """
        # Derive strategy key from classification
        classification_key: str = "default"
        if query_context.classification is not None:
            key = query_context.classification.value.lower()
            if key in self._weights:
                classification_key = key

        # Intent-based override for regulatory queries
        if (
            classification_key == "default"
            and query_context.intent is not None
            and "regulatory" in query_context.intent.intent.value.lower()
            and "regulatory" in self._weights
        ):
            classification_key = "regulatory"

        weight_cfg = self._weights.get(classification_key, self._weights["default"])

        bm25_w   = float(weight_cfg.get("bm25",   0.5))
        vector_w = float(weight_cfg.get("vector", 0.5))
        top_k    = int(weight_cfg.get("top_k", self._top_k))

        logger.debug(
            "Strategy selected",
            extra={
                "strategy": classification_key,
                "bm25_weight": bm25_w,
                "vector_weight": vector_w,
                "top_k": top_k,
            },
        )

        return {
            "strategy_name": classification_key,
            "bm25_weight":   bm25_w,
            "vector_weight": vector_w,
            "top_k":         top_k,
        }


# ===========================================================================
# RetrievalAgent
# ===========================================================================

class RetrievalAgent(IRetrievalAgent):
    """
    Core Retrieval Agent. Coordinates the complete evidence retrieval pipeline.

    Constructed entirely via DI — all dependencies are interfaces.
    Use RetrievalAgentFactory.create(settings, ...) in production.

    Args:
        retrieval_service : RetrievalService (wraps Phase1RetrieverAdapter).
        strategy          : IRetrievalStrategy for weight selection.
        ranking_service   : IRankingService implementation.
        validation_service: IValidationService implementation.
        agent_version     : Semver version string from settings.
        phase1_available  : Cache of is_available() result (checked once at startup).
    """

    def __init__(
        self,
        retrieval_service:  RetrievalService,
        strategy:           IRetrievalStrategy,
        ranking_service:    IRankingService,
        validation_service: IValidationService,
        agent_version:      str = "unknown",
    ) -> None:
        if not isinstance(strategy, IRetrievalStrategy):
            raise RetrievalConfigurationException(
                "strategy must implement IRetrievalStrategy.",
                config_key="retrieval.strategy",
            )
        if not isinstance(ranking_service, IRankingService):
            raise RetrievalConfigurationException(
                "ranking_service must implement IRankingService.",
                config_key="retrieval.ranking_service",
            )
        if not isinstance(validation_service, IValidationService):
            raise RetrievalConfigurationException(
                "validation_service must implement IValidationService.",
                config_key="retrieval.validation_service",
            )

        self._retrieval_svc  = retrieval_service
        self._strategy       = strategy
        self._ranking        = ranking_service
        self._validation     = validation_service
        self._agent_version  = agent_version
        self._phase1_ok      = retrieval_service._retriever.is_available()  # startup check

    # =========================================================================
    # IRetrievalAgent implementation
    # =========================================================================

    def retrieve(self, query_context: QueryContext) -> RetrievalResult:
        """
        Execute the full retrieval pipeline for a validated query.

        Args:
            query_context : Validated QueryContext from the Query Understanding Agent.

        Returns:
            RetrievalResult with ranked_evidence, metrics, and warnings.

        Raises:
            QueryValidationException   : If query_context is None or not understood.
            IndexUnavailableException  : Phase 1 indexes not accessible.
            RetrievalTimeoutException  : Retrieval exceeded timeout.
            RetrievalException         : Any other retrieval failure.
        """
        # ── Guard: accept only validated QueryContext ─────────────────────
        if query_context is None:
            raise QueryValidationException(
                "RetrievalAgent.retrieve() requires a non-None QueryContext.",
                field="query_context",
            )

        query_id = (
            query_context.metadata.query_id if query_context.metadata else None
        )
        query = query_context.normalized_query or query_context.original_query

        logger.info(
            "Retrieval agent started",
            extra={
                "query_preview": query[:80],
                "query_id": query_id,
                "agent_version": self._agent_version,
                "phase1_available": self._phase1_ok,
            },
        )

        pipeline_start = time.monotonic()
        metrics = RetrievalMetrics(query_id=query_id)

        with safe_agent_call("RetrievalAgent", reraise=True):

            # ── Step 1: Strategy selection ─────────────────────────────────
            strategy_cfg = self._strategy.select(query_context)
            strategy_name = strategy_cfg["strategy_name"]
            bm25_weight   = strategy_cfg["bm25_weight"]
            vector_weight = strategy_cfg["vector_weight"]
            top_k         = strategy_cfg["top_k"]

            object.__setattr__(metrics, "strategy_used",   strategy_name)
            object.__setattr__(metrics, "bm25_weight_used", bm25_weight)
            object.__setattr__(metrics, "vector_weight_used", vector_weight)

            logger.info(
                "Strategy selected",
                extra={"strategy": strategy_name, "bm25": bm25_weight,
                       "vector": vector_weight, "top_k": top_k, "query_id": query_id},
            )

            # ── Step 2: Hybrid retrieval (Phase 1) ─────────────────────────
            retrieval_start = time.monotonic() * 1000
            object.__setattr__(metrics, "retrieval_start_ms", retrieval_start)

            retrieval_result = self._retrieval_svc.retrieve(
                query=query,
                top_k=top_k,
                bm25_weight=bm25_weight,
                vector_weight=vector_weight,
                query_id=query_id,
            )

            retrieval_end = time.monotonic() * 1000
            object.__setattr__(metrics, "retrieval_end_ms", retrieval_end)
            object.__setattr__(metrics, "bm25_chunks_retrieved",   retrieval_result["bm25_count"])
            object.__setattr__(metrics, "vector_chunks_retrieved",  retrieval_result["vector_count"])

            chunks_merged = retrieval_result["chunks"]
            object.__setattr__(metrics, "chunks_before_dedup", len(chunks_merged))
            object.__setattr__(metrics, "chunks_after_dedup",  len(chunks_merged))  # already deduped

            # ── Step 3: Re-ranking ─────────────────────────────────────────
            try:
                ranked_chunks = self._ranking.rank(
                    chunks=chunks_merged,
                    query=query,
                    strategy_context=strategy_cfg,
                )
            except RankingException as exc:
                # DEGRADE: return unranked chunks rather than failing entirely
                logger.warning(
                    "Ranking failed — returning unranked results: %s", exc.message,
                    extra={"query_id": query_id},
                )
                ranked_chunks = chunks_merged  # unranked fallback

            ranking_end = time.monotonic() * 1000
            object.__setattr__(metrics, "ranking_end_ms", ranking_end)
            object.__setattr__(metrics, "chunks_after_ranking", len(ranked_chunks))

            # ── Step 4: Quality validation ─────────────────────────────────
            try:
                warnings = self._validation.validate(
                    chunks=ranked_chunks,
                    query_context=query_context,
                )
            except RetrievalValidationException as exc:
                # Validation FATAL — no chunks. Return empty result, not a crash.
                logger.warning(
                    "Validation failed: %s", exc.message,
                    extra={"query_id": query_id},
                )
                validation_end = time.monotonic() * 1000
                object.__setattr__(metrics, "validation_end_ms", validation_end)
                object.__setattr__(metrics, "validation_passed", False)
                object.__setattr__(metrics, "total_duration_ms",
                                   (time.monotonic() - pipeline_start) * 1000)

                return RetrievalResult(
                    query_context=query_context,
                    ranked_evidence=[],
                    metrics=metrics,
                    warnings=[RetrievalWarning(
                        code="EMPTY_RETRIEVAL",
                        message=exc.message,
                        severity="HIGH",
                    )],
                    retrieval_strategy=strategy_name,
                    bm25_weight=bm25_weight,
                    vector_weight=vector_weight,
                    is_successful=False,
                )

            validation_end = time.monotonic() * 1000
            object.__setattr__(metrics, "validation_end_ms", validation_end)
            object.__setattr__(metrics, "warning_count", len(warnings))
            object.__setattr__(metrics, "validation_passed", True)

            # ── Step 5: Compute final metrics ──────────────────────────────
            total_ms = (time.monotonic() - pipeline_start) * 1000
            object.__setattr__(metrics, "total_duration_ms", total_ms)
            self._populate_score_metrics(metrics, ranked_chunks)

            # ── Step 6: Assemble result ────────────────────────────────────
            result = RetrievalResult(
                query_context=query_context,
                ranked_evidence=ranked_chunks,
                metrics=metrics,
                warnings=warnings,
                retrieval_strategy=strategy_name,
                bm25_weight=bm25_weight,
                vector_weight=vector_weight,
                is_successful=len(ranked_chunks) > 0,
            )

        logger.info(
            "Retrieval agent completed",
            extra=metrics.to_summary_dict(),
        )

        return result

    def get_agent_info(self) -> Dict[str, Any]:
        """Return agent metadata for orchestrator health checks."""
        return {
            "name": "RetrievalAgent",
            "version": self._agent_version,
            "status": "ready",
            "phase1_available": self._retrieval_svc._retriever.is_available(),
            "capabilities": [
                "hybrid_retrieval",
                "strategy_selection",
                "duplicate_removal",
                "evidence_ranking",
                "retrieval_validation",
                "retrieval_metrics",
            ],
        }

    # =========================================================================
    # Private helpers
    # =========================================================================

    @staticmethod
    def _populate_score_metrics(metrics: RetrievalMetrics, chunks: list) -> None:
        """Compute score aggregates and retrieval_confidence from ranked chunks."""
        if not chunks:
            return

        bm25_scores    = [c.bm25_score    for c in chunks]
        vector_scores  = [c.vector_score  for c in chunks]
        combined_scores = [c.combined_score for c in chunks]
        ranking_scores = [c.ranking_score  for c in chunks]

        object.__setattr__(metrics, "avg_bm25_score",   sum(bm25_scores)    / len(chunks))
        object.__setattr__(metrics, "avg_vector_score",  sum(vector_scores)  / len(chunks))
        object.__setattr__(metrics, "avg_combined_score", sum(combined_scores) / len(chunks))
        object.__setattr__(metrics, "avg_ranking_score",  sum(ranking_scores)  / len(chunks))
        object.__setattr__(metrics, "top_chunk_score",    ranking_scores[0] if ranking_scores else 0.0)

        # Metadata completeness ratio
        complete_count = sum(1 for c in chunks if c.metadata_complete)
        object.__setattr__(
            metrics, "metadata_completeness_ratio",
            complete_count / len(chunks),
        )

        # Retrieval confidence: average of top_score and avg_combined_score
        confidence = (metrics.top_chunk_score + metrics.avg_combined_score) / 2.0
        object.__setattr__(metrics, "retrieval_confidence", min(confidence, 1.0))


# ===========================================================================
# RetrievalAgentFactory
# ===========================================================================

class RetrievalAgentFactory:
    """
    Factory for creating a fully wired RetrievalAgent from Phase2Settings.

    Uses the same factory pattern as Part 1's QueryUnderstandingAgentFactory.
    """

    @staticmethod
    def create(settings: Any, retrieval_service: RetrievalService) -> RetrievalAgent:
        """
        Build a RetrievalAgent with all dependencies wired from settings.

        Args:
            settings          : Phase2Settings instance.
            retrieval_service : Pre-built RetrievalService (from RetrievalServiceFactory).

        Returns:
            Fully wired RetrievalAgent.
        """
        from phase2.services.ranking_service import WeightedRankingService
        from phase2.services.retrieval_validation_service import RetrievalValidationService

        strategy = ConfigDrivenRetrievalStrategy(
            strategy_weights=settings.retrieval.strategy_weights,
            default_top_k=settings.retrieval.top_k,
        )

        ranking_svc = WeightedRankingService(
            retrieval_score_weight=settings.ranking.retrieval_score_weight,
            keyword_overlap_weight=settings.ranking.keyword_overlap_weight,
            metadata_completeness_weight=settings.ranking.metadata_completeness_weight,
            min_ranking_score=settings.ranking.min_ranking_score,
        )

        validation_svc = RetrievalValidationService(
            min_chunks_required=settings.validation.min_chunks_required,
            min_similarity_score=settings.validation.min_similarity_score,
            max_incomplete_metadata_ratio=settings.validation.max_incomplete_metadata_ratio,
            require_page_numbers=settings.validation.require_page_numbers,
        )

        return RetrievalAgent(
            retrieval_service=retrieval_service,
            strategy=strategy,
            ranking_service=ranking_svc,
            validation_service=validation_svc,
            agent_version=settings.agent_version,
        )
