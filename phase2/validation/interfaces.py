"""
phase2.validation.interfaces
============================

Abstract base classes and protocols defining the contracts for the Validation Suite.
This ensures strict adherence to Dependency Inversion and Interface Segregation principles.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from phase2.validation.models import (
    TestScenario,
    CategoryResult,
    ValidationReport,
    ValidationCategory
)


class ITestRunner(ABC):
    """
    Contract for running specific validation test suites (e.g., Performance, Security).
    """

    @abstractmethod
    def run(self, scenario: TestScenario) -> CategoryResult:
        """
        Execute the testing strategy defined by the given scenario.
        
        Args:
            scenario (TestScenario): Configuration and thresholds for this test run.
            
        Returns:
            CategoryResult: Structured results of the execution.
        """
        pass

    @abstractmethod
    def supports(self, category: ValidationCategory) -> bool:
        """
        Check if this runner handles a specific ValidationCategory.
        
        Args:
            category (ValidationCategory): The category to check.
            
        Returns:
            bool: True if supported.
        """
        pass


class IReportGenerator(ABC):
    """
    Contract for generating outputs from ValidationReports.
    """

    @abstractmethod
    def generate(self, report: ValidationReport, output_dir: str) -> str:
        """
        Convert a structured ValidationReport into a specific format and save it.
        
        Args:
            report (ValidationReport): The full test suite results.
            output_dir (str): Where to save the generated file.
            
        Returns:
            str: Path to the generated report file.
        """
        pass


class IMockDataProvider(ABC):
    """
    Contract for supplying simulated or extreme edge-case data for testing resilience.
    """

    @abstractmethod
    def get_mock_queries(self, scenario_type: str = "standard") -> List[str]:
        """Fetch a list of queries matching a specific scenario type."""
        pass

    @abstractmethod
    def get_malicious_payloads(self) -> List[str]:
        """Fetch known prompt injection strings or malformed inputs."""
        pass

    @abstractmethod
    def get_mock_documents(self, count: int) -> List[Dict[str, Any]]:
        """Fetch synthetic document structures for mocking the Retrieval output."""
        pass
