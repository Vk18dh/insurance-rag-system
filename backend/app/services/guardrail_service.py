import logging
import re
from typing import Tuple

logger = logging.getLogger(__name__)

class GuardrailService:
    """
    Lightweight, deterministic guardrail service to protect the Agentic RAG pipeline.
    This service is executed at the API boundary, separate from the core Phase 2 orchestration.
    """
    
    # Simple heuristics for prompt injection detection
    INJECTION_PATTERNS = [
        r"(?i)ignore all previous instructions",
        r"(?i)disregard previous",
        r"(?i)system prompt",
        r"(?i)you are an AI",
        r"(?i)forget everything",
        r"(?i)new instructions",
        r"(?i)bypass restrictions"
    ]
    
    # Simple heuristics for explicitly unsafe topics
    UNSAFE_PATTERNS = [
        r"(?i)how to hack",
        r"(?i)how to steal",
        r"(?i)illegal activities",
        r"(?i)bomb instructions"
    ]
    
    @classmethod
    def check_input(cls, query: str) -> Tuple[bool, str]:
        """
        Validates the input query.
        Returns (is_safe, reason).
        """
        if not query or len(query.strip()) < 3:
            return False, "Query is too short or malformed."
            
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, query):
                logger.warning(f"Input Guardrail triggered (Prompt Injection): {pattern}")
                return False, "Query blocked due to suspected prompt injection attempt."
                
        for pattern in cls.UNSAFE_PATTERNS:
            if re.search(pattern, query):
                logger.warning(f"Input Guardrail triggered (Unsafe Content): {pattern}")
                return False, "Query blocked due to unsafe or prohibited content."
                
        return True, ""
        
    @classmethod
    def check_output(cls, generated_answer: str, query: str, has_citations: bool) -> Tuple[bool, str]:
        """
        Validates the generated output from the RAG pipeline.
        Returns (is_safe, reason).
        """
        if not generated_answer or len(generated_answer.strip()) == 0:
            return False, "Generated answer is empty."
            
        # Basic hallucination/unsupported check: 
        # If the answer makes specific factual claims but has no citations (and isn't a generic refusal).
        # We rely on the VerificationAgent primarily, but as a last line of defense:
        answer_lower = generated_answer.lower()
        is_refusal = any(phrase in answer_lower for phrase in [
            "i could not find", "not present", "not explicitly mentioned", "i am unable to answer"
        ])
        
        # If it's NOT a refusal and it lacks citations, flag it if it uses absolute phrasing.
        if not is_refusal and not has_citations:
            absolute_phrases = ["according to the policy", "the rules state", "must be paid", "guaranteed"]
            if any(p in answer_lower for p in absolute_phrases):
                logger.warning("Output Guardrail triggered: Unsupported absolute claim without citations.")
                return False, "Output blocked due to unsupported claims lacking citations."
                
        # Basic safety check on output
        for pattern in cls.UNSAFE_PATTERNS:
            if re.search(pattern, generated_answer):
                logger.warning(f"Output Guardrail triggered (Unsafe Content in Output): {pattern}")
                return False, "Output blocked due to unsafe content."
                
        return True, ""
