# Policy Document Management — Implementation Plan

## 1. Executive Summary

Implement **ADMIN-only Policy Document Management** through the existing Management Website and FastAPI backend. An administrator uploads an approved insurance PDF and metadata; the backend records document metadata in PostgreSQL and invokes the **existing Phase 1 ingestion pipeline**. The document is extracted/OCR-processed, chunked, embedded, and indexed in both **ChromaDB (dense)** and **BM25 (sparse)**, after which it becomes available to the existing Agentic RAG pipeline.

The feature is an administrative knowledge-base capability, not a new RAG architecture. Do not create a second ingestion pipeline, remove BM25, replace ChromaDB, or modify Phase 2.

## 2. Requirements Traceability

| Requirement | Authority | Status for implementation |
|---|---|---|
| PDF/document ingestion | PRD/TRD | REQUIRED |
| OCR/layout processing where required | PRD/TRD | REQUIRED |
| Metadata preservation | PRD/Backend Schema | REQUIRED |
| ChromaDB dense retrieval | PRD/TRD/Backend Schema | REQUIRED |
| BM25 sparse retrieval | PRD/TRD/Backend Schema | REQUIRED |
| Admin document management | PRD/Backend Schema | REQUIRED |
| Expert review workflow | PRD/Backend Schema | EXISTING; PRESERVE |
| User/Management separation | PRD/App Flow/Implementation Plan | REQUIRED |
| Server-side RBAC | TRD/Backend Schema | REQUIRED |
| Admin Documents UI | UI/UX Brief | REQUIRED |
| `GET /admin/documents`, `POST /admin/documents` | Backend Schema | Intended API contracts; reconcile with repository |
| Full CRUD/reindex | Audit/implementation proposal | VERIFY before making mandatory |
| Audit records | PRD/Backend Schema | REQUIRED capability |

The PRD explicitly requires document ingestion, BM25 sparse indexing, dense vector indexing, and Admin document management. The backend schema explicitly assigns document management to ADMIN and defines ChromaDB/BM25 as the retrieval stores. fileciteturn19file6L1-L13 fileciteturn20file2L1-L17

## 3. Existing Architecture

Phase 1 owns ingestion, OCR/parsing, metadata, chunking, embeddings, ChromaDB, BM25 and hybrid retrieval. Phase 2 consumes those retrieval results and owns verification, reasoning, risk, contradiction detection, response construction and orchestration. The TRD explicitly requires this separation. fileciteturn20file9L1-L12

The application has exactly two frontend applications: a User Website and a Management Website. Expert and Admin are role-specific areas within Management. fileciteturn19file11L1-L15

## 4. Target Architecture

```text
ADMIN
  ↓
Management Website
  ↓
FastAPI /api/v1/admin/documents
  ↓
Document Service
  ├── PostgreSQL metadata
  └── secure PDF storage
          ↓
    Existing Phase 1 ingestion
          ↓
    extraction/OCR → metadata → chunks → embeddings
          ↓
       ┌───────────────┐
       ↓               ↓
   ChromaDB           BM25
   dense              sparse
       └───────┬───────┘
               ↓
        existing hybrid retrieval
               ↓
          Phase 2 Adapter
```

## 5. Database Design

Create a SQLAlchemy `Document` model only after inspecting the existing models.

Supported conceptual fields from the backend schema:

- `document_id`
- `document_name`
- `document_type`
- `source`
- `version`
- `publication_date`
- `ingestion_timestamp`
- `status`

Additional operational fields may be justified after repository inspection:

- `filename`
- `storage_reference`
- `uploaded_by`
- `page_count`
- `ingestion_error`
- `indexing_status`
- content hash for duplicate detection

Do **not** store embeddings or the BM25 index in PostgreSQL. The backend schema explicitly assigns ChromaDB to dense retrieval and BM25 to sparse retrieval. fileciteturn20file2L1-L17

## 6. Document Lifecycle

Use an explicit lifecycle:

```text
UPLOADING
   ↓
PROCESSING
   ↓
INDEXING
   ↓
COMPLETED
```

Any processing/indexing failure becomes:

```text
FAILED
```

A document must not be reported as searchable until both required retrieval indexes have been successfully updated.

## 7. Ingestion Design

First inspect `ingest.py`, `index.py`, and the actual Phase 1 services.

If they are CLI-oriented, extract the **smallest reusable service boundary** while preserving existing CLI behavior.

Do not implement a second PDF/OCR/chunking/embedding pipeline.

Required flow:

