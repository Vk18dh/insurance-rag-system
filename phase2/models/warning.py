"""
phase2.models.warning

Defines user Warning structs tracking severity.
"""
from enum import Enum
from pydantic import BaseModel, Field

class WarningSeverity(str, Enum):
    """Defines strict enum boundaries for user alerts natively."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ResponseWarning(BaseModel):
    """
    Represents an explicit alert or warning to surface to the frontend UI.
    """
    severity: WarningSeverity = Field(..., description="The severity level of the warning.")
    message: str = Field(..., description="The warning message to display to the user.")
    source_agent: str = Field(..., description="The agent that generated this warning (e.g. RiskAgent, ContradictionAgent, VerificationAgent).")
