import logging
import time
from typing import List

from phase2.interfaces.verification_interface import (
    ICitationValidator,
    ICompletenessChecker,
    IConsistencyChecker,
    IEvidenceValidator,
    IRelevanceChecker,
)
from phase2.models.evidence_score import EvidenceScore
from phase2.models.retrieval_result import RetrievalResult
from phase2.models.validation_metrics import ValidationMetrics
from phase2.models.verification_report import VerificationReport, VerificationStatus, VerificationWarning

logger = logging.getLogger(__name__)

class EvidenceValidator(IEvidenceValidator):
    """
    The master Quality Assurance orchestrator binding relevance, 
    citations, completeness, and consistency loops together natively.
    """
    def __init__(
        self,
        citation_validator: ICitationValidator,
        relevance_checker: IRelevanceChecker,
        consistency_checker: IConsistencyChecker,
        completeness_checker: ICompletenessChecker,
        strict_metadata: bool = True
    ):
        self.citation_validator = citation_validator
        self.relevance_checker = relevance_checker
        self.consistency_checker = consistency_checker
        self.completeness_checker = completeness_checker
        self.strict_metadata = strict_metadata

    def validate_evidence(self, retrieval_result: RetrievalResult) -> VerificationReport:
        """Passes the raw RetrievalResult through the 5 checklist logic nodes."""
        start_time = time.time()
        
        chunks = retrieval_result.ranked_evidence
        query_context = retrieval_result.query_context
        
        # Output artifacts
        scores: List[EvidenceScore] = []
        warnings: List[VerificationWarning] = []
        recommendations: List[str] = []
        
        # Counter constraints
        chunks_passed_relevance = 0
        chunks_valid_citations = 0

        # Step 1-5 Checks Per Chunk
        for chunk in chunks:
            # 1. Relevance
            relevance = self.relevance_checker.evaluate_relevance(chunk, query_context)
            if relevance >= getattr(self.relevance_checker, "min_relevance_score", 0.0):
                chunks_passed_relevance += 1

            # 2. Citation
            citation = self.citation_validator.validate_citations(chunk)
            if citation == 1.0:
                chunks_valid_citations += 1
            elif citation == 0.0:
                warnings.append(VerificationWarning(
                    warning_code="MISSING_CITATION",
                    severity="High",
                    message="Chunk is unusable due to missing document binding.",
                    chunk_id=chunk.chunk_id
                ))
                
            # 3. Metadata Completeness Evaluator
            meta_score = 1.0 if chunk.metadata_complete else 0.5
            if not chunk.metadata_complete and self.strict_metadata:
                warnings.append(VerificationWarning(
                    warning_code="INCOMPLETE_METADATA",
                    severity="Medium",
                    message="Strict boundaries found missing metadata traits natively.",
                    chunk_id=chunk.chunk_id
                ))

            # Score envelope
            overall_confidence = (relevance + citation + meta_score) / 3.0
            
            score = EvidenceScore(
                chunk_id=chunk.chunk_id,
                semantic_relevance=relevance,
                bm25_contribution=chunk.bm25_score,
                metadata_completeness_score=meta_score,
                citation_quality=citation,
                overall_confidence=overall_confidence,
                penalties=0.0
            )
            scores.append(score)

        # 4. Consistency Loop
        inconsistencies = self.consistency_checker.check_metadata_consistency(chunks)
        if inconsistencies > 0:
            warnings.append(VerificationWarning(
                warning_code="STRUCTURAL_INCONSISTENCY",
                severity="High",
                message=f"Found {inconsistencies} overlapping metadata boundary faults."
            ))
            recommendations.append("Do not fully trust retrieved metadata context mappings.")

        # 5. Completeness Checker
        # We define completeness purely by valid citation bounds (cannot answer from uncited fragments).
        valid_chunks = [c for c, s in zip(chunks, scores) if s.citation_quality > 0]
        completeness = self.completeness_checker.evaluate_completeness(valid_chunks, query_context)
        
        # Synthesize final state
        if completeness == "Incomplete":
            status = VerificationStatus.DEGRADED
            recommendations.append("Alert the user that verified context coverage is partial.")
        elif inconsistencies > 0 or chunks_passed_relevance == 0:
            status = VerificationStatus.FAILED
            recommendations.append("Reject evidence. Proceeding risks hallucination.")
        else:
            status = VerificationStatus.PASSED
            recommendations.append("Proceed cleanly with Reasoning generation.")
            
        if len(chunks) == 0:
            status = VerificationStatus.FAILED
            recommendations.append("Zero chunks provided. Fallback required natively.")

        elapsed = (time.time() - start_time) * 1000

        metrics = ValidationMetrics(
            total_chunks_evaluated=len(chunks),
            chunks_passed_relevance=chunks_passed_relevance,
            chunks_with_valid_citations=chunks_valid_citations,
            metadata_integrity_score=1.0 if len(chunks) == 0 else (sum(s.metadata_completeness_score for s in scores) / len(chunks)),
            structural_consistencies_found=inconsistencies,
            overall_evidence_completeness=completeness,
            execution_time_ms=elapsed
        )

        return VerificationReport(
            verification_status=status,
            evidence_quality_summary="Valid" if chunks_passed_relevance > 0 else "Poor",
            evidence_completeness_summary=completeness,
            citation_status_summary="Passed" if chunks_valid_citations == len(chunks) and len(chunks) > 0 else "Issues Detected",
            metadata_quality_summary="Strict limits passed" if inconsistencies == 0 else "Inconsistencies mapping observed",
            warnings=warnings,
            recommendations=recommendations,
            evidence_scores=scores,
            validation_metrics=metrics
        )