```text
PDF
 ↓
validation
 ↓
secure storage
 ↓
existing extraction/OCR
 ↓
existing metadata processing
 ↓
existing chunking
 ↓
existing embeddings
 ↓
ChromaDB + BM25
 ↓
validation
 ↓
COMPLETED
```

The existing Phase 1 responsibilities are explicitly protected by the TRD. fileciteturn20file9L1-L12

## 8. ChromaDB Integration

Keep ChromaDB as the dense semantic index.

For each uploaded document:

1. Produce chunks through existing Phase 1 logic.
2. Generate embeddings using the existing embedding implementation.
3. Store chunks using deterministic document/chunk IDs.
4. Preserve document name, page, section/clause and provenance metadata.
5. Validate that the expected records were written.

The resulting data must remain compatible with the existing retrieval contract.

## 9. BM25 Integration

BM25 is mandatory and must not be removed.

The current BM25 persistence mechanism must be inspected before implementation. If it is a shared pickle, do not mutate it unsafely while queries are executing.

Preferred safe approach:

```text
existing BM25 corpus
       +
new document chunks
       ↓
build temporary updated index
       ↓
validate
       ↓
atomic replacement
```

Use a lock around index replacement if required by the actual implementation.

If a full BM25 rebuild is technically required because the current representation cannot be safely appended, that is an **index update**, not a replacement of BM25.

## 10. Chroma/BM25 Failure Consistency

### Chroma succeeds, BM25 fails

Mark the document `FAILED`; do not mark it searchable.

### BM25 succeeds, Chroma fails

Mark the document `FAILED`; provide controlled retry/reindex recovery.

### Recovery

Use deterministic IDs and idempotent reindexing so failed documents can be retried without duplicate chunks.

Preserve the previous valid BM25 index until the replacement has been validated.

## 11. Duplicate and Version Handling

Do not rely on the browser filename.

Use a content hash and, where applicable, document/version metadata.

Recommended behavior:

```text
same content + same version → duplicate
new version → distinct document record
```

Archive/replace semantics must be implemented only if confirmed by the authoritative requirements or repository audit.

## 12. API Design

The backend schema identifies:

```text
GET  /api/v1/admin/documents
POST /api/v1/admin/documents
```

as intended Management APIs. fileciteturn20file2L14-L17

Before implementation, reconcile the repository and determine whether these already exist.

Additional endpoints should be considered only when justified:

```text
GET    /api/v1/admin/documents/{id}
PATCH  /api/v1/admin/documents/{id}
POST   /api/v1/admin/documents/{id}/reindex
DELETE /api/v1/admin/documents/{id}
```

Every endpoint must require server-side Admin authorization.

Expected access:

```text
USER   → 403
EXPERT → 403
ADMIN  → allowed
```

The backend schema explicitly states that USER and EXPERT cannot manage documents while ADMIN can. fileciteturn20file2L1-L17

## 13. File Upload Security

Implement configurable controls for:

- actual PDF validation, not extension alone,
- maximum upload size,
- malformed PDF rejection,
- filename sanitization,
- generated safe storage names,
- path traversal prevention,
- duplicate detection,
- protected storage outside public frontend directories,
- sanitized API errors.

Never trust the browser-provided filename.

Never expose API keys, stack traces or private audit information.

## 14. Ingestion Execution

Inspect the existing runtime before choosing synchronous versus background processing.

For larger PDFs, prefer controlled background processing with PostgreSQL status persistence:

```text
POST upload
 ↓
UPLOADING
 ↓
PROCESSING
 ↓
INDEXING
 ↓
COMPLETED / FAILED
```

Do not introduce a heavyweight queue unless the repository demonstrates a real need.

## 15. Admin Management Website

The UI brief explicitly defines an Admin area containing **Documents** and a reusable **DocumentManager** component. fileciteturn18file0L1-L15

Proposed Admin navigation:

```text
Admin
├── Dashboard
├── Users
├── Documents
├── System Health
├── Metrics
├── Errors
└── Audit
```

Documents page:

```text
Policy Documents

[ + Upload Policy ]

Document       Version     Status       Action
------------------------------------------------
Policy A       V03         COMPLETED    View
Policy B       V02         PROCESSING   View
Policy C       V01         FAILED       Retry
```

Upload form:

```text
Upload Policy

PDF File
Document Name
Document Type
Source
Version
Publication Date

[ Upload Policy ]
```

Only display metadata that survives reconciliation with the final backend contract.

## 16. Expert Permissions

Expert remains focused on:

- Review Queue,
- ReviewTask,
- evidence inspection,
- reasoning/risk/contradiction inspection,
- Approve,
- Correct,
- Comment.

