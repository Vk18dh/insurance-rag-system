"""
phase2.validation.exceptions
============================

Exception hierarchy specifically for the Validation Suite.
Captures semantic failures in test scenarios without reusing the core
Phase 2 domain exceptions, preserving the "external client" boundary.
"""


class ValidationException(Exception):
    """
    Base exception for all failures generated exclusively by the Validation Suite.
    """
    pass


class ConfigurationValidationException(ValidationException):
    """
    Raised when the ValidationSettings fail to load or contain illogical thresholds.
    """
    pass


class PerformanceDegradationException(ValidationException):
    """
    Raised when a performance test fails to meet configured latency/throughput thresholds.
    """
    def __init__(self, message: str, metric_diff: float):
        super().__init__(message)
        self.metric_diff = metric_diff


class SecurityBreachException(ValidationException):
    """
    Raised when a security test (like prompt injection) successfully bypasses guards.
    """
    pass


class ValidationTimeoutException(ValidationException):
    """
    Raised when load or concurrency tests exhaust their maximum allocated duration.
    """
    pass


class ValidationRunnerException(ValidationException):
    """
    Raised when an underlying ITestRunner crashes unexpectedly.
    """
    pass
