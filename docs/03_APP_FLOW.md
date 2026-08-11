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

## 4. User Result Screen

Display:
- answer,
- explanation,
- confidence,
- citations,
- document/page/section where available,
- warnings,
- expert-review status if applicable.

Never display raw exceptions, stack traces, prompts, secrets, or internal implementation details.

## 5. Expert Escalation Flow

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

## 6. Management Website

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

## 7. Expert Flow

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

## 8. Admin Flow

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

## 9. Expert/Admin Separation

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
- reasoning,
- approval/correction.

Admin access:
- operational/system management.

Expert must not automatically inherit Admin privileges.

## 10. Feature-Based Connection Between Applications

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

## 11. What Must NOT Happen

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
 ├── Results
 └── Review Status
```

And independently:

```text
Management Website
 ├── Expert
 └── Admin
```

## 12. User States

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

## 13. Management States

### Expert Empty
“No queries currently require expert review.”

### Admin Empty
“No recent system alerts.”

### Unauthorized
“You are not authorized to access this area.”

Do not expose implementation details.

## 14. Security Redirect Rules

If an unauthorized person accesses the Management Website:
- authenticate,
- determine role,
- deny unauthorized area access.

The backend must return appropriate authorization failures even if a user manually enters a protected URL.

## 15. Key Principle

> **Two websites, one shared backend, three roles, feature-based interaction only.**

The User Website is completely separate from the Management Website. Expert and Admin share the Management Website but remain strictly separated by server-side authorization.
