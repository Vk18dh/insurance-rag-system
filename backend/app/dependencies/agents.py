import functools
from phase2.config.settings import Phase2Settings
from phase2.orchestrator.orchestrator import AgentOrchestrator


@functools.lru_cache()
def get_agent_orchestrator() -> AgentOrchestrator:
    """
    Dependency generating or returning the singleton Agent Orchestrator.
    This guarantees that the heavy AI initialization doesn't occur blocking the event loop on every request.
    
    Since Part 11 mandates strict zero modifications to Phase 2, we initialize it using Phase 2's native structure.
    """
    settings = Phase2Settings()
    from phase2.config.settings import get_settings
    from phase2.agents.query_agent import QueryUnderstandingAgentFactory
    from phase2.services.query_processing_service import QueryProcessingServiceFactory, OpenRouterQueryAnalyzer
    from phase2.services.retrieval_service import RetrievalServiceFactory
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

    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    from phase2.config.settings import get_settings
    phase2_settings = get_settings()
    
    from pathlib import Path
    prompt_path = Path(phase2_settings.query_agent.prompt_template_path)
    prompt_template = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else "Missing Template"
    
    query_service = QueryProcessingServiceFactory.create(phase2_settings)
    query_agent = QueryUnderstandingAgentFactory.create(phase2_settings, query_service)
    
    retrieval_service = RetrievalServiceFactory.create(phase2_settings)
    retrieval_agent = RetrievalAgentFactory.create(phase2_settings, retrieval_service)
    verification_agent = VerificationAgentFactory.create(phase2_settings)
    
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    llm_analyzer = OpenRouterQueryAnalyzer(
        api_key=api_key,
        model_name=os.environ.get("PHASE2__LLM__MODEL_NAME", "openai/gpt-4o-mini"),
        prompt_template=prompt_template,
        supported_intents=phase2_settings.query_agent.supported_intents,
        timeout_seconds=phase2_settings.llm.timeout_seconds,
        max_retries=phase2_settings.llm.max_retries,
        temperature=phase2_settings.llm.temperature,
        max_output_tokens=phase2_settings.llm.max_output_tokens,
        base_delay_seconds=1.0,
        max_delay_seconds=phase2_settings.llm.timeout_seconds,
    )
    reasoning_agent = ReasoningAgentFactory.create(phase2_settings, llm_analyzer)
    risk_agent = RiskAgentFactory.create(phase2_settings, llm_analyzer)
    contradiction_agent = ContradictionAgentFactory.create(phase2_settings, llm_analyzer)
    response_builder = ResponseBuilderFactory.create(phase2_settings)
    
    agents_map = {
        "QueryUnderstandingAgent": query_agent,
        "RetrievalAgent": retrieval_agent,
        "VerificationAgent": verification_agent,
        "ReasoningAgent": reasoning_agent,
        "RiskAssessmentAgent": risk_agent,
        "ContradictionAgent": contradiction_agent,
        "ResponseBuilder": response_builder
    }
    
    workflow_engine = WorkflowEngine(phase2_settings.orchestrator.execution_sequence)
    context_manager = ContextManager()
    metrics_collector = MetricsCollector()
    timeout_manager = TimeoutManager()
    retry_manager = RetryManager()
    
    execution_manager = ExecutionManager(
        timeout_manager=timeout_manager,
        retry_manager=retry_manager,
        timeout_ms=phase2_settings.orchestrator.agent_timeout_ms,
        max_retries=phase2_settings.orchestrator.max_retries,
        retry_delay_ms=phase2_settings.orchestrator.retry_delay_ms
    )
    
    orchestrator = AgentOrchestrator(
        workflow_engine=workflow_engine,
        execution_manager=execution_manager,
        context_manager=context_manager,
        metrics_collector=metrics_collector,
        agents_map=agents_map
    )
    
    return orchestrator
