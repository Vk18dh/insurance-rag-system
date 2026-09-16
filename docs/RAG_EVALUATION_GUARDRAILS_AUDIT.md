# RAG Evaluation & Guardrails Audit

## 1. Current State Assessment

### 1.1 Current Phase 1 Architecture
- **Implementation**: Uses BM25 (sparse) and ChromaDB (dense vector) for hybrid search.
- **Workflow**: Documents ingested via `ingest.py` and wrapped by `RetrievalService` in `phase2/services/retrieval_service.py`.

### 1.2 Current Phase 2 Architecture
- **Implementation**: Agentic workflow orchestrated by `AgentOrchestrator` (`phase2/orchestrator/orchestrator.py`).
- **Agents**: `QueryUnderstandingAgent`, `RetrievalAgent`, `VerificationAgent`, `ReasoningAgent`, `RiskAssessmentAgent`, `ContradictionAgent`, `ResponseBuilder`.

### 1.3 Current LLM Provider Chain
- **Implementation**: Managed by `LLMProviderManager` (`phase2/services/llm_provider_manager.py`).
- **Chain**: OpenRouter (Primary) -> Groq Key 1 -> Groq Key 2 -> Local Ollama (Fallback).

### 1.4 Current Ollama Integration
- **Implementation**: `GenericOpenRouterExecutor` is used to send HTTP requests to the Ollama API (e.g., `http://ollama:11434/api/chat`).
- **Models**: Currently configured to use `qwen2.5:3b` in the `.env` settings.

### 1.5 Current PostgreSQL Models
- **Implementation**: Defined in `backend/app/models/`.
- **Existing Models**: `User`, `Conversation`, `Message`, `ReviewTask`, `Document`, `AuditLog`.

### 1.6 Current Admin Management Website
- **Implementation**: Next.js app in the `management/` directory.
- **Routing**: Features an `/admin` namespace with pages for Document Management and Audit Logs.

### 1.7 Current Authentication/RBAC
- **Implementation**: JWT-based authentication via `backend/app/routers/auth.py`.
- **Roles**: `USER`, `EXPERT`, `ADMIN`.

### 1.8 Current Audit System
- **Implementation**: `AuditService` logs actions securely to the `AuditLog` table.

### 1.9 Current HITL Workflow
- **Implementation**: Low confidence responses trigger a `ReviewTask` (pending state). Experts review, correct, and resolve it to a `CORRECTED` status.

### 1.10 Current Document Management
- **Implementation**: Admins upload PDFs via the `/api/v1/admin/documents` endpoint, which spawns a background ingestion task.

### 1.11 Existing Test Structure
- **Implementation**: Pytest suites under `phase2/tests/` and `backend/app/tests/`.

### 1.12 Existing Configuration Structure
- **Implementation**: Pydantic `BaseSettings` (`BackendSettings` and `Phase2Settings`) populated by `.env`.

---

## 2. Proposed Architecture & Safest Insertion Points

### 2.1 Guardrails
- **Input Guardrails**: Inserted at the REST API boundary (`backend/app/routers/query.py`) *before* delegating to `AgentOrchestrator`. A separate `GuardrailService` will evaluate input safety.
- **Output Guardrails**: Inserted at the REST API boundary *after* receiving the `OrchestrationResult` from `AgentOrchestrator`, but before returning the response to the user.

### 2.2 RAG Evaluation Engine
- **Engine**: A new `EvaluationService` (`backend/app/services/evaluation_service.py`) that queries the Local Ollama instance (`qwen2.5:3b`) directly, ensuring it never touches the cloud providers.
- **Integration**: Operates completely asynchronously or via an explicit admin API route. It will invoke the existing `AgentOrchestrator` to generate a response for a test case, then use Ollama to score it.

### 2.3 Evaluation Dataset & Results
- **Dataset**: Stored either as a seeded JSON file or in the PostgreSQL database.
- **Results**: New PostgreSQL models: `EvaluationRun` and `EvaluationCaseResult`.

### 2.4 Admin Evaluation UI
- **UI Path**: `management/app/admin/evaluation/page.tsx`
- **Features**: Triggers the evaluation, displays overall metrics, and allows drill-down into individual case results.

---

## 3. Explicit File Audit

### Proposed New Files
1. `backend/app/services/guardrail_service.py`
2. `backend/app/services/evaluation_service.py`
3. `backend/app/models/evaluation.py` (SQLAlchemy models)
4. `backend/app/schemas/evaluation.py` (Pydantic models)
5. `backend/app/routers/evaluation.py` (Admin APIs)
6. `management/app/admin/evaluation/page.tsx` (Admin UI)
7. `backend/app/tests/test_guardrails.py`
8. `backend/app/tests/test_rag_evaluation.py`
9. `backend/app/tests/test_evaluation_api.py`

### Files Requiring Modification (Smallest Additive Changes)
1. `backend/app/routers/query.py`: To inject calls to `GuardrailService.check_input()` and `GuardrailService.check_output()`.
2. `backend/app/main.py`: To include the new `evaluation.router` and create the new database tables on startup.
3. `backend/app/db/database.py`: To import the new `EvaluationRun` and `EvaluationCaseResult` models so they are created.
4. `management/app/admin/layout.tsx`: To add a navigation link for the new "Evaluation" dashboard.

### Frozen Files (Do Not Modify)
- **Phase 1**: `ingest.py`, everything under Phase 1 data ingestion.
- **Phase 2**: `phase2/agents/*`, `phase2/orchestrator/*`, `phase2/services/llm_provider_manager.py`, etc.
- **Models**: `backend/app/models/user.py`, `conversation.py`, `review_task.py`, `audit.py`.

### Database Changes
- **Tables added**: `evaluation_runs`, `evaluation_case_results`.
- No modifications to existing tables.

### API Changes
- **New Endpoints**: 
  - `GET /api/v1/admin/evaluations`
  - `GET /api/v1/admin/evaluations/{id}`
  - `POST /api/v1/admin/evaluations/run`
- **Existing Endpoints**: `POST /api/v1/query` gracefully handles guardrail rejection.

### Frontend Changes
- **Management UI**: New `/admin/evaluation` page. User website (`frontend/`) remains untouched.

### Security Considerations
- The Evaluation APIs will be strictly protected by the existing `get_current_admin_user` dependency.
- Guardrails must fail securely: If the guardrail system goes down, it should not arbitrarily block safe queries, but must fail closed for obvious violations. Output guardrail failure will yield a generic safe response without hallucination.
- No secrets will be exposed in evaluation outputs.
- Local Ollama usage ensures evaluation data doesn't leak to 3rd party APIs.

### Testing Strategy
- Tests will strictly assert that Guardrails do not interfere with valid responses and correctly block invalid ones.
- Evaluation tests will mock the Ollama endpoint to ensure CI stability without requiring the heavy local model.
- E2E testing will confirm the existing `ReviewTask` HITL loop remains unaffected.

### Risks
- Local Ollama (`qwen2.5:3b`) might struggle with complex JSON schema outputs. We will need robust JSON parsing and fallback defaults for evaluation metrics.
- Running evaluation blocks might be slow if processed synchronously; the evaluation should ideally run in a background task (FastAPI `BackgroundTasks`).

---
**STOP CONDITION MET**: Audit complete. Awaiting explicit approval to begin implementation.
