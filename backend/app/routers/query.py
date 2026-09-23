import time
import uuid
from fastapi import APIRouter, Depends, BackgroundTasks
from typing import Annotated

from backend.app.schemas.api import QueryRequest, QueryResponse, RetrievedSource
from backend.app.dependencies.agents import get_agent_orchestrator
from backend.app.dependencies.auth import get_current_user
from backend.app.schemas.auth import TokenPayload
from backend.app.dependencies.db import get_db
from sqlalchemy.orm import Session
from backend.app.services.conversation_service import ConversationService
from backend.app.repositories.conversation_repository import ConversationRepository
from backend.app.services.review_service import ReviewService
from backend.app.repositories.review_repository import ReviewRepository
from backend.app.schemas.review_task import ReviewTaskCreate
from backend.app.services.audit_service import AuditService
from backend.app.config.settings import BackendSettings
from phase2.orchestrator.orchestrator import AgentOrchestrator

def get_conversation_service(db: Annotated[Session, Depends(get_db)]) -> ConversationService:
    repo = ConversationRepository(db)
    return ConversationService(conversation_repository=repo)

def get_review_service(db: Annotated[Session, Depends(get_db)]) -> ReviewService:
    repo = ReviewRepository(db)
    return ReviewService(review_repository=repo)

router = APIRouter(prefix="/query", tags=["query"])

@router.post("", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    db: Session = Depends(get_db),
    conversation_service: ConversationService = Depends(get_conversation_service),
    review_service: ReviewService = Depends(get_review_service),
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    """
    Main entry point for AI analysis mappings. 
    Strictly intercepts REST and passes control downward to the Phase 2 AgentOrchestrator.
    """
    start = time.time()
    from backend.app.services.guardrail_service import GuardrailService
    
    # --- 1. INPUT GUARDRAILS ---
    is_safe_input, input_block_reason = GuardrailService.check_input(request.query)
    if not is_safe_input:
        AuditService.log_event(
            action="GUARDRAIL_INPUT_BLOCKED",
            actor_id=current_user.sub,
            role=current_user.role,
            outcome="FAILURE",
            safe_metadata={"reason": input_block_reason},
            db=db
        )
        return QueryResponse(
            query_id=str(uuid.uuid4()),
            message_id=None,
            conversation_id=None,
            final_answer="I cannot fulfill this request. " + input_block_reason,
            confidence_score=0.0,
            is_safe=False,
            sources=[],
            execution_time_ms=(time.time() - start) * 1000
        )
    
    if request.conversation_id:
        conv = conversation_service.get_conversation_by_id(request.conversation_id, current_user.sub)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found or access denied")
        conv_id = conv.id
    else:
        title = request.query[:50] + "..." if len(request.query) > 50 else request.query
        conv = conversation_service.create_conversation(user_id=current_user.sub, title=title)
        conv_id = conv.id
        
    # Persist the user message BEFORE execution
    conversation_service.append_message(conv_id, current_user.sub, "user", request.query)
    
    enriched_query = request.query
    
    conversation_service.commit()
    AuditService.log_event(
        action="QUERY_SUBMITTED",
        actor_id=current_user.sub,
        role=current_user.role,
        outcome="SUCCESS",
        safe_metadata={
            "query_hash": AuditService.hash_query(request.query),
            "conversation_id": conv_id
        },
        db=db
    )

    try:
        request_id = str(uuid.uuid4())
        
        from starlette.concurrency import run_in_threadpool
        # Pass enriched query into frozen Phase 2
        # This takes a long time, but we don't hold a DB connection anymore!
        result = await run_in_threadpool(orchestrator.orchestrate, enriched_query, conversation_id=conv_id)
        final_resp = result.shared_context.final_response
        
        if final_resp is None:
            # Fallback if pipeline broke cleanly securely
            errs = " | ".join(result.errors) if hasattr(result, 'errors') and result.errors else "Unknown silent failure"
            
            # Check for catastrophic provider/API failure and raise 503 instead of ReviewTask
            if any(term in errs for term in ["Providers exhausted", "HTTP Error", "API execution failure", "Model Not Found", "Connection Error", "Rate Limit Exceeded", "Authentication Error", "Execution bound forcefully"]):
                from fastapi import HTTPException
                raise HTTPException(status_code=503, detail=f"LLM Provider Service Unavailable or Timed Out: {errs}")

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
            final_lower = final_resp_answer.lower()
            if ("i could not find" in final_lower or 
                "not present" in final_lower or 
                "not explicitly mentioned" in final_lower or 
                "could not be found" in final_lower or
                "absent" in final_lower or
                "does not appear to exist" in final_lower or
                len(sources) == 0):
                confidence = 0.0
                is_safe = True
                sources = []
            else:
                # Safe attribution pulling metadata bounds natively
                confidence = getattr(final_resp.metadata, 'confidence', 0.95) if hasattr(final_resp, 'metadata') else 0.95

        # --- 2. OUTPUT GUARDRAILS ---
        is_safe_output, output_block_reason = GuardrailService.check_output(final_resp_answer, request.query, len(sources) > 0)
        if not is_safe_output:
            AuditService.log_event(
                action="GUARDRAIL_OUTPUT_BLOCKED",
                actor_id=current_user.sub,
                role=current_user.role,
                outcome="FAILURE",
                safe_metadata={"reason": output_block_reason, "conversation_id": conv_id},
                db=db
            )
            final_resp_answer = "I cannot fulfill this request. " + output_block_reason
            confidence = 0.0
            is_safe = False
            sources = []

        # Automated Escalation Logic
        settings = BackendSettings.load()
        threshold = settings.app.escalation_confidence_threshold
        
        escalation_reason = None
        if not is_safe:
            escalation_reason = "System constraints violated (unsafe/warnings present)"
        elif confidence < threshold:
            escalation_reason = f"Low confidence detected ({confidence} < {threshold})"

        review_task_id = None
        review_status = None

        # Persist the assistant message AFTER execution
        assistant_msg = conversation_service.append_message(conv_id, current_user.sub, "assistant", final_resp_answer)
        msg_id = assistant_msg.id if assistant_msg else None

        if escalation_reason:
            payload_data = {
                "query": request.query,
                "generated_answer": final_resp_answer,
                "citations": [{"document_id": s.document, "page_number": s.page, "text": s.content_snippet} for s in sources],
                "confidence": confidence,
                "warnings": getattr(final_resp, 'warnings', []) if hasattr(final_resp, 'warnings') else []
            }
            review_task_create = ReviewTaskCreate(
                conversation_id=conv_id,
                message_id=msg_id,
                reason=escalation_reason,
                payload=payload_data
            )
            created_task = review_service.create_task(review_task_create)
            review_task_id = created_task.id
            review_status = created_task.status.value if hasattr(created_task.status, 'value') else str(created_task.status)
            
            conversation_service.commit()
            AuditService.log_event(
                action="REVIEW_TASK_CREATED",
                actor_id=current_user.sub,
                role=current_user.role,
                target_id=review_task_id,
                outcome="SUCCESS",
                safe_metadata={"conversation_id": conv_id},
                db=db
            )

        response_model = QueryResponse(
            query_id=result.request_id,
            message_id=msg_id,
            conversation_id=conv_id,
            final_answer=final_resp_answer,
            confidence_score=confidence,
            is_safe=is_safe,
            sources=sources,
            execution_time_ms=(time.time() - start) * 1000,
            review_task_id=review_task_id,
            review_status=review_status
        )
        
        conversation_service.commit()
        return response_model
        
    except Exception as e:
        conversation_service.rollback()
        # Will be caught by Global Exception Middleware in Stage 8
        raise e
