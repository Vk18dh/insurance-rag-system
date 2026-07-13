import json
import logging
import time
from typing import Dict, Any

from phase2.interfaces.risk_agent_interface import (
    IRiskAssessmentService, IRiskAmbiguityDetector, ILegalSensitivityChecker, 
    IExclusionChecker, IRegulatoryChecker, IEscalationService
)
from phase2.interfaces.query_agent_interface import ILLMAnalyzer

from phase2.models.reasoning_result import ReasoningResult
from phase2.models.risk_assessment import RiskAssessmentResult
from phase2.models.risk_level import RiskLevel
from phase2.models.risk_processing_metrics import RiskProcessingMetrics
from phase2.exceptions.risk_exception import RiskException, ConfigurationException

logger = logging.getLogger(__name__)

class RiskAssessmentService(IRiskAssessmentService):
    """
    Central Orchestrator combining synchronous LLM bounds effectively minimizing latency,
    bridging strictly parsed dictionary constraints back through modular Services natively.
    """
    def __init__(
        self,
        llm_analyzer: ILLMAnalyzer,
        prompt_template_path: str,
        ambiguity_detector: IRiskAmbiguityDetector,
        legal_checker: ILegalSensitivityChecker,
        exclusion_checker: IExclusionChecker,
        regulatory_checker: IRegulatoryChecker,
        escalation_service: IEscalationService,
        supported_risk_categories: list = None
    ):
        self.llm = llm_analyzer
        self.prompt_template = self._load_template(prompt_template_path)
        
        self.ambiguity_detector = ambiguity_detector
        self.legal_checker = legal_checker
        self.exclusion_checker = exclusion_checker
        self.regulatory_checker = regulatory_checker
        self.escalation_service = escalation_service
        self.supported_risk_categories = supported_risk_categories or []

    def _load_template(self, path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Risk Prompt template failed to mount: {e}")
            raise ConfigurationException(f"Missing prompt logic constraints bounds: {e}")

    def assess_risk(self, reasoning_result: ReasoningResult) -> RiskAssessmentResult:
        start_ms = time.perf_counter()
        
        try:
            # 1. Format payload completely free from unverified documents cleanly.
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
            
            # 2. Singular < 1s LLM evaluation across 5 metrics securely.
            unified_risk_payload = self.llm.analyse(prompt)
            
            # 3. Synchronous Dictionary Dispatch parsing logic securely mapped.
            ambiguity_report = self.ambiguity_detector.detect(unified_risk_payload)
            legal_report = self.legal_checker.check(unified_risk_payload)
            exclusion_report = self.exclusion_checker.check(unified_risk_payload)
            regulatory_report = self.regulatory_checker.check(unified_risk_payload)
            escalation_report = self.escalation_service.evaluate(unified_risk_payload)
            
            # Count factors mapped truly natively.
            factors_detected = sum([
                1 if ambiguity_report.detected else 0,
                1 if legal_report.detected else 0,
                1 if exclusion_report.detected else 0,
                1 if regulatory_report.detected else 0
            ])
            
            # Parse overall Risk Level from High_risk
            high_risk_root = unified_risk_payload.get("high_risk", {})
            r_str = high_risk_root.get("risk_level", "LOW")
            try:
                ov_risk = RiskLevel(r_str)
            except ValueError:
                ov_risk = RiskLevel.LOW

            end_ms = time.perf_counter()
            exec_time = (end_ms - start_ms) * 1000.0

            logger.info(
                "Risk Analysis generation complete",
                extra={
                    "total_ms": exec_time,
                    "factors_detected": factors_detected,
                    "escalation": escalation_report.escalation_required
                }
            )

            return RiskAssessmentResult(
                reasoning_source=reasoning_result,
                overall_risk_level=ov_risk,
                ambiguity_report=ambiguity_report,
                legal_warnings=legal_report,
                regulatory_warnings=regulatory_report,
                exclusions_identified=exclusion_report,
                escalation=escalation_report,
                metrics=RiskProcessingMetrics(
                    execution_time_ms=exec_time,
                    risk_factors_detected=factors_detected
                )
            )

        except Exception as e:
            logger.exception(f"Fatal logic crash within Risk Execution natively: {e}")
            raise RiskException(f"Pipeline crashed organically generating factors seamlessly: {e}")
