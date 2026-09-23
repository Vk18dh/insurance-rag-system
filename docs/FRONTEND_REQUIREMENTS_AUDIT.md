# Frontend Requirements Audit

## 1. Existing Frontend Stack
- **Framework:** Next.js 16 (App Router)
- **Language:** TypeScript
- **Build system:** pnpm, Vite (tests), PostCSS
- **Routing:** Next.js App Router (`app/` directory)
- **State Management:** SWR for data fetching, React local state
- **Styling System:** Tailwind CSS v4, shadcn/ui, clsx, tailwind-merge
- **UI Components:** base-ui, lucide-react, framer-motion (motion), react-markdown
- **Current Pages:** `/login`, `/register`, `/`, `/c/[id]`
- **Verdict:** The stack is highly modern and perfectly suitable for building out a 3D interface (e.g. adding Three.js/React Three Fiber later). No need to replace it.

## 2. Existing Backend APIs
- **Query**: `POST /api/v1/query` (Requires Auth)
- **Conversations**: 
  - `POST /api/v1/conversations/` (Create, Requires Auth)
  - `GET /api/v1/conversations/` (List, Requires Auth)
  - `GET /api/v1/conversations/{id}` (Read, Requires Auth)
  - `GET /api/v1/conversations/{id}/messages` (Read history, Requires Auth)
- **Auth**:
  - `POST /api/v1/auth/login` (Public, OAuth2 form data structure)
  - `POST /api/v1/auth/register` (Public, JSON body)

## 3. Mandatory Functional Requirements
1. User registration: REQUIRED
2. User login/logout: REQUIRED
3. Authentication/session handling: REQUIRED
4. User profile: NOT CURRENTLY SUPPORTED
5. AI insurance question answering: REQUIRED
6. New conversation: REQUIRED
7. Conversation history: REQUIRED
8. Continue previous conversation: REQUIRED
9. Delete/clear conversation: NOT CURRENTLY SUPPORTED
10. Streaming response: NOT CURRENTLY SUPPORTED (Backend is strictly REST/blocking)
11. Loading/progress state: REQUIRED
12. Error handling: REQUIRED
13. Provider failure handling: REQUIRED (Handles HTTP 503 from backend)
14. Safe refusal handling: REQUIRED (Handles `is_safe=False` or fallback text)
15. HITL/review-related user messaging: OPTIONAL (Backend exposes `review_task_id` and `review_status`)
16. Citations/source display: REQUIRED
17. Retrieved source/document viewing: REQUIRED (Snippets are available)
18. Feedback on answers: NOT CURRENTLY SUPPORTED
19. Suggested questions: OPTIONAL (Frontend only feature)
20. Policy/product browsing: NOT CURRENTLY SUPPORTED
21. Policy details: NOT CURRENTLY SUPPORTED
22. Search: NOT CURRENTLY SUPPORTED
23. Logout/session expiration: REQUIRED
24. Responsive/mobile behavior: REQUIRED

## 4. AI Assistant Requirements
- **Submission**: `POST /api/v1/query` with JSON `{ "query": string, "conversation_id": optional string }`
- **Response Structure**:
  ```json
  {
    "query_id": "string",
    "message_id": "string",
    "conversation_id": "string",
    "final_answer": "string",
    "confidence_score": 0.95,
    "is_safe": true,
    "sources": [
      {
        "document": "string",
        "page": 1,
        "content_snippet": "string",
        "confidence": 1.0
      }
    ],
    "execution_time_ms": 1500,
    "review_task_id": "optional string",
    "review_status": "optional string"
  }
  ```
- **State Machine**:
  `IDLE` → `SUBMITTING` → `PROCESSING` (Long polling/waiting) → `ANSWER_RECEIVED` → `SHOW_CITATIONS`

  **Failure Branches**:
  - `PROCESSING` → `SAFE_REFUSAL` (System handles ambiguity/lack of constraints natively returning safe text, confidence 0.0, is_safe True)
  - `PROCESSING` → `GUARDRAIL_BLOCKED` (Returns is_safe=False and block reason in final_answer)
  - `PROCESSING` → `PROVIDER_FAILURE` (HTTP 503 LLM service unavailable)
  - `PROCESSING` → `NETWORK_ERROR` / `TIMEOUT`

## 5. Authentication Requirements
- **Login Flow**: Submits `username` and `password` as `FormData` to `/api/v1/auth/login`. Receives `{ access_token, token_type }`.
- **Registration Flow**: Submits JSON `{ username, password, role }` to `/api/v1/auth/register`.
- **Session/Storage**: Needs secure HTTP-only cookies ideally, or at minimum secure Bearer token context management.
- **Errors**: `401 Unauthorized` handling is required site-wide to trigger automatic logout and redirect to `/login`.

## 6. Conversation Requirements
- **Sidebar/History**: Needs a list of conversations fetched from `GET /api/v1/conversations/`.
- **Active Context**: Needs to fetch historical messages via `GET /api/v1/conversations/{id}/messages` and render them chronologically.
- **Context passing**: Subsequent queries must include the `conversation_id` in the `POST /api/v1/query` payload to map to the same AgentOrchestrator context.

## 7. Citation Requirements
Backend returns `document`, `page`, `content_snippet`, and `confidence`.
- **UX Recommendation**: Show small superscript numbers inline (or append a "Sources" section at the bottom of the answer).
- **Expandable Source**: Users can click the citation to reveal a popup/accordion showing the exact `content_snippet` and the `document` name + `page`.
- Do NOT expose internal UUIDs directly to the user UI unless necessary for React keys.

