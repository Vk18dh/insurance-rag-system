# 06 — Implementation Plan

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
---

# PROJECT STATUS BASELINE

> **Important:** This section is a project-status reference and is intentionally not part of the numbered implementation stages below. The numbered stages remain unchanged.

## Current Implementation Status

Before implementing anything, Gemini must inspect the actual repository and compare it against this baseline.

### Completed Phase 2 Components

| Part | Component | Current Status | Default Action |
|---|---|---|---|
| Part 1 | Query Understanding Agent | ✅ COMPLETE | Do not rebuild |
| Part 2 | Retrieval Agent | ✅ COMPLETE | Do not rebuild |
| Part 3 | Verification Agent | ✅ COMPLETE | Do not rebuild |
| Part 4 | Reasoning Agent | ✅ COMPLETE | Do not rebuild |
| Part 5 | Risk Agent | ✅ COMPLETE | Do not rebuild |
| Part 6 | Contradiction Detection Agent | ✅ COMPLETE | Do not rebuild |
| Part 7 | Agent Orchestrator | ✅ COMPLETE | Do not rebuild |
| Part 8 | Response Builder | ✅ COMPLETE | Do not rebuild |
| Part 9 | Observability Layer | ✅ COMPLETE | Do not rebuild |
| Part 10 | Validation & Production Readiness | ✅ COMPLETE | Do not rebuild |
| Part 11 | FastAPI / Frontend / Deployment | ⚠️ IMPLEMENTED — VERIFY | Inspect before modifying |

### Phase 1 Status

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

**Current status:** ✅ EXISTING IMPLEMENTATION — VERIFY BEFORE MODIFYING

Gemini must inspect the actual Phase 1 implementation before making any changes.

Do not rewrite Phase 1 simply to introduce a different framework, library, or implementation style.

### Overall Agent Pipeline

The intended execution pipeline is:

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

The following components are considered architecturally complete based on the previous implementation and verification work:

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

### Meaning of Frozen

"Frozen" does not mean that bugs can never be fixed.

It means:

> Do not refactor, redesign, replace, rename, move, or rebuild a completed component unless repository inspection demonstrates a concrete bug, security problem, integration incompatibility, requirement violation, or missing functionality.

If a modification is required:

1. Identify the exact problem.
2. Explain why the existing implementation is insufficient.
3. Identify affected interfaces/contracts.
4. Make the smallest necessary change.
5. Run relevant tests.
6. Run backward-compatibility tests.
7. Re-audit the affected component.
8. Document the change.

## Part 11 — Current Status

Part 11 has already been implemented according to the previous project verification work.

The previous implementation included:

- FastAPI backend,
- API adapter,
- authentication,
- dependency injection,
- exception handling,
- Docker integration,
- ChromaDB connectivity,
- BM25 integration,
- frontend integration,
- end-to-end pipeline integration.

However, the actual repository is the final authority.

Therefore:

> **Part 11 must be inspected and verified before additional implementation is performed.**

Do not automatically rebuild Part 11.

Potential remaining areas include:

- User Website,
- Management Website,
- Expert dashboard,
- Admin dashboard,
- server-side RBAC,
- expert-review workflow,
- User ↔ Management feature interaction,
- frontend/backend integration,
- final deployment configuration,
- final security verification.

Only mark an item as remaining after confirming that it is actually missing or incomplete in the repository.

## Final Frontend Architecture

The project must contain exactly **two frontend applications**.

### Application 1 — User Website

Example configurable URL:

```text
https://app.example.com
```

The actual URL must be configuration-driven.

The User Website contains:

- User authentication,
- User dashboard,
- insurance query interface,
- query history where required,
- results,
- citations,
- explanations,
- confidence,
- warnings,
- expert-review status.

The User Website must NOT contain:

- Expert Login,
- Admin Login,
- Management Login,
- Expert Dashboard link,
- Admin Dashboard link,
- Management Dashboard navigation.

### Application 2 — Management Website

