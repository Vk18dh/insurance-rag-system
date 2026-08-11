# 01 — Product Requirements Document (PRD)

## 1. Product Identity

**Project Name:** AI-Driven Insurance Knowledge Assessment System

**Product Type:** Insurance-domain Agentic Retrieval-Augmented Generation (Agentic RAG) system.

**Primary Purpose:** Provide reliable, explainable, evidence-grounded answers to insurance questions using approved insurance documents, hybrid retrieval, multi-agent verification/reasoning, risk assessment, contradiction detection, citations, observability, human-in-the-loop expert review, and resilient LLM provider failover.

The system is an academic/prototype implementation and must prioritize correctness, traceability, explainability, security, modularity, maintainability, testability, and reliability.

## 2. Product Vision

Build a trustworthy insurance knowledge assistant that does not depend on an LLM's internal knowledge alone. The system retrieves evidence from approved insurance documents, verifies that evidence, reasons over verified evidence, assesses risk and contradictions, and returns a transparent response with supporting citations.

The LLM layer must also remain resilient. The system will support two configured LLM API providers:

- **OpenRouter**
- **Grok / xAI API**

The system must automatically switch providers in the background when the active provider becomes unavailable or encounters a configured failover condition. The user and individual agents must not need to know which provider handled a request.

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
- audit and observability,
- resilient dual-provider LLM execution.

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

The project has **two separate frontend applications**.

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
- Management Dashboard navigation,
- Expert Dashboard navigation,
- Admin Dashboard navigation,
- normal links to the Management Application.

The Management Application must not become part of the User Application's navigation.

### The only connection is feature/workflow based.

Example:

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

The applications communicate through backend feature workflows, not frontend navigation.

## 7. Multi-Conversation Chat Management

The User Website must support multiple independent chat conversations for each authenticated user.

The user must be able to:
- create a new conversation,
- view previous conversations,
- open an existing conversation,
- continue an existing conversation,
- rename a conversation where supported,
- delete/archive a conversation where supported,
- see recent conversations first,
- start an independent conversation using **New Chat**.

Every conversation has a unique `conversation_id`.

Messages from one conversation must never appear in another conversation. Conversation context must never leak between users.

The LLM provider failover layer must not change conversation ownership or mix context. A provider switch is an infrastructure event, not a new conversation.

## 8. LLM Provider Resilience Requirement

The system uses a provider abstraction with two configured providers:

```text
Provider A → OpenRouter
Provider B → Grok / xAI
```

Recommended default strategy:

```text
Primary: OpenRouter
Secondary: Grok / xAI
```

The actual primary provider must be configuration-driven.

### Automatic failover

For each LLM request:

```text
Agent
  ↓
LLM Abstraction
  ↓
Provider Manager
  ↓
Active Provider
  ↓
Success → return response
  │
  Failure matching configured failover rules
  ↓
Secondary Provider
  ↓
Retry the complete request
  ↓
Success → return response
```

Failover conditions may include:
- rate limit/quota response,
- provider unavailable,
- timeout,
- transient 5xx/provider error,
- connection failure,
- configured provider outage.

Authentication/configuration errors should only trigger failover when explicitly configured; otherwise they should be surfaced as configuration failures rather than silently hidden.

### Important rules

- Agents must never contain OpenRouter/Grok switching logic.
- Provider SDK/API calls must not be scattered across agents.
- The provider manager must sit behind the existing LLM abstraction.
- API keys must come only from environment/secrets.
- Never expose provider API keys to the frontend.
- Do not combine partial outputs from two providers.
- If failover occurs after a failed/partial request, repeat the complete structured request against the secondary provider.
- Provider selection and failover events must be observable without exposing secrets.
- A successful response must have one authoritative provider result.

## 9. Reliability / Provider Recovery

The provider manager should support configuration-driven:
- retry limits,
- provider cooldown,
- circuit-breaker state,
- failback to the preferred provider after recovery,
- per-provider timeout,
- provider health state.

A temporary failure in one provider must not permanently disable that provider unless configured.

The user should normally experience only the final response, not provider switching.

## 10. Must-Have Features

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
- expert escalation
- LLM provider failover.

### Observability
- structured logging
- metrics
- tracing
- audit records
- health monitoring
- alerts
- provider-switch telemetry.

### User Application
- query interface
- suggested queries
- results
- citations
- explanations
- confidence
- warnings
- review status
- multi-conversation history.

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

## 11. Success Criteria

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
- multi-conversation chat is isolated,
- OpenRouter/Grok failover works automatically,
- users do not need to manually select or switch providers,
- provider failures are observable,
- no normal User → Management navigation exists,
- feature-based review interaction works,
- observability and validation work,
- deployment is reproducible.

## 12. Out of Scope

Unless explicitly added later:
- policy purchase,
- claims settlement,
- underwriting decisions,
- legally binding advice,
- autonomous legal/financial decisions,
- automatic policy modification,
- unrestricted web search replacing the approved knowledge base,
- Streamlit as the final frontend,
- exposing provider selection controls to normal users.

## 13. Product Principle

> **Never present unsupported insurance information as established fact.**

When evidence is insufficient, contradictory, or high-risk, communicate uncertainty and use the configured escalation/fallback workflow.

A provider switch must never be treated as evidence, confidence, or business reasoning. It is only an infrastructure resilience mechanism.
