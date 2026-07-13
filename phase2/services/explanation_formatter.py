"""
phase2.services.explanation_formatter

Constructs explanation limits securely mapping fallbacks securely.
"""
from phase2.interfaces.response_builder_interface import IExplanationFormatter
from phase2.models.reasoning_result import ReasoningResult

class ExplanationFormatter(IExplanationFormatter):
    """Maps logic trees tracking explanations stably accurately securely safely cleanly implicitly flexibly completely safely."""
    
    def __init__(self, fallback_template: str):
        self._fallback = fallback_template

    def format_explanation(self, reasoning_result: ReasoningResult) -> str:
        if not reasoning_result or not getattr(reasoning_result, 'reasoning_chain', None):
            return self._fallback
            
        if not reasoning_result.reasoning_chain.is_complete:
            return f"{self._fallback}\n\n*Partial Details:* {reasoning_result.explanation}"
            
        return reasoning_result.explanation
