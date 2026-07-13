import logging
from typing import List
from phase2.interfaces.orchestrator_interface import IWorkflowEngine

logger = logging.getLogger(__name__)

class WorkflowEngine(IWorkflowEngine):
    def __init__(self, execution_sequence: List[str] = None):
        self._sequence = execution_sequence or [
            "QueryUnderstandingAgent",
            "RetrievalAgent",
            "VerificationAgent",
            "ReasoningAgent",
            "RiskAssessmentAgent",
            "ContradictionAgent"
        ]

    def get_execution_sequence(self) -> List[str]:
        return list(self._sequence)
