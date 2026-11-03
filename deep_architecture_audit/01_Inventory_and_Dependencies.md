# PART 1 — COMPLETE REPOSITORY INVENTORY

```text
majorcode/
├── backend/
│   ├── app/
│   │   ├── api/          # Internal modular routers (planned)
│   │   ├── auth/         # JWT generation and validation logic
│   │   ├── config/       # Pydantic settings loading (.env parsing)
│   │   ├── core/         # Exception handlers and core types
│   │   ├── db/           # SQLAlchemy session and connection config
│   │   ├── dependencies/ # FastAPI dependency injection (e.g. get_db, get_current_user)
│   │   ├── middleware/   # Request/Response logging middleware
│   │   ├── models/       # SQLAlchemy database models (PostgreSQL tables)
│   │   ├── repositories/ # Data Access Layer for PostgreSQL
│   │   ├── routers/      # FastAPI API route handlers (entrypoints)
│   │   ├── schemas/      # Pydantic validation models for API IO
│   │   ├── services/     # Business logic wrapping repositories
│   │   └── tests/        # Pytest backend tests
│   └── requirements.txt  # (Empty in current view, dependencies in root)
├── data/
│   └── raw_llm.json      # Ingestion/Evaluation raw data sample
├── frontend/
│   ├── app/              # Next.js App Router (User Chat Interface)
│   ├── components/       # Shadcn UI and custom React components
│   ├── lib/              # API clients and utility functions
│   └── package.json      # Frontend UI dependencies (React, Tailwind)
├── management/
│   ├── app/              # Next.js App Router (Admin/Expert Dashboard)
│   ├── components/       # Admin UI components
│   └── package.json      # Management UI dependencies
├── phase2/
│   ├── agents/           # The 7 core AI Agents (Verification, Reasoning, etc.)
│   ├── config/           # Phase2 Settings (Model selection, thresholds)
│   ├── exceptions/       # Custom exceptions for AI failures (e.g., QueryProcessingException)
│   ├── interfaces/       # Abstract Base Classes defining Agent/Orchestrator contracts
│   ├── logging/          # Custom logger configurations
│   ├── logs/             # Generated execution logs
│   ├── models/           # Pydantic internal AI models (e.g., VerificationReport, ReasoningChain)
│   ├── observability/    # Metrics tracking (time, tokens, errors)
│   ├── orchestrator/     # Core workflow engine (AgentOrchestrator, TimeoutManager)
│   ├── prompts/          # Hardcoded prompt templates
│   ├── services/         # LLM Provider Adapters (OpenRouter, Groq, Ollama)
│   ├── tests/            # AI Agent evaluation and unit tests
│   ├── utils/            # Text normalization helpers
│   └── validation/       # Evaluation frameworks and test runners
├── scratch/              # Temporary debugging and execution scripts
├── scripts/              # Evaluation data generation and benchmark scripts
├── docker-compose.yml    # Infrastructure orchestrator mapping
└── requirements.txt      # Root Python dependencies for backend and phase2
```

### Folder Roles:
- **`backend/`**: Runtime code for the FastAPI REST application handling HTTP, Auth, and Database access.
- **`phase2/`**: Runtime AI code implementing the Agentic RAG logic. Completely decoupled from HTTP to allow running as a standalone engine.
- **`frontend/`**: Runtime user-facing web application.
- **`management/`**: Runtime expert-facing web application for HITL (Review Tasks).
- **`data/`**: Data folder for documents/PDFs and raw RAG outputs.

# PART 2 — FILE-BY-FILE ARCHITECTURE (CORE)

**FILE:** `backend/app/main.py`
**PURPOSE:** The FastAPI application entrypoint.
**USED BY:** Uvicorn (ASGI server via Docker).
**DEPENDS ON:** FastAPI, CORS middleware, all routers in `backend/app/routers/`.
**PROCESSING:** Loads settings, initializes database tables, injects dev seed users (`admin`, `expert`), attaches CORS, registers all `/api/v1` routes.
**WHY IT EXISTS:** Required bootstrapping file for any FastAPI application.