Example configurable URL:

```text
https://management.example.com
```

The actual URL must be configuration-driven.

The Management Website contains:

```text
Management Website
├── Expert Area
└── Admin Area
```

There are **not three websites**.

The architecture is:

```text
2 Frontend Applications
        +
3 Roles
```

Roles:

```text
USER
EXPERT
ADMIN
```

## User ↔ Management Interaction Rule

This is a mandatory architecture rule.

The User Website and Management Website are separate applications.

They may communicate through the shared backend when a product feature requires it.

They must NOT be connected through normal frontend navigation.

### Correct Example

```text
USER WEBSITE
      ↓
User submits insurance question
      ↓
Agentic RAG
      ↓
Low confidence / high risk
      ↓
ReviewTask created
      ↓
User sees:
"Expert review required"
```

The user remains on the User Website.

The user is NOT redirected to the Management Website.

Separately:

```text
MANAGEMENT WEBSITE
      ↓
Expert Login
      ↓
Expert Dashboard
      ↓
Review Queue
      ↓
ReviewTask
      ↓
Inspect Evidence
      ↓
Inspect Reasoning
      ↓
Inspect Risk
      ↓
Inspect Contradictions
      ↓
Approve / Correct / Comment
```

The backend updates the ReviewTask.

The User Website can later retrieve:

```text
Review Required
       ↓
Under Review
       ↓
Expert Approved
       OR
Expert Corrected
```

Therefore:

> **The User Website and Management Website are connected through feature workflows, not through frontend navigation.**

## Expert + Admin Architecture

Expert and Admin share the same Management Website.

```text
Management Website
        ↓
      Login
        ↓
Authentication + RBAC
        ↓
    ┌───────┴───────┐
    ↓               ↓
 EXPERT           ADMIN
    ↓               ↓
Expert Area      Admin Area
```

### Expert Area

- Review Queue
- Review Details
- User Query
- Generated Response
- Retrieved Evidence
- Citations
- Reasoning Chain
- Risk Assessment
- Contradiction Results
- Approve
- Correct
- Comment
- Review History

### Admin Area

- System Dashboard
- System Health
- Performance Metrics
- Errors
- Users
- Documents
- Audit/Operational Information
- Authorized system management functions

### Security Rule

Changing a frontend URL must never grant additional permissions.

For example:

```text
/management/expert
```

must not be convertible to:

```text
/management/admin
```

to obtain Admin privileges.

Server-side RBAC is authoritative.

## Repository Reconciliation Rule

The documentation describes the intended architecture.

The actual repository determines what is already implemented.

Before making changes Gemini must inspect:

```text
Repository
Git branch
Phase 1
Phase 2
Backend
Frontend
Configuration
Tests
Docker
Documentation
```

Then classify every major requirement as:

```text
COMPLETED
PARTIALLY COMPLETE
MISSING
BROKEN
NEEDS VERIFICATION
```

Gemini must not assume that a feature is missing merely because it is described in the documentation.

## Change-Control Rule

For every proposed modification to an existing completed component, Gemini must provide:

```text
Component:
Current implementation:
Problem found:
Evidence:
Why change is required:
Files affected:
Compatibility impact:
Tests required:
```

Only after this analysis should the change be implemented.

## Final Architecture Statement

> **The system consists of two frontend applications sharing a backend: a completely separate User Website and a Management Website. The Management Website contains role-specific Expert and Admin areas. The User Website never exposes or navigates to Management functionality. User-to-Expert/Admin interaction occurs only through actual product features and shared backend workflows, such as expert-review escalation. Server-side RBAC strictly separates USER, EXPERT and ADMIN permissions. Existing verified Agentic RAG components remain frozen unless a genuine defect, security issue, integration problem, or requirement gap is demonstrated.**

## 3. Phase 0 — Repository Baseline

Inspect:
- Git branch
- repository tree
- Phase 1
- Phase 2
- backend
- frontend
- deployment
- configuration
- tests
- existing documentation.

