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
            
        summary = getattr(reasoning_result.explanation, 'reasoning_summary', self._fallback)
        clause = getattr(reasoning_result.explanation, 'clause_interpretation', '')
        text = f"{summary}\n\n{clause}".strip()
        
        if not reasoning_result.reasoning_chain.is_complete:
            return f"{self._fallback}\n\n*Partial Details:* {text}"
            
        return text
