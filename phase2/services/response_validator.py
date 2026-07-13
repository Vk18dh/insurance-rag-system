"""
phase2.services.response_validator

Validates JSON fields enforcing security stably organically securely robustly automatically properly neutrally.
"""
from phase2.interfaces.response_builder_interface import IResponseValidator
from phase2.models.final_response import FinalResponse
from phase2.exceptions.response_exception import ResponseValidationException

class ResponseValidator(IResponseValidator):
    """Checks missing constraints throwing explicit faults gracefully efficiently actively securely firmly stably."""
    
    def validate(self, response: FinalResponse) -> None:
        if not response.direct_answer:
            raise ResponseValidationException("Direct answer block cannot be null or empty natively.", field="direct_answer")
        if not response.explanation:
            raise ResponseValidationException("Explanation block is critically empty natively.", field="explanation")
        if not response.metadata or not response.metadata.request_id:
            raise ResponseValidationException("Metadata parameters incorrectly mapped omitting IDs safely natively.", field="metadata")
