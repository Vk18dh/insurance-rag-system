import pytest
from typing import Dict, Any

from phase2.models.retrieved_chunk import RetrievedChunk, RetrievalSource
from phase2.models.reasoning_step import ReasoningStep, SupportingEvidence
from phase2.models.reasoning_chain import ReasoningChain
from phase2.services.clause_interpreter import ClauseInterpreter
from phase2.services.evidence_linker import EvidenceLinker
from phase2.services.explanation_service import ExplanationService

@pytest.fixture
def sample_chunk():
    return RetrievedChunk(
        chunk_id="chk_11",
        text="Death benefit applies unless suicide occurs within 12 months.",
        source_document="policy_v1.pdf",
        section_title="Exclusions",
        page_number="2",
        bm25_score=0.9,
        vector_score=0.0,
        combined_score=0.9,
        retrieval_source=RetrievalSource.BM25,
        metadata_complete=True,
        raw_metadata={}
    )

def test_clause_interpreter_basic(sample_chunk):
    interpreter = ClauseInterpreter(max_chunk_length=50)
    clauses = interpreter.interpret([sample_chunk], {})
    
    assert len(clauses) == 1
    # Check truncation
    assert len(clauses[0]["clause_text"]) == 65 # 50 char + 15 char "[TRUNCATED]"
    assert clauses[0]["source"] == "policy_v1.pdf"
    assert clauses[0]["chunk_id"] == "chk_11"

def test_evidence_linker_graphing():
    linker = EvidenceLinker()
    clauses = [
        {"chunk_id": "1", "clause_text": "text A"},
        {"chunk_id": "2", "clause_text": "text B"}
    ]
    linked = linker.link_evidence(clauses)
    assert len(linked) == 2
    assert linked[0]["logical_reference_id"] == "EVIDENCE_1"
    assert linked[1]["logical_reference_id"] == "EVIDENCE_2"

def test_explanation_service_valid():
    svc = ExplanationService()
    step1 = ReasoningStep(
        step_number=1,
        premise="Initial check",
        conclusion="Is valid",
        is_supported=True,
        evidence_used=[SupportingEvidence(chunk_id="A", source_document="docA.pdf", relevance_score=0.9)]
    )
    step2 = ReasoningStep(
        step_number=2,
        premise="Secondary hop",
        conclusion="Unknown leap",
        assumption="Assuming age > 18",
        is_supported=False,
        evidence_used=[]
    )
    chain = ReasoningChain(steps=[step1, step2], is_complete=True)
    
    explanation = svc.generate_explanation(chain)
    assert len(explanation.assumptions_flagged) == 2 # 1 explicit assumption + 1 unsupported leap
    assert "Step 1: Is valid" in explanation.reasoning_summary
    assert "Step 2: Assuming age > 18" in explanation.assumptions_flagged[0]
