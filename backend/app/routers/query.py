import time
from fastapi import APIRouter, Depends, BackgroundTasks
from typing import Annotated

from backend.app.dependencies.agents import get_agent_orchestrator
from phase2.orchestrator.orchestrator import AgentOrchestrator
from backend.app.schemas.api import QueryRequest, QueryResponse, RetrievedSource, AgentStep

router = APIRouter(prefix="/query", tags=["query"])

@router.post("", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    start = time.time()
    
    try:
        import uuid
        query_id = str(uuid.uuid4())
        
        result = orchestrator.orchestrate(request.query)
        
        # Pull final response output securely securely natively
        explanation = "Error orchestrating query"
        safe = True
        conf = 0.0
        frontend_sources = []
        
        if result.shared_context.reasoning_result:
            rr = result.shared_context.reasoning_result
            # Build rich markdown explanation from the structured Explanation model
            exp_obj = rr.explanation
            parts = []
            if hasattr(exp_obj, 'reasoning_summary') and exp_obj.reasoning_summary:
                parts.append(exp_obj.reasoning_summary.strip())
            if hasattr(exp_obj, 'clause_interpretation') and exp_obj.clause_interpretation:
                clean_clauses = exp_obj.clause_interpretation.replace(" | ", " ")
                parts.append(f"\n\n*Supporting Evidence: {clean_clauses}*")
            if hasattr(exp_obj, 'assumptions_flagged') and exp_obj.assumptions_flagged:
                flags = " ".join(exp_obj.assumptions_flagged)
                parts.append(f"\n\n*Note: {flags}*")
            explanation = "".join(parts) if parts else str(exp_obj)
            
            # --- START FINAL SYNTHESIS LLM PASS ---
            try:
                # Retrieve the LLM natively from the Reasoning branch
                reasoning_agent = getattr(orchestrator, "agents_map", {}).get("ReasoningAgent")
                analyzer = getattr(getattr(reasoning_agent, "_chain_builder", None), "llm", None)
                if analyzer:
                    synthesis_prompt = f"Your task is to write the final polished response to the user. Using ONLY the following verified logically-deduced facts, construct a highly specific, grounded, and concise final response answering the user query. Do NOT use generic language like 'The policy includes exclusions'. You MUST output the specific facts, numbers, or terms derived in the facts. \n\nUser Query: {request.query}\nDerived Logic Facts:\n{explanation}\n\nFinal Polished Answer:"
                    explanation = analyzer.analyse(synthesis_prompt)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Final synthesis failed, falling back to raw logic dump: {e}")
            # --- END FINAL SYNTHESIS LLM PASS ---
            conf = 0.7  # Sensible default
            if hasattr(rr, 'metrics') and rr.metrics:
                m = rr.metrics
                conf = getattr(m, 'confidence_score',
                       getattr(m, 'reasoning_completeness',
                       getattr(m, 'evidence_coverage_ratio', 0.7)))
            docs = []
            if hasattr(rr, 'verification_source') and rr.verification_source:
                vs = rr.verification_source
                # Try different attribute paths the VerificationSource may expose
                ret_result = getattr(vs, 'retrieval_result', None)
                if ret_result is not None:
                    docs = getattr(ret_result, 'ranked_evidence',
                           getattr(ret_result, 'documents',
                           getattr(ret_result, 'chunks', [])))
            for chunk in docs:
                # RetrievedChunk uses source_document / page_number / text
                src = getattr(chunk, 'source_document', getattr(chunk, 'source', 'Unknown'))
                pg = getattr(chunk, 'page_number', getattr(chunk, 'page', '1'))
                snippet = getattr(chunk, 'text', getattr(chunk, 'page_content', ''))
                try:
                    pg = int(pg)
                except (TypeError, ValueError):
                    pg = 1
                frontend_sources.append(RetrievedSource(
                    document=src,
                    page=pg,
                    content_snippet=snippet,
                    confidence=conf
                ))

        if result.shared_context.risk_result:
            safe = not getattr(result.shared_context.risk_result, 'requires_escalation', False)

        # Build telemetry explicitly
        agent_steps = []
        for step in result.execution_history:
            agent_steps.append(AgentStep(
                agent_name=step.agent_name,
                duration_ms=step.duration_ms,
                status=getattr(step.status, "value", str(step.status))
            ))
            
        return QueryResponse(
            query_id=query_id,
            final_answer=explanation,
            confidence_score=conf,
            is_safe=safe,
            sources=frontend_sources,
            execution_time_ms=(time.time() - start) * 1000,
            agent_steps=agent_steps
        )
        
    except Exception as e:
        # Will be caught by Global Exception Middleware
        raise e
