"""
phase2.exceptions.orchestration_exception
=========================================

Typed fallback traps executing securely on timeouts and context overlaps natively avoiding pipeline collapse gracefully.
"""

from phase2.exceptions.query_exception import QueryProcessingException

class OrchestrationException(QueryProcessingException):
    """Base class for strictly bounding integration loops effectively tracking missing dependencies."""
    pass

class TimeoutException(OrchestrationException):
    """Agents hitting maximum threshold timeouts explicitly firing interrupts cleanly."""
    pass

class AgentExecutionException(OrchestrationException):
    """Agent runtime traps cleanly breaking inner execution loops smoothly mapping traces."""
    pass

