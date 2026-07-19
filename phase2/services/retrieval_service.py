"""
phase2.services.retrieval_service
====================================

Phase 1 retrieval adapter and main retrieval service.

Components:
    Phase1RetrieverAdapter : IPhase1Retriever implementation.
        Wraps Phase 1's bm25_search() and vector_search() module functions.
        Converts raw Phase 1 dicts → typed RetrievedChunk objects.
        NEVER calls hybrid_search() — custom weight merging is done by
        RetrievalService so per-query strategy weights can be applied.

    RetrievalService : Orchestrates the full retrieval pipeline step.
        1. Calls Phase1RetrieverAdapter for BM25 + vector results (separate calls).
        2. Normalises scores (min-max, matching Phase 1's _normalise_scores logic).
        3. Merges results with configurable per-strategy weights.
        4. Deduplicates by chunk_id, keeping the higher combined score.
        5. Returns a flat, deduped List[RetrievedChunk] for the ranking stage.

    RetrievalServiceFactory : Creates a wired RetrievalService from settings.

Zero Phase 1 modification:
    Phase 1 is unchanged. The adapter wraps module-level functions via import.
    If Phase 1 is unavailable, IndexUnavailableException is raised.

Thread safety:
    Phase1RetrieverAdapter is stateless — safe for concurrent use.
    SentenceTransformer is loaded once per Phase 1 process, not here.
"""

from __future__ import annotations

import os
import time
import logging
from typing import Any, Dict, List, Optional

from phase2.exceptions.retrieval_exception import (
    IndexUnavailableException,
    RetrievalConfigurationException,
    RetrievalTimeoutException,
)
from phase2.interfaces.retrieval_interface import IPhase1Retriever
from phase2.models.retrieved_chunk import RetrievedChunk, RetrievalSource
from phase2.logging.logger import get_logger

logger = get_logger(__name__)


# ===========================================================================
# Phase1RetrieverAdapter
# ===========================================================================

