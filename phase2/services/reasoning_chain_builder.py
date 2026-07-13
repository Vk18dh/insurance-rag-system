import json
import logging
from typing import List, Dict, Any

from phase2.interfaces.reasoning_interface import IReasoningChainBuilder
from phase2.interfaces.query_agent_interface import ILLMAnalyzer
from phase2.models.verification_result import VerificationResult
from phase2.models.reasoning_step import ReasoningStep, SupportingEvidence
from phase2.models.reasoning_chain import ReasoningChain
from phase2.exceptions.reasoning_exception import ClauseInterpretationException, ReasoningException

logger = logging.getLogger(__name__)

class ReasoningChainBuilder(IReasoningChainBuilder):
    """
    Orchestrates the massive, highly constrained Prompt executing the discrete 
    multi-step logic inferences strictly tracking conclusions against `EVIDENCE_X` anchors.
    """
    def __init__(self, llm_analyzer: ILLMAnalyzer, prompt_template_path: str, max_steps: int = 5):
        self.llm = llm_analyzer
        self.max_steps = max_steps
        self.prompt_template = self._load_template(prompt_template_path)

    def _load_template(self, path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load reasoning prompt: {e}")
            raise ClauseInterpretationException(f"Prompt payload failed to mount: {e}")

    def build_chain(self, verification_result: VerificationResult, linked_clauses: List[Dict[str, Any]]) -> ReasoningChain:
        """
        Executes a singular, explicit LLM JSON call targeting specific deduction lists natively.
        Targeting < 3 second latency loops.
        """
        try:
            # Reconstruct original string constraints cleanly
            query_ctx = verification_result.retrieval_result.query_context
            query_text = getattr(query_ctx, "original_query", "Unknown Context")
            
            # Map evidence block
            evidence_str = json.dumps(linked_clauses, indent=2)
            
            prompt = self.prompt_template.format(
                QUERY=query_text,
                EVIDENCE_BLOCK=evidence_str,
                MAX_STEPS=self.max_steps
            )
            
            # Rely strictly on structured LLM outputs to parse native schema maps.
            # (Note: Fallback offline mocks must yield properly structured JSON strings tracking dict bounds)
            result_payload = self.llm.analyse(prompt)
            
            return self._parse_json_result(result_payload, linked_clauses)
            
        except Exception as e:
            logger.exception(f"Fatal anomaly occurred during Deductive Chain generation: {e}")
            raise ReasoningException(f"Deductive inference crashed: {e}")

    def _parse_json_result(self, result: Dict[str, Any], original_clauses: List[Dict[str, Any]]) -> ReasoningChain:
        """
        Validates the arbitrary LLM dictionary explicitly against the robust Pydantic Step models.
        """
        steps = []
        raw_steps = result.get("reasoning_steps", [])
        
        # Mapping index keys to actual chunk identifiers
        evidence_dict = {
            c["logical_reference_id"]: {"chunk_id": c["chunk_id"], "source": c["source"]} 
            for c in original_clauses
        }
        
        for idx, rs in enumerate(raw_steps):
            # Parse linked chunk definitions securely
            linked_evidence = []
            derived_unsupported = False
            
            raw_anchors = rs.get("evidence_used_ids", [])
            if not raw_anchors:
                derived_unsupported = True
                
            for anchor in raw_anchors:
                if anchor in evidence_dict:
                    meta = evidence_dict[anchor]
                    linked_evidence.append(SupportingEvidence(
                        chunk_id=meta["chunk_id"],
                        source_document=meta["source"]
                    ))
                else:
                    derived_unsupported = True # Fallacious linkage tracked downstream
                    
            steps.append(ReasoningStep(
                step_number=idx + 1,
                premise=rs.get("premise", "Extrapolated step"),
                evidence_used=linked_evidence,
                assumption=rs.get("assumption", "") or None,
                conclusion=rs.get("conclusion", "System constraint failure."),
                is_supported=not derived_unsupported
            ))
            
        logger.info("Reasoning chain steps formulated natively", extra={"total_steps_inferred": len(steps), "assumptions_detected": sum(1 for s in steps if s.assumption), "unsupported_links": sum(1 for s in steps if not s.is_supported)})
        return ReasoningChain(
            steps=steps, 
            is_complete=True if steps else False
        )
