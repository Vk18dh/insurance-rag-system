import time
import logging
from typing import Dict, Any

from phase2.config.settings import Phase2Settings
from phase2.interfaces.reasoning_interface import (
    IReasoningAgent,
    IClauseInterpreter,
    IEvidenceLinker,
    IReasoningChainBuilder,
    IExplanationService
)
from phase2.interfaces.query_agent_interface import ILLMAnalyzer
from phase2.models.verification_result import VerificationResult
from phase2.models.reasoning_result import ReasoningResult
from phase2.models.reasoning_metrics import ReasoningMetrics
from phase2.exceptions.handlers import safe_agent_call
from phase2.exceptions.reasoning_exception import InvalidVerificationException

logger = logging.getLogger(__name__)

class ReasoningAgent(IReasoningAgent):
    """
    Sits strictly between the QA Verification layer (Part 3) and Risk Layer (Part 5).
    Rejects invalidated context. Drives multi-step clause linkages using explicitly grouped dependencies.
    """
    def __init__(
        self,
        clause_interpreter: IClauseInterpreter,
        evidence_linker: IEvidenceLinker,
        chain_builder: IReasoningChainBuilder,
        explanation_service: IExplanationService
    ):
        self._interpreter = clause_interpreter
        self._linker = evidence_linker
        self._chain_builder = chain_builder
        self._explanation_svc = explanation_service

    def reason(self, verification_result: VerificationResult) -> ReasoningResult:
        query_ctx = verification_result.retrieval_result.query_context
        query_id = getattr(query_ctx, "query_id", "Unknown")
        
        with safe_agent_call("ReasoningAgent", reraise=True):
            logger.info(f"Reasoning phase executing for Query [{query_id}]")
            
            # 1. Validation Boundary
            if not verification_result.is_valid_for_reasoning:
                logger.warning(f"Verification boundary violated! Query [{query_id}] blocking chain generation.")
                # We will define the typed InvalidVerificationException in Stage 8, but raising standard ValueError handles safely
                raise InvalidVerificationException("VerificationResult failed QA upstream constraints. Reasoning Sequence aborted directly.")
            
            start_ms = time.perf_counter()
            
            # 2. Extract specific Verification Document evidence
            evidence_chunks = verification_result.retrieval_result.ranked_evidence
            
            # 3. Clause Interpretation
            clauses = self._interpreter.interpret(evidence_chunks, context={})
            
            # 4. Linkage Setup
            linked_evidence = self._linker.link_evidence(clauses)
            
            # 5. Native Chain execution
            chain = self._chain_builder.build_chain(verification_result, linked_evidence)
            
            # 6. Formatting explicitly for UX outputs (Explanation)
            explanation = self._explanation_svc.generate_explanation(chain)
            
            latency_ms = (time.perf_counter() - start_ms) * 1000
            
            # 7. Quality Metrics
            metrics = ReasoningMetrics(
                reasoning_completeness=1.0 if chain.is_complete else 0.5,
                evidence_coverage_ratio=self._calculate_coverage(chain, clauses),
                logical_consistency_score=1.0 if not chain.has_unsupported_deductions else 0.5,
                processing_time_ms=round(latency_ms, 2),
                total_steps=len(chain.steps)
            )
            
            result = ReasoningResult(
                verification_source=verification_result,
                reasoning_chain=chain,
                explanation=explanation,
                metrics=metrics
            )
            
            logger.info(f"Reasoning successfully generated for Query [{query_id}] spanning {metrics.total_steps} sequence bounds in {metrics.processing_time_ms}ms")
            
            return result

    def _calculate_coverage(self, chain, clauses) -> float:
        if not clauses:
            return 0.0
        used_ids = set()
        for step in chain.steps:
            for ev in step.evidence_used:
                used_ids.add(ev.chunk_id)
        return float(len(used_ids)) / float(len(clauses))

class ReasoningAgentFactory:
    """Provides dependency injection scaffolding linking isolated logic structures into the master agent instance."""
    @staticmethod
    def create(settings: Phase2Settings, llm_analyzer: ILLMAnalyzer) -> IReasoningAgent:
        from phase2.services.clause_interpreter import ClauseInterpreter
        from phase2.services.evidence_linker import EvidenceLinker
        from phase2.services.reasoning_chain_builder import ReasoningChainBuilder
        from phase2.services.explanation_service import ExplanationService

        interpreter = ClauseInterpreter(max_chunk_length=settings.reasoning.max_chunk_length)
        linker = EvidenceLinker(required_relationships=settings.reasoning.supported_clause_relationships)
        builder = ReasoningChainBuilder(llm_analyzer, prompt_template_path=settings.reasoning.prompt_template_path, max_steps=settings.reasoning.max_steps)
        explanation = ExplanationService(explanation_format=settings.reasoning.explanation_format)
        
        return ReasoningAgent(interpreter, linker, builder, explanation)
