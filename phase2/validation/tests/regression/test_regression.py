"""
phase2.validation.tests.regression.test_regression
==================================================

Verify backward compatibility with Phase 1 components.
"""

import pytest
from phase2.models.intent import IntentResult, IntentType
from phase2.models.query_metadata import QueryMetadata

from phase2.models.query_context import QueryContext

def test_backward_compatibility():
    """Verify backward compatibility of domain models with legacy field mappings."""
    legacy_data = {
        "primary_intent": "benefits",
        "confidence": 0.88,
        "reasoning": "Legacy schema format test"
    }
    result = IntentResult.model_validate(legacy_data)
    assert result.intent == IntentType.BENEFITS
    assert result.confidence == 0.88

    ctx = QueryContext(original_query="What is the surrender value?", normalized_query="what is surrender value")
    assert ctx.original_query == "What is the surrender value?"
    assert ctx.normalized_query == "what is surrender value"
