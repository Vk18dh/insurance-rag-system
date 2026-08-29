# 04 — UI/UX Design Brief

## 1. Design Objective

The system should feel:
- trustworthy,
- professional,
- clear,
- safe,
- explainable,
- appropriate for insurance/financial information.

Avoid:
- excessive animations,
- gaming-style dashboards,
- visual clutter,
- overly playful chatbot styling,
- exposing technical implementation details.

## 2. Two-Application UX Architecture

### User Website
Focused only on:
- asking insurance questions,
- understanding answers,
- citations,
- explanations,
- confidence,
- warnings,
- review status.

### Management Website
Focused on:
- Expert review,
- Admin operations.

Expert and Admin share the Management Website but have separate dashboards/permissions.

## 3. User Website

### Main layout

```text
Header
────────────────────────────
Brand
User Profile / Settings
────────────────────────────

Ask your insurance question

[....................................]
[ Ask ]

Suggested Questions
```

### Result

```text
Answer
────────────────────────────
Human-readable answer

Confidence
High / Moderate / Low

Explanation
────────────────────────────
Expandable explanation

Sources
────────────────────────────
Document | Page | Section
```

## 4. User Navigation

Keep it simple:
- Home
- Ask
- Results/History if required
- Profile/Settings if required

Do not include:
- Expert Login
- Admin Login
- Management Login
- Expert Dashboard
- Admin Dashboard.

## 5. Expert Review UX

Management Website → Expert area.

Recommended:

```text
Sidebar
  Review Queue
  Completed Reviews
  Profile

Main
  Query
  ─────────────────────
  Generated Answer
  ─────────────────────
  Confidence / Risk
  ─────────────────────
  Retrieved Evidence
  ─────────────────────
  Reasoning
  ─────────────────────
  Contradictions / Warnings
  ─────────────────────
  [Approve] [Correct] [Comment]
```

Evidence must be easy to inspect before approval.

## 6. Admin UX

Management Website → Admin area.

Recommended:
```text
Sidebar
  Dashboard
  Users
  Documents
  System Health
  Metrics
  Errors
  Audit

Main
  Metric Cards
  Charts
  Tables
  Alerts
```

Admin UI should prioritize operational information.

## 7. Management Navigation

The Management Website can have role-aware navigation.

Example:

```text
Expert:
Management
 └── Expert Dashboard
      ├── Review Queue
      └── Completed Reviews
```

```text
Admin:
Management
 └── Admin Dashboard
      ├── System
      ├── Users
      ├── Documents
      ├── Metrics
      └── Audit
```

Do not expose unauthorized menu items merely as a security measure; backend RBAC remains authoritative.

## 8. Citation UX

Citation cards should show, where available:
- document name,
- page,
- section/clause,
- supporting evidence snippet.

Do not display raw JSON.

## 9. Confidence UX

Use:
- High confidence
- Moderate confidence
- Low confidence
- Expert review required

Confidence must never be presented as legal certainty.

## 10. Warning UX

Example:

> **Expert Review Required**  
> The system detected insufficient confidence or elevated risk and has requested expert validation.

The warning should be clear but not alarmist.

## 11. Review Status UX

Possible states:
- No review required
- Review required
- Under expert review
- Expert approved
- Expert corrected

## 12. Theme

Use a professional, restrained palette. Centralize theme values in MUI.

Semantic colors:
- primary
- success
- warning
- error
- neutral.

Do not hardcode colors throughout individual components.

## 13. Typography

Use Inter or an equivalent readable sans-serif.

Clear hierarchy:
- page title,
- section heading,
- subsection,
- body,
- metadata/caption.

## 14. Reusable Components

### User
- QueryInput
- SuggestedQuery
- AnswerCard
- ConfidenceIndicator
- CitationCard
- ExplanationPanel
- WarningBanner
- ReviewStatus
- EvidenceCard

### Expert
- ReviewQueue
- ReviewDetail
- EvidenceViewer
- ReasoningViewer
- RiskIndicator
- ContradictionCard
- ReviewActionPanel

### Admin
- MetricCard
- DataTable
- HealthIndicator
- AlertPanel
- AuditTable
- DocumentManager

## 15. Responsiveness

User Website:
- desktop,
- tablet,
- mobile.

Management Website:
- desktop-first,
- tablet support,
- usable on smaller screens.

## 16. Accessibility

- sufficient contrast,
- keyboard navigation,
- semantic labels,
- readable font sizes,
- screen-reader status,
- no color-only meaning.

## 17. Critical UX Rule

The User Website must communicate expert review as a feature state.

Correct:
> “Your question requires expert review.”

Incorrect:
> “Open Expert Dashboard.”

The user does not need access to the Management Website to interact with the expert-review feature.

## 18. Critical Architecture Rule

> **Two websites, not one. User is separate. Expert + Admin share the Management Website.**

The shared backend connects them functionally, while frontend navigation remains separated.
## Multi-Conversation Chat UI

The User Website must provide a persistent conversation history interface.

### Desktop Layout

```text
┌──────────────────────────────────────────────────────────────┐
│ Insurance AI                                                 │
├────────────────┬─────────────────────────────────────────────┤
│ + New Chat     │ Current Conversation                        │
│                │                                             │
│ Recent Chats   │ User: What are the benefits of Jeevan       │
│                │ Shagun?                                     │
│ Jeevan Shagun  │                                             │
│ Bima Jyoti     │ AI: According to the policy...              │
│ Digi Term      │                                             │
│                │ [Citations]                                 │
│                │ [Confidence]                                │
│                │                                             │
│                │ Ask a follow-up...                          │
└────────────────┴─────────────────────────────────────────────┘