Expert must not receive document upload/edit/delete/reindex privileges. The backend access matrix explicitly gives document management only to ADMIN. fileciteturn20file2L14-L17

## 17. User Restrictions

The User Website must contain no:

- document upload,
- document deletion,
- document editing,
- reindex controls,
- Admin document-management navigation.

The two applications remain separate, with User ↔ Management interaction occurring through product workflows such as review status rather than frontend navigation. fileciteturn19file11L1-L15

## 18. Audit Logging

The PRD requires audit records, and the backend schema defines `AuditRecord`. Document operations should therefore integrate with the existing audit mechanism.

Potential event names should be reconciled with the current implementation:

```text
DOCUMENT_UPLOADED
DOCUMENT_PROCESSING
DOCUMENT_INDEXED
DOCUMENT_FAILED
DOCUMENT_REINDEXED
DOCUMENT_ARCHIVED
DOCUMENT_DELETED
```

Do not introduce duplicate audit infrastructure.

## 19. Error Handling

Use controlled error categories such as:

```text
INVALID_FILE
FILE_TOO_LARGE
MALFORMED_PDF
EXTRACTION_FAILED
EMBEDDING_FAILED
CHROMA_INDEX_FAILED
BM25_INDEX_FAILED
DUPLICATE_DOCUMENT
UNAUTHORIZED
```

Public responses must be sanitized; detailed diagnostics belong in protected logs/audit records.

## 20. Concurrency and Recovery

BM25 is shared mutable state and therefore requires controlled updates.

Use:

- index locking,
- temporary index construction,
- validation,
- atomic replacement,
- backup of the last known-good index.

For ChromaDB, use deterministic IDs so retries do not duplicate chunks.

A PostgreSQL `COMPLETED` status should be written only after retrieval-index validation succeeds.

## 21. Testing Strategy

### Backend

Test:

- Admin upload,
- USER → 403,
- EXPERT → 403,
- PDF validation,
- oversized/malformed PDFs,
- metadata validation,
- duplicate detection,
- lifecycle states,
- Chroma indexing,
- BM25 indexing,
- partial failure,
- recovery,
- idempotent reindexing.

### Critical integration test

```text
Admin uploads policy PDF
 ↓
PostgreSQL Document
 ↓
Phase 1 ingestion
 ↓
ChromaDB + BM25
 ↓
COMPLETED
 ↓
User asks relevant policy question
 ↓
Hybrid retrieval
 ↓
Retrieval Agent
 ↓
evidence/citation from newly uploaded document
```

### Frontend

Test:

- Admin-only Document navigation,
- upload form,
- PDF validation,
- metadata submission,
- status rendering,
- failure rendering,
- retry/reindex controls where implemented,
- document list/detail views.

### Regression

Run:

```text
pytest phase2/tests -v
pytest backend/app/tests -v
```

Also build both frontend applications.

## 22. Docker Impact

Reuse the existing Docker topology.

Do not add another database.

Required persistence:

- PostgreSQL,
- uploaded PDF storage,
- ChromaDB,
- BM25 index.

If local filesystem storage is used, mount it through a persistent Docker volume and keep it outside public frontend directories.

## 23. Exact Files to Inspect/Create/Modify

First inspect the actual repository. Candidate locations:

```text
backend/app/models/document.py
backend/app/schemas/document.py
backend/app/repositories/document_repository.py
backend/app/services/document_service.py
backend/app/routers/admin.py
backend/app/dependencies/auth.py
backend/app/config/settings.py

phase1/.../ingest.py
phase1/.../index.py
phase1/.../app.py

management/app/admin/page.tsx
management/components/admin/document-manager.tsx
management/components/admin/document-upload.tsx
management/components/admin/document-status.tsx
management/lib/api-client.ts

backend/app/tests/test_documents.py
backend/app/tests/test_document_rbac.py
backend/app/tests/test_document_ingestion.py
management/__tests__/documents.test.tsx
```

The exact paths must be determined from repository inspection.

## 24. Implementation Sequence

### Step 1 — Repository-first audit
Inspect models, routers, ingestion, ChromaDB, BM25, storage, Docker and tests.

### Step 2 — Document model
Create only justified PostgreSQL fields.

### Step 3 — Repository/service
Implement document persistence and lifecycle handling.

### Step 4 — Reusable Phase 1 boundary
Expose existing ingestion/indexing functions without changing their behavior or CLI use.

### Step 5 — ChromaDB update
Connect the new document to the existing dense index while preserving provenance.

### Step 6 — BM25 update
Implement safe update/rebuild and atomic replacement where necessary.

### Step 7 — Upload security
Validate file content, size, storage path and duplicates.

