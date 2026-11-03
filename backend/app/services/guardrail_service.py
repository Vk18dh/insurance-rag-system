import logging
import re
from typing import Tuple

logger = logging.getLogger(__name__)

class GuardrailService:
    """
    Lightweight, deterministic guardrail service to protect the Agentic RAG pipeline.
    This service is executed at the API boundary, separate from the core Phase 2 orchestration.
    """
    
    # Comprehensive patterns for prompt injection, jailbreak, and adversarial bypass
    INJECTION_PATTERNS = [
        r"(?i)ignore\s+(?:all\s+)?previous\s+instructions",
        r"(?i)disregard\s+(?:all\s+|any\s+|previous\s+|the\s+|insurance\s+|system\s+)?(?:instructions|rules|prompts|guidelines)",
        r"(?i)system\s+override",
        r"(?i)developer\s+mode",
        r"(?i)you\s+are\s+(?:dan|freed|an\s+unrestricted)",
        r"(?i)pretend\s+you\s+are\s+(?:an?\s+)?(?:unrestricted)?",
        r"(?i)forget\s+(?:everything|you\s+are)",
        r"(?i)(?:pre-?prompt|system\s+prompt|prompt\s+instructions)",
        r"(?i)bypass\s+restrictions",
        r"(?i)decode\s+and\s+execute",
        r"(?i)base64\s+payload"
    ]
    
    # Heuristics for malicious probes, fraud, and system intrusion attempts
    UNSAFE_PATTERNS = [
        r"(?i)\bhack(?:ing)?\b",
        r"(?i)how\s+to\s+steal",
        r"(?i)illegal\s+activities",
        r"(?i)(?:fabricate|forge|falsify)\s+(?:a\s+)?(?:fake\s+)?(?:death\s+certificate|medical\s+report|insurance\s+claim|document)",
        r"(?i)insurance\s+fraud",
        r"(?i)<\s*script[^>]*>",
        r"(?i)(?:drop\s+table|select\s+.*from|union\s+select)",
        r"(?i)cat\s+/(?:etc/passwd|\.env)",
        r"(?i)\bbomb\s+instructions\b",
        r"(?i)\bhow\s+to\s+murder\b",
        r"(?i)\b(?:how\s+to\s+(?:commit\s+)?suicide|ways\s+to\s+(?:commit\s+suicide|kill\s+oneself))\b"
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
            "i could not find", "not present", "not explicitly mentioned", "i am unable to answer", "clarify"
        ])
        
        # If it's NOT a refusal/clarification and it lacks citations, flag it.
        # The contract requires citations for factual responses.
        if not is_refusal and not has_citations:
            logger.warning("Output Guardrail triggered: Factual response generated without required citations.")
            return False, "Output blocked due to unsupported factual claims lacking citations."
                
        # Basic safety check on output
        for pattern in cls.UNSAFE_PATTERNS:
            if re.search(pattern, generated_answer):
                logger.warning(f"Output Guardrail triggered (Unsafe Content in Output): {pattern}")
                return False, "Output blocked due to unsafe content."
                
        return True, ""
