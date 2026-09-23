# Complete Architecture Audit

## 1. Top-Level Structure
- `backend/`: FastAPI application providing API routes, RBAC enforcement, and database repositories.
- `frontend/`: Next.js application for normal USER functionality (queries, chat history).
- `management/`: Next.js application for EXPERT and ADMIN functionality (review tasks, docs).
- `phase2/`: Core Agentic RAG logic (Query, Retrieval, Verification, Reasoning, Risk, Contradiction).
- `data/`: Persistent storage directories (Uploads, ChromaDB).
- `scripts/`: Evaluation and administrative Python scripts.

## 2. Component Analysis
### 2.1 Backend Services
- Uses FastAPI as the REST adapter.
- Enforces strict backend authorization rules per endpoint.
- Connects to PostgreSQL (`phase2_app.db` via SQLite for local dev/testing based on repo artifacts, need to verify Postgres configuration in Docker).

### 2.2 Phase 1 (Legacy / Ingestion)
- The directory `phase1/` does not exist. Instead, the legacy ingestion and monolithic code (`ingest.py`, `app.py`) resides in the root directory.

### 2.3 Phase 2 (Agentic RAG)
- Isolated in `phase2/`.
- Uses `LLMProviderManager` for OpenRouter -> Groq -> Local Ollama fallback.
- Uses `ChromaDB` for Dense embeddings and `BM25` for Sparse retrieval.

### 2.4 Frontend Applications
- Both `frontend/` and `management/` use Next.js, React, Tailwind CSS (or similar styling).
- They are completely independent frontend directories, physically enforcing the separation rule.

## 3. Discrepancies and Observations
- **Missing `phase1/` Directory**: The PRD refers to "Phase 1" responsibilities. These are implemented via top-level scripts rather than a dedicated `phase1/` namespace.
- **Database Architecture**: `phase2_app.db` (SQLite) is present in the root. Need to verify if PostgreSQL is correctly deployed via Docker, or if SQLite is being used in production.

## 4. Conclusion
The repository strictly adheres to the frontend separation rule and the Phase 2 multi-agent encapsulation rule. Further tests are required to confirm database persistence strategies (PostgreSQL vs SQLite).