### Step 8 — Admin API
Implement/reconcile document endpoints with server-side Admin RBAC.

### Step 9 — Status tracking
Persist processing/indexing lifecycle.

### Step 10 — Management UI
Add Admin-only DocumentManager, upload form, list, details and status.

### Step 11 — Audit integration
Use the existing audit mechanism.

### Step 12 — Tests
Add document, RBAC, indexing and failure-recovery tests.

### Step 13 — Regression
Run backend and Phase 2 suites.

### Step 14 — Docker verification
Clean rebuild, restart, and verify persistence.

### Step 15 — End-to-end retrieval
Upload a real insurance policy, then prove that a relevant User query retrieves evidence from that newly uploaded policy.

## 25. Risks

| Risk | Mitigation |
|---|---|
| BM25 index corruption | Lock + temporary index + validation + atomic replacement |
| Chroma/BM25 inconsistency | Explicit status + reindex/recovery |
| Large PDF timeout | Controlled background processing |
| Duplicate policies | Content hash + version |
| Unauthorized upload | Server-side Admin RBAC |
| Accidental Phase 1 change | Minimal reusable boundary + regression tests |
| Lost PDFs after restart | Persistent Docker volume |
| Retrieval provenance loss | Preserve document/page/section metadata |

## 26. Rollback Strategy

Before implementation:

```text
git status
git diff
git checkpoint/commit
```

During implementation:

- isolate changes,
- preserve the previous BM25 index,
- do not modify Phase 2,
- do not remove existing Chroma collections,
- keep the original CLI ingestion path working.

If the feature fails:

1. Disable the Admin document endpoint.
2. Restore previous document-service/router changes.
3. Restore the previous BM25 index if necessary.
4. Remove incomplete metadata records.
5. Re-run regression tests.

## 27. Definition of Done

### Admin
- [ ] Admin can open Documents.
- [ ] Admin can upload a valid PDF.
- [ ] Supported metadata is stored.
- [ ] Processing/indexing status is visible.
- [ ] Failures are safely reported.
- [ ] Required document operations work.

### Security
- [ ] USER receives 403.
- [ ] EXPERT receives 403.
- [ ] ADMIN is server-authorized.
- [ ] Unsafe files are rejected.
- [ ] Secrets are never exposed.

### Retrieval
- [ ] Existing Phase 1 ingestion is reused.
- [ ] ChromaDB is updated.
- [ ] BM25 is updated.
- [ ] Provenance is preserved.
- [ ] Hybrid retrieval remains functional.
- [ ] BM25 remains intact.

### End-to-end
- [ ] Newly uploaded policy answers a relevant User query.
- [ ] Citation identifies the correct document/page.
- [ ] Phase 2 remains unchanged.
- [ ] User and Management applications remain separated.

### Quality
- [ ] Document tests pass.
- [ ] RBAC tests pass.
- [ ] Ingestion/indexing tests pass.
- [ ] Phase 2 regression passes.
- [ ] Backend regression passes.
- [ ] User frontend builds.
- [ ] Management frontend builds.
- [ ] Docker verification passes.

## 28. Architecture Freeze

The following remain frozen unless repository inspection proves a concrete requirement violation or bug:

```text
BM25
ChromaDB
BGE-small
4096 chunk size
512 overlap
top_k = 8
min_relevance_score = 0.3

Phase 2 Agents
AgentOrchestrator
LLMProviderManager

OpenRouter
  ↓
Groq Key 1
  ↓
Groq Key 2
  ↓
Ollama

PostgreSQL application database

User Website
Management Website
```

No LangChain, LangGraph, CrewAI, AutoGen or other agent framework should be introduced.

The implementation plan must respect the project's change-control rule: inspect the repository first, make the smallest required change, test it, and document it. fileciteturn19file3L1-L19

## 29. Final Rule

Policy Document Management ends at safely making approved documents available to the existing retrieval layer.

It must not:

- generate answers,
- call Phase 2 agents directly,
- replace BM25,
- replace ChromaDB,
- modify Phase 2 orchestration,
- expose provider credentials,
- expose Admin functionality through the User Website.

The authoritative UI brief explicitly includes Documents and `DocumentManager` under Admin, while the backend schema explicitly denies document management to USER and EXPERT. fileciteturn18file0L1-L15 fileciteturn20file2L14-L17

## 30. Source Reconciliation

The six documents define the intended architecture; the executable repository and tests remain the final implementation authority. The plan therefore deliberately marks additional CRUD/reindex/version/archive behavior for repository/requirements reconciliation rather than silently treating every suggested operation as mandatory.

**Planning only. No production code changes are authorized by this document.**
