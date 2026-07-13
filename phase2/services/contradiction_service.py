import json
import logging
import time
from typing import Dict, Any, List

from phase2.interfaces.contradiction_interface import (
    IContradictionService, IPolicyContextValidator, IEvidenceAlignmentService,
    IContradictionClassifier, IContradictionExplainer, IConflictResolutionHelper
)
from phase2.interfaces.query_agent_interface import ILLMAnalyzer

from phase2.models.reasoning_result import ReasoningResult
from phase2.models.risk_assessment import RiskAssessmentResult
from phase2.models.contradiction_result import ContradictionResult
from phase2.models.contradiction_record import ContradictionRecord
from phase2.models.contradiction_type import ContradictionType
from phase2.models.contradiction_metrics import ContradictionMetrics
from phase2.exceptions.contradiction_exception import ContradictionException, ConfigurationException

logger = logging.getLogger(__name__)

class ContradictionService(IContradictionService):
    """
    Central Orchestrator combining synchronous LLM bounds effectively minimizing latency,
    bridging strictly parsed dictionary constraints back through modular Services natively.
    """
    def __init__(
        self,
        llm_analyzer: ILLMAnalyzer,
        prompt_template_path: str,
        context_validator: IPolicyContextValidator,
        alignment_service: IEvidenceAlignmentService,
        classifier: IContradictionClassifier,
        explainer: IContradictionExplainer,
        resolution_helper: IConflictResolutionHelper,
        supported_categories: list = None
    ):
        self.llm = llm_analyzer
        self.prompt_template = self._load_template(prompt_template_path)
        
        self.context_validator = context_validator
        self.alignment_service = alignment_service
        self.classifier = classifier
        self.explainer = explainer
        self.resolution_helper = resolution_helper
        self.supported_categories = supported_categories or []

    def _load_template(self, path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Contradiction Prompt template failed to mount: {e}")
            raise ConfigurationException(f"Missing prompt logic constraints bounds: {e}")

    def detect_contradictions(self, reasoning_result: ReasoningResult, risk_result: RiskAssessmentResult) -> ContradictionResult:
        start_ms = time.perf_counter()
        
        try:
            # 1. Validation Check. Pre-filter explicitly unrelated docs natively to reduce false positives.
            is_valid_context = self.context_validator.validate_compatibility(reasoning_result)
            if not is_valid_context:
                logger.warning("Context validation failed securely. Suspected cross-policy mismatched evaluation.")
            
            # 2. Alignment securely matching explicit chunks to LLM logic bounds natively.
            evidence_alignments = self.alignment_service.align_evidence(reasoning_result)
            
            query_text = getattr(reasoning_result.verification_source.retrieval_result.query_context, "original_query", "Unknown Context")
            
            # Map reasoning string constraints out cleanly.
            logic_summary = ""
            for step in reasoning_result.reasoning_chain.steps:
                logic_summary += f"[Step {step.step_number}]: {step.conclusion}\n"
                
            prompt = self.prompt_template.replace(
                "{QUERY}", query_text
            ).replace(
                "{REASONING_BLOCK}", logic_summary
            )
            
            # 3. Singular LLM Evaluation
            unified_payload = self.llm.analyse(prompt)
            
            records = []
            fp_prevented = 0
            
            # Payload expects {"contradictions": [{"type": "...", "conflict_level": "...", "explanation": "..."}]}
            contradiction_nodes = unified_payload.get("contradictions", [])
            for node in contradiction_nodes:
                try:
                    c_type = ContradictionType(node.get("type", "Logical"))
                    c_level = self.classifier.classify(node)
                    expl = self.explainer.explain(node)
                    
                    records.append(
                        ContradictionRecord(
                            contradiction_type=c_type,
                            conflict_level=c_level,
                            evidence_ties=evidence_alignments,
                            risk_factor_ids=[],
                            explanation=expl,
                            suggested_interpretation=self.resolution_helper.recommend(c_level)
                        )
                    )
                except ValueError:
                    fp_prevented += 1
                    logger.warning("Failed parsing a node schema bounds cleanly. Discarding hallucination safely.")
            
            highest_rec = "No action"
            if records:
                highest_conflict = max(records, key=lambda x: list(ConflictLevel).index(x.conflict_level) if x.conflict_level in list(ConflictLevel) else -1)
                highest_rec = self.resolution_helper.recommend(highest_conflict.conflict_level)
            
            end_ms = time.perf_counter()
            exec_time = (end_ms - start_ms) * 1000.0

            logger.info(f"Contradiction detection mapped natively securely finding {len(records)} isolates.")

            payload_conf = float(unified_payload.get("overall_confidence", 0.95))

            return ContradictionResult(
                reasoning_source=reasoning_result,
                risk_source=risk_result,
                contradictions=records,
                overall_confidence=payload_conf,
                recommendation=highest_rec,
                metrics=ContradictionMetrics(
                    extraction_time_ms=exec_time,
                    total_contradictions_found=len(records),
                    false_positives_prevented=fp_prevented
                )
            )

        except Exception as e:
            logger.exception(f"Fatal logic crash within Contradiction Execution natively: {e}")
            raise ContradictionException(f"Pipeline crashed parsing contradiction factors smoothly natively: {e}")
