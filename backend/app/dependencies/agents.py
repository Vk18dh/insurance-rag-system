import functools
from phase2.config.settings import Phase2Settings, get_settings
from phase2.orchestrator.orchestrator import AgentOrchestrator


@functools.lru_cache()
def _get_cached_agents_map():
    settings = get_settings()
    
    from phase2.agents.query_agent import QueryUnderstandingAgentFactory
    from phase2.services import QueryProcessingServiceFactory, RetrievalServiceFactory
    from phase2.agents.retrieval_agent import RetrievalAgentFactory
    from phase2.agents.verification_agent import VerificationAgentFactory
    from phase2.agents.reasoning_agent import ReasoningAgentFactory
    from phase2.agents.risk_agent import RiskAgentFactory
    from phase2.agents.contradiction_agent import ContradictionAgentFactory
    from phase2.agents.response_builder import ResponseBuilderFactory
    from phase2.services.query_processing_service import FallbackQueryAnalyzer

    query_service = QueryProcessingServiceFactory.create(settings)
    query_agent = QueryUnderstandingAgentFactory.create(settings, query_service)
    
    retrieval_service = RetrievalServiceFactory.create(settings)
    retrieval_agent = RetrievalAgentFactory.create(settings, retrieval_service)
    verification_agent = VerificationAgentFactory.create(settings)
    
    if settings.llm.provider.lower() in ("openrouter", "failover") or settings.llm.primary_provider.lower() in ("openrouter", "groq"):
        from phase2.services.llm_provider_manager import LLMProviderManager
        llm_analyzer = LLMProviderManager(settings=settings)
    else:
        llm_analyzer = FallbackQueryAnalyzer()
        
    reasoning_agent = ReasoningAgentFactory.create(settings, llm_analyzer)
    risk_agent = RiskAgentFactory.create(settings, llm_analyzer)
    contradiction_agent = ContradictionAgentFactory.create(settings, llm_analyzer)
    response_builder = ResponseBuilderFactory.create(settings, llm_analyzer)
    
    agents_map = {
        "QueryUnderstandingAgent": query_agent,
        "RetrievalAgent": retrieval_agent,
        "VerificationAgent": verification_agent,
        "ReasoningAgent": reasoning_agent,
        "RiskAssessmentAgent": risk_agent,
        "ContradictionAgent": contradiction_agent,
        "ResponseBuilder": response_builder
    }
    return agents_map

def get_agent_orchestrator() -> AgentOrchestrator:
    """
    Dependency generating a fresh Agent Orchestrator per request.
    This guarantees that the heavy AI initialization is cached in _get_cached_agents_map,
    but stateful components like ContextManager and MetricsCollector are isolated per request.
    """
    settings = get_settings()
    agents_map = _get_cached_agents_map()
    
    from phase2.orchestrator.workflow_engine import WorkflowEngine
    from phase2.orchestrator.execution_manager import ExecutionManager
    from phase2.orchestrator.context_manager import ContextManager
    from phase2.orchestrator.retry_manager import RetryManager
    from phase2.orchestrator.timeout_manager import TimeoutManager
    from phase2.orchestrator.metrics_collector import MetricsCollector

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
        agents_map=agents_map,
        observability=None,
        workflow_timeout_ms=settings.orchestrator.max_workflow_timeout_ms
    )
    
    return orchestrator
