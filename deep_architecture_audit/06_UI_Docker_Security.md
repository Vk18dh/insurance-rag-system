# PART 22 — SECURITY ARCHITECTURE
**Authentication & Authorization:**
- Uses JWT (JSON Web Tokens). Handled in `backend/app/auth/`.
- `get_current_user` decodes the token and attaches the `TokenPayload` to the request context.
- **RBAC (Role-Based Access Control):** The user database table (`users`) has a `role` Enum (`USER`, `EXPERT`, `ADMIN`).
- Endpoints like `/api/v1/expert/tasks` strictly require the `EXPERT` role. Normal users attempting access get HTTP 403.

**Data Security:**
- Passwords are cryptographically hashed using `bcrypt` before database insertion.
- All database interaction uses SQLAlchemy's ORM, mitigating SQL Injection completely.

**Audit Logging:**
- `AuditService` logs every query, guardrail block, and task escalation to PostgreSQL for compliance tracking.
- Prompts are "hashed" before logging (`query_hash`) to ensure privacy if required, while maintaining trackability.

# PART 23 — FRONTEND CODE ARCHITECTURE (User UI)
**Tech Stack:** Next.js (App Router), React, Tailwind, `lucide-react`.
**Location:** `frontend/app/`
**Routes:**
- `/` - Landing / Main Chat Interface (rendered by `(chat)/page.tsx`)
- `/login` - User Authentication
- `/register` - Account creation
**Components:**
- Uses Shadcn UI for standard elements (buttons, inputs).
- **State Management:** Standard React `useState` / `useEffect`. The chat UI holds `messages` array in state.
- **Rendering Citations:** Uses `react-markdown`. The backend returns a `sources` array in the JSON response, which the frontend maps into clickable badge components at the bottom of the AI response.

# PART 24 — MANAGEMENT FRONTEND (Expert UI)
**Location:** `management/app/`
**Routes:**
- `/` - Login redirect or dashboard.
- `/expert` - Dashboard for Insurance Experts.
- `/admin` - System admin dashboard.
**Features:**
- **Review Queue:** The `expert` route fetches PENDING `ReviewTasks` from the backend API.
- **Resolution UI:** Displays the User's Query, the AI's internal thought process (Reasoning, Risk, Evidence), and provides an input box for the expert to write the final definitive answer. When submitted, calls the `/resolve` endpoint.

# PART 25 — DOCKER ARCHITECTURE
The system uses Docker Compose (`docker-compose.yml`) to orchestrate 6 independent services, ensuring it runs identically on any OS.

| Service | Image/Dockerfile | Port | Purpose | Dependency |
|---|---|---|---|---|
| `backend` | Python 3.11 (FastAPI) | 8000 | Core API and AI Execution | `postgres`, `chromadb`, `ollama` |
| `frontend` | Node.js (Next.js) | 3000 | User Web UI | `backend` |
| `management`| Node.js (Next.js) | 3001 | Expert Web UI | `backend` |
| `chromadb` | `chromadb/chroma` | 8001 | Vector Database | None |
| `postgres` | `postgres:15-alpine` | 5432 | App Database | None |
| `ollama` | `ollama/ollama` | 11434 | Local AI Runtime | None |

**Volumes:** Uses named volumes (`chroma_data`, `pg_data`, `ollama_data`) to ensure data persists even if the containers are destroyed and recreated.

# PART 26 — CONFIGURATION
Configuration is managed via environment variables mapped to Pydantic Settings classes (`backend/app/config/settings.py` and `phase2/config/`).

**Security:**
- `BACKEND_JWT_SECRET`: Used to sign tokens. Must be kept secret.
- `BACKEND_ACCESS_TOKEN_EXPIRE_MINUTES`: Default 1440 (24h).

**Database:**
- `DATABASE_URL`: `postgresql+psycopg2://user:password@postgres:5432/majorcode`. Points the backend container to the postgres container.
- `CHROMA_PORT`: Defaults to 8001.

**Phase 2 / AI Configs:**
- `PHASE2__LLM__LOCAL_MODEL`: Configured to `qwen2.5:3b`.
- `PHASE2__RETRIEVAL__TOP_K`: Configures how many chunks are retrieved.
- `PHASE2__RETRIEVAL__SIMILARITY_THRESHOLD`: Math cutoff for ChromaDB.
- `PHASE2__SECURITY__MAX_PAYLOAD_LENGTH`: Prevents massive text dumps (buffer overflow/injection).
