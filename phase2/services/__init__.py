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
]
