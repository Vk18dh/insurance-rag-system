from unittest.mock import MagicMock
from phase2.services.policy_context_validator import PolicyContextValidator
from phase2.services.evidence_alignment_service import EvidenceAlignmentService
from phase2.services.contradiction_classifier import ContradictionClassifier
from phase2.services.contradiction_explainer import ContradictionExplainer
from phase2.services.conflict_resolution_helper import ConflictResolutionHelper
from phase2.models.conflict_level import ConflictLevel
import pytest

def test_classifier_extracts_cleanly():
    c = ContradictionClassifier()
    assert c.classify({"conflict_level": "CRITICAL"}) == ConflictLevel.CRITICAL
    assert c.classify({"conflict_level": "MISSING"}) == ConflictLevel.LOW # Graceful fallback tracking natively

def test_explainer_extracts_cleanly():
    e = ContradictionExplainer()
    assert e.explain({"explanation": "Logical clash bounded."}) == "Logical clash bounded."
    assert e.explain({}) == "Insufficient Evidence"

def test_resolution_helper_distributes_states():
    r = ConflictResolutionHelper()
    assert "Halt" in r.recommend(ConflictLevel.CRITICAL)
    assert "No action" in r.recommend(ConflictLevel.LOW)

def test_policy_context_validator_bounds():
    v = PolicyContextValidator()
    res = MagicMock()
    # Missing chunks
    res.verification_source.retrieval_result.ranked_evidence = []
    assert v.validate_compatibility(res) is False
    
    # Valid chunks
    mock_chunk = MagicMock()
    mock_chunk.source.source_document = "PolA.pdf"
    res.verification_source.retrieval_result.ranked_evidence = [mock_chunk] * 2
    assert v.validate_compatibility(res) is True

def test_evidence_alignment_traces_logic():
    svc = EvidenceAlignmentService()
    res = MagicMock()
    step = MagicMock()
    step.step_number = 1
    ev = MagicMock()
    ev.chunk_id = "chk1"
    step.evidence_used = [ev]
    res.reasoning_chain.steps = [step]
    
    alignment = svc.align_evidence(res)
    assert 1 in alignment.reasoning_step_ids
    assert "chk1" in alignment.retrieved_chunk_ids
