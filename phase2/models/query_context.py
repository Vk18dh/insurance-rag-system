"""
phase2.models.query_context
============================

Defines QueryContext — the single shared context object that flows through
every Phase 2 agent in the pipeline.

This is the central data contract of the entire Agentic RAG system.
Each agent receives a QueryContext, updates only its own domain fields,
and passes the object to the Orchestrator, which forwards it to the next agent.

Design principles:
    - Agents may only update their own field section.
    - All fields are Optional at construction (filled as pipeline progresses).
    - The model is fully serialisable (JSON, for logging and inter-service use).

Classes:
    ExtractedEntities   — Typed container for all insurance entities extracted
                          from the query.
    QueryContext        — Primary pipeline context object.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from phase2.models.intent import IntentResult
from phase2.models.query_metadata import AmbiguityInfo, QueryClassification, QueryMetadata


# ---------------------------------------------------------------------------
# ExtractedEntities
# ---------------------------------------------------------------------------
class ExtractedEntities(BaseModel):
    """
    Typed container for insurance entities extracted from the user query.

    New entity types should be added here without changing agent business logic.
    The extraction service uses configurable prompts to identify each category.

    Attributes:
        policy_names        : Insurance policy names mentioned (e.g. 'Jeevan Shagun').
        insurance_concepts  : Domain concepts (e.g. 'Sum Assured', 'Free Look Period').
        regulatory_terms    : Regulatory references (e.g. 'IRDAI', 'Section 45').
        numbers             : Numeric values present (amounts, ages, periods).
        dates               : Date expressions found in the query.
        coverage_periods    : Coverage or waiting period expressions.
        medical_terms       : Medical terminology referenced.
        risk_terms          : Risk-related terminology.
        named_entities      : Any other proper nouns identified by the extractor.
        raw_extraction      : Full raw extraction dict from LLM for extensibility.
    """

    policy_names: List[str] = Field(
        default_factory=list,
        description="Insurance policy names mentioned in the query.",
    )
    insurance_concepts: List[str] = Field(
        default_factory=list,
        description="Key insurance domain concepts (e.g. 'Sum Assured', 'Rider').",
    )
    regulatory_terms: List[str] = Field(
        default_factory=list,
        description="Regulatory references (e.g. 'IRDAI', 'UIN', 'Section 45').",
    )
    numbers: List[str] = Field(
        default_factory=list,
        description="Numeric values found (amounts, ages, years, periods).",
    )
    dates: List[str] = Field(
        default_factory=list,
        description="Date expressions extracted from the query.",
    )
    coverage_periods: List[str] = Field(
        default_factory=list,
        description="Coverage or waiting period expressions.",
    )
    medical_terms: List[str] = Field(
        default_factory=list,
        description="Medical terminology referenced in the query.",
    )
    risk_terms: List[str] = Field(
        default_factory=list,
        description="Risk-related terminology.",
    )
    named_entities: List[str] = Field(
        default_factory=list,
        description="Other proper nouns identified by the extractor.",
    )
    raw_extraction: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Full raw extraction output from LLM — for extensibility and debugging.",
    )

    def all_entities_flat(self) -> List[str]:
        """
        Return a flattened list of all extracted entity values (excluding raw_extraction).

        Useful for building retrieval queries that include all mentions.

        Returns:
            List[str]: Deduplicated flat list of all entity strings.
        """
        seen: set[str] = set()
        result: List[str] = []
        for values in [
            self.policy_names,
            self.insurance_concepts,
            self.regulatory_terms,
            self.numbers,
            self.dates,
            self.coverage_periods,
            self.medical_terms,
            self.risk_terms,
            self.named_entities,
        ]:
            for v in values:
                if v not in seen:
                    seen.add(v)
                    result.append(v)
        return result

    def is_empty(self) -> bool:
        """Return True when no entities were extracted."""
        return len(self.all_entities_flat()) == 0


# ---------------------------------------------------------------------------
# QueryContext — THE shared pipeline object
# ---------------------------------------------------------------------------
class QueryContext(BaseModel):
    """
    The primary context object shared across all Phase 2 agents.

    Lifecycle:
        1. Created by the Query Understanding Agent with query fields filled.
        2. Passed (by the Orchestrator) to the Retrieval Agent.
        3. Each subsequent agent enriches its own section and passes it forward.
        4. The Response Builder reads the fully populated context and produces
           the final user response.

    Field ownership:
        Query Understanding Agent  → original_query, normalized_query, intent,
                                     entities, classification, ambiguity, metadata
        Retrieval Agent            → retrieved_evidence (future)
        Verification Agent         → verification_results (future)
        Reasoning Agent            → reasoning_output (future)
        Risk Agent                 → risk_assessment (future)
        Contradiction Agent        → contradiction_analysis (future)

    Attributes:
        original_query      : Exact raw query as received from the user.
        normalized_query    : Cleaned/normalised version of the query.
        intent              : Structured intent detection result.
        entities            : Extracted insurance entities.
        classification      : Structural classification of the query.
        ambiguity           : Ambiguity detection result.
        metadata            : Processing metadata and audit record.
        retrieved_evidence  : Placeholder for Retrieval Agent output (future).
        verification_results: Placeholder for Verification Agent output (future).
        reasoning_output    : Placeholder for Reasoning Agent output (future).
        risk_assessment     : Placeholder for Risk Agent output (future).
        contradiction_analysis: Placeholder for Contradiction Agent output (future).
        pipeline_errors     : List of non-fatal errors accumulated across agents.
    """

    # ── Query Understanding Agent fields ────────────────────────────────────
    original_query: str = Field(
        description="Exact raw query as received from the user.",
    )
    normalized_query: Optional[str] = Field(
        default=None,
        description="Cleaned and normalised query text.",
    )
    intent: Optional[IntentResult] = Field(
        default=None,
        description="Intent detection result from the Query Understanding Agent.",
    )
    entities: Optional[ExtractedEntities] = Field(
        default=None,
        description="Insurance entities extracted from the query.",
    )
    classification: Optional[QueryClassification] = Field(
        default=None,
        description="Structural classification of the query (factual, comparative, etc.).",
    )
    ambiguity: Optional[AmbiguityInfo] = Field(
        default=None,
        description="Ambiguity detection result.",
    )
    metadata: Optional[QueryMetadata] = Field(
        default=None,
        description="Processing metadata and audit trail.",
    )

    # ── Future agent fields (placeholders) ──────────────────────────────────
    retrieved_evidence: Optional[Dict[str, Any]] = Field(
        default=None,
        description="[Future – Retrieval Agent] Retrieved evidence chunks.",
    )
    verification_results: Optional[Dict[str, Any]] = Field(
        default=None,
        description="[Future – Verification Agent] Evidence verification output.",
    )
    reasoning_output: Optional[Dict[str, Any]] = Field(
        default=None,
        description="[Future – Reasoning Agent] Multi-step reasoning chain.",
    )
    risk_assessment: Optional[Dict[str, Any]] = Field(
        default=None,
        description="[Future – Risk Agent] Risk classification and score.",
    )
    contradiction_analysis: Optional[Dict[str, Any]] = Field(
        default=None,
        description="[Future – Contradiction Agent] Detected contradictions.",
    )

    # ── Cross-agent diagnostics ──────────────────────────────────────────────
    pipeline_errors: List[str] = Field(
        default_factory=list,
        description="Non-fatal errors accumulated across all pipeline stages.",
    )

    class Config:
        """Pydantic model configuration."""

        frozen = False        # Agents must update their own fields
        extra = "forbid"      # Reject unknown fields to catch typos early

    # ── Helper methods ───────────────────────────────────────────────────────
    def add_pipeline_error(self, agent_name: str, message: str) -> None:
        """
        Record a non-fatal error from a specific agent.

        Args:
            agent_name : Name of the agent reporting the error.
            message    : Human-readable error description.
        """
        self.pipeline_errors.append(f"[{agent_name}] {message}")

    def is_query_understood(self) -> bool:
        """
        Return True when the Query Understanding Agent has completed its work.

        Returns:
            bool: True if intent, entities, classification and metadata are all set.
        """
        return all([
            self.intent is not None,
            self.entities is not None,
            self.classification is not None,
            self.metadata is not None,
        ])

    def to_retrieval_input(self) -> Dict[str, Any]:
        """
        Produce a dict of fields needed by the Retrieval Agent.

        This defines the integration point (Part 2 will consume this format).
        Includes per-category entity breakdowns and intent confidence so the
        Retrieval Agent can adapt its strategy for different entity types and
        low-confidence queries.

        Returns:
            Dict with query, intent, confidence, entities (flat + per-category),
            classification, is_ambiguous, query_id.
        """
        entities = self.entities
        return {
            "query": self.normalized_query or self.original_query,
            "intent": self.intent.intent.value if self.intent else None,
            "confidence": self.intent.confidence if self.intent else 0.0,
            "entities": entities.all_entities_flat() if entities else [],
            "policy_names": entities.policy_names if entities else [],
            "insurance_concepts": entities.insurance_concepts if entities else [],
            "regulatory_terms": entities.regulatory_terms if entities else [],
            "classification": self.classification.value if self.classification else None,
            "is_ambiguous": self.ambiguity.is_ambiguous if self.ambiguity else False,
            "query_id": self.metadata.query_id if self.metadata else None,
        }

    def __repr__(self) -> str:
        return (
            f"QueryContext(query_id={self.metadata.query_id if self.metadata else 'N/A'}, "
            f"intent={self.intent.intent.value if self.intent else 'None'}, "
            f"classification={self.classification})"
        )
