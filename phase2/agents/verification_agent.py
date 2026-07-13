import logging
from typing import Any

from phase2.interfaces.verification_interface import (
    IEvidenceValidator,
    IVerificationAgent,
)
from phase2.models.retrieval_result import RetrievalResult
from phase2.models.verification_result import VerificationResult
from phase2.exceptions.verification_exception import InvalidEvidenceException, VerificationException


logger = logging.getLogger(__name__)

class VerificationAgent(IVerificationAgent):
    """
    Top-level verification orchestrator serving as the impassable gateway 
    between raw retrieval output and explicit Reasoning input.
    """
    def __init__(self, evidence_validator: IEvidenceValidator):
        self.evidence_validator = evidence_validator

    def verify(self, retrieval_result: RetrievalResult) -> VerificationResult:
        """
        Executes the exhaustive verification boundaries.
        Reject inputs that violate schema instantly.
        """
        if not isinstance(retrieval_result, RetrievalResult):
            logger.error("Verification aborted: Input is not a valid RetrievalResult.")
            raise InvalidEvidenceException("Input validation failed: Expected RetrievalResult instance.")
            
        qid = "Unknown"
        if retrieval_result.query_context:
            qid = getattr(retrieval_result.query_context, "query_id", "Unknown")

        logger.info(f"Verification started for query_id '{qid}' with {len(retrieval_result.ranked_evidence)} chunks.")

        try:
            report = self.evidence_validator.validate_evidence(retrieval_result)
            
            # Reasoning agents can proceed unless the report actively failed boundaries.
            is_valid = report.verification_status.value != "failed"
            
            result = VerificationResult(
                retrieval_result=retrieval_result,
                report=report,
                is_valid_for_reasoning=is_valid
            )
            
            logger.info(f"Verification complete for '{qid}'. Status: {report.verification_status.value}. Valid for reasoning: {is_valid}")
            return result
        except InvalidEvidenceException:
            raise
        except Exception as e:
            logger.exception(f"Unhandled error during verification pipeline: {e}")
            raise VerificationException(f"Pipeline crashed during verification pass: {e}") from e


class VerificationAgentFactory:
    """Dependency Injection factory assembling the entire Verification stage."""
    
    @staticmethod
    def create(settings: Any) -> VerificationAgent:
        # Load configurable boundaries mapping the DI layers 
        # (Assuming Stage 6 will implement VerificationSettings on Phase2Settings)
        
        from phase2.services.citation_validator import CitationValidator
        from phase2.services.completeness_checker import CompletenessChecker
        from phase2.services.consistency_checker import ConsistencyChecker
        from phase2.services.evidence_validator import EvidenceValidator
        from phase2.services.relevance_checker import RelevanceChecker

        # Build sub-checkers
        citation_validator = CitationValidator(
            require_page_numbers=settings.verification.require_citations
        )
        consistency_checker = ConsistencyChecker()
        relevance_checker = RelevanceChecker(
            min_relevance_score=settings.verification.min_relevance_score
        )
        completeness_checker = CompletenessChecker(
            min_evidence_count=settings.verification.min_evidence_count
        )
        
        # Build top-level evidence validator
        evidence_validator = EvidenceValidator(
            citation_validator=citation_validator,
            relevance_checker=relevance_checker,
            consistency_checker=consistency_checker,
            completeness_checker=completeness_checker,
            strict_metadata=settings.verification.rules.get("strict_metadata", True)
        )
        
        # Build agent
        return VerificationAgent(evidence_validator=evidence_validator)
