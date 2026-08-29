# Database Architecture Verification

## 1. Application Database
**APPLICATION DATABASE: PostgreSQL / SQLite (Fallback for testing)**

- **PostgreSQL**: When the application runs via Docker (`docker-compose.yml`), a `postgres:15-alpine` container is provisioned. The `DATABASE_URL` environment variable is explicitly passed to the backend service as `postgresql://user:password@postgres:5432/majorcode`.
- **SQLite**: When running locally without Docker (e.g., during `pytest` executions), `backend/app/config/settings.py` defaults to `sqlite:///./phase2_app.db` if `DATABASE_URL` is not provided in the environment.

**Entities stored in PostgreSQL (when running in production/Docker):**
- **Users**: Mapped via `backend/app/models/user.py`
- **Conversations**: Mapped via `backend/app/models/conversation.py`
- **Messages**: Mapped via `backend/app/models/message.py`
- **ReviewTasks**: Mapped via `backend/app/models/review_task.py`

*Evidence:*
- `docker-compose.yml` (Lines 13, 21, 57-67)
- `backend/app/config/settings.py` (Lines 42-46)
- `backend/app/db/database.py` (Handles connection strings dynamically)

## 2. Retrieval Databases
**RETRIEVAL DATABASE: ChromaDB**
- ChromaDB remains the authoritative vector store for dense semantic retrieval.
- It is deployed as a standalone service (`chromadb/chroma:latest`) on port 8001 via `docker-compose.yml`.

**SPARSE RETRIEVAL: BM25**
- BM25 remains the authoritative engine for sparse keyword retrieval.
- Phase 2 actively integrates with Phase 1's BM25 index via `Phase1RetrieverAdapter` (e.g., `phase2/services/retrieval_service.py`), utilizing `bm25_search()`.

*Evidence:*
- `docker-compose.yml` (Lines 48-55)
- `phase2/services/retrieval_service.py` (Dynamically combines Vector and BM25 scores)

## 3. Test Database
**TEST DATABASE: SQLite**
- SQLite is exclusively used as the default fallback for local development and testing. Automated tests use `sqlite:///./phase2_app.db` or in-memory execution to avoid requiring a live Postgres instance.
- No SQLite test code or dependencies were removed.

## 4. Conclusion
PostgreSQL is strictly used for relational application data (Users, Conversations, Messages, ReviewTasks) and operates securely in the Docker composition. It has **never** replaced, modified, or absorbed the roles of ChromaDB (Vector) or BM25 (Sparse) retrieval mechanisms. Phase 1 and Phase 2 architectures remain fully preserved and decoupled from the relational application database.
