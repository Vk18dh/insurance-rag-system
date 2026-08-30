# Policy Document Management Final Audit

This document serves as the final repository audit and approval checkpoint before implementing the Policy Document Management feature, comparing the proposed implementation plan against the actual state of the repository.

## 1. Current Implementation

- **Phase 1 Ingestion (`ingest.py` / `index.py`)**: Exists as standalone CLI scripts. `ingest.py` reads from `data/pdfs/` and writes JSON to `data/extracted/`. `index.py` chunks the JSONs, embeds using `SentenceTransformer`, and writes to `ChromaDB` (`data/chroma_db`) and `BM25` (`data/bm25_index.pkl`).
- **ChromaDB Integration**: Configured in `config.py` to use `data/chroma_db`. Currently, `index.py` deletes the entire collection before rebuilding.
- **BM25 Implementation**: Uses `rank_bm25`, persisting the instance and chunk data to a pickle file (`data/bm25_index.pkl`).
- **PostgreSQL Models**: `User`, `Message`, `Conversation`, and `ReviewTask` exist in `backend/app/models/`. No `Document` model exists.
- **Admin Router**: `backend/app/routers/admin.py` exists with `/dashboard`, `/metrics`, and `/provider-health`. Document APIs are missing.
- **Management Website**: `management/app/admin/page.tsx` provides an Admin metrics dashboard. No document UI exists.
- **Auth/RBAC**: Fully implemented. `require_admin_role` exists in `backend/app/dependencies/auth.py` and is used in the admin router.

## 2. Required Implementation

The implementation must bridge the FastAPI backend (and Management UI) to the existing Phase 1 ingestion logic without breaking CLI compatibility or replacing existing stores.

## 3. Files That Must Change

- `backend/app/models/document.py` (New)
- `backend/app/schemas/document.py` (New)
- `backend/app/routers/admin.py` (Add `/documents` endpoints)
- `backend/app/services/ingestion_service.py` (New - wraps `ingest.py` and `index.py` logic)
- `ingest.py` & `index.py` (Refactor strictly to expose internal functions for the service, preserving CLI behavior)
- `management/app/admin/layout.tsx` (Add sidebar link)
- `management/app/admin/documents/page.tsx` (New - Document Manager UI)
- `management/components/admin/document-upload-dialog.tsx` (New)
- `backend/app/tests/test_documents.py` (New)

## 4. Files That Must Remain Frozen

- All Phase 2 Agent logic (`backend/app/agents/*` or `phase2/services/*`).
- `backend/app/routers/query.py`.
- Vector and sparse store abstractions.
- All User Website frontend code.

## 5. Database Changes

- **Requirement**: Create `Document` model in PostgreSQL to track upload and processing status (id, document_name, document_type, source, version, publication_date, ingestion_timestamp, status, error_message).
- **Migration**: Requires Alembic migration to create the table.

## 6. API Changes

- `GET /api/v1/admin/documents`: List documents.
- `POST /api/v1/admin/documents`: Upload PDF + metadata. Returns `202 Accepted` and executes ingestion in `fastapi.BackgroundTasks`.
- `DELETE /api/v1/admin/documents/{id}`: Remove document from DB, ChromaDB, and BM25.

## 7. Phase 1 Ingestion Integration

- `ingest.py` functions (`process_pdf`, `post_process_elements`) and `index.py` functions (`chunk_elements`) will be imported by `ingestion_service.py`.
- Uploaded PDFs will be saved to a safe `data/uploads/` directory before processing.

## 8. ChromaDB Integration

- The `delete_collection()` behavior in `index.py` will be bypassed during single-document API uploads. 
- The new chunks will be appended using `collection.add(...)` with deterministic chunk IDs tied to the `document_id`.

## 9. BM25 Integration

- BM25 cannot be appended natively.
- **Safe approach**: The background task will unpickle `bm25_index.pkl`, extract all existing chunks, append the new document's chunks, re-tokenize, fit a new `BM25Okapi` instance, and re-pickle. A lock (e.g., `asyncio.Lock` or file-based lock) will prevent concurrent corruption during multiple uploads.

## 10. Admin UI Changes

- Add a "Documents" tab.
- Build a Data Table listing policy metadata and status (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`).
- Build a modal for PDF upload and metadata entry.

## 11. Security

- PDF MIME validation (`application/pdf`).
- Save uploaded files with sanitized names (e.g., `{uuid}.pdf`).
- Endpoints protected by `require_admin_role`.
- No exposed stack traces on ingestion failure (saved to DB `error_message` instead).

## 12. Docker/Storage Changes

- Ensure `data/uploads/` is tracked and mounted correctly, similar to `data/pdfs/` and `data/chroma_db/`.

## 13. Testing Plan

- Backend unit tests for `ADMIN` only access.
- Upload validation (reject bad files).
- Integration test: Upload triggers background task, which updates ChromaDB and the BM25 pickle.
- E2E Test: Uploaded policy answers a relevant Phase 2 query.

## 14. Risks

- **BM25 Race Conditions**: Concurrent uploads could corrupt the pickle file if not locked.
- **Event Loop Blocking**: `unstructured` OCR is CPU bound. Must use `BackgroundTasks` properly (or a separate process) to not block FastAPI.

## 15. Rollback Plan

- Remove the `Document` DB table.
- Remove API endpoints from `admin.py`.
- Revert `ingest.py` and `index.py` to baseline.
- Restore `data/bm25_index.pkl` from a backup.

## 16. Corrections to POLICY_DOCUMENT_MANAGEMENT_IMPLEMENTATION_PLAN.md

- **Embedding Model**: The authoritative requirements specify `BGE-small`. However, `config.py` currently defaults to `all-MiniLM-L6-v2`. The implementation plan did not explicitly address this discrepancy. We will enforce `BGE-small` via the `.env` overrides or adjust `config.py` if authorized, to match the architecture freeze requirement.
- **Database Migrations**: The plan did not mention generating an Alembic migration for the `Document` table, which is mandatory for deployment.
- **File Locks**: The plan suggested BM25 locks but must make file-locking mandatory to prevent pickle corruption on concurrent Admin uploads.
