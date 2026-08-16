# 03 — App Flow & User Journey

## 1. Application Model

There are exactly **two frontend applications**:

### User Website
```text
https://app.example.com
```

### Management Website
```text
https://management.example.com
```

The URLs above are examples. Actual URLs are configuration values.

The Management Website contains:
- Expert functionality
- Admin functionality

There is no separate Expert website and no separate Admin website.

## 2. Critical Navigation Rule

The User Website and Management Website are separate applications.

The User Website must not contain:
- Expert Login,
- Admin Login,
- Management Login,
- Expert Dashboard links,
- Admin Dashboard links,
- Management Dashboard links.

There must be no normal frontend navigation:

```text
User Dashboard → Management Website
```

The only connection is through actual product features/workflows.

## 3. User Website Flow

```text
User Website
      ↓
User Login/Register (if required)
      ↓
User Dashboard
      ↓
Select existing conversation OR New Chat
      ↓
Enter Insurance Question
      ↓
Submit
      ↓
FastAPI
      ↓
Agent Orchestrator
      ↓
Query Agent
      ↓
Retrieval Agent
      ↓
Verification Agent
      ↓
Reasoning Agent
      ↓
Risk Agent
      ↓
Contradiction Agent
      ↓
Response Builder
      ↓
FinalResponse
      ↓
User Website
```

## 4. Multi-Conversation Flow

```text
User
 ↓
Chat History
 ├── Conversation A
 ├── Conversation B
 └── Conversation C
```

Selecting a conversation loads only its messages and context.

Selecting **New Chat** creates a new `conversation_id`.

A follow-up question inside a conversation uses only the allowed context for that conversation.

Provider failover does not create a new conversation.

Example:

```text
Conversation A
 ├── Question 1
 ├── Answer 1
 └── Follow-up

Conversation B
 ├── Question 2
 └── Answer 2
```

A response from Conversation A must never receive Conversation B's history.

## 5. LLM Provider Flow

The provider switching is invisible to the user:

```text
User Query
    ↓
Agent
    ↓
LLM Abstraction
    ↓
Provider Manager
    ↓
OpenRouter
    │
    ├── Success → continue
    │
    └── Configured failure
              ↓
           Groq
              ↓
           Success
              ↓
         Continue pipeline
```

The user should not see:
- API keys,
- internal provider errors,
- provider stack traces,
- provider switching controls.

A non-sensitive status may be logged internally, but the public response remains provider-neutral.

## 6. Provider Failure Scenarios

### Scenario A — OpenRouter succeeds

```text
OpenRouter
   ↓
Success
   ↓
Continue
```

### Scenario B — OpenRouter rate-limited

```text
OpenRouter
   ↓
Rate limit
   ↓
Provider Manager
   ↓
Groq
   ↓
Success
   ↓
Continue
```

### Scenario C — OpenRouter timeout

```text
OpenRouter
   ↓
Timeout
   ↓
Configured retry
   ↓
Still failing
   ↓
Groq
```

### Scenario D — Both fail

```text
OpenRouter
   ↓
Fail
   ↓
Groq
   ↓
Fail
   ↓
Configured graceful error/fallback
```

The system must not invent an answer because both providers failed.

## 7. User Result Screen

Display:
- answer,
- explanation,
- confidence,
- citations,
- document/page/section where available,
- warnings,
- expert-review status if applicable.

Never display raw exceptions, stack traces, prompts, secrets, or internal implementation details.

## 8. Expert Escalation Flow

```text
User Website
      ↓
User submits query
      ↓
Agentic RAG pipeline
      ↓
Risk / Confidence analysis
      ↓
Escalation required
      ↓
Backend creates ReviewTask
      ↓
User Website:
"Your query requires expert review."
```

The user remains on the User Website.

The system does **not** redirect the user to the Management Website.

## 9. Management Website

```text
management.example.com
        ↓
Management Login
        ↓
Authentication + RBAC
        ↓
      ┌───────────────┐
      │ Role          │
      └───────┬───────┘
              │
       ┌──────┴──────┐
       ▼             ▼
    EXPERT          ADMIN
       │             │
       ▼             ▼
 Expert Area      Admin Area
```

## 10. Expert Flow

```text
Management Website
      ↓
Expert Login
      ↓
EXPERT authorization
      ↓
Expert Dashboard
      ↓
Review Queue
      ↓
Select ReviewTask
      ↓
Inspect:
  - user query
  - generated answer
  - citations
  - retrieved evidence
  - reasoning
  - risk
  - contradictions
      ↓
Approve / Correct / Comment
      ↓
Submit
      ↓
Backend updates ReviewTask
```

## 11. Admin Flow

```text
Management Website
      ↓
Admin Login
      ↓
ADMIN authorization
      ↓
Admin Dashboard
      ↓
System Health
Performance
Errors
Audit
Documents
Users
```

## 12. Expert/Admin Separation

Although Expert and Admin share the Management Website:

```text
/management/expert/*
/management/admin/*
```

are conceptual protected areas.

Changing the URL must not bypass authorization.

Expert access:
- review workflows,
- evidence,
- reasoning/risk/contradiction.

Admin access:
- operational/system management.

Expert must not automatically inherit Admin privileges.

## 13. Feature-Based Connection Between Applications

The applications connect through shared backend features.

Example:

```text
USER WEBSITE
      ↓
Question
      ↓
Agentic RAG
      ↓
Escalation
      ↓
ReviewTask
```

Then independently:

```text
MANAGEMENT WEBSITE
      ↓
Expert Login
      ↓
Review Queue
      ↓
ReviewTask
      ↓
Expert Decision
```

Then:

```text
Backend
      ↓
ReviewTask updated
      ↓
USER WEBSITE
      ↓
Updated review status/result
```

This is the intended connection.

## 14. What Must NOT Happen

Incorrect:

```text
User Dashboard
 ├── Home
 ├── Ask Question
 ├── Expert Login   ❌
 └── Admin Login    ❌
```

Incorrect:

```text
User Dashboard
       ↓
[Open Management Dashboard] ❌
```

Correct:

```text
User Dashboard
 ├── Home
 ├── Ask Question
 ├── Chat History
 ├── Results
 └── Review Status
```

And independently:

```text
Management Website
 ├── Expert
 └── Admin
```

## 15. User States

### Empty
“No results yet. Ask an insurance question to begin.”

### Processing
- Understanding your question…
- Finding relevant evidence…
- Validating the information…
- Preparing your response…

### Low Confidence
“This response has low confidence.”

### Expert Review
“Your query requires expert review.”

### Expert Review Completed
“Expert review completed.”

## 16. Management States

### Expert Empty
“No queries currently require expert review.”

### Admin Empty
“No recent system alerts.”

### Unauthorized
“You are not authorized to access this area.”

Do not expose implementation details.

## 17. Security Redirect Rules

If an unauthorized person accesses the Management Website:
- authenticate,
- determine role,
- deny unauthorized area access.

The backend must return appropriate authorization failures even if a user manually enters a protected URL.

## 18. Provider-Neutral User Experience

The user interface must not provide:
- provider selection,
- API selection,
- model selection,
- API key configuration,
- manual failover controls.

The provider layer operates in the background.

If provider failover causes increased latency, the UI may show a generic processing state, but must not expose internal provider failure details.

## 19. Key Principle

> **Two websites, one shared backend, three roles, feature-based interaction only.**

The User Website is completely separate from the Management Website. Expert and Admin share the Management Website but remain strictly separated by server-side authorization.

The LLM provider layer is independent of this application separation and silently provides OpenRouter/Groq failover behind the existing LLM abstraction.
