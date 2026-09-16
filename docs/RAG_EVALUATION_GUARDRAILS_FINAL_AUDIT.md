# RAG Evaluation & Guardrails Final Audit

## 1. Which requirements already exist?
- Local Ollama fallback integration.
- Admin authentication and RBAC via JWT (`ADMIN`, `EXPERT`, `USER`).
- `AgentOrchestrator` structure, `VerificationAgent` for HITL escalation.
- ChromaDB and BM25 retrievers.
- Background task execution via FastAPI `BackgroundTasks`.

## 2. Which requirements are missing?
- Guardrails layer checking inputs (prompt injections/unsafe) and outputs (unsafe/unsupported) with strict audit logging (no payload storage).
- Evaluation Dataset JSON with versioning.
- Evaluation Engine running `AgentOrchestrator` against the dataset and scoring via local Ollama.
- Strong isolation during evaluation to prevent writing to production `ReviewTask` tables or any other business logic.
- Database tables for storing evaluation results.
- Admin APIs (asynchronous queuing) and Management UI for triggering and viewing evaluations.

## 3. Which files need modification?
- `backend/app/routers/query.py` (injects Input/Output Guardrails wrapping the `AgentOrchestrator` call).
- `backend/app/main.py` (registers new evaluation router).
- `backend/app/db/database.py` (exposes evaluation models for initialization).
- `management/app/admin/layout.tsx` (adds sidebar nav link for Evaluations).

## 4. Which new files are required?
- `data/evaluation/rag_evaluation_dataset.json`
- `backend/app/services/guardrail_service.py`
- `backend/app/services/evaluation_service.py`
- `backend/app/models/evaluation.py`
- `backend/app/schemas/evaluation.py`
- `backend/app/routers/evaluation.py`
- `management/app/admin/evaluation/page.tsx`
- `management/app/admin/evaluation/[id]/page.tsx`
- `backend/app/tests/test_guardrails.py`
- `backend/app/tests/test_rag_evaluation.py`
- `backend/app/tests/test_evaluation_api.py`

## 5. Which database tables are required?
- `evaluation_runs`: id, started_at, completed_at, status, dataset_version, evaluator_model, evaluation_timestamp, scoring_schema_version, total_cases, passed_cases, failed_cases, overall_score.
- `evaluation_case_results`: id, run_id, case_id, query, category, generated_answer, retrieved_sources, retrieval_score, relevance_score, faithfulness_score, hallucination_score, citation_score, hitl_expected, hitl_actual, pass (boolean), evaluator_reason, raw_evaluator_output, parsed_success, evaluation_latency, created_at.

## 6. How will Ollama be used?
A local `qwen2.5:3b` model will be directly invoked via HTTP in the `EvaluationService` using strict JSON schema prompts to score cases. It will entirely bypass OpenRouter/Groq ensuring cost-free, offline evaluation. No silent fallback to cloud models will be permitted; if Ollama fails, the run Fails.

## 7. How will Guardrails integrate without duplicating Verification Agent?
- Input Guardrails act as a lightweight firewall *before* the pipeline starts (detecting prompt injection/abusive language). Logs `GUARDRAIL_INPUT_BLOCKED`.
- Output Guardrails act as a final safety check *after* pipeline completion. Logs `GUARDRAIL_OUTPUT_BLOCKED`.
- They do NOT perform semantic document relevance checking or trigger `ReviewTask`s (which remains the Verification Agent's job). Guardrail failure yields a controlled generic refusal.

## 8. How will evaluation results appear in Admin UI?
A new `/admin/evaluation` route in the management app will show a summary list of `EvaluationRun`s (polling while `QUEUED`/`RUNNING`) with top-level aggregate scores. A drill-down view will display detailed `EvaluationCaseResult` entries with expected vs. actual behavior and individual scores.

## 9. How will RBAC be enforced?
The evaluation API endpoints will use the strict `get_current_admin_user` dependency from `backend/app/dependencies/auth.py`. 403 Forbidden will be returned for USER and EXPERT roles.

## 10. How will existing Phase 1/2 freeze constraints be preserved?
No files in `phase1/` or `phase2/` will be modified. All evaluation and guardrail logic will live in the `backend/app/` boundary layer, interacting with Phase 2 solely via its public interfaces. The evaluation context will be strictly isolated (mocking or intercepting the orchestration save actions) to prevent creating production `ReviewTask` records or modifying databases.

## 11. What risks exist?
- Local `qwen2.5:3b` may struggle to output reliable, structured JSON for evaluations, requiring robust error handling and fallback parsing to record `parsed_success=False`.
- Synchronous execution of large datasets could block the server; evaluation will run asynchronously in background tasks and return a status payload immediately.

## 12. What exact tests will prove completion?
- `test_guardrails.py` (valid query passes, injection rejected, unsafe output handled, audit events logged correctly).
- `test_rag_evaluation.py` (local ollama judge called, strict JSON parsing, fallback logic, run isolation from DB).
- `test_evaluation_api.py` (RBAC enforcement: Admin 200, User 403, Expert 403; background task queuing).
- Regression suite: `pytest phase2/tests -v` and `pytest backend/app/tests -v`.
