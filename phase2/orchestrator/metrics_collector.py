import time
from typing import List, Dict

from phase2.interfaces.orchestrator_interface import IMetricsCollector
from phase2.models.execution_status import ExecutionStatus
from phase2.models.execution_step import ExecutionStep
from phase2.models.workflow_metrics import WorkflowMetrics

class MetricsCollector(IMetricsCollector):
    def __init__(self):
        self._execution_history: List[ExecutionStep] = []
        self._start_times: Dict[str, float] = {}
        self._workflow_start_ms = time.perf_counter() * 1000.0

    def start_agent(self, agent_name: str) -> None:
        self._start_times[agent_name] = time.perf_counter() * 1000.0

    def end_agent(self, agent_name: str, status: ExecutionStatus, retry_count: int, error_msg: str = None) -> None:
        end_ms = time.perf_counter() * 1000.0
        start_ms = self._start_times.get(agent_name, end_ms)
        step = ExecutionStep(
            agent_name=agent_name,
            status=status,
            start_time_ms=start_ms,
            end_time_ms=end_ms,
            duration_ms=end_ms - start_ms,
            retry_count=retry_count,
            error_message=error_msg
        )
        self._execution_history.append(step)

    def get_execution_history(self) -> List[ExecutionStep]:
        return list(self._execution_history)

    def compile_metrics(self) -> WorkflowMetrics:
        total_time = (time.perf_counter() * 1000.0) - self._workflow_start_ms
        retries = sum(step.retry_count for step in self._execution_history)
        timeouts = sum(1 for step in self._execution_history if step.status == ExecutionStatus.TIMEOUT)
        failed = sum(1 for step in self._execution_history if step.status == ExecutionStatus.FAILURE)
        success = sum(1 for step in self._execution_history if step.status == ExecutionStatus.SUCCESS)

        return WorkflowMetrics(
            total_execution_time_ms=total_time,
            total_retries=retries,
            total_timeouts=timeouts,
            failed_nodes=failed,
            successful_nodes=success
        )
