from enum import Enum

class ExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    TIMEOUT = "TIMEOUT"
    PARTIAL_FAILURE = "PARTIAL_FAILURE"
    SKIPPED = "SKIPPED"
