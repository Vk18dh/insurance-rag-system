# 06 — Stage 9: Management Website Implementation

This plan outlines the implementation of the Management Website required by the authoritative project documentation (Stage 9).

## Stage 9 Scope

The objective is to implement the Management Website, providing interfaces for EXPERT and ADMIN roles, strictly separated from the Customer/User Website.

## User Review Required

> [!WARNING]
> Please review this implementation plan. It introduces a separate frontend application (`management/`) and updates the FastAPI backend to support ReviewTask workflows and Admin observability metrics.

## Stage 9 Requirements Matrix

| Requirement | Source MD | Backend Implementation | Frontend Implementation | Test | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Separate Management App** | 01_PRD, 03_APP_FLOW | N/A | `management/` Next.js app | Docker test | DEFERRED |
| **Expert Login** | 03_APP_FLOW, 05_SCHEMA | Reuses `POST /api/v1/auth/login` | `management/app/login/page.tsx` | UI Test | DEFERRED |
| **Admin Login** | 03_APP_FLOW, 05_SCHEMA | Reuses `POST /api/v1/auth/login` | `management/app/login/page.tsx` | UI Test | DEFERRED |
| **RBAC / Role Verification** | 02_TRD, 05_SCHEMA | `dependencies/auth.py` (exists) | Next.js Middleware / Layout auth | UI Test | DEFERRED |
| **ReviewTask Data Model** | 05_SCHEMA | `models/review_task.py` | `management/lib/api-client.ts` | Backend Test | DEFERRED |
| **Expert Dashboard/Queue** | 01_PRD, 04_UI_UX | `GET /api/v1/expert/reviews` | `management/app/expert/page.tsx` | UI Test | DEFERRED |
| **ReviewTask Detail** | 04_UI_UX, 05_SCHEMA | `GET /api/v1/expert/reviews/{id}` | `management/app/expert/[id]/page.tsx` | UI Test | DEFERRED |
| **Expert Actions (Approve/Correct)** | 04_UI_UX, 05_SCHEMA | `POST /api/v1/expert/reviews/{id}/action`| Action panels in Review Detail | UI Test | DEFERRED |
| **Admin Dashboard** | 01_PRD, 04_UI_UX | N/A (UI layout) | `management/app/admin/page.tsx` | UI Test | DEFERRED |
| **Admin Metrics & Health** | 05_SCHEMA | `GET /api/v1/admin/metrics`, `health` | Dashboard Metric Cards | UI Test | DEFERRED |
| **No User ↔ Mgmt Navigation** | 01_PRD, 02_TRD | Backend role enforcement | Separate apps (no links) | UI Test | DEFERRED |

## Proposed Changes

### Backend Missing Contracts

Based on the audit, the backend is missing the ReviewTask contracts and the Admin metrics endpoints.

#### [NEW] backend/app/models/review_task.py
- SQLAlchemy model for `ReviewTask` representing human-in-the-loop escalation tasks.

#### [NEW] backend/app/schemas/review_task.py
- Pydantic models for ReviewTask API requests/responses.

#### [MODIFY] backend/app/routers/expert.py
- Add `GET /reviews`, `GET /reviews/{id}`, and `POST /reviews/{id}/approve`, `POST /reviews/{id}/correct`.

#### [MODIFY] backend/app/routers/admin.py
- Add `GET /metrics`, `GET /provider-health`, etc., returning mock or basic system metrics for now, relying on actual DB stats where possible.

#### [NEW] backend/app/tests/test_management_api.py
- Unit tests for the new Expert and Admin endpoints to ensure RBAC enforcement and correct schema serialization.

---

### Management Frontend (New Application)

We will initialize a new Next.js application in `management/` using the same underlying stack (React, Tailwind, Shadcn UI) to allow easy reuse of UI patterns, but completely isolated routing and navigation from `frontend/`.

#### [NEW] management/
- A new Next.js application directory (e.g., `npx create-next-app management`).

#### [NEW] management/app/login/page.tsx
- Authentication entry point specifically for Management. Logs in and checks if the role is `EXPERT` or `ADMIN`.

