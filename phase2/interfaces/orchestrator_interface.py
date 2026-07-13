from abc import ABC, abstractmethod
from typing import Any, Callable, List, TypeVar

from phase2.models.orchestration_result import OrchestrationResult, SharedContext
from phase2.models.execution_status import ExecutionStatus
from phase2.models.workflow_metrics import WorkflowMetrics
from phase2.models.execution_step import ExecutionStep

T = TypeVar('T')

class IMetricsCollector(ABC):
    """Hooks compiling telemetry cleanly isolating latency calculations safely."""
    @abstractmethod
    def start_agent(self, agent_name: str) -> None:
        pass
        
    @abstractmethod
    def end_agent(self, agent_name: str, status: ExecutionStatus, retry_count: int, error_msg: str = None) -> None:
        pass
        
    @abstractmethod
    def get_execution_history(self) -> List[ExecutionStep]:
        pass
        
    @abstractmethod
    def compile_metrics(self) -> WorkflowMetrics:
        pass


class ITimeoutManager(ABC):
    """Enforces execution upper bounds blocking hanging APIs cleanly."""
    @abstractmethod
    def execute_with_timeout(self, timeout_ms: float, func: Callable[..., T], *args, **kwargs) -> T:
        pass


class IRetryManager(ABC):
    """Manages explicit transient loop limits natively tracking configuration bindings."""
    @abstractmethod
    def execute_with_retry(self, max_retries: int, delay_ms: float, func: Callable[..., T], *args, **kwargs) -> T:
        pass


class IContextManager(ABC):
    """Limits direct coupling effectively managing the SharedExecutionContext safely."""
    @abstractmethod
    def get_context(self) -> SharedContext:
        pass
        
    @abstractmethod
    def update_context(self, agent_name: str, result: Any) -> None:
        pass


class IExecutionManager(ABC):
    """Resolves inputs to arbitrary explicitly injected agents mapping fallback wrappers properly."""
    @abstractmethod
    def execute_agent(self, agent_name: str, func: Callable[..., Any], *args, **kwargs) -> Any:
        pass


class IWorkflowEngine(ABC):
    """Configured directed graph boundary preventing skipped steps explicitly."""
    @abstractmethod
    def get_execution_sequence(self) -> List[str]:
        pass


class IAgentOrchestrator(ABC):
    """The central root controller executing queries smoothly safely robustly natively."""
    @abstractmethod
    def orchestrate(self, query: str) -> OrchestrationResult:
        pass
