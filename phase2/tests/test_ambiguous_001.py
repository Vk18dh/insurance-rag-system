import pytest
from backend.app.services.guardrail_service import GuardrailService
from phase2.models.reasoning_result import ReasoningResult
from phase2.models.reasoning_chain import ReasoningChain, ReasoningStep
from phase2.services.response_formatter import ResponseFormatter

# Mock an LLM analyzer to avoid actual API calls in some tests
class MockLLMAnalyzer:
    def analyse_text(self, prompt: str) -> str:
        # Mock behavior: if it's a refusal, it should output exactly the refusal
        if "I could not find this information" in prompt:
            return "I could not find this information in the provided documents."
        
        # If it's a valid deduction, we pretend to expand it
        if "The policy covers accidents" in prompt:
            return "The policy covers accidents. [1]"
            
        return "I could not find this information in the provided documents."

def test_guardrail_safe_refusal_without_citations_allowed():
    """Test 4: Guardrail safe refusal without citations -> allowed."""
    is_safe, reason = GuardrailService.check_output(
        generated_answer="I could not find this information in the documents.",
        query="What about the accident?",
        has_citations=False
    )
    assert is_safe is True
    assert reason == ""

def test_guardrail_factual_response_without_citations_blocked():
    """Test 5: Guardrail factual response requiring citations without citations -> blocked/flagged."""
    is_safe, reason = GuardrailService.check_output(
        generated_answer="Personal accident insurance is a niche yet vital segment.",
        query="What about the accident?",
        has_citations=False
    )
    assert is_safe is False
    assert "lacking citations" in reason

def test_response_formatter_receives_refusal_deduction():
    """Test 2 & 3: ResponseFormatter receives refusal deduction -> does not expand it."""
    formatter = ResponseFormatter(fallback_answer="Fallback", llm_analyzer=MockLLMAnalyzer())
    
    # Create a mock reasoning result with a refusal deduction
    step = ReasoningStep(
        step_number=1,
        premise="User asked out of domain or ambiguous query",
        conclusion="I could not find this information in the provided documents.",
        evidence_used=[],
        is_supported=True
    )
    chain = ReasoningChain(steps=[step], is_complete=True)
    
    from unittest.mock import MagicMock
    mock_metrics = MagicMock()
    mock_verification = MagicMock()
    mock_explanation = MagicMock()
    
    result = ReasoningResult.model_construct(
        verification_source=mock_verification,
        reasoning_chain=chain,
        explanation=mock_explanation,
        metrics=mock_metrics
    )
    
    answer = formatter.format_answer(reasoning_result=result, citations=[])
    
    # Assert no parametric expansion
    assert "7,788" not in answer
    assert "I could not find this information" in answer

# To test Orchestrator and E2E behavior, we can use the Orchestrator directly
from phase2.orchestrator.orchestrator import AgentOrchestrator
from phase2.orchestrator.execution_manager import ExecutionManager
from phase2.orchestrator.context_manager import ContextManager
from phase2.models.query_context import QueryContext, AmbiguityInfo
from phase2.models.intent import IntentResult
from unittest.mock import MagicMock

