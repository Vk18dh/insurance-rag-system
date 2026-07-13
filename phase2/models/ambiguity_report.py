from pydantic import Field
from phase2.models.risk_factor import RiskFactor

class AmbiguityReport(RiskFactor):
    """Identifies unclear interpretations natively."""
    ambiguity_type: str = Field("None", description="Categorical origin of ambiguity.")
