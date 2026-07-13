"""
phase2.services — Public service exports.

Part 1: QueryProcessingService, QueryProcessingServiceFactory
Part 2: RetrievalService, RetrievalServiceFactory, ReRankingService, RetrievalValidationService (new)
"""

from phase2.services.query_processing_service import (
    FallbackQueryAnalyzer,
    GeminiQueryAnalyzer,
    QueryProcessingService,
    QueryProcessingServiceFactory,
)
from phase2.services.retrieval_service import (
    Phase1RetrieverAdapter,
    RetrievalService,
    RetrievalServiceFactory,
)
from phase2.services.ranking_service import WeightedRankingService
from phase2.services.retrieval_validation_service import RetrievalValidationService

# Part 3 (new)
from phase2.services.citation_validator import CitationValidator
from phase2.services.completeness_checker import CompletenessChecker
from phase2.services.consistency_checker import ConsistencyChecker
from phase2.services.evidence_validator import EvidenceValidator
from phase2.services.relevance_checker import RelevanceChecker

# Phase 2 Part 4 (Reasoning Agent) Services
from phase2.services.clause_interpreter import ClauseInterpreter
from phase2.services.evidence_linker import EvidenceLinker
from phase2.services.reasoning_chain_builder import ReasoningChainBuilder
from phase2.services.explanation_service import ExplanationService

# Part 5 services (new)
from phase2.services.ambiguity_detector import AmbiguityDetector
from phase2.services.legal_sensitivity_checker import LegalSensitivityChecker
from phase2.services.exclusion_checker import ExclusionChecker
from phase2.services.regulatory_checker import RegulatoryChecker
from phase2.services.escalation_service import EscalationService

# Part 6 services
from phase2.services.policy_context_validator import PolicyContextValidator
from phase2.services.evidence_alignment_service import EvidenceAlignmentService
from phase2.services.contradiction_classifier import ContradictionClassifier
from phase2.services.contradiction_explainer import ContradictionExplainer
from phase2.services.conflict_resolution_helper import ConflictResolutionHelper
from phase2.services.contradiction_service import ContradictionService
from phase2.services.risk_assessment_service import RiskAssessmentService

__all__ = [
    # Part 1
    "FallbackQueryAnalyzer",
    "GeminiQueryAnalyzer",
    "QueryProcessingService",
    "QueryProcessingServiceFactory",
    # Part 2
    "Phase1RetrieverAdapter",
    "RetrievalService",
    "RetrievalServiceFactory",
    "WeightedRankingService",
    "RetrievalValidationService",
    # Part 3
    "CitationValidator",
    "CompletenessChecker",
    "ConsistencyChecker",
    "EvidenceValidator",
    "RelevanceChecker",
    
    # Part 4
    "ClauseInterpreter",
    "EvidenceLinker",
    "ReasoningChainBuilder",
    "ExplanationService",
    # Part 5
    "AmbiguityDetector",
    "LegalSensitivityChecker",
    "ExclusionChecker",
    "RegulatoryChecker",
    "EscalationService",
    "RiskAssessmentService",
]
