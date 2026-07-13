import os
import json
import logging
from phase2.config.settings import get_settings

# Force offline mapping securely natively
os.environ["PHASE2__LLM__PROVIDER"] = "offline"
os.environ["PHASE2__ENVIRONMENT"] = "testing"

from phase2.agents.query_agent import QueryUnderstandingAgentFactory
from phase2.services.query_processing_service import FallbackQueryAnalyzer
from phase2.services import QueryProcessingServiceFactory, RetrievalServiceFactory
from phase2.agents.retrieval_agent import RetrievalAgentFactory
from phase2.agents.verification_agent import VerificationAgentFactory
from phase2.agents.reasoning_agent import ReasoningAgentFactory
from phase2.agents.risk_agent import RiskAgentFactory
from phase2.agents.contradiction_agent import ContradictionAgentFactory
from phase2.agents.response_builder import ResponseBuilderFactory

from phase2.orchestrator.orchestrator import AgentOrchestrator
from phase2.orchestrator.workflow_engine import WorkflowEngine
from phase2.orchestrator.execution_manager import ExecutionManager
from phase2.orchestrator.context_manager import ContextManager
from phase2.orchestrator.retry_manager import RetryManager
from phase2.orchestrator.timeout_manager import TimeoutManager
from phase2.orchestrator.metrics_collector import MetricsCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("e2e_driver")

def run():
    settings = get_settings()
    logger.info("Initializing Agent dependency injection cleanly...")
    
    query_service = QueryProcessingServiceFactory.create(settings)
    query_agent = QueryUnderstandingAgentFactory.create(settings, query_service)
    
    retrieval_service = RetrievalServiceFactory.create(settings)
    retrieval_agent = RetrievalAgentFactory.create(settings, retrieval_service)
    verification_agent = VerificationAgentFactory.create(settings)
    
    llm_analyzer = FallbackQueryAnalyzer()
    reasoning_agent = ReasoningAgentFactory.create(settings, llm_analyzer)
    risk_agent = RiskAgentFactory.create(settings, llm_analyzer)
    contradiction_agent = ContradictionAgentFactory.create(settings, llm_analyzer)
    response_builder = ResponseBuilderFactory.create(settings)
    
    agents_map = {
        "QueryUnderstandingAgent": query_agent,
        "RetrievalAgent": retrieval_agent,
        "VerificationAgent": verification_agent,
        "ReasoningAgent": reasoning_agent,
        "RiskAssessmentAgent": risk_agent,
        "ContradictionAgent": contradiction_agent,
        "ResponseBuilder": response_builder
    }
    
    logger.info("Initializing Orchestrator dependencies natively...")
    workflow_engine = WorkflowEngine(settings.orchestrator.execution_sequence)
    context_manager = ContextManager()
    metrics_collector = MetricsCollector()
    timeout_manager = TimeoutManager()
    retry_manager = RetryManager()
    
    execution_manager = ExecutionManager(
        timeout_manager=timeout_manager,
        retry_manager=retry_manager,
        timeout_ms=settings.orchestrator.agent_timeout_ms,
        max_retries=settings.orchestrator.max_retries,
        retry_delay_ms=settings.orchestrator.retry_delay_ms
    )
    
    orchestrator = AgentOrchestrator(
        workflow_engine=workflow_engine,
        execution_manager=execution_manager,
        context_manager=context_manager,
        metrics_collector=metrics_collector,
        agents_map=agents_map
    )
    
    logger.info("Starting pipeline trajectory reliably...")
    result = orchestrator.orchestrate("What is the waiting period for pre-existing conditions?")
    
    print("\n--- E2E Orchestrator Result ---")
    print(f"UUID: {result.request_id}")
    print(f"Status: {result.overall_status.value}")
    print(f"Total Time: {result.metrics.total_execution_time_ms:.2f}ms")
    print(f"Errors: {result.errors}")
    print(f"Execution Output Nodes:")
    for step in result.execution_history:
        print(f"  [{step.status.value}] {step.agent_name} -> {step.duration_ms:.2f}ms, Retries: {step.retry_count}")

if __name__ == "__main__":
    run()
