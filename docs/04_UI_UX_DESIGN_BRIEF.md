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
- review status,
- multiple conversations.

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

Chat History       Main Chat Area

[New Chat]         Ask your insurance question

Conversation A     [....................................]
Conversation B     [ Ask ]

Conversation C     Suggested Questions
```

The conversation list must be visually separate from the main chat content.

### Multi-Conversation Requirements

Provide:
- New Chat,
- conversation list,
- active conversation indicator,
- recent conversations,
- rename where supported,
- archive/delete where supported.

Selecting a conversation loads only that conversation.

## 4. User Result

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

## 5. User Navigation

Keep it simple:
- Home
- Chat / Ask
- Chat History
- Profile/Settings if required.

Do not include:
- Expert Login
- Admin Login
- Management Login
- Expert Dashboard
- Admin Dashboard
- Management Dashboard.

## 6. Expert Review UX

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

## 7. Admin UX

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

## 8. Management Navigation

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

## 9. Citation UX

Citation cards should show, where available:
- document name,
- page,
- section/clause,
- supporting evidence snippet.

Do not display raw JSON.

## 10. Confidence UX

Use:
- High confidence
- Moderate confidence
- Low confidence
- Expert review required

Confidence must never be presented as legal certainty.

## 11. Warning UX

Example:

> **Expert Review Required**  
> The system detected insufficient confidence or elevated risk and has requested expert validation.

The warning should be clear but not alarmist.

## 12. Review Status UX

Possible states:
- No review required
- Review required
- Under expert review
- Expert approved
- Expert corrected

## 13. LLM Provider UX

The LLM provider mechanism is an infrastructure concern and must remain invisible to normal users.

Do not add:
- OpenRouter selector,
- Grok selector,
- model selector,
- API key field,
- "switch API" button,
- provider status controls for ordinary users.

If OpenRouter fails and Grok handles the request, the UI should continue normally.

Internal Management/Admin observability may show non-secret provider telemetry such as:
- provider currently preferred,
- provider switch count,
- provider availability,
- latency,
- failure category.

Do not expose API keys or raw provider error payloads.

## 14. Theme

Use a professional, restrained palette. Centralize theme values in MUI.

Semantic colors:
- primary
- success
- warning
- error
- neutral.

Do not hardcode colors throughout individual components.

## 15. Typography

Use Inter or an equivalent readable sans-serif.

Clear hierarchy:
- page title,
- section heading,
- subsection,
- body,
- metadata/caption.

## 16. Reusable Components

### User
- QueryInput
- ChatSidebar
- NewChatButton
- ConversationList
- ConversationItem
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
- ProviderHealthPanel

## 17. Responsiveness

User Website:
- desktop,
- tablet,
- mobile.

Management Website:
- desktop-first,
- tablet support,
- usable on smaller screens.

## 18. Accessibility

- sufficient contrast,
- keyboard navigation,
- semantic labels,
- readable font sizes,
- screen-reader status,
- no color-only meaning.

## 19. Critical UX Rule

The User Website must communicate expert review as a feature state.

Correct:
> “Your question requires expert review.”

Incorrect:
> “Open Expert Dashboard.”

The user does not need access to the Management Website to interact with the expert-review feature.

## 20. Critical Architecture Rule

> **Two websites, not one. User is separate. Expert + Admin share the Management Website.**

The shared backend connects them functionally, while frontend navigation remains separated.

## 21. Provider Resilience UX Rule

> **Automatic provider switching must be invisible to the normal user.**

OpenRouter and Grok are implementation providers, not user-facing product choices.
