from unittest.mock import MagicMock
from phase2.agents.contradiction_agent import ContradictionAgent
from phase2.models.contradiction_result import ContradictionResult

def test_contradiction_agent_orchestrates_cleanly():
    settings = MagicMock()
    svc = MagicMock()
    res = ContradictionResult.model_construct(
        reasoning_source=MagicMock(),
        risk_source=MagicMock(),
        contradictions=[],
        overall_confidence=0.9,
        recommendation="No action limits applied."
    )
    svc.detect_contradictions.return_value = res
    
    agent = ContradictionAgent(settings, svc)
    out = agent.process(MagicMock(), MagicMock())
    
    assert out.overall_confidence == 0.9
    assert out.recommendation == "No action limits applied."
    svc.detect_contradictions.assert_called_once()
