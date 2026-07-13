from typing import List
from pydantic import BaseModel, Field

class RiskFactor(BaseModel):
    """
    Base model mapping common structures for any identified Risk.
    Forces all derived risks to explicitly trace back to verified Reasoning Steps.
    """
    detected: bool = Field(..., description="Whether this specific dimension triggered affirmatively.")
    affected_step_numbers: List[int] = Field(default_factory=list, description="Reasoning Step indices tied to this risk.")
    description: str = Field(..., description="Contextual explanation or 'Insufficient Evidence' string.")
