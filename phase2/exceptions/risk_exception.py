"""
Risk Agent Exception Hierarchies.

Strictly mapped typed exceptions to handle LLM mapping mismatches, missing evidence bounds, 
and constraint failures within the Risk Assessment pipeline layer natively.
"""
from phase2.exceptions.query_exception import Phase2BaseException

class RiskException(Phase2BaseException):
    """Base exception for all Risk Agent failures."""
    pass

class AmbiguityException(RiskException):
    """Raised when ambiguity checks structurally fail."""
    def __init__(self, message: str, context: dict = None):
        super().__init__(message, error_code="RISK_AMBIGUITY_ERR", context=context)

class LegalSensitivityException(RiskException):
    """Raised when legal checks structurally fail."""
    def __init__(self, message: str, context: dict = None):
        super().__init__(message, error_code="RISK_LEGAL_ERR", context=context)

class RegulatoryException(RiskException):
    """Raised when regulatory interpretation bounds fail."""
    def __init__(self, message: str, context: dict = None):
        super().__init__(message, error_code="RISK_REGULATORY_ERR", context=context)

class ConfigurationException(RiskException):
    """Raised when Risk configuration boundaries are invalid."""
    def __init__(self, message: str, context: dict = None):
        super().__init__(message, error_code="RISK_CONFIG_ERR", context=context)

class TimeoutException(RiskException):
    """Raised when the LLM constraint breaches the 1-second logic bound."""
    def __init__(self, message: str, context: dict = None):
        super().__init__(message, error_code="RISK_TIMEOUT_ERR", context=context)
