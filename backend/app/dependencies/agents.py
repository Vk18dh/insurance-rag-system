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
    
    # In a full deployment, these agents would be wired via absolute imports directly from Phase 2.
    # To keep this testable and avoid circular/missing imports if Phase 2 parts are detached,
    # we instantiate it gracefully here using Phase 2's expected signature.
    from phase2.agents.query_agent import QueryUnderstandingAgentFactory
    from phase2.services import QueryProcessingServiceFactory, RetrievalServiceFactory
    from phase2.agents.retrieval_agent import RetrievalAgentFactory
    from phase2.agents.verification_agent import VerificationAgentFactory
    from phase2.agents.reasoning_agent import ReasoningAgentFactory
    from phase2.agents.risk_agent import RiskAgentFactory
    from phase2.agents.contradiction_agent import ContradictionAgentFactory
    from phase2.agents.response_builder import ResponseBuilderFactory
    from phase2.services.query_processing_service import FallbackQueryAnalyzer
    from phase2.orchestrator.workflow_engine import WorkflowEngine
    from phase2.orchestrator.execution_manager import ExecutionManager
    from phase2.orchestrator.context_manager import ContextManager
    from phase2.orchestrator.retry_manager import RetryManager
    from phase2.orchestrator.timeout_manager import TimeoutManager
    from phase2.orchestrator.metrics_collector import MetricsCollector

    query_service = QueryProcessingServiceFactory.create(settings)
    query_agent = QueryUnderstandingAgentFactory.create(settings, query_service)
    
    retrieval_service = RetrievalServiceFactory.create(settings)
    retrieval_agent = RetrievalAgentFactory.create(settings, retrieval_service)
    verification_agent = VerificationAgentFactory.create(settings)
    
    # We load the real analyzer or fallback depending on what factory chooses, but
    # for simplicity if a generic analyzer interface is needed, FallbackQueryAnalyzer is a stand-in
    # Wait, usually the factory doesn't need an explicit 'analyzer' if it creates it.
    # The E2E test passed FallbackQueryAnalyzer manually. Let's use it for the LLM based agents to ensure it loads natively.
    # Use GenericOpenRouterExecutor for reasoning if openrouter provider is set
    if settings.llm.provider.lower() == "openrouter":
        from phase2.services.llm_adapters import GenericOpenRouterExecutor
        llm_analyzer = GenericOpenRouterExecutor(
            api_key=settings.llm.api_key,
            model_name=settings.llm.model_name
        )
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
    
    workflow_engine = WorkflowEngine(settings.orchestrator.execution_sequence)
    context_manager = ContextManager()
    metrics_collector = MetricsCollector()
    timeout_manager = TimeoutManager()
    retry_manager = RetryManager()
    
    execution_manager = ExecutionManager(
        timeout_manager=timeout_manager,
        retry_manager=retry_manager,
        timeout_ms=settings.orchestrator.max_workflow_timeout_ms,
        max_retries=settings.orchestrator.max_retries,
        retry_delay_ms=settings.orchestrator.retry_delay_ms
    )
    
    orchestrator = AgentOrchestrator(
        workflow_engine=workflow_engine,
        execution_manager=execution_manager,
        context_manager=context_manager,
        metrics_collector=metrics_collector,
        agents_map=agents_map,
        observability=None
    )
    
    return orchestrator
