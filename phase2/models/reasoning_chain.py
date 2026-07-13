from typing import List
from pydantic import BaseModel, Field
from phase2.models.reasoning_step import ReasoningStep

class ReasoningChain(BaseModel):
    """
    The composite sequence of ReasoningSteps mapping an analytical progression.
    Ensures that logical steps do not skip verification bounds.
    """
    steps: List[ReasoningStep] = Field(default_factory=list)
    is_complete: bool = Field(
        ..., 
        description="Indicates if the chain successfully reached a logical termination point relative to the query."
    )
    
    @property
    def has_unsupported_deductions(self) -> bool:
        """Convenience property identifying unstable reasoning sequences."""
        return any(not step.is_supported for step in self.steps)
    
    @property
    def total_assumptions(self) -> int:
        """Convenience metric counting all detected leaps in logic."""
        return sum(1 for step in self.steps if step.assumption)
