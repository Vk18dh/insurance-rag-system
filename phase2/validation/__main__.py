"""
phase2.validation.__main__
==========================

CLI entry point for the Agentic RAG Validation Suite.

Usage:
    python -m phase2.validation
"""

import sys
import os
from .runner import ValidationRunner, PytestRunner
from .services import JsonReportGenerator, MarkdownReportGenerator
from .models import TestScenario, ValidationCategory
from .config.validation_settings import ValidationSettings
from .logger import logger

def main():
    logger.info("Initializing Agentic RAG Validation Suite...")
    
    settings = ValidationSettings.load_from_yaml()
    logger.info("Loaded ValidationSettings successfully.")
    
    # 1. Initialize Runners
    base_test_dir = "phase2/validation/tests"
    pytest_runner = PytestRunner(base_test_dir=base_test_dir)
    runners = [pytest_runner]
    
    # 2. Initialize Generators
    generators = []
    if settings.generate_json:
        generators.append(JsonReportGenerator())
    if settings.generate_markdown:
        generators.append(MarkdownReportGenerator())
        
    # 3. Create Orchestrator
    orchestrator = ValidationRunner(
        runners=runners,
        report_generators=generators,
        environment=os.getenv("FASTAPI_ENV", "development"),
        version="Phase2-Part10"
    )
    
    # 4. Generate Scenarios
    scenarios = [
        TestScenario(category=ValidationCategory.UNIT, max_retries=1),
        TestScenario(category=ValidationCategory.INTEGRATION, max_retries=1),
        TestScenario(category=ValidationCategory.SYSTEM, max_retries=1),
        TestScenario(category=ValidationCategory.PERFORMANCE, max_retries=1),
        TestScenario(category=ValidationCategory.STRESS, max_retries=1),
        TestScenario(category=ValidationCategory.CONCURRENCY, max_retries=1),
        TestScenario(category=ValidationCategory.SECURITY, max_retries=1),
        TestScenario(category=ValidationCategory.REGRESSION, max_retries=1),
        TestScenario(category=ValidationCategory.RECOVERY, max_retries=1),
        TestScenario(category=ValidationCategory.DEPLOYMENT, max_retries=1),
    ]
    
    logger.info(f"Executing {len(scenarios)} validation categories...")
    
    # 5. Execute
    success = orchestrator.execute_suite(
        scenarios=scenarios, 
        output_dir=settings.reports_output_dir
    )
    
    if success:
        logger.info("✅ VALIDATION SUITE PASSED SUCCESSFULLY.")
        sys.exit(0)
    else:
        logger.error("❌ VALIDATION SUITE FAILED. Check reports for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
