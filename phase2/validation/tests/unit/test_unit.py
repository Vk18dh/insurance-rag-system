"""
phase2.validation.tests.unit.test_unit
======================================

Validates independent business logic elements (Unit Testing).
"""

import pytest
from datetime import datetime
from phase2.validation.models import (
    ValidationCategory,
    TestScenario,
    PerformanceMetrics,
    CategoryResult,
    ValidationReport
)
from phase2.validation.services import MockDataProvider, JsonReportGenerator

def test_validation_layer_unit():
    """Validate data integrity and defaults of validation domain models."""
    scenario = TestScenario(category=ValidationCategory.UNIT, concurrent_users=2)
    assert scenario.category == ValidationCategory.UNIT
    assert scenario.concurrent_users == 2
    assert scenario.max_retries == 3

    metrics = PerformanceMetrics(total_requests=10, successful_requests=9, failed_requests=1, avg_latency_ms=12.5)
    assert metrics.total_requests == 10
    assert metrics.successful_requests == 9
    assert metrics.failed_requests == 1
    assert metrics.avg_latency_ms == 12.5

def test_validation_block_exists():
    """Validate mock data provider and category reporting serialization."""
    provider = MockDataProvider()
    standard_queries = provider.get_mock_queries("standard")
    assert len(standard_queries) == 3
    assert any("Jeevan Anand" in q for q in standard_queries)

    cat_result = CategoryResult(
        category=ValidationCategory.UNIT,
        passed=True,
        total_tests=2,
        passed_tests=2,
        failed_tests=0,
        skipped_tests=0,
        duration_seconds=0.05
    )
    assert cat_result.passed is True
    assert cat_result.total_tests == cat_result.passed_tests + cat_result.failed_tests
