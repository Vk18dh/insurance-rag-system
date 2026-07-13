import pytest
from unittest.mock import MagicMock
from phase2.orchestrator.orchestrator import AgentOrchestrator
from phase2.orchestrator.workflow_engine import WorkflowEngine
from phase2.orchestrator.execution_manager import ExecutionManager
from phase2.orchestrator.context_manager import ContextManager
from phase2.orchestrator.retry_manager import RetryManager
from phase2.orchestrator.timeout_manager import TimeoutManager
from phase2.orchestrator.metrics_collector import MetricsCollector
from phase2.models.execution_status import ExecutionStatus
from phase2.exceptions.orchestration_exception import OrchestrationException

class FakeOrchestrator(AgentOrchestrator):
    def _resolve_agent_args(self, agent_name, query):
        return ()

def test_orchestrator_successful_execution():
    workflow_engine = WorkflowEngine(["MockAgentA", "MockAgentB"])
    context_manager = ContextManager()
    metrics_collector = MetricsCollector()
    timeout_manager = TimeoutManager()
    retry_manager = RetryManager()
    execution_manager = ExecutionManager(timeout_manager, retry_manager)
    
    agent_a = MagicMock()
    agent_a.process.return_value = {"param": "A"}
    
    agent_b = MagicMock()
    agent_b.retrieve.return_value = {"param": "B"}
    
    agents_map = {
        "MockAgentA": agent_a,
        "MockAgentB": agent_b
    }
    
    orchestrator = FakeOrchestrator(
        workflow_engine=workflow_engine,
        execution_manager=execution_manager,
        context_manager=context_manager,
        metrics_collector=metrics_collector,
        agents_map=agents_map
    )
    
    result = orchestrator.orchestrate("Test query")
    
    assert result.overall_status == ExecutionStatus.SUCCESS
    assert len(result.execution_history) == 2
    assert result.execution_history[0].agent_name == "MockAgentA"
    assert result.execution_history[1].agent_name == "MockAgentB"
    assert result.metrics.total_execution_time_ms >= 0

def test_orchestrator_failure_handling():
    workflow_engine = WorkflowEngine(["MockAgentA"])
    context_manager = ContextManager()
    metrics_collector = MetricsCollector()
    timeout_manager = TimeoutManager()
    retry_manager = RetryManager()
    
    # Fast retry for test explicitly bound
    execution_manager = ExecutionManager(timeout_manager, retry_manager, max_retries=1, retry_delay_ms=10.0)
    
    agent_a = MagicMock()
    agent_a.process.side_effect = Exception("Test failure manually fired natively.")
    
    agents_map = {"MockAgentA": agent_a}
    
    orchestrator = FakeOrchestrator(
        workflow_engine=workflow_engine,
        execution_manager=execution_manager,
        context_manager=context_manager,
        metrics_collector=metrics_collector,
        agents_map=agents_map
    )
    
    result = orchestrator.orchestrate("Test query securely generated")
    
    assert result.overall_status == ExecutionStatus.FAILURE
    assert len(result.execution_history) == 1
    assert result.execution_history[0].status == ExecutionStatus.FAILURE
    assert "Test failure manually fired natively" in result.errors[0]
