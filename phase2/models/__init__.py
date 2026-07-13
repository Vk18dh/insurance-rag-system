"""
phase2.models — Public API exports.

Import from here to keep downstream imports stable when internal
module structure changes.

    from phase2.models import (
        IntentType, IntentResult,
        QueryClassification, AmbiguityInfo, QueryMetadata,
        ExtractedEntities, QueryContext,
    )
"""

from phase2.models.intent import IntentResult, IntentType
from phase2.models.query_context import ExtractedEntities, QueryContext
from phase2.models.query_metadata import AmbiguityInfo, QueryClassification, QueryMetadata

__all__ = [
    # intent
    "IntentType",
    "IntentResult",
    # query_metadata
    "QueryClassification",
    "AmbiguityInfo",
    "QueryMetadata",
    # query_context
    "ExtractedEntities",
    "QueryContext",
]
