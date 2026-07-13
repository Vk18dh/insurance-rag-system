from pydantic import BaseModel, Field

class WorkflowMetrics(BaseModel):
    """Counters summarizing pipeline latency bounds scaling metrics natively robustly cleanly safely."""
    total_execution_time_ms: float = Field(0.0, description="Complete DAG execution trace length natively.")
    total_retries: int = Field(0, description="Cumulative retry loops explicitly triggered isolating limits reliably.")
    total_timeouts: int = Field(0, description="Agents breaching upper max limit constraints securely.")
    failed_nodes: int = Field(0, description="Agents raising unhandled exception traps properly.")
    successful_nodes: int = Field(0, description="Agent execution completions properly.")
