# 02 — Technical Requirements Document (TRD)

## 1. Technical Objective

Define the technology stack, architecture constraints, interfaces, deployment model, configuration strategy, security model, LLM provider resilience model, and engineering rules for the AI-Driven Insurance Knowledge Assessment System.

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


                    LLM PROVIDER LAYER
                              │
                     Existing LLM Abstraction
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
               OpenRouter          Groq
                Provider A          Provider B
                    │                   │
                    └──── Automatic ───┘
                         Failover
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

The LLM layer must use the existing abstraction rather than direct provider calls from agents.

Required architecture:

```text
Agent
  ↓
ILLMAnalyzer / existing LLM abstraction
  ↓
LLM Provider Manager
  ↓
Provider Adapter Interface
  ├── OpenRouter Adapter
  └── Groq Adapter
```

### Provider Requirements

Supported providers:
- OpenRouter
- Groq

The provider names, models, endpoints, timeouts, retry limits, and failover rules must be configuration-driven.

API keys must be supplied through environment variables/secrets.

Suggested environment variables:

```text
OPENROUTER_API_KEY
GROQ_API_KEY
```

Actual names must be reconciled with the existing repository before implementation.

### Automatic Provider Switching

The Provider Manager must:
1. select the configured preferred provider,
2. execute the complete request,
3. classify provider errors,
4. retry according to configured limits,
5. switch to the secondary provider when a configured failover condition occurs,
6. retry the complete request using the secondary provider,
7. return one validated response,
8. record provider/failover telemetry.

The system must not expose provider switching to normal users.

### Provider State

The Provider Manager may maintain a controlled health state such as:

```text
AVAILABLE
DEGRADED
COOLDOWN
UNAVAILABLE
```

State changes must be thread-safe and configuration-driven.

### Failback

When configured, the manager may return to the preferred provider after a successful health/cooldown period.

### Do Not Do This

```text
QueryAgent → OpenRouter SDK
ReasoningAgent → Groq SDK
RiskAgent → OpenRouter SDK
```

Correct:

```text
All LLM agents
      ↓
Existing LLM abstraction
      ↓
Provider Manager
      ↓
OpenRouter OR Groq
```

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

The provider failover layer may use LangChain provider integrations if they fit the existing abstraction, but provider-specific logic must remain behind the project's LLM interface.

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
- Orchestrator controls execution,
- agents use the LLM abstraction,
- provider failover is invisible to agents.

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
Management Website → Expert area

ADMIN
  ↓
Management Website → Admin area
```

Backend authorization is authoritative.

## 12. Application URLs

Use configuration:

```text
USER_APP_URL
MANAGEMENT_APP_URL
```

Actual deployment URLs must not be hardcoded in application logic.

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

## 14. Configuration

Externalize:
- model/provider,
- provider priority,
- provider timeouts,
- provider retries,
- provider cooldown,
- failover conditions,
- thresholds,
- agent timeouts,
- paths,
- vector store,
- database/storage,
- CORS,
- JWT,
- observability,
- application URLs.

Never store secrets in source control.

Example logical configuration:

```yaml
llm:
  strategy: automatic_failover
  primary_provider: openrouter
  secondary_provider: groq

  providers:
    openrouter:
      enabled: true
      model: configured_value
      timeout_seconds: configured_value

    groq:
      enabled: true
      model: configured_value
      timeout_seconds: configured_value

  failover:
    enabled: true
    max_retries_per_provider: configured_value
    switch_on_timeout: true
    switch_on_rate_limit: true
    switch_on_transient_error: true
    cooldown_seconds: configured_value
    failback_enabled: true
```

This is a schema example, not permission to hardcode these values.

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
- no frontend secrets,
- no API keys in logs,
- no API keys in error messages.

Provider failover must not disclose secret material.

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
- alerts,
- provider used,
- provider switch count,
- provider failure reason category,
- provider latency.

Never log:
- API keys,
- Authorization headers,
- raw sensitive prompts unless explicitly approved,
- secret provider responses.

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

Additional provider tests:
- primary success,
- primary timeout → secondary success,
- primary rate limit → secondary success,
- primary 5xx → secondary success,
- both providers unavailable,
- malformed provider response,
- provider authentication/configuration failure,
- failback after recovery,
- concurrent requests,
- no context leakage,
- no secret leakage,
- structured output compatibility across providers.

## 18. Deployment

Docker baseline:
- User frontend
- Management frontend
- FastAPI backend
- ChromaDB/vector service where required
- persistent storage
- environment configuration
- health checks.

LLM credentials are injected as runtime secrets/environment variables.

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
11. Do not place OpenRouter/Groq SDK calls inside individual agents.
12. Do not expose provider-selection controls to normal users.
13. Do not combine partial responses from multiple providers.
14. A provider switch must not change conversation_id or user context.
15. Provider secrets must never be committed or exposed.
16. Do not silently hide permanent configuration/authentication errors behind repeated failover.
