from enum import Enum

class RiskLevel(str, Enum):
    """Enumeration describing operational urgency."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