#### [NEW] management/app/expert/*
- Expert Dashboard, Review Queue, and Review Task Detail pages.

#### [NEW] management/app/admin/*
- Admin Dashboard, System Health, and Metrics.

#### [MODIFY] docker-compose.yml
- Add the `management` service, mapping port 3001, to serve the management app in the Docker topology.

## Verification Plan

### Automated Tests
- `pytest backend/app/tests/test_management_api.py` (Backend APIs & RBAC)
- `vitest` (Frontend Management UI routing & auth logic)

### Manual Verification
- Log in as `USER` on Management app → should be denied access.
- Log in as `EXPERT` on Management app → should see Expert Dashboard, denied Admin Dashboard.
- Log in as `ADMIN` on Management app → should see Admin Dashboard.
- Verify Docker integration with `docker-compose up --build`.

## 1. Purpose

Provide the controlled implementation, audit and verification sequence for the complete AI-Driven Insurance Knowledge Assessment System.

The repository already contains substantial implementation. This is a **completion and verification plan**, not permission to rebuild the system from scratch.

## 2. Golden Rules

1. Read all six documents before modifying code.
2. Inspect the actual repository first.
3. Treat working code as the baseline.
4. Do not rebuild completed functionality.
5. Do not move Phase 1 or Phase 2 without a verified critical reason.
6. Preserve existing contracts.
7. Preserve backward compatibility.
8. No hardcoded configurable business rules.
9. Agents do not directly call agents.
10. Agent Orchestrator controls execution.
11. FastAPI is an adapter.
12. React is presentation.
13. User and Management are separate frontend applications.
14. Expert and Admin share the Management Application.
15. User → Management navigation is prohibited.
16. Cross-application interaction is feature/workflow based.
17. Backend RBAC is authoritative.
18. Run tests after meaningful changes.
19. Do not claim completion without verification.
20. LLM provider selection and failover must remain behind the existing LLM abstraction.
21. Never commit API keys or secrets.
22. A provider switch must not change conversation identity or business logic.

---

# PROJECT STATUS BASELINE

> This section is a project-status reference and is intentionally not a new implementation phase.

## Current Implementation Status

Before implementing anything, Gemini must inspect the actual repository and compare it against this baseline.

| Part | Component | Baseline Status | Default Action |
|---|---|---|---|
| Part 1 | Query Understanding Agent | COMPLETE | Do not rebuild |
| Part 2 | Retrieval Agent | COMPLETE | Do not rebuild |
| Part 3 | Verification Agent | COMPLETE | Do not rebuild |
| Part 4 | Reasoning Agent | COMPLETE | Do not rebuild |
| Part 5 | Risk Agent | COMPLETE | Do not rebuild |
| Part 6 | Contradiction Detection Agent | COMPLETE | Do not rebuild |
| Part 7 | Agent Orchestrator | COMPLETE | Do not rebuild |
| Part 8 | Response Builder | COMPLETE | Do not rebuild |
| Part 9 | Observability Layer | COMPLETE | Do not rebuild |
| Part 10 | Validation & Production Readiness | COMPLETE | Do not rebuild |
| Part 11 | FastAPI / Frontend / Deployment | IMPLEMENTED — VERIFY | Inspect before modifying |

## Phase 1 Status

Phase 1 is the foundational RAG/retrieval layer and is considered an existing implementation.

It includes, where applicable:
- document ingestion,
- PDF processing,
- OCR/layout processing,
- metadata extraction,
- chunking,
- embedding generation,
- ChromaDB/vector retrieval,
- BM25 sparse retrieval,
- hybrid retrieval,
- ranking,
- source/document/page metadata preservation.

**Status:** EXISTING IMPLEMENTATION — VERIFY BEFORE MODIFYING

Gemini must inspect the actual Phase 1 implementation before making changes.

## Intended Agent Pipeline

```text
User Query
    ↓
Query Understanding Agent
    ↓
Retrieval Agent
    ↓
Verification Agent
    ↓
Reasoning Agent
    ↓
Risk Agent
    ↓
Contradiction Detection Agent
    ↓
Response Builder
    ↓
FinalResponse
```

## Frozen Components

The following are considered architecturally complete based on previous implementation and verification work:

