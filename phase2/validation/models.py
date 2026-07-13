"""
phase2.validation.models
========================

Dataclasses and Pydantic models used by the Validation Suite.

These models define the structure of a test scenario, the metrics 
recorded during execution, and the final unified report generated 
by the ValidationRunner.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ValidationCategory(str, Enum):
    """Categories of tests supported by the validation suite."""
    UNIT = "unit"
    INTEGRATION = "integration"
    SYSTEM = "system"
    PERFORMANCE = "performance"
    STRESS = "stress"
    CONCURRENCY = "concurrency"
    SECURITY = "security"
    REGRESSION = "regression"
    RECOVERY = "recovery"
    DEPLOYMENT = "deployment"


class TestScenario(BaseModel):
    """
    Configuration parameters for a specific category test execution.
    Usually populated from ValidationSettings.
    """
    category: ValidationCategory
    target_module: Optional[str] = None
    concurrent_users: int = Field(default=1, ge=1)
    duration_seconds: int = Field(default=0, ge=0)
    max_retries: int = Field(default=3, ge=0)


class PerformanceMetrics(BaseModel):
    """
    Metrics collected during performance, load, and stress test runs.
    """
    total_requests: int = Field(default=0, ge=0)
    successful_requests: int = Field(default=0, ge=0)
    failed_requests: int = Field(default=0, ge=0)
    avg_latency_ms: float = Field(default=0.0, ge=0.0)
    p95_latency_ms: float = Field(default=0.0, ge=0.0)
    p99_latency_ms: float = Field(default=0.0, ge=0.0)
    throughput_rps: float = Field(default=0.0, ge=0.0)
    max_memory_mb: Optional[float] = Field(default=None, ge=0.0)
    max_cpu_percent: Optional[float] = Field(default=None, ge=0.0)


class SecurityAuditResult(BaseModel):
    """
    Specific outcome detail for security and resilience testing.
    """
    vulnerability_type: str
    passed: bool
    details: str
    severity: str = Field(default="LOW")


class CategoryResult(BaseModel):
    """
    The result of running a specific ValidationCategory.
    """
    category: ValidationCategory
    passed: bool
    total_tests: int = Field(default=0, ge=0)
    passed_tests: int = Field(default=0, ge=0)
    failed_tests: int = Field(default=0, ge=0)
    skipped_tests: int = Field(default=0, ge=0)
    duration_seconds: float = Field(default=0.0, ge=0.0)
    performance_metrics: Optional[PerformanceMetrics] = None
    security_results: List[SecurityAuditResult] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class ValidationReport(BaseModel):
    """
    The unified root report summarizing the execution of the Validation Suite.
    """
    timestamp_utc: datetime = Field(default_factory=datetime.utcnow)
    overall_passed: bool
    total_duration_seconds: float = Field(default=0.0, ge=0.0)
    categories: Dict[ValidationCategory, CategoryResult] = Field(default_factory=dict)
    environment: str = Field(default="development")
    version: str = Field(default="1.0.0")
    
    def add_category_result(self, result: CategoryResult) -> None:
        self.categories[result.category] = result
        if not result.passed:
            self.overall_passed = False
