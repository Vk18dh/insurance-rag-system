from pydantic import Field
from phase2.models.risk_factor import RiskFactor

class RegulatoryWarning(RiskFactor):
    """Checks interpretation bounds against IRDAI compliance."""
    concern_type: str = Field("None", description="Category of regulatory warning.")
