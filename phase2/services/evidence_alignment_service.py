import logging
from phase2.interfaces.contradiction_interface import IEvidenceAlignmentService
from phase2.models.reasoning_result import ReasoningResult
from phase2.models.evidence_alignment import EvidenceAlignment

logger = logging.getLogger(__name__)

class EvidenceAlignmentService(IEvidenceAlignmentService):
    def align_evidence(self, reasoning_result: ReasoningResult) -> EvidenceAlignment:
        """
        Extracts mapped conclusion clauses identifying exact chunk correlations securely.
        """
        try:
            step_ids = []
            chunk_ids = []
            
            for step in reasoning_result.reasoning_chain.steps:
                step_ids.append(step.step_number)
                for ev in step.supporting_evidence:
                    if ev.chunk_id not in chunk_ids:
                        chunk_ids.append(ev.chunk_id)
            
            return EvidenceAlignment(
                reasoning_step_ids=step_ids,
                retrieved_chunk_ids=chunk_ids
            )
        except Exception as e:
            logger.error(f"Failed mapping evidence links isolating ties securely: {e}")
            return EvidenceAlignment()