```text
Part 1  — Query Understanding Agent
Part 2  — Retrieval Agent
Part 3  — Verification Agent
Part 4  — Reasoning Agent
Part 5  — Risk Agent
Part 6  — Contradiction Detection Agent
Part 7  — Agent Orchestrator
Part 8  — Response Builder
Part 9  — Observability Layer
Part 10 — Validation & Production Readiness
```

"Frozen" means do not refactor, redesign, replace, rename, move, or rebuild unless repository inspection demonstrates a concrete bug, security problem, integration incompatibility, requirement violation, or missing functionality.

## Part 11 Status

Part 11 has already been implemented according to previous verification work and must be inspected rather than automatically rebuilt.

Potential areas to verify:
- User Website,
- Management Website,
- Expert dashboard,
- Admin dashboard,
- server-side RBAC,
- expert-review workflow,
- multi-conversation support,
- frontend/backend integration,
- final deployment configuration,
- final security verification,
- LLM provider failover.

Only classify an item as missing after checking the actual repository.

# LLM PROVIDER FAILOVER IMPLEMENTATION

## Objective

Add a provider-resilience layer that automatically switches between:

```text
OpenRouter
Groq
```

without changing the agent architecture.

## Required Architecture

```text
Query / Reasoning / Risk / other LLM-dependent component
                         ↓
                Existing LLM Abstraction
                         ↓
                 LLM Provider Manager
                         ↓
              ┌──────────┴──────────┐
              ↓                     ↓
         OpenRouter             Groq
         Provider A             Provider B
              └──────────┬──────────┘
                         ↓
                  Validated output
```

## Critical Rule

Do NOT implement:

```text
QueryAgent → if OpenRouter fails → Groq
ReasoningAgent → if OpenRouter fails → Groq
RiskAgent → if OpenRouter fails → Groq
```

Instead, implement provider switching once behind the existing abstraction.

## Provider Manager Responsibilities

The provider manager should:
- select preferred provider,
- execute requests,
- classify errors,
- apply configured retries,
- switch providers when configured,
- enforce provider timeouts,
- maintain thread-safe provider health state,
- support cooldown/circuit-breaker behavior,
- optionally fail back to the preferred provider,
- emit non-sensitive telemetry,
- return one validated provider result.

## Failover Policy

Recommended default:

```text
Primary: OpenRouter
Secondary: Groq
```

But this must be configuration-driven.

### Failover-triggering errors

Potentially trigger failover for:
- rate limit,
- quota exhaustion,
- timeout,
- connection error,
- provider unavailable,
- transient 5xx.

Authentication/configuration failures should only fail over if explicitly configured. Otherwise, report a configuration error so a broken credential is not silently hidden.

## Request Integrity

If Provider A partially fails:

```text
Provider A
   ↓
partial/invalid response
```

do NOT combine it with Provider B.

Instead:

```text
Provider B
   ↓
repeat complete provider-neutral request
   ↓
validate full response
```

## Provider Configuration

Use configuration, not source-code constants.

Example logical block:

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

Do not copy placeholder values into production blindly.

Suggested secrets:

```text
OPENROUTER_API_KEY
GROQ_API_KEY
```

Reconcile names with the repository.

## Provider Testing

Mandatory:
- OpenRouter success,
- Groq success,
- OpenRouter timeout → Groq success,
- OpenRouter rate limit → Groq success,
- OpenRouter 5xx → Groq success,
- both providers unavailable,
- malformed response,
- invalid credentials,
- provider cooldown,
- provider recovery/failback,
- concurrent requests,
- no cross-conversation context leakage,
- no secret leakage,
- schema consistency across providers.

## Provider Acceptance Criteria

- Agents do not import provider SDKs directly.
- Switching is automatic.
- User does not select provider.
- Provider failure does not create a new conversation.
- Provider switch does not alter retrieval evidence.
- Provider switch does not bypass Verification/Risk/Contradiction stages.
- Provider telemetry is available to observability.
- Secrets are not logged.
- Both providers produce compatible validated output schemas.

# MULTI-CONVERSATION IMPLEMENTATION

## Objective