class Phase1RetrieverAdapter(IPhase1Retriever):
    """
    Adapter that wraps Phase 1's module-level search functions.

    Responsibility:
        - Import Phase 1's bm25_search and vector_search at runtime.
        - Convert raw dict results to typed RetrievedChunk objects.
        - Check index availability via is_available().
        - Raise IndexUnavailableException on failure (never return None).

    Why not call hybrid_search()?
        Phase 1's hybrid_search() uses the global BM25_WEIGHT and VECTOR_WEIGHT
        constants from config.py. The Retrieval Agent needs per-query configurable
        weights (policy_specific vs regulatory vs general). So we call bm25_search
        and vector_search separately, then merge with WeightedMergeService.

    Args:
        bm25_index_path      : Path to BM25 pickle file (from Phase2Settings.phase1).
        chroma_dir           : Path to ChromaDB directory (from Phase2Settings.phase1).
        chroma_collection    : ChromaDB collection name.
        timeout_seconds      : Per-call timeout in seconds.
    """

    def __init__(
        self,
        bm25_index_path: str,
        chroma_dir: str,
        chroma_collection: str,
        timeout_seconds: float = 10.0,
    ) -> None:
        if not bm25_index_path or not bm25_index_path.strip():
            raise RetrievalConfigurationException(
                "bm25_index_path must not be empty.",
                config_key="phase1.bm25_index_path",
            )
        if not chroma_dir or not chroma_dir.strip():
            raise RetrievalConfigurationException(
                "chroma_dir must not be empty.",
                config_key="phase1.chroma_dir",
            )
        if timeout_seconds <= 0:
            raise RetrievalConfigurationException(
                "timeout_seconds must be > 0.",
                config_key="retrieval.timeout_seconds",
            )

        self._bm25_index_path  = bm25_index_path
        self._chroma_dir       = chroma_dir
        self._chroma_collection = chroma_collection
        self._timeout_seconds  = timeout_seconds

    # ──────────────────────────────────────────────────────────────────────
    # IPhase1Retriever implementation
    # ──────────────────────────────────────────────────────────────────────

    def bm25_search(self, query: str, top_k: int) -> List[RetrievedChunk]:
        """
        Execute Phase 1 BM25 search and return typed RetrievedChunk objects.

        Internally calls app.bm25_search(query, top_k) and converts results.

        Raises:
            IndexUnavailableException : BM25 pickle not found.
        """
        if not os.path.isfile(self._bm25_index_path):
            raise IndexUnavailableException(
                "BM25 index file not found. Run index.py to build the index.",
                index_type="bm25",
            )

        try:
            from app import bm25_search as _phase1_bm25
            start = time.monotonic()
            raw_results: List[Dict[str, Any]] = _phase1_bm25(query, top_k=top_k)
            elapsed = (time.monotonic() - start) * 1000
            logger.debug(
                "Phase 1 BM25 search completed",
                extra={"top_k": top_k, "results": len(raw_results), "elapsed_ms": round(elapsed, 1)},
            )
            return [self._dict_to_chunk(r, RetrievalSource.BM25, bm25_score=r.get("score", 0.0))
                    for r in raw_results]

        except IndexUnavailableException:
            raise
        except Exception as exc:
            logger.warning("Phase 1 BM25 search failed: %s", exc)
            raise IndexUnavailableException(
                f"BM25 retrieval failed: {type(exc).__name__}",
                index_type="bm25",
            ) from exc

    def vector_search(self, query: str, top_k: int) -> List[RetrievedChunk]:
        """
        Execute Phase 1 vector search and return typed RetrievedChunk objects.

        Internally calls app.vector_search(query, top_k) and converts results.

        Raises:
            IndexUnavailableException : ChromaDB directory not found.
        """
        if not os.path.isdir(self._chroma_dir):
            raise IndexUnavailableException(
                "ChromaDB directory not found. Run index.py to build the index.",
                index_type="vector",
            )

        try:
            from app import vector_search as _phase1_vector
            start = time.monotonic()
            raw_results: List[Dict[str, Any]] = _phase1_vector(query, top_k=top_k)
            elapsed = (time.monotonic() - start) * 1000
            logger.debug(
                "Phase 1 vector search completed",
                extra={"top_k": top_k, "results": len(raw_results), "elapsed_ms": round(elapsed, 1)},
            )
            return [self._dict_to_chunk(r, RetrievalSource.VECTOR, vector_score=r.get("score", 0.0))
                    for r in raw_results]

        except IndexUnavailableException:
            raise
        except Exception as exc:
            logger.warning("Phase 1 vector search failed: %s", exc)
            raise IndexUnavailableException(
                f"Vector retrieval failed: {type(exc).__name__}",
                index_type="vector",
            ) from exc

    def is_available(self) -> bool:
        """Check whether both Phase 1 indexes are accessible (no I/O)."""
        return (
            os.path.isfile(self._bm25_index_path)
            and os.path.isdir(self._chroma_dir)
        )

    # ──────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _dict_to_chunk(
        raw: Dict[str, Any],
        source: RetrievalSource,
        *,
        bm25_score: float = 0.0,
        vector_score: float = 0.0,
    ) -> RetrievedChunk:
        """
        Convert a Phase 1 raw dict to a typed RetrievedChunk.

        Phase 1 dict schema (from app.py):
            chunk_id, text, score, source_document, page_number, section_title

        The raw dict is stored in raw_metadata for auditability.
        """
        page_ref = str(raw.get("page_number", "N/A")) if raw.get("page_number") is not None else "N/A"
        source_doc = raw.get("source_document", "unknown") or "unknown"
        section = raw.get("section_title", "Unknown") or "Unknown"

        metadata_complete = (
            source_doc.lower() not in ("unknown", "")
            and page_ref.lower() not in ("n/a", "none", "")
        )

        return RetrievedChunk(
            chunk_id=raw.get("chunk_id", ""),
            text=raw.get("text", ""),
            source_document=source_doc,
            page_number=page_ref,
            section_title=section,
            bm25_score=bm25_score if source == RetrievalSource.BM25 else 0.0,
            vector_score=vector_score if source == RetrievalSource.VECTOR else 0.0,
            combined_score=raw.get("score", 0.0),
            retrieval_source=source,
            metadata_complete=metadata_complete,
            raw_metadata=raw,
        )


# ===========================================================================
# RetrievalService
# ===========================================================================

