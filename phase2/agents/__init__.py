"""
phase2.agents — Public agent exports.

Part 1: QueryUnderstandingAgent
Part 2: RetrievalAgent (new)
"""

from phase2.agents.query_agent import QueryUnderstandingAgent, QueryUnderstandingAgentFactory
from phase2.agents.retrieval_agent import RetrievalAgent, RetrievalAgentFactory

# Part 3 (new)
from phase2.agents.verification_agent import VerificationAgent, VerificationAgentFactory

# Part 4 (new)
from phase2.agents.reasoning_agent import ReasoningAgent, ReasoningAgentFactory

# Part 5 agents (new)
from phase2.agents.risk_agent import RiskAgent, RiskAgentFactory

# Part 6 agents (new)
from phase2.agents.contradiction_agent import ContradictionAgent, ContradictionAgentFactory

__all__ = [
    # Part 1
    "QueryUnderstandingAgent",
    "QueryUnderstandingAgentFactory",
    # Part 2
    "RetrievalAgent",
    "RetrievalAgentFactory",
    # Part 3
    "VerificationAgent",
    "VerificationAgentFactory",
    # Part 4
    "ReasoningAgent",
    "ReasoningAgentFactory",
    # Part 5
    "RiskAgent",
    "RiskAgentFactory",
    # Part 6
    "ContradictionAgent",
    "ContradictionAgentFactory",
]
