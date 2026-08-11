# 01 — Product Requirements Document (PRD)

## 1. Product Identity

**Project Name:** AI-Driven Insurance Knowledge Assessment System

**Product Type:** Insurance-domain Agentic Retrieval-Augmented Generation (Agentic RAG) system.

**Primary Purpose:** Provide reliable, explainable, evidence-grounded answers to insurance questions using approved insurance documents, hybrid retrieval, multi-agent verification/reasoning, risk assessment, contradiction detection, citations, observability, and human-in-the-loop expert review.

## 2. Product Vision

Build a trustworthy insurance knowledge assistant that does not depend on an LLM's internal knowledge alone. The system retrieves evidence from approved insurance documents, verifies that evidence, reasons over verified evidence, assesses risk and contradictions, and returns a transparent response with supporting citations.

The system is an academic/prototype implementation and must prioritize correctness, traceability, explainability, security, modularity, maintainability, and testability.

## 3. Problem Statement

Insurance policies and regulatory documents are lengthy, technical, and difficult to search manually. A conventional chatbot can produce plausible but unsupported answers. In insurance, unsupported information can create financial, compliance, or legal risk.

The system addresses this using:
- document ingestion and OCR,
- metadata and clause-aware processing,
- hybrid sparse + dense retrieval,
- evidence verification,
- multi-agent reasoning,
- risk assessment,
- contradiction detection,
- confidence-aware expert escalation,
- citations and explanations,
- audit and observability.

## 4. Users and Roles

### 4.1 User

The normal end user asks natural-language insurance questions and receives:
- grounded answers,
- explanations,
- confidence information,
- citations,
- warnings when appropriate,
- expert-review status when a query is escalated.

### 4.2 Expert

An expert reviewer handles escalated/flagged queries. The expert can:
- review the generated response,
- inspect retrieved evidence,
- inspect reasoning/risk/contradiction information,
- approve a response,
- modify/correct a response,
- add comments/annotations.

### 4.3 Administrator

An administrator manages system-level operations, including:
- users/access,
- insurance documents,
- system monitoring,
- performance,
- errors,
- audit/operational information.

## 5. Critical Application Architecture

The project has **two separate frontend applications**:

### Application A — User Application

Example configurable URL:

```text
https://app.example.com
```

Purpose:
- user authentication,
- user dashboard,
- insurance query,
- results,
- citations,
- explanations,
- confidence,
- review status.

### Application B — Management Application

Example configurable URL:

```text
https://management.example.com
```

Purpose:
- Expert functionality,
- Administrator functionality.

The Management Application contains role-specific areas:

```text
Management Application
├── Expert Dashboard
└── Admin Dashboard
```

Expert and Admin are **not separate websites**.

## 6. Critical Separation Rule

The User Application and Management Application are separate sites.

The User Application must **not** contain:
- Expert Login,
- Admin Login,
- Expert Dashboard navigation,
- Admin Dashboard navigation,
- Management Dashboard navigation,
- normal links to the Management Application.

The Management Application must not become part of the User Application's navigation.

### The only connection is feature/workflow based.

For example:

```text
User Application
      ↓
User asks a question
      ↓
Agentic RAG
      ↓
Low confidence / high risk
      ↓
ReviewTask created
      ↓
User sees "Expert review required"
```

The user remains on the User Application.

Separately:

```text
Management Application
      ↓
Expert Login
      ↓
Expert Dashboard
      ↓
Review Queue
      ↓
Expert reviews the ReviewTask
      ↓
Approve / Correct / Comment
```

Then:

```text
Expert decision
      ↓
Shared backend
      ↓
ReviewTask updated
      ↓
User Application can display updated review status/result
```

The applications communicate through backend feature workflows, not frontend navigation.

## 7. Role Isolation

The Management Application uses server-side RBAC.

```text
USER   → User Application
EXPERT → Management Application → Expert area
ADMIN  → Management Application → Admin area
```

An Expert cannot gain Admin access simply by changing a URL.

An Admin may have broader permissions according to the authorization policy.

Frontend route protection is for user experience only. Backend authorization is authoritative.

## 8. Must-Have Features

### Knowledge Processing
- PDF/document ingestion
- OCR/layout extraction where required
- metadata extraction
- chunking
- embedding generation
- dense vector indexing
- BM25 sparse indexing
- hybrid retrieval
- source/page metadata preservation.

### Query and Answering
- natural-language query
- query understanding
- intent identification
- query normalization
- retrieval
- grounded response
- citations
- explanation
- confidence information.

### Multi-Agent Validation
- Query Understanding Agent
- Retrieval Agent
- Verification Agent
- Reasoning Agent
- Risk Agent
- Contradiction Detection Agent
- Response Builder
- Agent Orchestrator.

### Reliability
- evidence grounding
- verification
- contradiction detection
- risk classification
- confidence assessment
- expert escalation.

### Observability
- structured logging
- metrics
- tracing
- audit records
- health monitoring
- alerts.

### User Application
- query interface
- suggested queries
- results
- citations
- explanations
- confidence
- warnings
- review status.

### Management Application — Expert
- review queue
- evidence inspection
- reasoning inspection
- risk/contradiction inspection
- approval
- correction
- comments.

### Management Application — Admin
- system metrics
- performance analytics
- error cases
- document management
- user/access management
- operational monitoring.

## 9. User Stories

### User
- Ask an insurance question in natural language.
- See where an answer came from.
- Understand the explanation.
- Understand confidence/uncertainty.
- Know when expert review is required.
- See the result/status after expert review.

### Expert
- See escalated queries.
- Inspect evidence before deciding.
- Inspect reasoning/risk/contradiction information.
- Approve or correct responses.
- Add comments.

### Administrator
- Manage users/access.
- Manage documents.
- Monitor performance and health.
- Inspect authorized operational/audit information.

## 10. Out of Scope

Unless explicitly added later:
- policy purchase,
- claims settlement,
- underwriting decisions,
- legally binding advice,
- autonomous legal/financial decisions,
- automatic policy modification,
- unrestricted web search replacing the approved knowledge base,
- Streamlit as the final frontend.

## 11. Non-Functional Requirements

### Performance
The project requirements target approximately 5–10 seconds for normal queries and support multiple simultaneous users.

### Security
- authentication,
- role-based authorization,
- protected audit data,
- secrets through environment/configuration,
- sanitized errors,
- role isolation.

### Reliability
- graceful LLM/API failure handling,
- retrieval failure handling,
- fallback behavior,
- expert escalation for risky/low-confidence outputs.

### Explainability
- evidence-grounded answer,
- citations,
- human-readable explanation,
- confidence/risk information.

## 12. Success Criteria

The product is successful when:
- approved documents can be ingested,
- hybrid retrieval works,
- the complete agent pipeline executes,
- answers contain supporting citations,
- verification/reasoning/risk/contradiction operate,
- low-confidence cases can be escalated,
- experts can process escalated cases,
- administrators can manage/monitor the system,
- User and Management applications remain separate,
- the Management Application provides role-specific Expert/Admin areas,
- no normal User → Management navigation exists,
- feature-based review interaction works,
- observability and validation work,
- deployment is reproducible.

## 13. Product Principle

> **Never present unsupported insurance information as established fact.**

When evidence is insufficient, contradictory, or high-risk, communicate uncertainty and use the configured escalation/fallback workflow.