Done when actual state and genuine gaps are documented without unnecessary code changes.

## 4. Phase 1 — RAG Foundation

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

Done when approved documents can be indexed and relevant evidence retrieved with provenance.

## 5. Phase 2 — Query Agent

Verify:
- normalization,
- intent,
- entities,
- ambiguity,
- QueryContext,
- LLM abstraction,
- fallback,
- configuration.

Done when structured QueryContext is reliably produced.

## 6. Phase 3 — Retrieval Agent

Verify:
- Phase 1 adapter,
- hybrid retrieval,
- ranking,
- deduplication,
- RetrievalResult,
- configuration,
- exception handling.

Done when evidence reaches downstream agents without duplicate retrieval logic.

## 7. Phase 4 — Verification Agent

Verify:
- evidence relevance,
- validity,
- grounding,
- ambiguity,
- VerificationResult,
- exception handling.

Done when verified evidence is available to reasoning.

## 8. Phase 5 — Reasoning Agent

Verify:
- clause interpretation,
- evidence linking,
- reasoning chain,
- assumptions,
- explanation,
- metrics,
- externalized prompts.

Done when reasoning is explainable and based on verified evidence.

## 9. Phase 6 — Risk Agent

Verify:
- ambiguity,
- legal sensitivity,
- exclusions,
- regulatory concerns,
- escalation,
- unified LLM analysis,
- configured thresholds.

Done when RiskAssessmentResult identifies risk and escalation appropriately.

## 10. Phase 7 — Contradiction Agent

Verify:
- policy context,
- evidence alignment,
- classification,
- explanation,
- resolution routing,
- ContradictionResult.

Done when contradictions are explicitly represented.

## 11. Phase 8 — Response Builder

Verify:
- answer,
- explanation,
- citations,
- warnings,
- confidence,
- fallback,
- safe serialization.

Done when FinalResponse is stable and user-safe.

## 12. Phase 9 — Agent Orchestrator

Verify:
- configured sequence,
- context propagation,
- retries,
- timeouts,
- execution status,
- metrics,
- failure handling.

Expected logical sequence:
```text
Query
 ↓
Retrieval
 ↓
Verification
 ↓
Reasoning
 ↓
Risk
 ↓
Contradiction
 ↓
Response
```

Done when the complete sequence executes through one orchestration boundary.

## 13. Phase 10 — Observability

Verify:
- structured logs,
- metrics,
- tracing,
- audit,
- storage,
- health,
- alerts,
- privacy,
- thread safety.

Done when observability is non-invasive and can be disabled without breaking the core pipeline.

## 14. Phase 11 — Validation

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

Done when the validation suite generates reports and enforces configured quality gates.

## 15. Phase 12 — FastAPI Integration

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

FastAPI calls the existing Orchestrator.

It must not duplicate:
- retrieval,
- reasoning,
- risk,
- contradiction,
- response-generation business logic.

Done when a REST query reaches FinalResponse.

## 16. Phase 13 — User Website

Build/verify the separate User Website.

Required:
- user login/register where required,
- user dashboard,
- insurance query,
- suggested queries,
- results,
- citations,
- explanation,
- confidence,
- warnings,
- review status,
- loading/error states.

### Prohibited
The User Website must not contain:
- Expert Login,
- Admin Login,
- Management Login,
- Expert Dashboard link,
- Admin Dashboard link,
- Management Dashboard navigation.

Done when a user can complete the full query journey without entering the Management Website.

## 17. Phase 14 — Management Website

Build/verify a **separate Management Website**.

Example configurable URL:
```text
https://management.example.com
```

It contains two protected role areas:

```text
Management Website
├── Expert Area
└── Admin Area
```

### Expert Area
Required:
- Expert Login
- review queue
- review detail
- evidence
- reasoning
- risk
- contradictions
- approve
- correct
- comment.

### Admin Area
Required:
- Admin Login
- system dashboard
- health
- metrics
- errors
- users
- documents
- audit/operational data.

