"""
phase2.models — Public model exports.

Part 1 models (QueryContext, IntentResult, etc.) are already exported here.
Part 2 adds: RetrievedChunk, RetrievalResult, RetrievalMetrics.
"""

# Part 1 models (unchanged)
from phase2.models.intent import IntentResult, IntentType
from phase2.models.query_context import ExtractedEntities, QueryContext
from phase2.models.query_metadata import AmbiguityInfo, QueryClassification, QueryMetadata

# Part 2 models (new)
from phase2.models.retrieved_chunk import RetrievalSource, RetrievedChunk
from phase2.models.retrieval_metrics import RetrievalMetrics
from phase2.models.retrieval_result import RetrievalResult, RetrievalWarning

# Part 3 models (new)
from phase2.models.evidence_score import EvidenceScore
from phase2.models.validation_metrics import ValidationMetrics
from phase2.models.verification_report import VerificationReport, VerificationStatus, VerificationWarning
from phase2.models.verification_result import VerificationResult

__all__ = [
    # Part 1
    "IntentResult",
    "IntentType",
    "ExtractedEntities",
    "QueryContext",
    "AmbiguityInfo",
    "QueryClassification",
    "QueryMetadata",
    # Part 2
    "RetrievalSource",
    "RetrievedChunk",
    "RetrievalMetrics",
    "RetrievalResult",
    "RetrievalWarning",
    # Part 3
    "EvidenceScore",
    "ValidationMetrics",
    "VerificationReport",
    "VerificationStatus",
    "VerificationWarning",
    "VerificationResult",
]
