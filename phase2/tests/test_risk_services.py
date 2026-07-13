import pytest
from phase2.services.ambiguity_detector import AmbiguityDetector
from phase2.services.legal_sensitivity_checker import LegalSensitivityChecker
from phase2.services.exclusion_checker import ExclusionChecker
from phase2.services.regulatory_checker import RegulatoryChecker
from phase2.services.escalation_service import EscalationService
from phase2.exceptions.risk_exception import AmbiguityException

def test_ambiguity_detector_happy_path():
    detector = AmbiguityDetector()
    payload = {
        "ambiguity": {
            "is_ambiguous": True,
            "ambiguous_steps": [1, 2],
            "ambiguity_type": "Multiple Interpretations",
            "description": "The logic is unclear."
        }
    }
    res = detector.detect(payload)
    assert res.detected is True
    assert res.affected_step_numbers == [1, 2]
    assert res.ambiguity_type == "Multiple Interpretations"

def test_ambiguity_detector_empty_payload():
    detector = AmbiguityDetector()
    res = detector.detect({})
    assert res.detected is False
    assert res.affected_step_numbers == []
    assert res.ambiguity_type == "None"

def test_legal_sensitivity_checker_happy_path():
    checker = LegalSensitivityChecker()
    payload = {
        "legal_sensitivity": {
            "is_sensitive": True,
            "sensitive_steps": [3],
            "legal_category": "Fraud",
            "description": "Possible misrepresentation."
        }
    }
    res = checker.check(payload)
    assert res.detected is True
    assert res.affected_step_numbers == [3]
    assert res.legal_category == "Fraud"

def test_exclusion_checker():
    checker = ExclusionChecker()
    payload = {"exclusions": {"has_exclusions": True, "excluded_steps": [4], "exclusion_type": "Waiting Period"}}
    res = checker.check(payload)
    assert res.detected is True
    assert res.affected_step_numbers == [4]
    assert res.exclusion_type == "Waiting Period"

def test_regulatory_checker():
    checker = RegulatoryChecker()
    payload = {"regulatory": {"has_regulatory_concerns": True, "regulatory_steps": [1], "concern_type": "IRDAI Compliance"}}
    res = checker.check(payload)
    assert res.detected is True
    assert res.affected_step_numbers == [1]
    assert res.concern_type == "IRDAI Compliance"

def test_escalation_service_high_risk():
    service = EscalationService()
    payload = {"high_risk": {"is_high_risk_query": True, "justification": "Threat"}}
    res = service.evaluate(payload)
    assert res.escalation_required is True
    assert "recommend" in res.recommended_action
    assert res.reasoning == "Threat"

def test_escalation_service_low_risk():
    service = EscalationService()
    payload = {"high_risk": {"is_high_risk_query": False, "justification": "Safe"}}
    res = service.evaluate(payload)
    assert res.escalation_required is False
    assert res.reasoning == "Safe"
