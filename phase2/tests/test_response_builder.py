import pytest
from phase2.agents.response_builder import ResponseBuilderFactory
from phase2.models.risk_assessment import RiskAssessmentResult
from phase2.models.risk_level import RiskLevel
from phase2.models.risk_factor import RiskFactor
from phase2.models.contradiction_result import ContradictionResult

class MockSettings:
    class RespConfig:
        fallback_explanation = "mock_exp_fallback"
        fallback_answer = "mock_ans_fallback"
    
    response_builder = RespConfig()
    agent_version = "2.0.0"

def test_missing_data_fallbacks():
    """Validates that missing upstream dependencies gracefully default exactly natively safely."""
    settings = MockSettings()
    agent = ResponseBuilderFactory.create(settings)
    
    resp = agent.build_response(None, None, None, None)
    
    assert resp.direct_answer == settings.response_builder.fallback_answer
    assert resp.explanation == settings.response_builder.fallback_explanation
    assert len(resp.citations) == 0
    assert len(resp.warnings) == 0

def test_warnings_generated():
    """Validates explicit risk escalation limits translating safely."""
    settings = MockSettings()
    agent = ResponseBuilderFactory.create(settings)
    
    from unittest.mock import MagicMock
    risk = MagicMock()
    risk.overall_risk_level.value = "high"
    
    contra = MagicMock()
    contra.contradictions = [MagicMock()]
    contra.has_critical_conflict = True
    contra.recommendation = "Severe logic gap."
    
    resp = agent.build_response(None, None, risk, contra)
    
    assert len(resp.warnings) == 2
    
    warning_msgs = [w.message for w in resp.warnings]
    assert "Risk threshold breached" in warning_msgs[0] or "Risk threshold breached" in warning_msgs[1]
    assert any("Severe logic gap" in x for x in warning_msgs)