Replace any single-chat-only behavior with isolated conversation management.

Required:
- Conversation model,
- Message model,
- conversation ownership,
- New Chat,
- history,
- continue chat,
- conversation retrieval,
- optional rename/archive/delete,
- authorization.

## Rules

```text
User A
 ├── Conversation 1
 └── Conversation 2

User B
 └── Conversation 3
```

No context may cross these boundaries.

Provider switching must operate within the active conversation.

# IMPLEMENTATION STAGES

## Stage 0 — Repository Baseline

Inspect:
- Git branch,
- repository tree,
- Phase 1,
- Phase 2,
- backend,
- frontend,
- deployment,
- configuration,
- tests,
- existing documentation.

Classify requirements as:

```text
COMPLETED
PARTIALLY COMPLETE
MISSING
BROKEN
NEEDS VERIFICATION
```

Do not modify code during the first inspection unless required to safely run verification.

## Stage 1 — RAG Foundation Verification

Verify:
- ingestion,
- OCR/layout extraction,
- metadata,
- chunking,
- embeddings,
- ChromaDB,
- BM25,
- hybrid retrieval,
- source/page preservation.

## Stage 2 — Agent Pipeline Verification

Verify Parts 1–8 as frozen components.

Run their existing tests.

Do not rewrite them simply to change frameworks.

## Stage 3 — Orchestrator Verification

Verify:
- configured sequence,
- context propagation,
- retries,
- timeouts,
- execution status,
- metrics,
- failure handling.

## Stage 4 — Observability Verification

Verify:
- structured logs,
- metrics,
- tracing,
- audit,
- storage,
- health,
- alerts,
- privacy,
- provider-switch telemetry.

## Stage 5 — Validation Verification

Run:
- unit,
- integration,
- system,
- performance,
- stress,
- concurrency,
- security,
- regression,
- recovery,
- deployment.

## Stage 6 — LLM Provider Manager

Inspect the existing LLM abstraction first.

Then:
1. define/confirm provider-neutral interface,
2. create OpenRouter adapter if missing,
3. create Groq adapter if missing,
4. create Provider Manager,
5. add configuration,
6. add environment secret loading,
7. add failover policy,
8. add provider health/cooldown,
9. integrate with existing abstraction,
10. run all agent tests.

Do not modify every agent individually unless the existing architecture genuinely requires an interface migration.

## Stage 7 — FastAPI Integration

Verify/implement:
- `/api/v1`,
- authentication,
- RBAC,
- request validation,
- response validation,
- dependency injection,
- exception handling,
- CORS,
- health/readiness,
- OpenAPI.

FastAPI must call the existing Orchestrator.

## Stage 8 — User Website

Verify/implement:
- user login/register where required,
- user dashboard,
- query interface,
- New Chat,
- Chat History,
- conversation switching,
- results,
- citations,
- explanations,
- confidence,
- warnings,
- review status.

Do not expose Management navigation.

## Stage 9 — Management Website

Verify/implement a separate frontend application containing:

```text
Management
├── Expert
└── Admin
```

### Expert
- login,
- review queue,
- review detail,
- evidence,
- reasoning,
- risk,
- contradictions,
- approve,
- correct,
- comment.

### Admin
- login,
- dashboard,
- system health,
- metrics,
- errors,
- users,
- documents,
- audit.

Use server-side RBAC.

## Stage 10 — Feature-Based Review Workflow

Verify:

```text
User Website
 ↓
Query
 ↓
Agentic RAG
 ↓
Escalation
 ↓
ReviewTask
 ↓
User sees review status
```

And independently:

```text
Management Website
 ↓
Expert Login
 ↓
Review Queue
 ↓
ReviewTask
 ↓
Expert Decision
 ↓
Backend
 ↓
User Website
```

No user redirect to Management.

## Stage 11 — Deployment

Verify:
- User frontend,
- Management frontend,
- FastAPI,
- ChromaDB,
- persistent storage,
- networking,
- secrets,
- health checks,
- startup ordering.

## Stage 12 — Final Security

