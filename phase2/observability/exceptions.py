"""
phase2.observability.exceptions
================================
Domain-specific exception hierarchy for the Observability Layer.

No business logic is changed — these exceptions are raised only
inside observability services and never propagate to agents.
"""


class ObservabilityException(Exception):
    """Base exception for all observability failures."""


class StorageException(ObservabilityException):
    """Raised when a storage backend cannot persist an event."""


class AuditException(ObservabilityException):
    """Raised when the audit service encounters an irrecoverable error."""


class MetricsException(ObservabilityException):
    """Raised when metrics recording fails."""


class TracingException(ObservabilityException):
    """Raised when trace context cannot be assigned or propagated."""


class HealthMonitorException(ObservabilityException):
    """Raised when health evaluation logic faults."""
