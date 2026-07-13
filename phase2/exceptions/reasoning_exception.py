from phase2.exceptions.query_exception import Phase2BaseException

class ReasoningException(Phase2BaseException):
    """Base exception for all Reasoning Agent (Part 4) related failures."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, **kwargs)

class InvalidVerificationException(ReasoningException):
    """Raised when the Reasoning Agent refuses a malformed or failed VerificationResult payload."""
    pass

class ClauseInterpretationException(ReasoningException):
    """Raised when evidence mapping limits are violated restricting interpretation natively."""
    pass

class ExplanationException(ReasoningException):
    """Raised when UX parsing loops fail to interpret sequence mappings securely."""
    pass

class ReasoningTimeoutException(ReasoningException):
    """Raised when the strict <3s LLM telemetry limit thresholds are hit."""
    pass
