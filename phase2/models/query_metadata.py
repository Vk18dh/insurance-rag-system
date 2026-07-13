"""
phase2.models.query_metadata
=============================

Defines the QueryMetadata model — the processing diagnostics and audit record
attached to every query processed by the Query Understanding Agent.

This model is intentionally separated from QueryContext so that audit/telemetry
data does not pollute the business-relevant context fields.

Classes:
    QueryClassification — Classification of the query's structural type.
    AmbiguityInfo       — Structured ambiguity signal with clarification hints.
    QueryMetadata       — Full processing metadata record.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# QueryClassification
# ---------------------------------------------------------------------------
class QueryClassification(str, Enum):
    """
    Structural category of the user query.

    Used by the Retriever Agent to select the most appropriate retrieval
    strategy (single-doc lookup vs. multi-doc synthesis, etc.).

    Values are configurable through settings.query_agent.classification_types.
    """

    FACTUAL = "factual"
    COMPARATIVE = "comparative"
    REGULATORY = "regulatory"
    RISK = "risk"
    POLICY_SPECIFIC = "policy_specific"
    MULTI_DOCUMENT = "multi_document"
    GENERAL = "general"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# AmbiguityInfo
# ---------------------------------------------------------------------------
class AmbiguityInfo(BaseModel):
    """
    Captures whether the user's query is ambiguous and provides structured
    hints that the Orchestrator can use to decide whether to request
    clarification.

    Attributes:
        is_ambiguous        : True if the query is underspecified.
        ambiguity_type      : Short tag for the ambiguity category
                              (e.g. 'missing_policy', 'vague_term').
        missing_entities    : List of entity categories the query lacks
                              (e.g. ['policy_name', 'coverage_period']).
        clarification_hints : Suggested questions to resolve ambiguity.
                              NOT shown to user directly — decision is made
                              by the Orchestrator per workflow config.
        confidence          : Confidence that the query IS ambiguous (0.0–1.0).
    """

    is_ambiguous: bool = Field(
        default=False,
        description="True when the query is underspecified or vague.",
    )
    ambiguity_type: Optional[str] = Field(
        default=None,
        description="Short category tag (e.g. 'missing_policy', 'vague_term').",
    )
    missing_entities: List[str] = Field(
        default_factory=list,
        description="Entity categories absent from the query.",
    )
    clarification_hints: List[str] = Field(
        default_factory=list,
        description="Suggested questions to resolve ambiguity — for orchestrator use only.",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence that the query is ambiguous.",
    )

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp(cls, v: float) -> float:
        """Clamp confidence to [0.0, 1.0]."""
        return max(0.0, min(1.0, float(v)))


# ---------------------------------------------------------------------------
# QueryMetadata
# ---------------------------------------------------------------------------
class QueryMetadata(BaseModel):
    """
    Processing metadata and audit record for a single query lifecycle.

    This model is attached to every QueryContext and provides full traceability
    without exposing raw user data to logging systems.

    Attributes:
        query_id            : UUID assigned at query receipt — used for log correlation.
        received_at         : UTC timestamp when the raw query was received.
        processed_at        : UTC timestamp when processing completed.
        processing_time_ms  : Total processing duration in milliseconds.
        language            : Detected or assumed language code (e.g. 'en').
        char_count          : Length of the raw query in characters.
        word_count          : Approximate word count of the raw query.
        validation_passed   : True if the query passed all input validation checks.
        validation_errors   : List of validation error messages (empty on success).
        normalization_applied: True if text normalisation was applied.
        agent_version       : Version of the Query Understanding Agent.
        extra               : Extensible key-value store for agent-specific metadata.
    """

    query_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="UUID v4 identifier for this query (log correlation key).",
    )
    received_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of query receipt.",
    )
    processed_at: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp when all processing steps completed.",
    )
    processing_time_ms: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Total wall-clock processing time in milliseconds.",
    )
    language: str = Field(
        default="en",
        description="BCP-47 language code detected/assumed for the query.",
    )
    char_count: int = Field(
        default=0,
        ge=0,
        description="Character count of the raw query.",
    )
    word_count: int = Field(
        default=0,
        ge=0,
        description="Approximate word count of the raw query.",
    )
    validation_passed: bool = Field(
        default=False,
        description="True when the query passed all input validation checks.",
    )
    validation_errors: List[str] = Field(
        default_factory=list,
        description="Validation error messages; empty list on success.",
    )
    normalization_applied: bool = Field(
        default=False,
        description="True when text normalisation was applied to the raw query.",
    )
    agent_version: str = Field(
        default="unknown",
        description="Semver version of the Query Understanding Agent that processed this query.",
    )
    extra: Dict[str, str] = Field(
        default_factory=dict,
        description="Extensible metadata store for agent-specific fields.",
    )

    def mark_processed(self, start_time_ms: float, end_time_ms: float) -> None:
        """
        Stamp the completion timestamp and processing duration.

        Args:
            start_time_ms : Monotonic start time in milliseconds.
            end_time_ms   : Monotonic end time in milliseconds.
        """
        self.processed_at = datetime.now(timezone.utc)
        self.processing_time_ms = max(0.0, end_time_ms - start_time_ms)

    def add_validation_error(self, message: str) -> None:
        """
        Append a validation error message and mark validation as failed.

        Args:
            message: Human-readable description of the validation failure.
        """
        self.validation_errors.append(message)
        self.validation_passed = False

    class Config:
        """Pydantic model configuration."""

        frozen = False
