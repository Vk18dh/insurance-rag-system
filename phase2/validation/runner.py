"""
phase2.validation.runner
========================

The core orchestrator of the Validation Suite. 
Runs test categories, aggregates results, and invokes ReportGenerators.
"""

import sys
import time
import pytest
from typing import List, Dict

from phase2.validation.interfaces import ITestRunner, IReportGenerator
from phase2.validation.models import (
    ValidationReport, 
    CategoryResult, 
    TestScenario, 
    ValidationCategory
)


class PytestRunner(ITestRunner):
    """
    Executes standard pytest suites programmatically for specific categories.
    """
    
    def __init__(self, base_test_dir: str):
        self.base_test_dir = base_test_dir
        
    def supports(self, category: ValidationCategory) -> bool:
        # We drive all these categories via pytest
        return category in {
            ValidationCategory.UNIT, 
            ValidationCategory.INTEGRATION, 
            ValidationCategory.SYSTEM,
            ValidationCategory.PERFORMANCE,
            ValidationCategory.STRESS,
            ValidationCategory.CONCURRENCY,
            ValidationCategory.REGRESSION,
            ValidationCategory.RECOVERY,
            ValidationCategory.SECURITY,
            ValidationCategory.DEPLOYMENT
        }

    def run(self, scenario: TestScenario) -> CategoryResult:
        start_time = time.time()
        
        # Path targeting e.g. "phase2/validation/tests/unit"
        test_path = f"{self.base_test_dir}/{scenario.category.value}"
        
        # We capture output to avoid polluting stdout during automated runs
        pytest_args = [test_path, "-v", "--tb=short", "--disable-warnings"]
        
        class ExitCodeTracker:
            def __init__(self):
                self.passed = 0
                self.failed = 0
                self.skipped = 0
                
            def pytest_runtest_logreport(self, report):
                if report.when == "call":
                    if report.passed:
                        self.passed += 1
                    elif report.failed:
                        self.failed += 1
                    elif report.skipped:
                        self.skipped += 1

        tracker = ExitCodeTracker()
        
        exit_code = pytest.main(pytest_args, plugins=[tracker])
        
        duration = time.time() - start_time
        passed = (exit_code == pytest.ExitCode.OK or exit_code == pytest.ExitCode.NO_TESTS_COLLECTED)
        
        # Determine total tests dynamically from plugin tracking
        total = tracker.passed + tracker.failed + tracker.skipped
        
        return CategoryResult(
            category=scenario.category,
            passed=passed,
            total_tests=total,
            passed_tests=tracker.passed,
            failed_tests=tracker.failed,
            skipped_tests=tracker.skipped,
            duration_seconds=duration,
        )


class ValidationRunner:
    """
    Main orchestrator for the entire validation suite.
    Iterates through scenarios, uses the correct runner, aggregates into a ValidationReport,
    and runs the configured report generators.
    """
    
    def __init__(
        self, 
        runners: List[ITestRunner], 
        report_generators: List[IReportGenerator],
        environment: str = "production",
        version: str = "1.0.0"
    ):
        self.runners = runners
        self.report_generators = report_generators
        self.environment = environment
        self.version = version

    def execute_suite(self, scenarios: List[TestScenario], output_dir: str) -> bool:
        """
        Execute a complete validation run against a list of scenarios.
        
        Returns: True if all passed, False otherwise.
        """
        report = ValidationReport(
            overall_passed=True, 
            environment=self.environment, 
            version=self.version
        )
        
        start_time = time.time()
        
        for scenario in scenarios:
            # Find appropriate runner
            runner = next((r for r in self.runners if r.supports(scenario.category)), None)
            
            if not runner:
                # Fallback record error
                report.add_category_result(CategoryResult(
                    category=scenario.category,
                    passed=False,
                    errors=[f"No runner found for category: {scenario.category.value}"]
                ))
                continue
                
            # Execute
            try:
                result = runner.run(scenario)
                report.add_category_result(result)
            except Exception as e:
                report.add_category_result(CategoryResult(
                    category=scenario.category,
                    passed=False,
                    errors=[f"Runner exception: {str(e)}"]
                ))
                
        report.total_duration_seconds = time.time() - start_time
        
        # Generate outputs
        for generator in self.report_generators:
            generator.generate(report, output_dir)
            
        return report.overall_passed
