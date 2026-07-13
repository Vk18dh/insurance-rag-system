import logging
from typing import Any, Callable

from phase2.interfaces.orchestrator_interface import IExecutionManager, ITimeoutManager, IRetryManager

logger = logging.getLogger(__name__)

class ExecutionManager(IExecutionManager):
    def __init__(self, timeout_manager: ITimeoutManager, retry_manager: IRetryManager, timeout_ms: float = 30000.0, max_retries: int = 1, retry_delay_ms: float = 200.0):
        self._timeout_manager = timeout_manager
        self._retry_manager = retry_manager
        self._timeout_ms = timeout_ms
        self._max_retries = max_retries
        self._retry_delay_ms = retry_delay_ms

    def execute_agent(self, agent_name: str, func: Callable[..., Any], *args, **kwargs) -> Any:
        def timed_execution():
            return self._timeout_manager.execute_with_timeout(self._timeout_ms, func, *args, **kwargs)

        return self._retry_manager.execute_with_retry(self._max_retries, self._retry_delay_ms, timed_execution)
