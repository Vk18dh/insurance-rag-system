"""
phase2.services.response_formatter

Constructs short form direct answers configuring zero-hallucination policies accurately efficiently securely securely.
"""
from phase2.interfaces.response_builder_interface import IResponseFormatter
from phase2.models.reasoning_result import ReasoningResult

class ResponseFormatter(IResponseFormatter):
    """
    Transfers reasoning conclusions securely smoothly handling fallbacks neutrally implicitly stably explicitly explicitly properly safely cleanly.
    """
    
    def __init__(self, fallback_answer: str):
        self._fallback_answer = fallback_answer

    def format_answer(self, reasoning_result: ReasoningResult) -> str:
        if not reasoning_result or not getattr(reasoning_result, 'reasoning_chain', None):
            return self._fallback_answer
            
        if not reasoning_result.reasoning_chain.is_complete:
            return self._fallback_answer
            
        steps = reasoning_result.reasoning_chain.steps
        if not steps:
            return self._fallback_answer
            
        # Natively trace the final step deduction gracefully representing the direct conclusion smoothly quietly safely cleanly smoothly purely efficiently safely.
        final_deduction = getattr(steps[-1], 'conclusion', self._fallback_answer)
        return final_deduction if final_deduction else self._fallback_answer
