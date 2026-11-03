"""
phase2.validation.tests.stress.test_stress
==========================================

Stress tests (oversized queries). System must degrade gracefully, not crash.
"""

import pytest
from phase2.validation.services import MockDataProvider
from backend.app.services.guardrail_service import GuardrailService

def test_stress_oversized_query_handling():
    """Verify that oversized stress queries degrade gracefully without throwing unhandled exceptions."""
    provider = MockDataProvider()
    stress_queries = provider.get_mock_queries("stress")
    assert len(stress_queries) > 0
    oversized_query = stress_queries[0]
    assert len(oversized_query) > 500

    is_safe, reason = GuardrailService.check_input(oversized_query)
    assert isinstance(is_safe, bool)
    assert isinstance(reason, str)
