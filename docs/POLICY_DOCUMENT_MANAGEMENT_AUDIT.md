# Policy Document Management Audit

This document is a comprehensive audit of the Policy Document Management requirements derived exclusively from the six authoritative project documents: `01_PRD.md`, `02_TRD.md`, `03_APP_FLOW.md`, `04_UI_UX_DESIGN_BRIEF.md`, `05_BACKEND_SCHEMA.md`, and `06_IMPLEMENTATION_PLAN_FINAL.md`. 

---

## 1. Requirements from Authoritative Documents

The authoritative documents dictate that the system requires an administrative capacity to manage the insurance documents that power the Agentic RAG pipeline.

- **01_PRD.md**: Explicitly states "document management" is an Administrator functionality (Sections 4.3 and 10). "Knowledge Processing" includes PDF/document ingestion.
- **02_TRD.md**: Section 13 defines the exact backend API requirements: `GET /api/v1/admin/documents` and `POST /api/v1/admin/documents`.
- **03_APP_FLOW.md**: Section 8 defines the Admin Flow to include "Documents".
- **04_UI_UX_DESIGN_BRIEF.md**: Section 6 lists "Documents" in the Admin sidebar. Section 14 lists `DocumentManager` as a reusable component for Admin.
- **05_BACKEND_SCHEMA.md**: Section 6 defines the exact `Document` schema. Section 14 (API Access Matrix) explicitly grants `manage documents` solely to the `ADMIN` role.
- **06_IMPLEMENTATION_PLAN_FINAL.md**: Section 9 requires the Admin area to implement "documents". 

---

## 2. Existing Ingestion Pipeline

**Current Architecture (CLI/Batch-based)**
The current ingestion system is isolated into two root scripts (`ingest.py` and `index.py`) running sequentially in a batch process:
1. `ingest.py`: Reads all PDFs from a `PDF_DIR`. Uses `unstructured` (`partition_pdf` with `hi_res` strategy) for OCR and layout parsing (extracting text, titles, tables). It cleans the elements (normalizing whitespace, merging sentences, decoding tables) and writes structured JSON files to `JSON_DIR`.
2. `index.py`: Reads the JSON files. Uses LlamaIndex `SentenceSplitter` for clause-aware chunking. Generates dense embeddings using `SentenceTransformer` and inserts them into `ChromaDB`. Concurrently, it builds a sparse keyword index using `rank_bm25` and saves it via `pickle`.

**Gap**: The existing pipeline is file-system batch-oriented and not integrated into the live FastAPI `backend` for dynamic, single-document upload via API.

---

## 3. Existing Management Website

An inspection of `management/app/admin/page.tsx` reveals:
- An Admin Dashboard exists with `Active Users`, `Queries Today`, `Escalation Rate`, `Avg Latency`, `System Status`, and `LLM Provider Health`.
- **Gap**: There is no "Documents" sidebar, no `DocumentManager` component, no upload UI, and no policy list. 

---

## 4. Missing Functionality

Based on the audit, the following are entirely missing:
1. **Backend Database Models**: A PostgreSQL `Document` model mapping the properties listed in `05_SCHEMA`.
2. **Backend APIs**: Implementation of `GET /api/v1/admin/documents` and `POST /api/v1/admin/documents` in `backend/app/routers/admin.py`.
3. **API-to-Ingestion Bridge**: Logic to take an uploaded PDF buffer from FastAPI, stream it securely to storage, and asynchronously trigger the `ingest.py` and `index.py` logic on the single document.
4. **Management UI**: A dedicated frontend page (`/admin/documents`) for uploading PDFs, viewing the catalog, and checking ingestion status.

---

## 5. Required vs. Optional Features

Classification based purely on the six authoritative documents:

| Feature | Classification | Source / Rationale |
|---|---|---|
| **Policy PDF Upload** | **REQUIRED** | `02_TRD` (`POST /api/v1/admin/documents`) |
| **Policy Listing** | **REQUIRED** | `02_TRD` (`GET /api/v1/admin/documents`) |
| **Policy Metadata Management** | **REQUIRED** | `05_SCHEMA` defines `Document` metadata properties. |
| **Document Versioning** | **REQUIRED** | `05_SCHEMA` lists `version` in the Document schema. |
| **Ingestion Status** | **REQUIRED** | `05_SCHEMA` lists `status` in the Document schema. |
| **Ingestion Error Status** | **OPTIONAL** | Not strictly specified, but implied by `status` tracking. |
| **Document Deletion/Archive** | **NOT SPECIFIED** | The documents specify "manage documents" but do not mandate a `DELETE` endpoint. |
| **Document Replacement** | **NOT SPECIFIED** | No `PUT` endpoint is defined. Versioning implies uploading new versions instead. |
| **Manual Re-indexing** | **NOT SPECIFIED** | Not requested by the architectural documents. |

**Recommendation for unspecified items**: Add a `DELETE` endpoint for repository pruning, but document replacement should just be a new upload with an incremented `version` (immutability).

---

## 6. Admin Permissions

**ADMIN** role is explicitly authorized to:
- Upload policy documents (`POST /api/v1/admin/documents`).
- List policy documents (`GET /api/v1/admin/documents`).
- View ingestion status and metadata.

*Not explicitly specified but implicitly recommended*: Delete/archive. 

---

## 7. Expert Permissions