### Important
Expert and Admin are on the same website, but their permissions are separate.

Changing:
```text
/management/expert
```
to:
```text
/management/admin
```
must not grant access.

Done when authorized Experts and Admins can perform their respective workflows.

## 18. Phase 15 — Feature-Based User ↔ Management Connection

This phase is critical.

### Correct architecture

```text
USER WEBSITE
     ↓
Query
     ↓
Agentic RAG
     ↓
Low confidence/high risk
     ↓
ReviewTask created
     ↓
User sees review status
```

Separately:

```text
MANAGEMENT WEBSITE
     ↓
Expert Login
     ↓
Expert Review Queue
     ↓
ReviewTask
     ↓
Approve/Correct
     ↓
Backend updates ReviewTask
```

Then:

```text
Backend
     ↓
Updated status/result
     ↓
USER WEBSITE
```

### Prohibited

```text
User Website
     ↓
Expert Dashboard ❌
```

```text
User Website
     ↓
Admin Dashboard ❌
```

```text
User Website
     ↓
Management Login ❌
```

The connection exists only because a product feature requires shared backend state.

## 19. Phase 16 — Deployment

Verify:
- User frontend container/build,
- Management frontend container/build,
- FastAPI,
- ChromaDB/vector service,
- persistent storage,
- networking,
- environment variables,
- health checks,
- startup ordering.

Done when deployment starts reliably.

## 20. Phase 17 — End-to-End User Test

```text
Insurance PDF
 ↓
Ingestion
 ↓
ChromaDB + BM25
 ↓
User Website
 ↓
FastAPI
 ↓
Agent Orchestrator
 ↓
Query
 ↓
Retrieval
 ↓
Verification
 ↓
Reasoning
 ↓
Risk
 ↓
Contradiction
 ↓
Response Builder
 ↓
FinalResponse
 ↓
User Website
```

Verify:
- answer,
- citations,
- explanation,
- confidence,
- warnings,
- metadata.

## 21. Phase 18 — End-to-End Expert Review Test

```text
User Website
 ↓
Query
 ↓
Risk/Confidence
 ↓
Escalation
 ↓
ReviewTask
 ↓
User sees:
"Expert review required"
```

Then independently:

```text
Management Website
 ↓
Expert Login
 ↓
Expert Area
 ↓
Review Queue
 ↓
ReviewTask
 ↓
Evidence + Reasoning + Risk + Contradictions
 ↓
Approve / Correct / Comment
 ↓
Backend
 ↓
User Website
 ↓
Updated review status/result
```

This must work without navigating the user into the Management Website.

## 22. Phase 19 — Admin Test

```text
Management Website
 ↓
Admin Login
 ↓
Admin Area
 ↓
System Health
 ↓
Metrics
 ↓
Documents
 ↓
Users
 ↓
Audit
```

Verify that an Expert cannot access Admin functionality without explicit authorization.

## 23. Phase 20 — Security Verification

Test:
- unauthorized access,
- invalid/expired JWT,
- User → Expert endpoint,
- User → Admin endpoint,
- Expert → Admin endpoint,
- malformed input,
- oversized input,
- prompt injection,
- path traversal,
- unsafe upload,
- secret exposure,
- stack-trace exposure,
- direct protected URL access.

## 24. Phase 21 — Final Documentation

Maintain:
- README,
- six docs in `docs/`,
- API documentation,
- deployment instructions,
- environment example,
- architecture diagrams,
- testing instructions.

## 25. Final Definition of Done

The project is complete only when:

### RAG
- [ ] documents ingest
- [ ] OCR works where required
- [ ] metadata is preserved
- [ ] ChromaDB works
- [ ] BM25 works
- [ ] hybrid retrieval works
- [ ] citations preserve provenance

### Agents
- [ ] Query Agent
- [ ] Retrieval Agent
- [ ] Verification Agent
- [ ] Reasoning Agent
- [ ] Risk Agent
- [ ] Contradiction Agent
- [ ] Response Builder
- [ ] Orchestrator

