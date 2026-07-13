from pydantic import Field
from phase2.models.risk_factor import RiskFactor

class LegalWarning(RiskFactor):
    """Flags outputs involving rejection, cancellation, fraud etc."""
    legal_category: str = Field("None", description="Categorical legal classification.")
