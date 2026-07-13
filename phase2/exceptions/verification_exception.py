"""
phase2.exceptions.verification_exception
=========================================
Custom exception hierarchy for the Verification Agent (Part 3).
"""

from phase2.exceptions.query_exception import Phase2BaseException


class VerificationException(Phase2BaseException):
    """Base exception for all Verification Agent failures."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, **kwargs)


class InvalidEvidenceException(VerificationException):
    """Raised when evidence structural payloads violate base Verification schemas."""
    def __init__(self, message: str, **kwargs):
        self.is_retryable = False
        super().__init__(message, **kwargs)


class MetadataException(VerificationException):
    """Raised on critical missing/invalid structural metadata limits."""
    def __init__(self, message: str, **kwargs):
        self.is_retryable = False
        super().__init__(message, **kwargs)


class CitationException(VerificationException):
    """Raised when retrieved chunks strictly lack source anchor points."""
    def __init__(self, message: str, **kwargs):
        self.is_retryable = False
        super().__init__(message, **kwargs)


class VerificationConfigurationException(VerificationException):
    """Raised on invalid tuning bounds inside phase2_config."""
    def __init__(self, message: str, **kwargs):
        self.is_retryable = False
        super().__init__(message, **kwargs)


class VerificationTimeoutException(VerificationException):
    """Raised if deterministic checks exceed hard real-time latency thresholds."""
    def __init__(self, message: str, **kwargs):
        self.is_retryable = True
        super().__init__(message, **kwargs)