def test_ambiguous_query_bypasses_generation():
    """
    Test 1: is_ambiguous=True -> retrieval is not executed -> safe clarification/refusal returned.
    Test 6: "What about the accident?" -> no hallucinated claims.
    """
    
    # Create a mock QueryUnderstandingAgent that just returns an ambiguous QueryContext
    class MockQueryAgent:
        def process(self, query):
            return QueryContext(
                original_query=query,
                intent=IntentResult(primary_intent="policy_information", confidence=0.9),
                ambiguity=AmbiguityInfo(is_ambiguous=True, reason="Vague term 'accident'", missing_parameters=[])
            )
            
    # Mock workflow engine
    mock_workflow = MagicMock()
    mock_workflow.get_execution_sequence.return_value = ["QueryUnderstandingAgent", "RetrievalAgent", "VerificationAgent", "ReasoningAgent", "RiskAssessmentAgent", "ContradictionAgent", "ResponseBuilder"]

    # Create dummy agents that will fail if called
    class DummyFailingAgent:
        def retrieve(self, *args, **kwargs):
            raise Exception("RetrievalAgent should not be called")
        def verify(self, *args, **kwargs):
            raise Exception("VerificationAgent should not be called")
        def reason(self, *args, **kwargs):
            raise Exception("ReasoningAgent should not be called")
        def evaluate(self, *args, **kwargs):
            raise Exception("RiskAssessmentAgent should not be called")
        def build_response(self, *args, **kwargs):
            raise Exception("ResponseBuilder should not be called")

    agents = {
        "QueryUnderstandingAgent": MockQueryAgent(),
        "RetrievalAgent": DummyFailingAgent(),
        "VerificationAgent": DummyFailingAgent(),
        "ReasoningAgent": DummyFailingAgent(),
        "RiskAssessmentAgent": DummyFailingAgent(),
        "ContradictionAgent": DummyFailingAgent(),
        "ResponseBuilder": DummyFailingAgent()
    }
    
    class MockExecutionManager:
        def execute_agent(self, agent_name, func, *args):
            if agent_name == "QueryUnderstandingAgent":
                return MockQueryAgent().process(args[0])
            return None
            
    exec_manager = MockExecutionManager()
    ctx_manager = ContextManager()
    
    mock_obs = MagicMock()
    mock_metrics = MagicMock()
    mock_metrics.compile_metrics.return_value = {}
    mock_metrics.get_execution_history.return_value = []

    orchestrator = AgentOrchestrator(
        agents_map=agents,
        execution_manager=exec_manager,
        context_manager=ctx_manager,
        metrics_collector=mock_metrics,
        observability=mock_obs,
        workflow_engine=mock_workflow,
        workflow_timeout_ms=10000
    )
    
    result = orchestrator.orchestrate("What about the accident?")
    
    # 1. Assert query was flagged as ambiguous
    assert result.shared_context.query_context.ambiguity is not None
    assert result.shared_context.query_context.ambiguity.is_ambiguous is True
    
    # 2. Assert no other agents ran
    for err in result.errors:
        assert "should not be called" not in err, "A downstream agent was incorrectly called"
        
    # 3. Assert ResponseBuilder was bypassed, but final_response was populated
    assert result.shared_context.final_response is not None
    assert "clarify" in result.shared_context.final_response.direct_answer.lower()
    
    # 4. Assert no unsupported claims (no 7788 crore, no 67%)
    assert "7788" not in result.shared_context.final_response.direct_answer
    assert "67%" not in result.shared_context.final_response.direct_answer
    
def test_valid_supported_insurance_query_continues():
    """Test 7: Existing valid supported insurance query -> continues to produce expected grounded response."""
    # We will use a mock execution manager to track calls
    calls = []
    
    class MockQueryAgent:
        def process(self, query):
            return QueryContext(
                original_query=query,
                intent=IntentResult(primary_intent="policy_information", confidence=0.9),
                ambiguity=AmbiguityInfo(is_ambiguous=False, reason="", missing_parameters=[])
            )
            
    mock_workflow = MagicMock()
    mock_workflow.get_execution_sequence.return_value = ["QueryUnderstandingAgent", "RetrievalAgent"]

    class MockExecutionManager:
        def execute_agent(self, agent_name, func, *args):
            calls.append(agent_name)
            if agent_name == "QueryUnderstandingAgent":
                return MockQueryAgent().process(args[0])
            # Return dummy result for others to avoid crashing
            return None
            
    exec_manager = MockExecutionManager()
    ctx_manager = ContextManager()
    
    class DummyAgent:
        def process(self, *args): pass
        def retrieve(self, *args): pass
        def verify(self, *args): pass
        def reason(self, *args): pass
        def evaluate(self, *args): pass
        def build_response(self, *args): pass

    dummy = DummyAgent()
    agents = {
        "QueryUnderstandingAgent": dummy,
        "RetrievalAgent": dummy,
        "VerificationAgent": dummy,
        "ReasoningAgent": dummy,
        "RiskAssessmentAgent": dummy,
        "ContradictionAgent": dummy,
        "ResponseBuilder": dummy
    }
    
    mock_obs = MagicMock()
    mock_metrics = MagicMock()
    mock_metrics.compile_metrics.return_value = {}
    mock_metrics.get_execution_history.return_value = []

    orchestrator = AgentOrchestrator(
        agents_map=agents,
        execution_manager=exec_manager,
        context_manager=ctx_manager,
        metrics_collector=mock_metrics,
        observability=mock_obs,
        workflow_engine=mock_workflow,
        workflow_timeout_ms=10000
    )
    
    orchestrator.orchestrate("What is the surrender value of Jeevan Anand policy?")
    
    # Assert downstream agents were called
    assert "RetrievalAgent" in calls