### Reliability
- [ ] verification
- [ ] confidence
- [ ] risk
- [ ] contradiction
- [ ] expert escalation
- [ ] fallback
- [ ] observability

### Applications
- [ ] separate User Website
- [ ] separate Management Website
- [ ] Expert area inside Management Website
- [ ] Admin area inside Management Website
- [ ] server-side RBAC
- [ ] no User → Management navigation
- [ ] feature-based review connection

### Backend
- [ ] FastAPI
- [ ] authentication
- [ ] authorization
- [ ] API contracts
- [ ] exception handling
- [ ] health/readiness

### Quality
- [ ] unit tests
- [ ] integration tests
- [ ] system tests
- [ ] security tests
- [ ] performance tests
- [ ] recovery tests
- [ ] regression tests

### Deployment
- [ ] Docker
- [ ] environment configuration
- [ ] persistent storage
- [ ] health checks

## 26. Final Architectural Statement

> **The system consists of two frontend applications sharing a backend: a completely separate User Website and a Management Website. The Management Website contains role-specific Expert and Admin areas. The User Website never exposes or navigates to Management functionality. User-to-Expert/Admin interaction occurs only through actual product features and shared backend workflows, such as expert-review escalation. Server-side RBAC strictly separates USER, EXPERT and ADMIN permissions.**

## 27. Change-Control Rule

After a phase is marked complete:
- do not rebuild it casually,
- do not change contracts without impact analysis,
- add tests before changing behavior,
- document breaking changes,
- create a Git checkpoint before significant changes.

The six documents are the planning/source-of-truth layer; executable code and tests remain the final authority for actual implementation behavior.

---

# PROJECT COMPLETION CONTROL

This section is a final control reference and does not introduce another implementation phase.

## Current Baseline

The implementation history identifies the following as completed and requiring verification rather than automatic rebuilding:

- Part 1 — Query Understanding Agent
- Part 2 — Retrieval Agent
- Part 3 — Verification Agent
- Part 4 — Reasoning Agent
- Part 5 — Risk Agent
- Part 6 — Contradiction Detection Agent
- Part 7 — Agent Orchestrator
- Part 8 — Response Builder
- Part 9 — Observability Layer
- Part 10 — Validation & Production Readiness

Part 11 is implemented according to the previous project verification work, but the repository must be inspected before declaring the final application complete.

## Mandatory Repository-First Workflow

Before every significant implementation:

```text
READ THE SIX DOCS
       ↓
INSPECT THE REPOSITORY
       ↓
CHECK EXISTING IMPLEMENTATION
       ↓
CHECK TESTS
       ↓
IDENTIFY THE ACTUAL GAP
       ↓
MAKE THE SMALLEST REQUIRED CHANGE
       ↓
RUN TESTS
       ↓
RUN INTEGRATION/E2E CHECK
       ↓
AUDIT THE CHANGE
       ↓
REPORT RESULTS
```

Do not rebuild a component merely because it appears in the plan.

## Final Product Definition

The final product has:

```text
                    SHARED BACKEND
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ▼                             ▼
   USER WEBSITE                 MANAGEMENT WEBSITE
   USER role                    EXPERT + ADMIN roles
          │                             │
          └──── feature/backend ────────┘
                interaction only
```

There are exactly two frontend applications:

1. User Website.
2. Management Website.

Expert and Admin are separate role areas within the Management Website.

The User Website does not expose Management navigation or Management login.

User ↔ Expert/Admin interaction happens through backend features such as review escalation and status/result updates.

## Final Git Rule

Before and after meaningful changes:

```text
git status
git diff
pytest
git add <intended files>
git commit
```

Do not commit secrets, real credentials, `.env` files containing secrets, generated runtime databases, caches, or unnecessary logs.

The six documents in `docs/` form the planning and requirements layer. The executable repository, tests, and verified runtime behavior remain the final authority for actual implementation state.
