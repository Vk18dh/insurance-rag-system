"""
phase2.exceptions.response_exception

Defines boundaries for formatting and validation errors inside the composer limits securely.
"""

class ResponseException(Exception):
    """Base exception spanning Response compilation errors strictly cleanly."""
    pass

class ResponseValidationException(ResponseException):
    """Raised when compiled objects violate strict structural rules natively."""
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(f"Validation dropped on field '{field}': {message}" if field else message)

class CitationException(ResponseException):
    """Raised when Verification mapping limits fault on invalid arrays safely."""
    pass

class FormattingException(ResponseException):
    """Exception denoting template interpolation errors mapping dynamically."""
    pass

class ResponseConfigurationException(ResponseException):
    """Errors loading fallbacks or thresholds."""
    pass
