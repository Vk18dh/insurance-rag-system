import time
import uuid
from fastapi import APIRouter, Depends, BackgroundTasks
from typing import Annotated

from backend.app.schemas.api import QueryRequest, QueryResponse, RetrievedSource
from backend.app.dependencies.agents import get_agent_orchestrator
from phase2.orchestrator.orchestrator import AgentOrchestrator

router = APIRouter(prefix="/query", tags=["query"])

@router.post("", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    """
    Main entry point for AI analysis mappings. 
    Strictly intercepts REST and passes control downward to the Phase 2 AgentOrchestrator.
    """
    start = time.time()
    
    # Part 11 Rule: "FastAPI acts only as an HTTP adapter. Existing business logic must never migrate into FastAPI."
    # We call orchestrator.process_query() explicitly.
    try:
        request_id = str(uuid.uuid4())
        
        # Part 11 strict conformance: executing explicitly down the orchestration stack seamlessly.
        result = orchestrator.orchestrate(request.query)
        final_resp = result.shared_context.final_response
        
        if final_resp is None:
            # Fallback if pipeline broke cleanly securely
            errs = " | ".join(result.errors) if hasattr(result, 'errors') and result.errors else "Unknown silent failure"
            if "VerificationResult failed QA upstream constraints" in errs:
                final_resp_answer = "I could not find related evidence in the insurance documents to answer your query. I am actively refusing to hallucinate an answer outside my domain bounds."
                sources = []
                confidence = 0.0
                is_safe = True
            elif "Query must be at least" in errs:
                final_resp_answer = "Your query is too short for me to understand. Please provide more context about what you're looking for in the insurance documents."
                sources = []
                confidence = 0.0
                is_safe = True
            else:
                final_resp_answer = f"Pipeline failed to execute. Error details: {errs}"
                sources = []
                confidence = 0.0
                is_safe = False
        else:
            final_resp_answer = final_resp.direct_answer
            sources = []
            for c in final_resp.citations:
                page_val = int(c.page_number) if c.page_number and str(c.page_number).isdigit() else 0
                sources.append(RetrievedSource(
                    document=c.source_document,
                    page=page_val,
                    content_snippet=c.snippet or "",
                    confidence=1.0  # Safe default since citations are vetted
                ))
            
            is_safe = len(final_resp.warnings) == 0
            
            # If the response explicitly hit the grounded refusal, force Low Confidence natively
            if "I could not find this information in the provided documents" in final_resp_answer:
                confidence = 0.0
                is_safe = True
                sources = []
            else:
                # Safe attribution pulling metadata bounds natively
                confidence = getattr(final_resp.metadata, 'confidence', 0.95) if hasattr(final_resp, 'metadata') else 0.95

        response_model = QueryResponse(
            query_id=result.request_id,
            final_answer=final_resp_answer,
            confidence_score=confidence,
            is_safe=is_safe,
            sources=sources,
            execution_time_ms=(time.time() - start) * 1000
        )
        return response_model
        
    except Exception as e:
        # Will be caught by Global Exception Middleware in Stage 8
        raise e