**EXPERT** role is heavily restricted regarding document management:
- Upload policy? **NO** (`05_SCHEMA` Matrix: Manage documents = No).
- View Policy (Catalog)? **NO** (Not in Expert workflow).
- Inspect Evidence? **YES** (Only via `ReviewTask` citations).
- Modify Policy? **NO**.
- Re-index? **NO**.

---

## 8. User Restrictions

**USER** role is strictly isolated:
- Absolutely no document-management capabilities (`05_SCHEMA`).
- Can only view citations/snippets provided dynamically by the RAG pipeline.

---

## 9. Backend API Requirements

The FastAPI router `backend/app/routers/admin.py` must be expanded:

- `GET /api/v1/admin/documents` (List all documents with pagination/status).
- `POST /api/v1/admin/documents` (Accept `multipart/form-data` with PDF file and metadata parameters: `document_type`, `version`, `source`).

*(Recommended addition)*: `DELETE /api/v1/admin/documents/{id}` for cleanup.

---

## 10. Frontend Requirements

In the Management Website (`management/app/admin`):
- Update Admin Sidebar to include a "Documents" navigation link.
- Create `/admin/documents/page.tsx`.
- Implement `DocumentManager` (Data Table showing `Document Name`, `Version`, `Status`, `Date`).
- Implement an Upload Dialog/Form requesting the PDF, type, and version.

---

## 11. PostgreSQL Impact

Must introduce a `Document` SQLAlchemy model in `backend/app/models/document.py`:
- `id` (UUID)
- `document_name` (String)
- `document_type` (String)
- `source` (String)
- `version` (String)
- `publication_date` (DateTime)
- `ingestion_timestamp` (DateTime)
- `status` (Enum: `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`)

---

## 12. ChromaDB Impact

When a document is uploaded and parsed, its chunks must be inserted into the existing `ChromaDB` collection. 
**Requirement**: The index logic must be updated to append to the collection rather than invoking `client.delete_collection` (which `index.py` currently does during batch processing).

---

## 13. BM25 Impact

The BM25 sparse retrieval relies on `rank_bm25` which is pickled to disk. 
**Requirement**: Because `rank_bm25` is typically immutable after generation, adding a new document dynamically requires either:
1. Reloading the pickle, appending the new tokens, and re-fitting the BM25 index.
2. Generating a full background rebuild of the BM25 index upon document upload completion.

BM25 **must not be removed**.

---

## 14. Security

If PDF upload is implemented, the following protections are mandated:
- **PDF Validation**: Enforce `application/pdf` MIME type checks.
- **File-Size Limits**: Reject excessively large files (e.g., > 50MB) via FastAPI `UploadFile` constraints.
- **Filename Sanitization**: Strip dangerous characters to prevent path traversal when saving to disk.
- **Safe Storage**: Uploads should be stored in a dedicated `data/uploads` volume, not the execution directory.
- **Authentication**: Strict RBAC verification on the `POST` endpoint via `require_admin_role`.

---

## 15. Failure Handling

Ingestion is a heavy process (OCR + Embeddings). 
- **Async Execution**: The `POST` API must accept the file, create a DB record (`status="PENDING"`), and trigger a background task (e.g., `fastapi.BackgroundTasks`), immediately returning `202 Accepted`.
- **Error Capturing**: If `unstructured` or `Chroma` fails, the background task must catch the exception, log it (without raw stack traces in the DB), and update the Postgres record to `status="FAILED"`.

---

## 16. Testing Plan

Tests required for this feature (`pytest backend/app/tests`):
1. **RBAC Rejection**: Verify `USER` and `EXPERT` get HTTP 403 when hitting `POST /api/v1/admin/documents`.
2. **Admin Upload**: Verify `ADMIN` can upload a valid PDF and the DB record is created.
3. **PDF Validation**: Upload a `.txt` disguised as `.pdf` and verify rejection.
4. **Ingestion Mock**: Mock the background task and verify ChromaDB/BM25 append logic.

---

## 17. Risks

1. **Blocking the Event Loop**: `ingest.py` uses heavy CPU-bound processing. It must be strictly offloaded to a background thread/process to prevent FastAPI from hanging.
2. **BM25 Rebuild Cost**: Re-pickling the BM25 index for every document upload might be slow if the corpus gets very large.

---

## 18. Exact Files Requiring Modification

- `backend/app/models/document.py` (NEW)
- `backend/app/schemas/document.py` (NEW)
- `backend/app/routers/admin.py` (MODIFY)
- `backend/app/services/ingestion_service.py` (NEW - bridging `ingest.py` into backend)
- `ingest.py` and `index.py` (MODIFY - adapting for single-document append vs batch rebuild)
- `management/app/admin/layout.tsx` (MODIFY - add sidebar link)
- `management/app/admin/documents/page.tsx` (NEW - UI)

---

## 19. Recommended Implementation Sequence

1. **Database Layer**: Create the `Document` SQLAlchemy model and generate a migration/DB upgrade.
2. **Service Layer Adaptation**: Refactor `ingest.py` and `index.py` into a reusable backend service (`ingestion_service.py`) that supports appending a single document to Chroma and rebuilding the BM25 pickle.
3. **API Endpoints**: Implement `GET` and `POST /api/v1/admin/documents` in FastAPI using `BackgroundTasks`.
4. **Security & Tests**: Add RBAC tests and file validation logic.
5. **Frontend UI**: Build the Admin Documents data table, Upload Dialog, and real-time status indicators in the Next.js Management app.
