"""
phase2.models.intent
====================

Defines the Intent domain model used by the Query Understanding Agent.

Intents are NOT hardcoded into business logic. The list of supported intents
is loaded from configuration (settings.query_agent.supported_intents) so that
new intent categories can be added without touching source code.

Classes:
    IntentType      — String-based enum of supported intent categories.
    IntentResult    — Typed result of intent detection, including confidence.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# IntentType — loaded values must match what appears in config/settings.yaml
# NOTE: This enum exists so downstream agents can use typed comparisons.
#       The canonical *list* of enabled intents is governed by settings.
# ---------------------------------------------------------------------------
class IntentType(str, Enum):
    """
    Enumeration of all supported insurance query intent categories.

    New categories can be added here AND in settings.query_agent.supported_intents
    without any other code change. Agents reference IntentType members, not
    raw strings, to prevent typos and enable IDE completion.
    """

    POLICY_INFORMATION = "policy_information"
    BENEFITS = "benefits"
    EXCLUSIONS = "exclusions"
    PREMIUM = "premium"
    ELIGIBILITY = "eligibility"
    CLAIM_PROCESS = "claim_process"
    MATURITY = "maturity"
    SURRENDER = "surrender"
    LOAN = "loan"
    NOMINATION = "nomination"
    RIDER = "rider"
    TAX_BENEFIT = "tax_benefit"
    WAITING_PERIOD = "waiting_period"
    REGULATORY_INFORMATION = "regulatory_information"
    COMPLIANCE = "compliance"
    GENERAL_INQUIRY = "general_inquiry"
    UNKNOWN = "unknown"


class IntentResult(BaseModel):
    """
    Structured output of the intent detection step.

    Attributes:
        intent      : The primary detected intent category.
        confidence  : Confidence score in the range [0.0, 1.0].
        secondary   : Optional secondary intent when the query spans two topics.
        raw_label   : The raw label returned by the LLM/classifier before mapping.
        explanation : Short human-readable justification for the chosen intent.
    """

    intent: IntentType = Field(
        default=IntentType.UNKNOWN,
        description="Primary detected intent category.",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for the primary intent (0.0 – 1.0).",
    )
    secondary: Optional[IntentType] = Field(
        default=None,
        description="Optional secondary intent for multi-topic queries.",
    )
    raw_label: Optional[str] = Field(
        default=None,
        description="Raw LLM-returned label before normalisation.",
    )
    explanation: Optional[str] = Field(
        default=None,
        description="Human-readable justification for the classified intent.",
    )

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        """Clamp confidence to [0.0, 1.0] even if LLM returns out-of-range value."""
        return max(0.0, min(1.0, float(v)))

    class Config:
        """Pydantic model configuration."""

        use_enum_values = False  # Preserve enum members for type-checking
        frozen = False           # Context is updated incrementally by agents

    def is_high_confidence(self, threshold: float) -> bool:
        """
        Return True when the detected confidence meets or exceeds the threshold.

        Args:
            threshold: The minimum confidence value loaded from settings.

        Returns:
            bool: True if confidence >= threshold, False otherwise.
        """
        return self.confidence >= threshold

    def __repr__(self) -> str:
        return (
            f"IntentResult(intent={self.intent.value}, "
            f"confidence={self.confidence:.2f}, "
            f"secondary={self.secondary})"
        )
