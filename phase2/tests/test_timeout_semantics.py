import time
import pytest
from phase2.orchestrator.orchestrator import AgentOrchestrator
from phase2.orchestrator.execution_manager import ExecutionManager
from phase2.orchestrator.timeout_manager import TimeoutManager
from phase2.orchestrator.retry_manager import RetryManager
from phase2.orchestrator.context_manager import ContextManager
from phase2.orchestrator.metrics_collector import MetricsCollector
from phase2.orchestrator.workflow_engine import WorkflowEngine
from phase2.models.execution_status import ExecutionStatus

class FastAgent:
    def process(self, *args):
        return {"status": "fast"}

class SlowAgent:
    def process(self, *args):
        time.sleep(0.5)
        return {"status": "slow"}

def setup_orchestrator(agent_timeout_ms=300, workflow_timeout_ms=900, slow_agent_name="VerificationAgent"):
    workflow_engine = WorkflowEngine(["QueryUnderstandingAgent", "RetrievalAgent", slow_agent_name])
    context_manager = ContextManager()
    metrics_collector = MetricsCollector()
    timeout_manager = TimeoutManager()
    retry_manager = RetryManager()
    
    execution_manager = ExecutionManager(
        timeout_manager=timeout_manager,
        retry_manager=retry_manager,
        timeout_ms=agent_timeout_ms,
        max_retries=1,
        retry_delay_ms=10.0
    )
    
    agents_map = {
        "QueryUnderstandingAgent": FastAgent(),
        "RetrievalAgent": FastAgent(),
        slow_agent_name: SlowAgent()
    }
    
    return AgentOrchestrator(
        workflow_engine=workflow_engine,
        execution_manager=execution_manager,
        context_manager=context_manager,
        metrics_collector=metrics_collector,
        agents_map=agents_map,
        workflow_timeout_ms=workflow_timeout_ms
    )

def test_a_individual_agent_timeout():
    # TEST A: Individual agent timeout
    # agent timeout = 100ms, workflow timeout = 900ms. SlowAgent takes 500ms.
    orchestrator = setup_orchestrator(agent_timeout_ms=100, workflow_timeout_ms=900)
    result = orchestrator.orchestrate("test query")
    
    # Should fail due to timeout of SlowAgent
    assert result.overall_status == ExecutionStatus.FAILURE
    assert any("Execution bound forcefully terminated securely" in err for err in result.errors)

def test_b_workflow_timeout():
    # TEST B: Workflow timeout
    # agent timeout = 600ms, workflow timeout = 400ms. SlowAgent takes 500ms.
    orchestrator = setup_orchestrator(agent_timeout_ms=600, workflow_timeout_ms=400)
    result = orchestrator.orchestrate("test query")
    
    # Should fail due to workflow timeout
    assert result.overall_status == ExecutionStatus.FAILURE
    assert any("Execution bound forcefully terminated securely after 400" in err for err in result.errors)

def test_c_normal_fast_execution():
    # TEST C: Normal fast execution
    # agent timeout = 600ms, workflow timeout = 900ms. SlowAgent takes 500ms.
    orchestrator = setup_orchestrator(agent_timeout_ms=600, workflow_timeout_ms=900)
    result = orchestrator.orchestrate("test query")
    
    assert result.overall_status == ExecutionStatus.SUCCESS
    assert not result.errors

if __name__ == "__main__":
    pytest.main(["-v", __file__])
