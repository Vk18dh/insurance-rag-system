"""
phase2.validation.tests.integration.test_integration
====================================================

Integration tests focusing on handoffs between agents and services.
"""

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
from phase2.validation.services import MockDataProvider

class IntegrationFakeOrchestrator(AgentOrchestrator):
    def _resolve_agent_args(self, agent_name, query):
        return ()

def test_orchestrator_mock_integration():
    """Verify orchestrator execution sequence handoff via integrated mock components."""
    provider = MockDataProvider()
    queries = provider.get_mock_queries("standard")
    assert len(queries) > 0

    workflow_engine = WorkflowEngine(["MockAgentA"])
    context_manager = ContextManager()
    metrics_collector = MetricsCollector()
    timeout_manager = TimeoutManager()
    retry_manager = RetryManager()
    execution_manager = ExecutionManager(timeout_manager, retry_manager)
    
    agent_a = MagicMock()
    agent_a.process.return_value = {"param": "A"}
    
    agents_map = {"MockAgentA": agent_a}
    
    orch = IntegrationFakeOrchestrator(
        workflow_engine=workflow_engine,
        execution_manager=execution_manager,
        context_manager=context_manager,
        metrics_collector=metrics_collector,
        agents_map=agents_map
    )
    result = orch.orchestrate(queries[0])
    assert result.request_id is not None
    assert result.overall_status == ExecutionStatus.SUCCESS
    assert len(result.execution_history) == 1
    assert result.execution_history[0].agent_name == "MockAgentA"

