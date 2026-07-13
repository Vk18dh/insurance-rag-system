from phase2.exceptions.query_exception import QueryProcessingException

class ContradictionException(QueryProcessingException):
    """Base exception for all Contradiction Agent overlaps."""
    pass

class ContextValidationException(ContradictionException):
    """Raised when evidence mappings explicitly violate Policy isolation rules."""
    pass

class EvidenceAlignmentException(ContradictionException):
    """Raised when factual traces fail to link back cleanly to chunk limits."""
    pass

class ConflictClassificationException(ContradictionException):
    """Raised when JSON variables hallucinate outside Enum mapping boundaries securely."""
    pass

class ConfigurationException(ContradictionException):
    """Raised when required Prompts or String overlaps are missing globally."""
    pass

class TimeoutException(ContradictionException):
    """Raised when analytical limits surpass 1-second thresholds statically."""
    pass
