import pytest
from unittest.mock import Mock, MagicMock
from phase2.agents.risk_agent import RiskAgent, RiskAgentFactory
from phase2.interfaces.query_agent_interface import ILLMAnalyzer
from phase2.models.reasoning_result import ReasoningResult
from phase2.models.risk_assessment import RiskAssessmentResult
from phase2.config.settings import Phase2Settings

@pytest.fixture
def mock_reasoning_result():
    # Use model_construct to bypass Pydantic runtime validation on the mock instance natively.
    mock_res = ReasoningResult.model_construct(
        verification_source=MagicMock(),
        reasoning_chain=MagicMock(),
        metrics=MagicMock()
    )
    mock_res.verification_source.retrieval_result.query_context.original_query = "What is the waiting period?"
    mock_res.verification_source.retrieval_result.query_context.query_id = "Q_123"
    
    mock_step_1 = Mock()
    mock_step_1.step_number = 1
    mock_step_1.conclusion = "Wait period is 30 days."
    mock_res.reasoning_chain.steps = [mock_step_1]
    return mock_res

@pytest.fixture
def mock_llm_analyzer():
    llm = Mock(spec=ILLMAnalyzer)
    # The JSON payload simulates a complete output.
    llm.analyse.return_value = {
        "ambiguity": {
            "is_ambiguous": False
        },
        "legal_sensitivity": {
            "is_sensitive": False
        },
        "exclusions": {
            "has_exclusions": True,
            "excluded_steps": [1],
            "exclusion_type": "Waiting Period",
            "description": "Explicit 30 days"
        },
        "regulatory": {
            "has_regulatory_concerns": False
        },
        "high_risk": {
            "is_high_risk_query": False,
            "risk_level": "LOW",
            "justification": "Routine inquiry"
        }
    }
    return llm

def test_risk_agent_integration(mock_reasoning_result, mock_llm_analyzer, monkeypatch):
    # Avoid reading the actual file on disk during tests if it doesn't exist.
    # We patch open directly, or we can just patch `_load_template`.
    from phase2.services.risk_assessment_service import RiskAssessmentService
    
    # We create the factory manually or patch the file reading.
    monkeypatch.setattr(RiskAssessmentService, "_load_template", lambda self, path: "Mock Template {QUERY} {REASONING_BLOCK}")
    
    settings = MagicMock()
    settings.risk.prompt_template_path = "mock"
    settings.risk.supported_risk_categories = []
    agent = RiskAgentFactory.create(settings, mock_llm_analyzer)
    
    result = agent.evaluate(mock_reasoning_result)
    
    assert isinstance(result, RiskAssessmentResult)
    assert result.overall_risk_level.value == "LOW"
    
    # Assert specific exclusion was picked up
    assert result.exclusions_identified.detected is True
    assert result.exclusions_identified.affected_step_numbers == [1]
    
    # Others should be false
    assert result.ambiguity_report.detected is False
    assert result.legal_warnings.detected is False
    assert result.regulatory_warnings.detected is False
    
    # Escalation
    assert result.escalation.escalation_required is False

    # Metrics
    assert result.metrics.risk_factors_detected == 1
    assert result.metrics.execution_time_ms >= 0.0
