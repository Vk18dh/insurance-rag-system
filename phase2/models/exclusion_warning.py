from pydantic import Field
from phase2.models.risk_factor import RiskFactor

class ExclusionWarning(RiskFactor):
    """Flags logic tied to suicide, waiting periods, etc."""
    exclusion_type: str = Field("None", description="Categorical exclusion grouping.")
