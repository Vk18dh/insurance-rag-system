# 05 — Backend Schema, Data Contracts & Access Architecture

## 1. Purpose

Define logical data domains, typed contracts, role permissions, review workflows, API payloads, storage responsibilities, conversation management, and LLM provider resilience.

This is broader than a conventional SQL schema because the project uses Pydantic models, ChromaDB, BM25, agent result contracts and observability.

## 2. Identity

### User
Conceptual:
- id
- name
- email
- role
- status
- created_at
- updated_at

Roles:
```text
USER
EXPERT
ADMIN
```

## 3. Application Mapping

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

The application URL does not determine authority. Server-side RBAC determines authority.

## 4. Authorization

### USER
Can:
- submit queries,
- create conversations,
- view own conversations,
- view own results,
- view citations,
- view own review status.

Cannot:
- expert review queue,
- expert review actions,
- admin endpoints,
- system-wide audit/metrics unless explicitly authorized.

### EXPERT
Can:
- view authorized review tasks,
- inspect evidence,
- inspect reasoning/risk/contradiction,
- approve,
- correct,
- comment.

Cannot:
- perform Admin operations unless explicitly granted Admin permissions.

### ADMIN
Can:
- manage users/access,
- manage documents,
- view operational metrics,
- view authorized audit information,
- manage approved system operations.

## 5. Conversation Domain

### Conversation
Conceptual:
```text
conversation_id
user_id
title
status
created_at
updated_at
last_message_at
```

### Message
Conceptual:
```text
message_id
conversation_id
role
content
created_at
execution_id
```

Roles may include:
```text
USER
ASSISTANT
SYSTEM
```

### Conversation Rules

- Every conversation belongs to exactly one user.
- Every message belongs to exactly one conversation.
- Conversation history must be isolated.
- Authorization must verify ownership before returning conversation data.
- A new chat must generate a new conversation identifier.
- Provider failover must never generate a new conversation.
- Conversation context must not be shared across users.

The executable repository models are authoritative.

## 6. Query Domain

### Query
Conceptual:
```text
query_id
user_id
conversation_id
query_text
created_at
status
```

### QueryContext
Structured normalized query contract containing fields required by the Query Agent and downstream agents.

The executable Pydantic model in the repository is authoritative.

## 7. Knowledge Domain

### Document
```text
document_id
document_name
document_type
source
version
publication_date
ingestion_timestamp
status
```

### DocumentChunk
```text
chunk_id
document_id
text
page_number
section
clause
metadata
```

### Indexes
- ChromaDB → dense semantic retrieval.
- BM25 → sparse keyword retrieval.

## 8. Agent Contracts

### RetrievalResult
Preserves:
- retrieved chunks,
- scores/ranking,
- metadata,
- source document,
- page number,
- retrieval metrics,
- query context.

### VerificationResult
Represents:
- evidence validity,
- relevance,
- grounding,
- ambiguity,
- verification metadata.

### ReasoningResult
Represents:
- reasoning chain,
- reasoning steps,
- explanation,
- assumptions,
- metrics,
- verification source.

### RiskAssessmentResult
Represents:
- ambiguity,
- legal sensitivity,
- exclusion concerns,
- regulatory concerns,
- risk level,
- escalation recommendation.

### ContradictionResult
Contains:
- overall confidence,
- contradiction records,
- contradiction type/level,
- explanation,
- metrics.

### FinalResponse
Public response should contain:
```text
answer
explanation
citations[]
warnings[]
confidence
risk/review status
safe metadata
request/execution identifier where appropriate
```

Do not expose:
- raw prompts,
- API keys,
- stack traces,
- private audit data,
- internal implementation objects.

## 9. Citation

Conceptual:
```text
citation_id
document_id
document_name
page_number
section/clause
evidence_text
```

Citations must originate from retrieved/verified evidence.

## 10. Warning

Conceptual:
```text
type
severity
message
source/agent
```

Possible categories:
- low confidence,
- contradiction,
- legal sensitivity,
- expert review,
- insufficient evidence.

## 11. Human Review

### ReviewTask
```text
review_id
query_id
conversation_id
status
reason
created_at
assigned_expert_id
completed_at
```

States:
```text
PENDING
IN_REVIEW
APPROVED
CORRECTED
CANCELLED
```