## 8. Error & Failure States
- **HTTP 503 Service Unavailable**: Provider is out of credits or rate-limited. Frontend must show a graceful fallback: "AI providers are currently unavailable. Please try again later."
- **HTTP 401 Unauthorized**: Redirect to login.
- **HTTP 422 Unprocessable Entity**: Form validation failure.
- **Timeout/Latency**: The query takes several seconds (seen 5-10s in logs). A robust loading skeleton or animated processing state is mandatory.

## 9. HITL/User Review States
- The backend exposes `review_task_id` and `review_status` (e.g. `PENDING`) in the `QueryResponse`.
- **UX Recommendation**: If `review_task_id` is present, display a small, non-intrusive badge or tooltip on the message saying "This answer is pending expert review due to low confidence."

## 10. Existing Frontend Components
- `login`, `register`, `(chat)` app router structure already exists.
- `shadcn` components available (likely Buttons, Inputs, Cards).
- `react-markdown` setup for rendering AI responses.
- Can heavily reuse the existing layout structure, but styles will need an overhaul for the 3D phase.

## 11. Required Pages
- **Login** - REQUIRED (Auth)
- **Register** - REQUIRED (Auth)
- **AI Assistant (Chat)** - REQUIRED (Backend dependency: query, conversations)
- **Landing/Home** - OPTIONAL (Marketing/Redirect to App)
- **System unavailable / 404** - REQUIRED
*(Not Required: Profile, Policy Details, Search, Settings - no backend support).*

## 12. 3D Opportunities
- **A. Functional UI**: Chat input, message history, authentication forms, sidebar navigation (must remain 2D HTML/CSS for accessibility/typing speed).
- **B. 3D Experience**: 
  - An interactive 3D avatar/assistant reacting to the "Processing" state.
  - A 3D node-graph visualization of the returned `citations` and how they connect to the query.
- **C. Decorative 3D**: Ambient animated background (WebGL) that shifts colors based on system confidence.
*Risk*: Do not make text readable inside WebGL.

## 13. UX Requirements
- **Waiting for AI**: The AI takes ~5-8 seconds. We need a multi-stage loading animation (e.g., "Analyzing query...", "Retrieving documents...", "Synthesizing answer...").
- **Receiving refusal**: Soft color coding (yellow/orange instead of harsh red) for safe refusals.
- **Screen readers**: Notify dynamically when the AI response finishes loading (using `aria-live`).

## 14. Accessibility Requirements
- All forms must be fully keyboard navigable.
- Focus states must be explicitly styled.
- 3D features must respect `prefers-reduced-motion` and disable themselves gracefully.

## 15. Mobile Requirements
- 3D elements should be severely downgraded or removed entirely on mobile to save battery and memory.
- Touch targets must be at least 44x44px (chat submit button, citation expanders).
- The layout must compress to a single column, with the sidebar becoming a hamburger menu.

## 16. Performance Requirements
- Bundle size: WebGL (Three.js/R3F) libraries must be lazy-loaded using Next.js `next/dynamic` so the initial TTI (Time to Interactive) remains fast.
- The chat text renderer should not be blocked by 3D asset initialization.

## 17. Premium UX Features
- **HIGH VALUE**: Suggested follow-up questions (Frontend UI logic).
- **HIGH VALUE**: "Show Source" interaction with a slide-out drawer reading the `content_snippet`.
- **MEDIUM VALUE**: Multi-stage animated loading state.
- **OPTIONAL**: "Explain Simply" (not natively supported by backend, would require frontend logic).

## 18. Recommended Frontend Architecture
- **API/Data Layer**: SWR for fetching conversation history. Fetch API for submitting queries.
- **State Management**: React `useState`/`useContext` for active conversation and user session.
- **3D Components**: `next/dynamic` wrapper around R3F Canvas components.
- **Server-Independent UI**: Forms, Buttons, Skeletons.

## 19. Functional vs 3D Components
- **Functional**: Chat feed, Input bar, Sidebar, Login form, Citation accordion.
- **3D**: Background ambient visualizer, AI "thinking" avatar, Data retrieval particle animation.

## 20. Implementation Priority

**MUST HAVE BEFORE DEMO**
- Login / Register forms
- Basic Chat interface (submit query, see response)
- Loading skeleton (due to long latency)
- Markdown rendering
- Error handling for API timeouts / 503s

**SHOULD HAVE**
- Conversation History / Sidebar
- Citation snippet viewer
- HITL "pending review" badge

**NICE TO HAVE**
- WebGL / 3D ambient background
- 3D AI Assistant visualizer
- Suggested follow-up questions

| Feature | Backend Support | Frontend Required | 3D Opportunity | Priority |
|---|---|---|---|---|
| Auth Flow | Yes | Yes | None | Must Have |
| Query Submission | Yes | Yes | Ambient/Avatar | Must Have |
| Markdown Responses | Yes | Yes | None | Must Have |
| Loading States | Yes | Yes | Animated 3D loader | Must Have |
| Provider Fallback UI | Yes | Yes | None | Must Have |
| Citation Viewer | Yes | Yes | Node Graph | Should Have |
| Conv History | Yes | Yes | None | Should Have |
| 3D Background | N/A | No | Full WebGL | Nice to Have |