Test:
- invalid JWT,
- expired JWT,
- User → Expert endpoint,
- User → Admin endpoint,
- Expert → Admin endpoint,
- direct protected URLs,
- malformed inputs,
- oversized inputs,
- prompt injection,
- path traversal,
- upload security,
- secret exposure,
- provider secret exposure,
- stack-trace exposure,
- conversation ownership.

## Stage 13 — Final E2E

### User

```text
Login
 ↓
New Chat
 ↓
Ask insurance question
 ↓
Agentic RAG
 ↓
FinalResponse
 ↓
Citation + Explanation + Confidence
```

### Provider failover

```text
User Query
 ↓
OpenRouter
 ↓
Simulated failure
 ↓
Groq
 ↓
FinalResponse
```

### Expert

```text
Risk escalation
 ↓
ReviewTask
 ↓
Management Website
 ↓
Expert
 ↓
Approve/Correct
 ↓
User sees updated status
```

### Admin

```text
Management Website
 ↓
Admin
 ↓
Health/Metrics/Documents/Users/Audit
```

# FINAL DEFINITION OF DONE

## RAG
- [ ] documents ingest
- [ ] OCR works where required
- [ ] metadata preserved
- [ ] ChromaDB works
- [ ] BM25 works
- [ ] hybrid retrieval works
- [ ] citations preserve provenance

## Agents
- [ ] Query Agent
- [ ] Retrieval Agent
- [ ] Verification Agent
- [ ] Reasoning Agent
- [ ] Risk Agent
- [ ] Contradiction Agent
- [ ] Response Builder
- [ ] Orchestrator

## LLM Provider Resilience
- [ ] OpenRouter adapter
- [ ] Groq adapter
- [ ] provider-neutral abstraction
- [ ] automatic failover
- [ ] rate-limit handling
- [ ] timeout handling
- [ ] transient-error handling
- [ ] provider health/cooldown
- [ ] optional failback
- [ ] no provider logic in agents
- [ ] no provider selection in User UI
- [ ] no secrets in Git/logs
- [ ] provider failover tests

## Conversations
- [ ] multiple conversations
- [ ] New Chat
- [ ] chat history
- [ ] conversation ownership
- [ ] isolated messages
- [ ] follow-up context isolation
- [ ] provider switch preserves conversation

## Applications
- [ ] separate User Website
- [ ] separate Management Website
- [ ] Expert area
- [ ] Admin area
- [ ] server-side RBAC
- [ ] no User → Management navigation
- [ ] feature-based review connection

## Backend
- [ ] FastAPI
- [ ] authentication
- [ ] authorization
- [ ] API contracts
- [ ] exception handling
- [ ] health/readiness

## Quality
- [ ] unit tests
- [ ] integration tests
- [ ] system tests
- [ ] security tests
- [ ] performance tests
- [ ] recovery tests
- [ ] regression tests
- [ ] provider failover tests
- [ ] conversation isolation tests

## Deployment
- [ ] Docker
- [ ] environment configuration
- [ ] persistent storage
- [ ] health checks

# FINAL ARCHITECTURAL STATEMENT

> **The system consists of two frontend applications sharing a backend: a completely separate User Website and a Management Website. The Management Website contains role-specific Expert and Admin areas. The User Website never exposes or navigates to Management functionality. User-to-Expert/Admin interaction occurs only through actual product features and shared backend workflows, such as expert-review escalation. Server-side RBAC strictly separates USER, EXPERT and ADMIN permissions. The Agentic RAG pipeline remains orchestrated through the existing interfaces and Orchestrator. OpenRouter and Groq are provider implementations behind the LLM abstraction, with automatic background failover, provider health handling, and no provider-selection responsibility exposed to agents or normal users. Multi-conversation chat remains isolated by conversation_id and user ownership.**

# FINAL GIT CONTROL

Before meaningful changes:

```text
git status
git branch --show-current
git diff
```

After meaningful changes:

```text
pytest
git diff
git status
git add <intended files>
git commit
```

Never commit:
- `.env`,
- real API keys,
- access tokens,
- credentials,
- private certificates,
- generated secrets,
- unnecessary runtime logs/databases.

Use an example environment file for documentation, for example:

```text
.env.example
```

with placeholders only.
