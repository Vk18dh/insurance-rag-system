import logging
from typing import Any

from phase2.interfaces.orchestrator_interface import IContextManager
from phase2.models.orchestration_result import SharedContext

logger = logging.getLogger(__name__)

class ContextManager(IContextManager):
    def __init__(self):
        self._context = SharedContext()

    def get_context(self) -> SharedContext:
        return self._context

    def update_context(self, agent_name: str, result: Any) -> None:
        property_map = {
            "QueryUnderstandingAgent": "query_context",
            "RetrievalAgent": "retrieval_result",
            "VerificationAgent": "verification_result",
            "ReasoningAgent": "reasoning_result",
            "RiskAssessmentAgent": "risk_result",
            "ContradictionAgent": "contradiction_result"
        }
        target_property = property_map.get(agent_name)
        if target_property:
            setattr(self._context, target_property, result)
            logger.info(f"Context mapped seamlessly attaching '{target_property}' securely natively.")
        else:
            logger.warning(f"Context unbound securely mapping missed limits cleanly on: {agent_name}")
