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
]