**FILE:** `backend/app/routers/query.py`
**PURPOSE:** Handles the `/api/v1/query` endpoint where users submit questions.
**USED BY:** Next.js frontend chat interface.
**DEPENDS ON:** `AgentOrchestrator` (from phase2), `ConversationService`, `GuardrailService`, `ReviewService`.
**INPUT:** `QueryRequest` (User's query string).
**PROCESSING:** Runs input guardrails. Creates/loads Conversation in DB. Calls `AgentOrchestrator` to execute the multi-agent AI flow. If an exception triggers (e.g., low confidence), creates a `ReviewTask` in PostgreSQL. Returns the AI response.
**OUTPUT:** `QueryResponse` containing the text, confidence, and source citations.
**WHY IT EXISTS:** Bridges the HTTP REST layer with the internal AI logic layer.

**FILE:** `phase2/orchestrator/orchestrator.py`
**PURPOSE:** The central nervous system of the Agentic RAG pipeline.
**USED BY:** `backend/app/routers/query.py`.
**DEPENDS ON:** All 7 agents in `phase2/agents/`, `TimeoutManager`, `ContextManager`.
**INPUT:** Normalized user query.
**PROCESSING:** Instantiates all agents. Executes them sequentially (Query -> Retrieval -> Verification -> Reasoning -> Risk -> Contradict -> Build). Passes state (retrieved chunks, logic chains) between them.
**OUTPUT:** `OrchestrationResult` containing final markdown and citations.
**WHY IT EXISTS:** Eliminates monolithic "God classes" by enforcing a strict step-by-step verified workflow.

**FILE:** `phase2/services/llm_provider_manager.py`
**PURPOSE:** Manages fallback between AI providers.
**USED BY:** All AI agents to generate text.
**DEPENDS ON:** `GroqProvider`, `OpenRouterProvider`, `LocalLLMProvider`.
**INPUT:** Prompt, System Instruction.
**PROCESSING:** Tries OpenRouter. If fails/429/500, tries Groq. If fails, tries Local Ollama. Uses cooldown periods to avoid spamming dead APIs.
**OUTPUT:** Raw LLM string response.
**WHY IT EXISTS:** Guarantees 100% uptime even if a cloud API goes down.

# PART 3 — COMPLETE DEPENDENCY MAP

`Next.js Frontend (Browser)`
  ↓ HTTP POST `/api/v1/query`
`FastAPI Router (backend/app/routers/query.py)`
  ↓ Instantiates and calls
`AgentOrchestrator (phase2/orchestrator/orchestrator.py)`
  ↓ Calls (in sequence)
  1. `QueryUnderstandingAgent`
  2. `RetrievalAgent`
     → Queries `ChromaDB` (via sentence-transformers)
     → Queries `BM25` (via rank-bm25)
  3. `VerificationAgent`
  4. `ReasoningAgent`
  5. `RiskAssessmentAgent`
  6. `ContradictionAgent`
  7. `ResponseBuilder`
  ↓ All Agents call
`LLMProviderManager (phase2/services/llm_provider_manager.py)`
  ↓ Calls
`External HTTP/REST (Groq API, OpenRouter API) OR Local HTTP (Ollama)`
  ↓ Results bubble back up
`FastAPI Router`
  ↓ Calls
`ReviewService & ConversationService (backend/app/services/)`
  ↓ Calls
`PostgreSQL (via SQLAlchemy)`
  ↓ Returns JSON
`Next.js Frontend`

# PART 4 — LIBRARY-BY-LIBRARY EXPLANATION

### Python Libraries (Backend/AI)
| Library | Used In | Purpose | Simple Explanation |
|---|---|---|---|
| `fastapi` | Backend | Web framework | Builds the API endpoints. |
| `sqlalchemy` | Backend | ORM | Translates Python code into SQL queries for PostgreSQL. |
| `psycopg2-binary` | Backend | DB Driver | The actual connector that talks to PostgreSQL. |
| `pydantic` | Backend / Phase2 | Data validation | Ensures JSON inputs/outputs have the correct fields. |
| `pyjwt` | Backend | Authentication | Creates and reads secure login tokens. |
| `chromadb` | Phase2 | Vector Database | Stores meaning as numbers and searches by similarity. |
| `sentence-transformers` | Phase2 | AI Embedding | The AI library that converts text into the numbers for ChromaDB. |
| `rank-bm25` | Phase2 | Keyword Search | Finds exact matching words in the text. |
| `unstructured` | Phase2 | PDF Parsing | Extracts raw text out of PDF files. |

### JS/TS Libraries (Frontend/Management)
| Library | Used In | Purpose | Simple Explanation |
|---|---|---|---|
| `next` | Frontend | Web Framework | Builds the website and handles routing. |
| `react` | Frontend | UI Library | Builds interactive buttons and layouts. |
| `tailwindcss` | Frontend | Styling | Makes the website look good with simple CSS classes. |
| `shadcn` | Frontend | UI Components | Pre-built beautiful components (buttons, dialogs). |
| `lucide-react` | Frontend | Icons | Provides the small graphical icons on the site. |
| `react-markdown` | Frontend | Text Formatting | Converts the AI's raw `**bold**` text into actual bold HTML. |

# PART 35 — FINAL VERIFIED INVENTORY (TABLE 1: IMPORTANT FOLDERS)
| Folder | Type | Description | IMPLEMENTED |
|---|---|---|---|
| `backend/app/models` | Database | PostgreSQL tables (SQLAlchemy) | IMPLEMENTED |
| `backend/app/routers` | API | HTTP endpoint controllers | IMPLEMENTED |
| `phase2/agents` | AI | The 7-agent pipeline logic | IMPLEMENTED |
| `phase2/services` | AI | LLM provider failover adapters | IMPLEMENTED |
| `frontend/app` | UI | Main user chat interface | IMPLEMENTED |
| `management/app` | UI | Expert HITL review dashboard | IMPLEMENTED |
