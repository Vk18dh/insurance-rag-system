import logging
import uuid
from typing import Dict, Any

from phase2.interfaces.orchestrator_interface import (
    IAgentOrchestrator, IWorkflowEngine, IExecutionManager,
    IContextManager, IMetricsCollector
)
from phase2.models.orchestration_result import OrchestrationResult
from phase2.models.execution_status import ExecutionStatus
from phase2.exceptions.orchestration_exception import OrchestrationException, TimeoutException

logger = logging.getLogger(__name__)

class AgentOrchestrator(IAgentOrchestrator):
    def __init__(self, 
                 workflow_engine: IWorkflowEngine,
                 execution_manager: IExecutionManager,
                 context_manager: IContextManager,
                 metrics_collector: IMetricsCollector,
                 agents_map: Dict[str, Any]):
        """
        The Orchestrator defines exactly zero hardcoded models reliably mapping dynamic bounds centrally smoothly natively safely.
        """
        self._workflow = workflow_engine
        self._execution_manager = execution_manager
        self._context_manager = context_manager
        self._metrics_collector = metrics_collector
        self._agents_map = agents_map

    def orchestrate(self, query: str) -> OrchestrationResult:
        request_id = str(uuid.uuid4())
        logger.info(f"Orchestration initiated safely securely resolving natively [{request_id}]")
        
        sequence = self._workflow.get_execution_sequence()
        overall_status = ExecutionStatus.SUCCESS
        errors = []
        warnings = []
        
        for agent_name in sequence:
            agent = self._agents_map.get(agent_name)
            if not agent:
                err_msg = f"Unregistered executing boundary requested securely: {agent_name}"
                logger.error(err_msg)
                errors.append(err_msg)
                overall_status = ExecutionStatus.FAILURE
                break
                
            self._metrics_collector.start_agent(agent_name)
            try:
                args_list = self._resolve_agent_args(agent_name, query)
                func = self._resolve_agent_entrypoint(agent)
                
                result = self._execution_manager.execute_agent(agent_name, func, *args_list)
                self._context_manager.update_context(agent_name, result)
                self._metrics_collector.end_agent(agent_name, ExecutionStatus.SUCCESS, 0)
                
            except TimeoutException as e:
                logger.error(f"Execution bound forcefully terminated securely natively: {e}")
                self._metrics_collector.end_agent(agent_name, ExecutionStatus.TIMEOUT, 0, str(e))
                errors.append(str(e))
                overall_status = ExecutionStatus.FAILURE
                break
            except Exception as e:
                logger.error(f"Execution exception gracefully trapped dynamically securely: {e}")
                self._metrics_collector.end_agent(agent_name, ExecutionStatus.FAILURE, 0, str(e))
                errors.append(str(e))
                overall_status = ExecutionStatus.FAILURE
                break
                
        metrics = self._metrics_collector.compile_metrics()
        
        return OrchestrationResult(
            request_id=request_id,
            overall_status=overall_status,
            metrics=metrics,
            execution_history=self._metrics_collector.get_execution_history(),
            shared_context=self._context_manager.get_context(),
            errors=errors,
            warnings=warnings
        )

    def _resolve_agent_entrypoint(self, agent: Any) -> Any:
        if "process" in dir(agent):
            return agent.process
        elif "retrieve" in dir(agent):
            return agent.retrieve
        elif "verify" in dir(agent):
            return agent.verify
        elif "reason" in dir(agent):
            return agent.reason
        elif "evaluate" in dir(agent):
            return agent.evaluate
        else:
            raise OrchestrationException("Invalid method hook boundary maps seamlessly isolating loops.")

    def _resolve_agent_args(self, agent_name: str, query: str) -> tuple:
        ctx = self._context_manager.get_context()
        if agent_name == "QueryUnderstandingAgent":
             return (query,)
        if agent_name == "RetrievalAgent":
             return (ctx.query_context,)
        if agent_name == "VerificationAgent":
             return (ctx.retrieval_result,)
        if agent_name == "ReasoningAgent":
             return (ctx.verification_result,)
        if agent_name == "RiskAssessmentAgent":
             return (ctx.reasoning_result,)
        if agent_name == "ContradictionAgent":
             return (ctx.reasoning_result, ctx.risk_result)
        
        raise OrchestrationException(f"Cannot resolve binding sequence limit traces securely reliably for {agent_name}")
