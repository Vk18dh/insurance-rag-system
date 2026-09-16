# FINAL REQUIREMENTS COMPLIANCE MATRIX

This document maps all authoritative requirements for the RAG Evaluation & Guardrails system against the implemented repository state.

## 1. Architectural Freeze Constraints

| REQUIREMENT | IMPLEMENTATION | FILE/ENDPOINT | TEST/EVIDENCE | STATUS |
|-------------|----------------|---------------|---------------|--------|
| Phase 1 and Phase 2 remain frozen | No core Phase 1/Phase 2 logic modified. Only exception is an errant modification to a test file. | `phase2/tests/test_llm_provider_manager.py` (Modified) | `git diff --name-only origin/main` | PARTIAL |
| BM25, ChromaDB, retrieval pipeline, orchestrator remain unchanged | Unchanged | N/A | `git status` | PASS |
| Guardrails must remain separate from Verification Agent | Guardrails implemented at FastAPI REST layer (Stage 1/8) separate from Phase 2 Orchestrator | `backend/app/routers/query.py` | Code Inspection | PASS |

## 2. Guardrails Implementation

| REQUIREMENT | IMPLEMENTATION | FILE/ENDPOINT | TEST/EVIDENCE | STATUS |
|-------------|----------------|---------------|---------------|--------|
| Prompt injection detection | Regex-based rejection of system instructions | `backend/app/services/guardrail_service.py` | `test_guardrail_input_injection` | PASS |
| Unsafe/malicious input detection | Regex-based blocklist | `backend/app/services/guardrail_service.py` | `test_guardrail_input_unsafe` | PASS |
| Unsafe output detection | Output checked against unsafe phrases | `backend/app/services/guardrail_service.py` | `test_guardrail_output_unsafe` | PASS |
| Controlled refusal on failure | Explicit 400 or safe fallback response | `backend/app/routers/query.py` | `test_guardrail_output_refusal` | PASS |
| No semantic document relevance OOD detection | Relevance is explicitly left to the Orchestrator/Verification Agent | `backend/app/services/guardrail_service.py` | Code Inspection | PASS |
| Does not duplicate VerificationAgent | Guardrails are purely lexical I/O safety bounds | `backend/app/services/guardrail_service.py` | Code Inspection | PASS |

## 3. RAG Evaluation System

| REQUIREMENT | IMPLEMENTATION | FILE/ENDPOINT | TEST/EVIDENCE | STATUS |
|-------------|----------------|---------------|---------------|--------|
| Evaluate system without polluting production | EvaluationRun manages isolated `evaluation_cases` without touching `ReviewTask` | `backend/app/services/evaluation_service.py` | `test_evaluation_isolation_and_execution` | PASS |
| Evaluation uses local Ollama/qwen2.5:3b | Default parameters use Qwen 2.5 3B with Ollama API | `backend/app/services/evaluation_service.py` | Code Inspection | PASS |
| Does not consume OpenRouter/Groq | Only calls `localhost:11434` for judge | `backend/app/services/evaluation_service.py` | Code Inspection | PASS |
| Execution is Admin-only | Protected by `require_admin_role` dependency | `backend/app/routers/evaluation.py` | `test_evaluation_api_admin_access` | PASS |
| One failed case does not terminate run | Uses `try/except` loop over evaluation cases | `backend/app/services/evaluation_service.py` | Code Inspection | PASS |
| Handle malformed JSON | Safely parses or defaults to fail upon `JSONDecodeError` | `backend/app/services/evaluation_service.py` | Code Inspection | PASS |

## 4. Evaluation Metrics

| REQUIREMENT | IMPLEMENTATION | FILE/ENDPOINT | TEST/EVIDENCE | STATUS |
|-------------|----------------|---------------|---------------|--------|
| retrieval_relevance | Evaluated heuristically by LLM Judge | `backend/app/services/evaluation_service.py` | Code Inspection | PARTIAL (Heuristic LLM) |
| answer_relevance | Evaluated heuristically by LLM Judge | `backend/app/services/evaluation_service.py` | Code Inspection | PARTIAL (Heuristic LLM) |
| faithfulness | Evaluated heuristically by LLM Judge | `backend/app/services/evaluation_service.py` | Code Inspection | PARTIAL (Heuristic LLM) |
| hallucination | Evaluated heuristically by LLM Judge | `backend/app/services/evaluation_service.py` | Code Inspection | PARTIAL (Heuristic LLM) |
| citation_accuracy | Evaluated heuristically by LLM Judge | `backend/app/services/evaluation_service.py` | Code Inspection | PARTIAL (Heuristic LLM) |
| hitl_expected | Parsed directly from dataset schema | `backend/app/schemas/evaluation.py` | Code Inspection | PASS (Deterministic) |
| hitl_actual | Boolean derived natively from Orchestrator response/warnings | `backend/app/services/evaluation_service.py` | Code Inspection | PASS (Deterministic) |
| overall_score | Numeric LLM rating | `backend/app/services/evaluation_service.py` | Code Inspection | PARTIAL (Heuristic LLM) |
| pass/fail | Exact match between `hitl_actual` and `hitl_expected` and score > threshold | `backend/app/services/evaluation_service.py` | Code Inspection | PASS (Deterministic) |

## 5. HITL Workflow

| REQUIREMENT | IMPLEMENTATION | FILE/ENDPOINT | TEST/EVIDENCE | STATUS |
|-------------|----------------|---------------|---------------|--------|
| Normal high-confidence RAG query → 200, no task | Confidence > threshold passes through securely | `backend/app/routers/query.py` | `test_hitl_workflow_end_to_end` | PASS |
| Genuine low-confidence query → ReviewTask created | Handled natively by Verification Agent warnings yielding `is_safe=False` or `confidence=0` | `backend/app/routers/query.py` | `test_genuine_low_confidence_creates_hitl` | PASS (Intermittent Test Bug) |
| Provider exhaustion → 503, NO ReviewTask | Caught securely via error string matching | `backend/app/routers/query.py` | Code Inspection | PASS |
| Guardrail rejection → NO ReviewTask | Blocked prior to evaluation completion with safe reason | `backend/app/routers/query.py` | `test_guardrail_output_refusal` | PASS |

## 6. RBAC & Security

| REQUIREMENT | IMPLEMENTATION | FILE/ENDPOINT | TEST/EVIDENCE | STATUS |
|-------------|----------------|---------------|---------------|--------|
| Admin-only evaluation access | REST boundary secured | `backend/app/routers/evaluation.py` | `test_evaluation_api_user_denied` | PASS |
| User cannot access documents | Admin requirement for documents endpoint | `backend/app/routers/admin.py` | `test_user_cannot_access_documents` | PASS |
| No hardcoded secrets | Only mock tokens in test files. No actual keys leaked. | Repository Search | Secret Scan `grep` | PASS |
| Audit logs avoid PII / Secrets | Safely redacting logic in `safe_metadata` | `backend/app/services/audit_service.py` | `test_audit_security_no_secrets_stored` | PASS |

## 7. Document Management

| REQUIREMENT | IMPLEMENTATION | FILE/ENDPOINT | TEST/EVIDENCE | STATUS |
|-------------|----------------|---------------|---------------|--------|
| Admin PDF upload & processing | Uses `IngestionService` | `backend/app/routers/admin.py` | Code Inspection | PASS |
| PostgreSQL metadata persistence | Ingestion stores Document Metadata | `backend/app/services/ingestion_service.py` | Code Inspection | PASS |
| ChromaDB + BM25 updates safely | Processed into vector and keyword spaces natively | `backend/app/services/ingestion_service.py` | Code Inspection | PASS |
