# Audit System Implementation Plan

This implementation plan details the additive Security/Action Audit System. It adheres strictly to the authoritative requirements without replacing or modifying the Phase 2 observability trace system.

## 1. Frozen Architectures
The following core architectures are completely frozen and will NOT be modified or rewritten:
- Phase 1 (Ingestion)
- BM25 & ChromaDB
- Current embedding model (`all-MiniLM-L6-v2`)
- Hybrid retrieval mechanism
- All Phase 2 agents
- `AgentOrchestrator`
- `LLMProviderManager`

## 2. PostgreSQL & Database Migrations
- **File:** `backend/app/models/audit.py`
- **Description:** Add `SecurityAuditLog` to the existing application database.
- **Migration Strategy:** Because `alembic` is NOT present in the repository, this plan retains the startup `Base.metadata.create_all()` hook.
- **Limitation Documented:** Relying on `create_all()` means schema alterations (like adding/dropping columns) are not automatically managed in production without dropping tables or manually applying SQL migrations. However, because this is an additive feature (a completely new table), `create_all()` safely creates the `audit_logs` table without wiping existing data.

## 3. Append-Only Constraint & Immutability
Audit records must be strictly append-only through the application API.
- **Supported Endpoints:** Create (Internal API hooks), Admin Read (Public REST API).
- **Forbidden Endpoints:** There must NOT be any Update or Delete endpoint exposed via the API.

## 4. SecurityAuditLog Model
The `SecurityAuditLog` SQLAlchemy model will explicitly contain the following fields:
- `id` (UUID, primary key)
- `timestamp` (UTC DateTime)
- `actor_id` (String/UUID)
- `role` (String)
- `action` (String)
- `target_id` (String)
- `outcome` (String)
- `safe_metadata` (JSON)

## 5. Security & Secret Protection
**NEVER store:**
- passwords
- JWT tokens
- Authorization headers
- API keys
- provider credentials
- raw provider responses
- other secrets

## 6. Audit Event Definitions
The system will safely generate events for the following scenarios:

**Authentication Auditing:**
- `LOGIN_SUCCESS`
- `LOGIN_FAILURE`
- `REGISTER`

**Security Auditing:**
- `RBAC_DENIED`: Record RBAC denial events without storing sensitive request data.

**Query Auditing:**
- `QUERY_SUBMITTED`: Do not automatically persist the raw user query. Store a non-reversible query hash and safe metadata unless the authoritative documents explicitly require raw query text.

**Document Auditing:**
- Record document upload and ingestion lifecycle events, including:
  - `DOCUMENT_UPLOADED`
  - `DOCUMENT_INGESTION_SUCCESS`
  - `DOCUMENT_INGESTION_FAILED`

**HITL (Human-in-the-loop) Auditing:**
- `REVIEW_TASK_CREATED`
- `REVIEW_TASK_APPROVED`
- `REVIEW_TASK_CORRECTED`

## 7. Audit Failure Isolation
- **Design:** The `AuditService` must isolate write failures so that a failure to write an audit record does not silently corrupt or incorrectly change the underlying business operation.
- **Transaction Handling:** The audit recording mechanism will use a separate `try...except` block (and ideally an independent database session or `begin_nested()`) that swallows database exceptions, logs them to the terminal/standard output as a fallback, and allows the primary business transaction to complete successfully.

## 8. Admin API
- **Endpoint:** `GET /api/v1/admin/audit`
- **RBAC:** Require ADMIN role.
- **Capabilities:**
  - Pagination (`skip`, `limit`)
  - Action filtering
  - Actor filtering

## 9. Testing Strategy
- **RBAC tests:**
  - Verify USER → 403
  - Verify EXPERT → 403
  - Verify ADMIN → allowed
- **Immutability tests:**
  - Verify there is no application route allowing modification/deletion of audit records.
- **Security tests:**
  - Verify passwords, JWTs, Authorization headers, and API keys never appear in persisted audit records.
- **Integration tests:**
  - Verify audit events are actually created for:
    - login
    - query
    - document upload/ingestion
    - ReviewTask creation
    - Expert approval
    - Expert correction
    - RBAC denial

## 10. Management Website
- Add route: `/admin/audit`
- Add component: `AuditTable`
- Add Admin-only navigation pointing to the Audit page.

## 11. Separation of Concerns
- Keep the existing Phase 2 observability `AuditRecord` completely separate from this `SecurityAuditLog`.
