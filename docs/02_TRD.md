# 02 — Technical Requirements Document (TRD)

## 1. Technical Objective

Define the technology stack, architecture constraints, interfaces, deployment model, configuration strategy, security model, and engineering rules for the AI-Driven Insurance Knowledge Assessment System.

Existing working modules are the baseline. Do not rewrite or move them without a verified defect, incompatibility, or requirement gap.

## 2. High-Level Architecture

```text
                 ┌─────────────────────────┐
                 │      USER WEBSITE       │
                 │ React + TypeScript      │
                 │ User Dashboard          │
                 └────────────┬────────────┘
                              │
                     HTTPS / API calls
                              │
                              ▼
                 ┌─────────────────────────┐
                 │       FASTAPI           │
                 │ HTTP/API Adapter        │
                 │ Auth + RBAC             │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │   AGENT ORCHESTRATOR    │
                 └────────────┬────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
     Query                 Retrieval           Verification
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
                         Reasoning
                              │
                              ▼
                            Risk
                              │
                              ▼
                       Contradiction
                              │
                              ▼
                       Response Builder
                              │
                              ▼
                        FinalResponse
                              │
                              ▼
                    FastAPI → User Website


        ┌──────────────────────────────────────────┐
        │       MANAGEMENT WEBSITE                 │
        │  Separate frontend application            │
        │                                           │
        │  ┌────────────────┐ ┌──────────────────┐ │
        │  │ Expert Area    │ │ Admin Area       │ │
        │  │ Review Queue   │ │ Monitoring       │ │
        │  │ Approve/Edit   │ │ Documents/Users  │ │
        │  └────────────────┘ └──────────────────┘ │
        └──────────────────────────────────────────┘
                              │
                         Same backend
                         + RBAC + APIs
```

## 3. Frontend Stack

Required:
- React
- TypeScript
- Vite
- Material UI (MUI)

### User Website
A standalone frontend for USER functionality.

### Management Website
A separate frontend for EXPERT and ADMIN functionality.

Expert and Admin share this application but have different protected areas and permissions.

The User Website must not contain normal links to the Management Website.

## 4. Backend Stack

- Python
- FastAPI
- Pydantic
- Python typing
- YAML/environment configuration
- dependency injection
- structured logging.

FastAPI is an adapter and orchestration entry boundary. It must not contain retrieval/reasoning/risk/contradiction business logic.

## 5. RAG Stack

### Document Processing
- PDF ingestion
- OCR/layout extraction where required
- metadata extraction
- chunking.

### Dense Retrieval
Use the embedding implementation already established by the repository, such as Sentence-BERT where applicable.

### Vector Store
ChromaDB.

### Sparse Retrieval
BM25.

### Hybrid Retrieval
Combine semantic and keyword retrieval through the existing retrieval architecture.

Preserve source document/page metadata.

## 6. LLM Architecture

Use the existing LLM abstraction.

Requirements:
- no provider SDK calls scattered across agents,
- provider/model configuration externalized,
- prompts externalized where required,
- structured output validation,
- timeout/retry configuration,
- provider-specific code hidden behind interfaces.

The repository's current provider/model configuration is authoritative. Do not replace it without a verified requirement.

## 7. LangChain

LangChain may be used where already appropriate for:
- document processing,
- text splitting,
- embeddings,
- vector stores,
- retriever abstractions,
- prompt/runnable abstractions.

Do not force every agent into LangChain's agent framework.

The project's multi-agent architecture remains controlled by its interfaces and Agent Orchestrator.

Do not migrate to LangGraph/CrewAI/AutoGen merely for stylistic reasons.

## 8. Agent Architecture

Execution sequence:

```text
Query Understanding
        ↓
Retrieval
        ↓
Verification
        ↓
Reasoning
        ↓
Risk
        ↓
Contradiction Detection
        ↓
Response Builder
```

Rules:
- specialized responsibilities,
- typed contracts,
- dependency injection,
- stateless services where possible,
- configurable limits,
- no direct agent-to-agent calls,
- Orchestrator controls execution.

## 9. Phase 1 Responsibilities

Phase 1 owns:
- ingestion,
- OCR,
- parsing,
- metadata,
- chunking,
- embeddings,
- ChromaDB,
- BM25,
- hybrid retrieval.

Phase 2 must reuse Phase 1 retrieval capabilities.

## 10. Phase 2 Responsibilities

Phase 2 owns:
- query understanding,
- retrieval adaptation/orchestration,
- evidence verification,
- reasoning,
- risk assessment,
- contradiction detection,
- response construction,
- orchestration,
- observability,
- validation.

## 11. Authentication and Authorization

Roles:
```text
USER
EXPERT
ADMIN
```

### Application mapping
```text
USER
  ↓
User Website

EXPERT
  ↓
Management Website → Expert Area

ADMIN
  ↓
Management Website → Admin Area
```

### Critical rule
The frontend must not be the security boundary.

Backend authorization must enforce:
- User cannot access Expert endpoints.
- User cannot access Admin endpoints.
- Expert cannot access Admin endpoints unless explicitly granted Admin permissions.
- Admin access is independently authorized.

## 12. Application URLs

Use configuration:

```text
USER_APP_URL
MANAGEMENT_APP_URL
```

Example only:

```text
https://app.example.com
https://management.example.com
```

Do not hardcode actual deployment URLs in application logic.

## 13. API Requirements

Versioned APIs:
```text
/api/v1/
```

Minimum:
```text
POST /api/v1/auth/login
POST /api/v1/query
GET  /api/v1/health
GET  /api/v1/ready
GET  /api/v1/version
```

Management endpoints must be role-protected.

Examples:
```text
GET  /api/v1/expert/reviews
GET  /api/v1/expert/reviews/{id}
POST /api/v1/expert/reviews/{id}/approve
POST /api/v1/expert/reviews/{id}/correct

GET  /api/v1/admin/metrics
GET  /api/v1/admin/errors
GET  /api/v1/admin/documents
POST /api/v1/admin/documents
```

These examples must be reconciled with the actual repository before implementation.

## 14. Configuration

Externalize:
- model/provider
- thresholds
- timeouts
- retries
- paths
- vector store
- database/storage
- CORS
- JWT
- observability
- application URLs.

Never store secrets in source control.

## 15. Security

- authentication,
- server-side RBAC,
- sanitized errors,
- protected audit logs,
- PII masking/hashing where required,
- prompt-injection resistance,
- upload validation,
- path traversal protection,
- request-size limits,
- secure CORS,
- no frontend secrets.

## 16. Observability

Must support:
- structured logs,
- execution metrics,
- agent timings,
- retries,
- failures,
- traces,
- audit events,
- health,
- alerts.

Observability must not alter business results.

## 17. Testing

Required:
- unit,
- integration,
- system/E2E,
- regression,
- security,
- performance,
- stress,
- concurrency,
- recovery,
- deployment.

## 18. Deployment

Docker baseline:
- User frontend
- Management frontend
- FastAPI backend
- ChromaDB/vector service where required
- persistent storage
- environment configuration
- health checks.

## 19. Hard Constraints

1. Do not move Phase 1/Phase 2 without a verified critical reason.
2. Do not rebuild completed modules.
3. Do not hardcode configurable business logic.
4. Do not bypass the Orchestrator.
5. Do not put RAG/agent logic in FastAPI.
6. Do not put RAG/business logic in React.
7. Do not expose Management login/navigation from the User Website.
8. Do not treat frontend route hiding as authorization.
9. Do not merge User and Management applications into one frontend navigation.
10. Preserve existing contracts and backward compatibility.
