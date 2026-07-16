from phase2.interfaces.reasoning_interface import IExplanationService
from phase2.models.reasoning_chain import ReasoningChain
from phase2.models.explanation import Explanation

import logging

logger = logging.getLogger(__name__)

class ExplanationService(IExplanationService):
    """
    Safely stringifies discrete step chains into flattened human-readable summaries 
    expressly noting tracked assumptions and decoupled logic leaps.
    """
    def __init__(self, explanation_format: str = "structured"):
        self.explanation_format = explanation_format

    def generate_explanation(self, reasoning_chain: ReasoningChain) -> Explanation:
        """
        Aggregates sequential constraints securely avoiding direct LLM concatenation cycles.
        """
        if not reasoning_chain.steps:
            return Explanation(
                reasoning_summary="No logical inferences were formulated cleanly from the source payload.",
                clause_interpretation="Empty constraints.",
                assumptions_flagged=["Complete derivation failure"],
                confidence_inputs={"status": "failed_degraded_output"}
            )
            
        assumptions = []
        summary = ""
        clauses = []
        
        for step in reasoning_chain.steps:
            if step.assumption:
                assumptions.append(f"Logic leap (Step {step.step_number}): {step.assumption}")
            if not step.is_supported:
                assumptions.append(f"Failure (Step {step.step_number}): UNSUPPORTED conclusion logic leap.")
                
            summary += f"{step.conclusion} "
            
            # Map evidence docs cleanly
            if step.evidence_used:
                docs = ", ".join([e.source_document for e in step.evidence_used])
                clauses.append(f"{step.premise} [Source: {docs}]")
                
        logger.info("Explainable sequence mapped", extra={"explanation_format": self.explanation_format, "assumptions_flagged": len(assumptions)})
        return Explanation(
            reasoning_summary=summary.strip(),
            clause_interpretation=" | ".join(clauses),
            assumptions_flagged=assumptions,
            confidence_inputs={
                "unsupported_triggers": len([s for s in reasoning_chain.steps if not s.is_supported]),
                "logical_hops": len(reasoning_chain.steps)
            }
        )