### ExpertReview
```text
review_id
expert_id
decision
corrected_answer
comment
reviewed_at
```

## 12. Review Workflow

```text
Query
 ↓
Risk / Confidence
 ↓
Escalation
 ↓
ReviewTask
 ↓
Management Website / Expert Area
 ↓
Expert Review
 ↓
APPROVED or CORRECTED
 ↓
Backend stores outcome
 ↓
User Website retrieves updated status/result
```

This is the only intended User ↔ Management feature connection.

## 13. LLM Provider Domain

### Provider Configuration

Conceptual:

```text
provider_id
provider_name
enabled
priority
model
timeout_seconds
retry_limit
cooldown_seconds
```

Supported provider adapters:

```text
OPENROUTER
GROK_XAI
```

The actual provider names/enums in executable code must be reconciled with the repository.

### ProviderExecution

For observability/telemetry only:

```text
execution_id
provider
model
started_at
completed_at
latency_ms
status
failover_triggered
failure_category
```

Do not store API keys.

Do not expose provider credentials through API responses.

### Provider Failover State

Conceptual:
```text
AVAILABLE
DEGRADED
COOLDOWN
UNAVAILABLE
```

Provider state must be thread-safe.

### Provider Request Contract

The agent should submit one provider-neutral request to the existing LLM abstraction:

```text
request
  ↓
LLM Provider Manager
  ↓
OpenRouter OR Grok
  ↓
validated response
```

The request must contain the required prompt/messages and structured-output requirements without exposing provider-specific details to the agent.

## 14. Observability

### AuditRecord
Supports:
- hashed/masked query information,
- response metadata,
- citations,
- warnings,
- timestamp,
- execution identifier,
- permitted identity context.

### ExecutionMetrics
Supports:
- total latency,
- per-agent latency,
- retry count,
- timeout count,
- failure count,
- provider switch count.

### TraceContext
Supports:
```text
request_id
execution_id
span_id
parent_span_id
```

## 15. Storage

### Vector Store
ChromaDB.

### Sparse Index
BM25.

### Observability
Configured JSON/SQLite or the existing repository implementation.

### Relational Storage
Only introduce/use a relational database where required by authentication, conversation storage, review tasks or other approved application functionality.

Do not introduce unnecessary infrastructure.

## 16. API Access Matrix

| Resource | USER | EXPERT | ADMIN |
|---|---:|---:|---:|
| Submit query | Yes | Optional | Optional |
| Create conversation | Yes | — | Authorized |
| View own conversations | Yes | — | Authorized |
| View own result | Yes | — | Authorized |
| View citations | Yes | Yes | Authorized |
| Review queue | No | Yes | Authorized |
| Approve/correct | No | Yes | Authorized |
| System metrics | No | Limited | Yes |
| Provider health | No | No | Yes |
| Manage documents | No | No | Yes |
| Manage users | No | No | Yes |
| Audit | No | Limited | Yes |

## 17. Minimum API

```text
POST /api/v1/auth/login
POST /api/v1/query
GET  /api/v1/conversations
POST /api/v1/conversations
GET  /api/v1/conversations/{conversation_id}
DELETE /api/v1/conversations/{conversation_id}
GET  /api/v1/health
GET  /api/v1/ready
GET  /api/v1/version
```

Management APIs may include:
```text
GET  /api/v1/expert/reviews
GET  /api/v1/expert/reviews/{id}
POST /api/v1/expert/reviews/{id}/approve
POST /api/v1/expert/reviews/{id}/correct

GET  /api/v1/admin/metrics
GET  /api/v1/admin/errors
GET  /api/v1/admin/documents
POST /api/v1/admin/documents
GET  /api/v1/admin/provider-health
```

These are intended contracts and must be reconciled with the existing repository before implementation.

## 18. Security Rules

- server-side RBAC,
- validate all payloads,
- protect audit logs,
- never trust frontend role claims,
- no secrets in responses,
- sanitized errors,
- least privilege,
- protected document operations,
- secure file handling,
- API keys only in environment/secrets,
- no provider credentials in logs,
- conversation ownership checks on every conversation endpoint.

## 19. Schema Authority

The executable Pydantic models and tested API schemas in the repository are the final implementation authority. This document describes the intended domain contracts and must be reconciled before breaking schema changes.