class RetrievalService:
    """
    Orchestrates Phase 1 retrieval with configurable per-strategy weights.

    Pipeline:
        1. Calls IPhase1Retriever.bm25_search() + vector_search() separately.
        2. Normalises scores independently (min-max within each result set).
        3. Merges both result sets with the given bm25_weight and vector_weight.
        4. Deduplicates by chunk_id — keeps highest combined_score and merges
           bm25/vector scores so the ranking service has full signal.
        5. Returns sorted List[RetrievedChunk].

    Why separate BM25/vector calls?
        Phase 1's hybrid_search() uses fixed global weights.
        The strategy selector provides per-query weights (e.g. 0.7/0.3 for
        policy-specific queries, 0.3/0.7 for conceptual queries).

    Args:
        phase1_retriever : IPhase1Retriever implementation.
        timeout_seconds  : Hard timeout for combined retrieval operations.
    """

    def __init__(
        self,
        phase1_retriever: IPhase1Retriever,
        timeout_seconds: float = 10.0,
    ) -> None:
        if not isinstance(phase1_retriever, IPhase1Retriever):
            raise RetrievalConfigurationException(
                "phase1_retriever must implement IPhase1Retriever.",
                config_key="retrieval.phase1_retriever",
            )
        self._retriever = phase1_retriever
        self._timeout   = timeout_seconds

    def retrieve(
        self,
        query: str,
        top_k: int,
        bm25_weight: float,
        vector_weight: float,
        query_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute dual-search retrieval with configurable weights.

        Args:
            query         : Normalised query string.
            top_k         : Final number of chunks to return.
            bm25_weight   : Weight for BM25 scores.
            vector_weight : Weight for vector scores.
            query_id      : Optional correlation ID for logging.

        Returns:
            Dict with keys:
                chunks         : List[RetrievedChunk] — merged, sorted, deduped
                bm25_count     : int — chunks from BM25
                vector_count   : int — chunks from vector
                elapsed_ms     : float — total retrieval time (ms)

        Raises:
            IndexUnavailableException  : Phase 1 index not found.
            RetrievalTimeoutException  : Exceeded timeout_seconds.
        """
        start = time.monotonic()

        logger.info(
            "Retrieval started",
            extra={
                "query_preview": query[:80],
                "top_k": top_k,
                "bm25_weight": bm25_weight,
                "vector_weight": vector_weight,
                "query_id": query_id,
            },
        )

        # Retrieve from both backends (2x top_k for merge headroom)
        fetch_k = top_k * 2

        # ── BM25 ─────────────────────────────────────────────────────────
        try:
            bm25_chunks = self._retriever.bm25_search(query, top_k=fetch_k)
        except IndexUnavailableException:
            logger.warning("BM25 index unavailable — falling back to vector-only retrieval.")
            bm25_chunks = []

        # ── Vector ───────────────────────────────────────────────────────
        try:
            vector_chunks = self._retriever.vector_search(query, top_k=fetch_k)
        except IndexUnavailableException:
            logger.warning("Vector index unavailable — falling back to BM25-only retrieval.")
            vector_chunks = []

        # Both unavailable
        if not bm25_chunks and not vector_chunks:
            raise IndexUnavailableException(
                "Both BM25 and vector indexes are unavailable.",
                index_type="both",
                query_id=query_id,
            )

        elapsed_ms = (time.monotonic() - start) * 1000
        if elapsed_ms > self._timeout * 1000:
            raise RetrievalTimeoutException(
                f"Retrieval exceeded timeout ({self._timeout}s).",
                operation="hybrid_retrieval",
                elapsed_ms=elapsed_ms,
                timeout_ms=self._timeout * 1000,
                query_id=query_id,
            )

        # ── Normalise scores (per-backend min-max) ────────────────────────
        bm25_chunks   = self._normalise_bm25_scores(bm25_chunks)
        vector_chunks = self._normalise_vector_scores(vector_chunks)

        # ── Merge and deduplicate ─────────────────────────────────────────
        merged = self._merge(bm25_chunks, vector_chunks, bm25_weight, vector_weight)
        merged_sorted = sorted(merged, key=lambda c: c.combined_score, reverse=True)[:top_k]

        logger.info(
            "Retrieval completed",
            extra={
                "bm25_count": len(bm25_chunks),
                "vector_count": len(vector_chunks),
                "merged_count": len(merged_sorted),
                "elapsed_ms": round(elapsed_ms, 1),
                "query_id": query_id,
            },
        )

        return {
            "chunks": merged_sorted,
            "bm25_count": len(bm25_chunks),
            "vector_count": len(vector_chunks),
            "elapsed_ms": elapsed_ms,
        }

    # ──────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _normalise_bm25_scores(chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        """Min-max normalise bm25_score to [0, 1]."""
        if not chunks:
            return chunks
        scores = [c.bm25_score for c in chunks]
        min_s, max_s = min(scores), max(scores)
        spread = max_s - min_s if max_s != min_s else 1.0
        for c in chunks:
            # Mutate via model_copy for Pydantic v2 immutability
            object.__setattr__(c, "bm25_score", (c.bm25_score - min_s) / spread)
        return chunks

    @staticmethod
    def _normalise_vector_scores(chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        """
        Vector scores from ChromaDB are cosine distances (lower is better, 0.0 = perfect match).
        We must invert them to similarities [0, 1] so higher is better during the hybrid merge.
        """
        if not chunks:
            return chunks
        scores = [c.vector_score for c in chunks]
        min_s, max_s = min(scores), max(scores)
        spread = max_s - min_s if max_s != min_s else 1.0
        
        for c in chunks:
            # 1.0 is the best (formerly min_s distance), 0.0 is the worst (formerly max_s distance)
            object.__setattr__(c, "vector_score", 1.0 - ((c.vector_score - min_s) / spread))
        return chunks

    @staticmethod
    def _merge(
        bm25_chunks: List[RetrievedChunk],
        vector_chunks: List[RetrievedChunk],
        bm25_weight: float,
        vector_weight: float,
    ) -> List[RetrievedChunk]:
        """
        Merge BM25 + vector chunks into a deduplicated dict keyed by chunk_id.

        For duplicate chunk_ids: keep the higher individual scores and sum
        the weighted contributions so the ranking service sees both signals.
        Mark merged chunks with RetrievalSource.HYBRID.
        """
        combined: Dict[str, RetrievedChunk] = {}

        for chunk in bm25_chunks:
            weighted = chunk.bm25_score * bm25_weight
            object.__setattr__(chunk, "combined_score", weighted)
            combined[chunk.chunk_id] = chunk

        for chunk in vector_chunks:
            vec_contrib = chunk.vector_score * vector_weight
            if chunk.chunk_id in combined:
                existing = combined[chunk.chunk_id]
                # Merge: accumulate combined_score and set both individual scores
                object.__setattr__(existing, "combined_score", existing.combined_score + vec_contrib)
                object.__setattr__(existing, "vector_score", chunk.vector_score)
                object.__setattr__(existing, "retrieval_source", RetrievalSource.HYBRID)
            else:
                object.__setattr__(chunk, "combined_score", vec_contrib)
                combined[chunk.chunk_id] = chunk

        return list(combined.values())


# ===========================================================================
# RetrievalServiceFactory
# ===========================================================================

class RetrievalServiceFactory:
    """
    Factory for creating a fully wired RetrievalService from Phase2Settings.

    Follows the factory pattern established by Part 1's QueryProcessingServiceFactory.
    """

    @staticmethod
    def create(settings: Any) -> RetrievalService:
        """
        Build a RetrievalService with a Phase1RetrieverAdapter.

        Args:
            settings : Phase2Settings instance.

        Returns:
            RetrievalService wired with a Phase1RetrieverAdapter.
        """
        import os
        
        # Load Phase 1 target paths strictly from configuration 
        # (Zero Hardcoding Policy)
        # We ensure they are absolute relative to the current working directory.
        bm25_path = os.path.abspath(settings.phase1.bm25_index_path)
        chroma_dir = os.path.abspath(settings.phase1.chroma_dir)

        adapter = Phase1RetrieverAdapter(
            bm25_index_path=bm25_path,
            chroma_dir=chroma_dir,
            chroma_collection=settings.phase1.chroma_collection_name,
            timeout_seconds=settings.retrieval.timeout_seconds,
        )

        return RetrievalService(
            phase1_retriever=adapter,
            timeout_seconds=settings.retrieval.timeout_seconds,
        )
